from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from scenariolens.ingest.waymo_motion import (
    inspect_waymo_motion_slice,
    load_waymo_motion,
    waymo_motion_slice_ready,
)
from scenariolens.io import load_scenarios
from scenariolens.report import ranked_scores, score_reasons
from scenariolens.schema import Scenario, ScenarioScore

FAILURE_STUDY_FORMAT = "scenariolens.failure_study.v1"
FAILURE_STUDY_INPUT_FORMATS = ("native", "scenariolens-json")


@dataclass(frozen=True)
class FailureStudyResult:
    """Files produced by a public-safe baseline failure study."""

    ready: bool
    scenario_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_failure_study(
    input_path: str | Path,
    output_dir: str | Path,
    max_scenarios: int | None = 100,
    top: int = 10,
    min_tag_count: int = 1,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> FailureStudyResult:
    """Generate aggregate baseline-failure analysis for a scenario slice."""

    if input_format not in FAILURE_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported failure-study input format: "
            f"{input_format}. Expected one of: {', '.join(FAILURE_STUDY_INPUT_FORMATS)}"
        )

    source = Path(input_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    ready, preflight, scenarios = _load_input_scenarios(
        source=source,
        input_format=input_format,
        max_scenarios=max_scenarios,
    )
    scores = ranked_scores(scenarios) if ready else ()
    payload = failure_study_payload(
        input_path=source,
        output_dir=target,
        input_format=input_format,
        max_scenarios=max_scenarios,
        top=top,
        min_tag_count=min_tag_count,
        ready=ready,
        preflight=preflight,
        scores=scores,
    )
    report = failure_study_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return FailureStudyResult(
        ready=ready,
        scenario_count=len(scenarios),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def failure_study_payload(
    input_path: Path,
    output_dir: Path,
    input_format: str,
    max_scenarios: int | None,
    top: int,
    min_tag_count: int,
    ready: bool,
    preflight: dict[str, object] | None,
    scores: tuple[ScenarioScore, ...],
) -> dict[str, object]:
    """Return a deterministic public-safe failure-study manifest."""

    scores_by_failure = _scores_by_baseline_failure(scores)
    return {
        "format": FAILURE_STUDY_FORMAT,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios": max_scenarios,
        "top": top,
        "min_tag_count": min_tag_count,
        "ready": ready,
        "scenario_count": len(scores),
        "preflight": preflight or {},
        "aggregate": _aggregate(scores),
        "tag_failures": _tag_failures(scores, min_tag_count=min_tag_count),
        "component_failures": _component_failures(scores),
        "quadrants": _quadrants(scores),
        "hardest_scenarios": [
            _scenario_row(score, rank)
            for rank, score in enumerate(scores_by_failure[:top], start=1)
        ],
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
    }


def failure_study_markdown(payload: dict[str, object]) -> str:
    """Return Markdown report from a failure-study payload."""

    aggregate = _required_mapping(payload, "aggregate")
    baseline = _required_mapping(aggregate, "baseline")
    score_summary = _required_mapping(aggregate, "score")
    tag_failures = _required_list(payload, "tag_failures")
    component_failures = _required_list(payload, "component_failures")
    quadrants = _required_list(payload, "quadrants")
    hardest = _required_list(payload, "hardest_scenarios")

    lines = [
        "# ScenarioLens Real-Slice Failure Study",
        "",
        "This report summarizes public-safe aggregate findings from ScenarioLens "
        "baseline failure analysis. Raw Waymo files and per-scenario derived "
        "outputs remain outside git.",
        "",
        "## Run Scope",
        "",
        f"- Input: `{payload['input_path']}`",
        f"- Input format: `{payload['input_format']}`",
        f"- Ready for analysis: {payload['ready']}",
        f"- Scenarios analyzed: {payload['scenario_count']}",
        f"- Max scenarios requested: {payload['max_scenarios']}",
        "- Raw scenario data committed: no",
        "",
        "## Executive Findings",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Score min / median / mean / max | {_range_text(score_summary)} |",
        f"| Evaluated baseline targets | {baseline['evaluated_target_total']} |",
        f"| Target-weighted mean baseline ADE | {_float_text(baseline['mean_ade_m'])} m |",
        f"| Target-weighted mean baseline FDE | {_float_text(baseline['mean_fde_m'])} m |",
        f"| Max baseline FDE | {_float_text(baseline['max_fde_m'])} m |",
        f"| Weighted miss rate | {_percent_text(baseline['weighted_miss_rate'])} |",
        f"| Mean baseline failure score | {_float_text(baseline['mean_failure_score'])} |",
        "| Interaction/FDE correlation | "
        f"{_optional_float_text(baseline.get('score_fde_correlation'))} |",
        "",
    ]

    if not payload["ready"]:
        lines.extend(
            [
                "## Next Action",
                "",
                "Fix the input path or use an ingestable ScenarioLens JSON file, "
                "then rerun `failure-study`.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Failure By Tag",
            "",
            "| Tag | Scenarios | Targets | Mean ADE | Mean FDE | Max FDE | "
            "Miss Rate | Mean Score |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in tag_failures:
        lines.append(
            f"| `{row['tag']}` | {row['scenario_count']} | "
            f"{row['evaluated_target_total']} | {_float_text(row['mean_ade_m'])} m | "
            f"{_float_text(row['mean_fde_m'])} m | {_float_text(row['max_fde_m'])} m | "
            f"{_percent_text(row['weighted_miss_rate'])} | "
            f"{_float_text(row['mean_interaction_score'])} |"
        )

    lines.extend(
        [
            "",
            "## Failure By Score Component",
            "",
            "| Component | Positive Scenarios | Mean Component | Mean FDE | Miss Rate |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in component_failures:
        lines.append(
            f"| `{row['component']}` | {row['scenario_count']} | "
            f"{_float_text(row['mean_component_score'])} | "
            f"{_float_text(row['mean_fde_m'])} m | "
            f"{_percent_text(row['weighted_miss_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Interaction/FDE Quadrants",
            "",
            "| Quadrant | Scenarios | Mean FDE | Miss Rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in quadrants:
        lines.append(
            f"| {row['label']} | {row['scenario_count']} | "
            f"{_float_text(row['mean_fde_m'])} m | "
            f"{_percent_text(row['weighted_miss_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Hardest Baseline-Failure Scenarios",
            "",
            "| Rank | Scenario | Score | FDE | Miss Rate | Tags | Main Reason |",
            "| ---: | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in hardest:
        tags = ", ".join(f"`{tag}`" for tag in row["tags"])
        reason = row["reasons"][0] if row["reasons"] else "included for review"
        lines.append(
            f"| {row['rank']} | `{row['scenario_id']}` | "
            f"{_float_text(row['interaction_score'])} | "
            f"{_optional_meter_text(row['baseline_fde_m'])} | "
            f"{_optional_percent_text(row['baseline_miss_rate'])} | "
            f"{tags} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a screening study, not a benchmark claim.",
            "- High FDE means the constant-velocity baseline is a poor explanation "
            "of the target motion in that scenario.",
            "- Tag-level differences help identify scenario families that deserve "
            "a stronger baseline, replay, perturbation, or Waymax experiment.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _load_input_scenarios(
    source: Path,
    input_format: str,
    max_scenarios: int | None,
) -> tuple[bool, dict[str, object] | None, tuple[Scenario, ...]]:
    if input_format == "scenariolens-json":
        scenarios = load_scenarios(source)
        if max_scenarios is not None:
            scenarios = scenarios[:max_scenarios]
        return True, None, scenarios

    preflight = inspect_waymo_motion_slice(source)
    if not waymo_motion_slice_ready(preflight):
        return False, asdict(preflight), ()
    return True, asdict(preflight), load_waymo_motion(source, max_scenarios=max_scenarios)


def _aggregate(scores: tuple[ScenarioScore, ...]) -> dict[str, object]:
    baseline_scores = _baseline_scores(scores)
    evaluated_targets = sum(
        score.prediction_target_evaluated_count for score in baseline_scores
    )
    weighted_misses = sum(
        (score.baseline_miss_rate or 0.0) * score.prediction_target_evaluated_count
        for score in baseline_scores
    )
    return {
        "score": _numeric_summary(tuple(score.interaction_score for score in scores)),
        "baseline": {
            "scenarios_with_evaluated_targets": len(baseline_scores),
            "evaluated_target_total": evaluated_targets,
            "mean_ade_m": _weighted_mean_metric(baseline_scores, "baseline_ade_m"),
            "mean_fde_m": _weighted_mean_metric(baseline_scores, "baseline_fde_m"),
            "max_fde_m": _max_optional(
                score.baseline_max_fde_m for score in baseline_scores
            ),
            "weighted_miss_rate": _float_rate(weighted_misses, evaluated_targets),
            "mean_failure_score": _mean(
                tuple(score.baseline_failure_score for score in baseline_scores)
            ),
            "score_fde_correlation": _correlation(
                tuple(
                    (score.interaction_score, score.baseline_fde_m)
                    for score in baseline_scores
                    if score.baseline_fde_m is not None
                )
            ),
        },
    }


def _tag_failures(
    scores: tuple[ScenarioScore, ...],
    min_tag_count: int,
) -> list[dict[str, object]]:
    tag_scores: dict[str, list[ScenarioScore]] = {}
    for score in scores:
        tags = score.tags or ("untagged",)
        for tag in tags:
            tag_scores.setdefault(tag, []).append(score)

    rows = [
        _group_row(tag, tuple(group))
        for tag, group in tag_scores.items()
        if len(group) >= min_tag_count
    ]
    return sorted(
        rows,
        key=lambda row: (
            -float(row["mean_fde_m"]),
            -float(row["weighted_miss_rate"]),
            str(row["tag"]),
        ),
    )


def _component_failures(scores: tuple[ScenarioScore, ...]) -> list[dict[str, object]]:
    component_scores: dict[str, list[ScenarioScore]] = {}
    for score in scores:
        for component, value in score.component_scores.items():
            if value > 0.0:
                component_scores.setdefault(component, []).append(score)

    rows: list[dict[str, object]] = []
    for component, group in component_scores.items():
        group_tuple = tuple(group)
        baseline_scores = _baseline_scores(group_tuple)
        evaluated_targets = sum(
            score.prediction_target_evaluated_count for score in baseline_scores
        )
        weighted_misses = sum(
            (score.baseline_miss_rate or 0.0)
            * score.prediction_target_evaluated_count
            for score in baseline_scores
        )
        rows.append(
            {
                "component": component,
                "scenario_count": len(group_tuple),
                "mean_component_score": round(
                    _mean(
                        tuple(score.component_scores[component] for score in group_tuple)
                    ),
                    3,
                ),
                "mean_fde_m": _weighted_mean_metric(baseline_scores, "baseline_fde_m"),
                "weighted_miss_rate": _float_rate(weighted_misses, evaluated_targets),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            -float(row["mean_fde_m"]),
            -float(row["weighted_miss_rate"]),
            str(row["component"]),
        ),
    )


def _quadrants(scores: tuple[ScenarioScore, ...]) -> list[dict[str, object]]:
    baseline_scores = tuple(
        score for score in scores if score.baseline_fde_m is not None
    )
    if not baseline_scores:
        return []
    score_threshold = _median(
        tuple(sorted(score.interaction_score for score in baseline_scores))
    )
    fde_threshold = _median(
        tuple(sorted(float(score.baseline_fde_m) for score in baseline_scores))
    )
    buckets = {
        "High interaction / high FDE": [],
        "High interaction / low FDE": [],
        "Low interaction / high FDE": [],
        "Low interaction / low FDE": [],
    }
    for score in baseline_scores:
        high_score = score.interaction_score >= score_threshold
        high_fde = float(score.baseline_fde_m) >= fde_threshold
        if high_score and high_fde:
            label = "High interaction / high FDE"
        elif high_score:
            label = "High interaction / low FDE"
        elif high_fde:
            label = "Low interaction / high FDE"
        else:
            label = "Low interaction / low FDE"
        buckets[label].append(score)

    return [_quadrant_row(label, tuple(group)) for label, group in buckets.items()]


def _quadrant_row(label: str, scores: tuple[ScenarioScore, ...]) -> dict[str, object]:
    baseline_scores = _baseline_scores(scores)
    evaluated_targets = sum(
        score.prediction_target_evaluated_count for score in baseline_scores
    )
    weighted_misses = sum(
        (score.baseline_miss_rate or 0.0) * score.prediction_target_evaluated_count
        for score in baseline_scores
    )
    return {
        "label": label,
        "scenario_count": len(scores),
        "mean_fde_m": _weighted_mean_metric(baseline_scores, "baseline_fde_m"),
        "weighted_miss_rate": _float_rate(weighted_misses, evaluated_targets),
    }


def _group_row(tag: str, scores: tuple[ScenarioScore, ...]) -> dict[str, object]:
    baseline_scores = _baseline_scores(scores)
    evaluated_targets = sum(
        score.prediction_target_evaluated_count for score in baseline_scores
    )
    weighted_misses = sum(
        (score.baseline_miss_rate or 0.0) * score.prediction_target_evaluated_count
        for score in baseline_scores
    )
    return {
        "tag": tag,
        "scenario_count": len(scores),
        "evaluated_target_total": evaluated_targets,
        "mean_ade_m": _weighted_mean_metric(baseline_scores, "baseline_ade_m"),
        "mean_fde_m": _weighted_mean_metric(baseline_scores, "baseline_fde_m"),
        "max_fde_m": _max_optional(
            score.baseline_max_fde_m for score in baseline_scores
        ),
        "weighted_miss_rate": _float_rate(weighted_misses, evaluated_targets),
        "mean_interaction_score": round(
            _mean(tuple(score.interaction_score for score in scores)),
            3,
        ),
        "mean_baseline_failure_score": round(
            _mean(tuple(score.baseline_failure_score for score in baseline_scores)),
            3,
        ),
        "mean_vru_count": round(
            _mean(tuple(score.vulnerable_road_user_count for score in scores)),
            3,
        ),
        "mean_agent_count": round(_mean(tuple(score.agent_count for score in scores)), 3),
    }


def _scenario_row(score: ScenarioScore, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "scenario_id": score.scenario_id,
        "interaction_score": round(score.interaction_score, 3),
        "baseline_ade_m": score.baseline_ade_m,
        "baseline_fde_m": score.baseline_fde_m,
        "baseline_max_fde_m": score.baseline_max_fde_m,
        "baseline_miss_rate": score.baseline_miss_rate,
        "baseline_failure_score": round(score.baseline_failure_score, 3),
        "prediction_target_evaluated_count": score.prediction_target_evaluated_count,
        "tags": list(score.tags),
        "reasons": list(score_reasons(score)),
    }


def _scores_by_baseline_failure(
    scores: tuple[ScenarioScore, ...],
) -> tuple[ScenarioScore, ...]:
    scored = tuple(score for score in scores if score.baseline_fde_m is not None)
    if not scored:
        scored = scores
    return tuple(
        sorted(
            scored,
            key=lambda score: (
                _optional_sort_value(score.baseline_fde_m),
                _optional_sort_value(score.baseline_max_fde_m),
                score.baseline_failure_score,
                score.interaction_score,
            ),
            reverse=True,
        )
    )


def _baseline_scores(scores: tuple[ScenarioScore, ...]) -> tuple[ScenarioScore, ...]:
    return tuple(
        score for score in scores if score.prediction_target_evaluated_count > 0
    )


def _weighted_mean_metric(scores: tuple[ScenarioScore, ...], field_name: str) -> float:
    numerator = 0.0
    denominator = 0
    for score in scores:
        value = getattr(score, field_name)
        if value is None:
            continue
        weight = score.prediction_target_evaluated_count
        numerator += float(value) * weight
        denominator += weight
    return _float_rate(numerator, denominator)


def _numeric_summary(values: tuple[float, ...]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    sorted_values = tuple(sorted(float(value) for value in values))
    return {
        "min": round(sorted_values[0], 3),
        "median": round(_median(sorted_values), 3),
        "mean": round(_mean(sorted_values), 3),
        "max": round(sorted_values[-1], 3),
    }


def _correlation(pairs: tuple[tuple[float, float | None], ...]) -> float | None:
    clean_pairs = tuple((float(x), float(y)) for x, y in pairs if y is not None)
    if len(clean_pairs) < 2:
        return None
    xs = tuple(pair[0] for pair in clean_pairs)
    ys = tuple(pair[1] for pair in clean_pairs)
    mean_x = _mean(xs)
    mean_y = _mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in clean_pairs)
    x_var = sum((x - mean_x) ** 2 for x in xs)
    y_var = sum((y - mean_y) ** 2 for y in ys)
    if x_var == 0.0 or y_var == 0.0:
        return None
    return round(numerator / ((x_var * y_var) ** 0.5), 3)


def _mean(values: tuple[float, ...] | tuple[int, ...]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def _median(sorted_values: tuple[float, ...]) -> float:
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def _float_rate(numerator: float, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)


def _max_optional(values: Iterable[float | None]) -> float:
    clean_values = tuple(float(value) for value in values if value is not None)
    return round(max(clean_values), 3) if clean_values else 0.0


def _optional_sort_value(value: float | None) -> float:
    return float(value) if value is not None else -1.0


def _required_mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping[key]
    if not isinstance(value, dict):
        raise TypeError(f"failure study {key} must be a dictionary")
    return value


def _required_list(mapping: dict[str, object], key: str) -> list[dict[str, object]]:
    value = mapping[key]
    if not isinstance(value, list):
        raise TypeError(f"failure study {key} must be a list")
    return value


def _float_text(value: object) -> str:
    return f"{float(value):.2f}"


def _optional_float_text(value: object) -> str:
    if value is None:
        return "n/a"
    return _float_text(value)


def _optional_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{_float_text(value)} m"


def _percent_text(value: object) -> str:
    return f"{float(value) * 100:.2f}%"


def _optional_percent_text(value: object) -> str:
    if value is None:
        return "n/a"
    return _percent_text(value)


def _range_text(summary: dict[str, object]) -> str:
    return (
        f"{_float_text(summary['min'])} / {_float_text(summary['median'])} / "
        f"{_float_text(summary['mean'])} / {_float_text(summary['max'])}"
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
