from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.baseline_compare import fallback_reason_counts
from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    load_failure_study_input,
)
from scenariolens.prediction import (
    DEFAULT_MISS_THRESHOLD_M,
    PredictionBaselineComparison,
    compare_prediction_baselines,
)

BASELINE_COMPARISON_STUDY_FORMAT = "scenariolens.baseline_comparison_study.v1"
BASELINE_COMPARISON_STUDY_INPUT_FORMATS = FAILURE_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class BaselineComparisonStudyResult:
    """Files produced by a public-safe lane-aware baseline diagnostic."""

    ready: bool
    source_count: int
    scenario_count: int
    evaluated_target_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_baseline_comparison_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 10,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> BaselineComparisonStudyResult:
    """Generate aggregate baseline comparison analysis for one or more inputs."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = baseline_comparison_study_payload(
        input_paths=tuple(Path(path) for path in input_paths),
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        input_format=input_format,
    )
    report = baseline_comparison_study_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return BaselineComparisonStudyResult(
        ready=bool(payload["ready"]),
        source_count=int(payload["source_count"]),
        scenario_count=int(payload["scenario_count"]),
        evaluated_target_count=int(aggregate["evaluated_target_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def baseline_comparison_study_payload(
    input_paths: tuple[Path, ...],
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    input_format: str,
) -> dict[str, object]:
    """Return a deterministic public-safe baseline-comparison manifest."""

    if not input_paths:
        raise ValueError("At least one input path is required for baseline comparison.")
    if input_format not in BASELINE_COMPARISON_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported baseline-compare-study input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(BASELINE_COMPARISON_STUDY_INPUT_FORMATS)}"
        )
    if top < 1:
        raise ValueError("top must be at least 1.")

    ready = True
    sources: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []
    all_comparisons: list[PredictionBaselineComparison] = []

    for source_index, source in enumerate(input_paths, start=1):
        input_ready, preflight, scenarios = load_failure_study_input(
            source=source,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )
        if not input_ready:
            ready = False
            sources.append(
                {
                    "input_path": str(source),
                    "source_name": _source_name(source),
                    "ready": False,
                    "scenario_count": 0,
                    "preflight": preflight or {},
                    **_aggregate_comparisons(()),
                    "fallback_reasons": {},
                }
            )
            continue

        comparisons = tuple(compare_prediction_baselines(scenario) for scenario in scenarios)
        all_comparisons.extend(comparisons)
        source_rows = _scenario_rows(
            source=source,
            source_index=source_index,
            comparisons=comparisons,
        )
        scenario_rows.extend(source_rows)
        sources.append(
            {
                "input_path": str(source),
                "source_name": _source_name(source),
                "ready": True,
                "scenario_count": len(scenarios),
                "preflight": preflight or {},
                **_aggregate_comparisons(comparisons),
                "fallback_reasons": fallback_reason_counts(comparisons),
            }
        )

    aggregate = _aggregate_comparisons(tuple(all_comparisons))
    return {
        "format": BASELINE_COMPARISON_STUDY_FORMAT,
        "input_paths": [str(path) for path in input_paths],
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios_per_input": max_scenarios,
        "top": top,
        "ready": ready,
        "source_count": len(input_paths),
        "scenario_count": sum(int(source["scenario_count"]) for source in sources),
        "aggregate": aggregate,
        "sources": sources,
        "fallback_reasons": fallback_reason_counts(tuple(all_comparisons)),
        "top_improvements": _rank_improvements(scenario_rows, top=top),
        "top_regressions": _rank_regressions(scenario_rows, top=top),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
    }


def baseline_comparison_study_markdown(payload: dict[str, object]) -> str:
    """Return Markdown report from a baseline comparison study payload."""

    aggregate = _required_mapping(payload, "aggregate")
    sources = _required_list(payload, "sources")
    fallback_reasons = _required_mapping(payload, "fallback_reasons")
    top_improvements = _required_list(payload, "top_improvements")
    top_regressions = _required_list(payload, "top_regressions")

    lines = [
        "# ScenarioLens Real Waymo Lane-Aware Baseline Study",
        "",
        "This report compares the default constant-velocity prediction baseline "
        "against ScenarioLens' lightweight lane-aware baseline over public-safe "
        "aggregate scenario slices. Raw Waymo files and per-scenario derived "
        "outputs remain outside git.",
        "",
        "## Run Scope",
        "",
        f"- Inputs: {', '.join(f'`{path}`' for path in payload['input_paths'])}",
        f"- Input format: `{payload['input_format']}`",
        f"- Ready for analysis: {payload['ready']}",
        f"- Sources compared: {payload['source_count']}",
        f"- Scenarios analyzed: {payload['scenario_count']}",
        f"- Evaluated prediction targets: {aggregate['evaluated_target_count']}",
        f"- Max scenarios per input: {payload['max_scenarios_per_input']}",
        "- Raw scenario data committed: no",
        "",
        "## Executive Findings",
        "",
        "| Metric | Constant velocity | Lane-aware | Delta / Count |",
        "| --- | ---: | ---: | ---: |",
        f"| Mean ADE | {_meter_text(aggregate['constant_velocity_ade_m'])} | "
        f"{_meter_text(aggregate['lane_aware_ade_m'])} | n/a |",
        f"| Mean FDE | {_meter_text(aggregate['constant_velocity_fde_m'])} | "
        f"{_meter_text(aggregate['lane_aware_fde_m'])} | "
        f"{_signed_meter_text(aggregate['fde_improvement_m'])} |",
        f"| Miss rate | {_percent_text(aggregate['constant_velocity_miss_rate'])} | "
        f"{_percent_text(aggregate['lane_aware_miss_rate'])} | n/a |",
        f"| Target handling | n/a | n/a | {aggregate['map_used_count']} map-used / "
        f"{aggregate['fallback_count']} fallback |",
        "",
    ]

    if not payload["ready"]:
        lines.extend(
            [
                "## Next Action",
                "",
                "Fix the failing input path or use an ingestable ScenarioLens JSON "
                "file, then rerun `baseline-compare-study`.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Per-Source Summary",
            "",
            "| Source | Scenarios | Targets | CV FDE | Lane FDE | FDE delta | CV miss | Lane miss | Map used | Fallbacks |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in sources:
        assert isinstance(source, dict)
        lines.append(
            "| "
            f"`{source['source_name']}` | "
            f"{source['scenario_count']} | "
            f"{source['evaluated_target_count']} | "
            f"{_meter_text(source['constant_velocity_fde_m'])} | "
            f"{_meter_text(source['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(source['fde_improvement_m'])} | "
            f"{_percent_text(source['constant_velocity_miss_rate'])} | "
            f"{_percent_text(source['lane_aware_miss_rate'])} | "
            f"{source['map_used_count']} | "
            f"{source['fallback_count']} |"
        )

    lines.extend(["", "## Fallback Reasons", ""])
    if fallback_reasons:
        for reason, count in fallback_reasons.items():
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Largest Lane-Aware Improvements",
            "",
            "| Rank | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback reason |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_ranked_rows(lines, top_improvements)

    lines.extend(
        [
            "",
            "## Largest Lane-Aware Regressions",
            "",
            "Negative deltas mean the naive lane-following baseline had higher FDE "
            "than constant velocity. Those rows are useful diagnostics for map "
            "matching, lane direction, and behavior assumptions.",
            "",
            "| Rank | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback reason |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_ranked_rows(lines, top_regressions)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            _diagnostic_note(aggregate),
            "- Lane-aware is intentionally conservative: pedestrians, missing maps, "
            "low-speed targets, and distant lane matches fall back to constant velocity.",
            "- A regression is not a project failure. It marks a scenario where the "
            "simple lane-following assumption needs richer map, agent intent, or replay context.",
            "- This is a scenario-triage diagnostic, not a Waymo benchmark claim or "
            "production prediction model.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _scenario_rows(
    source: Path,
    source_index: int,
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario_index, comparison in enumerate(comparisons, start=1):
        reasons = fallback_reason_counts((comparison,))
        top_reason = "none"
        if reasons:
            reason, count = next(iter(reasons.items()))
            top_reason = f"{reason} ({count})"
        rows.append(
            {
                "source_input": str(source),
                "source_name": _source_name(source),
                "source_index": source_index,
                "scenario_index": scenario_index,
                "scenario_id": comparison.scenario_id,
                "target_source": comparison.target_source,
                "requested_target_count": comparison.requested_target_count,
                "evaluated_target_count": comparison.evaluated_track_count,
                "constant_velocity_ade_m": comparison.constant_velocity_ade_m,
                "constant_velocity_fde_m": comparison.constant_velocity_fde_m,
                "constant_velocity_miss_rate": comparison.constant_velocity_miss_rate,
                "lane_aware_ade_m": comparison.lane_aware_ade_m,
                "lane_aware_fde_m": comparison.lane_aware_fde_m,
                "lane_aware_miss_rate": comparison.lane_aware_miss_rate,
                "fde_improvement_m": comparison.fde_improvement_m,
                "map_used_count": comparison.map_used_count,
                "fallback_count": comparison.fallback_count,
                "top_fallback_reason": top_reason,
            }
        )
    return rows


def _aggregate_comparisons(
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> dict[str, object]:
    track_rows = tuple(
        row for comparison in comparisons for row in comparison.track_results
    )
    return {
        "evaluated_target_count": len(track_rows),
        "constant_velocity_ade_m": _mean(
            tuple(row.constant_velocity_ade_m for row in track_rows)
        ),
        "constant_velocity_fde_m": _mean(
            tuple(row.constant_velocity_fde_m for row in track_rows)
        ),
        "constant_velocity_miss_rate": _mean(
            tuple(
                1.0
                if row.constant_velocity_fde_m > DEFAULT_MISS_THRESHOLD_M
                else 0.0
                for row in track_rows
            )
        ),
        "lane_aware_ade_m": _mean(tuple(row.lane_aware_ade_m for row in track_rows)),
        "lane_aware_fde_m": _mean(tuple(row.lane_aware_fde_m for row in track_rows)),
        "lane_aware_miss_rate": _mean(
            tuple(
                1.0
                if row.lane_aware_fde_m > DEFAULT_MISS_THRESHOLD_M
                else 0.0
                for row in track_rows
            )
        ),
        "fde_improvement_m": _mean(tuple(row.fde_improvement_m for row in track_rows)),
        "map_used_count": sum(row.lane_map_used for row in track_rows),
        "fallback_count": sum(
            row.lane_fallback_reason is not None for row in track_rows
        ),
    }


def _rank_improvements(
    rows: list[dict[str, object]],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        _rankable_rows(rows),
        key=lambda row: (
            -float(row["fde_improvement_m"]),
            -int(row["map_used_count"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_regressions(
    rows: list[dict[str, object]],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        _rankable_rows(rows),
        key=lambda row: (
            float(row["fde_improvement_m"]),
            -int(row["map_used_count"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rankable_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [row for row in rows if row["fde_improvement_m"] is not None]


def _append_ranked_rows(lines: list[str], rows: list[object]) -> None:
    if not rows:
        lines.append("| n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | n/a |")
        return

    for rank, row in enumerate(rows, start=1):
        assert isinstance(row, dict)
        lines.append(
            "| "
            f"{rank} | "
            f"`{row['source_name']}` | "
            f"`{row['scenario_id']}` | "
            f"{row['evaluated_target_count']} | "
            f"{_meter_text(row['constant_velocity_fde_m'])} | "
            f"{_meter_text(row['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(row['fde_improvement_m'])} | "
            f"{row['map_used_count']} | "
            f"{row['fallback_count']} | "
            f"`{row['top_fallback_reason']}` |"
        )


def _source_name(path: Path) -> str:
    return path.name or str(path)


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f} m"


def _signed_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _percent_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _diagnostic_note(aggregate: dict[str, object]) -> str:
    improvement = aggregate.get("fde_improvement_m")
    if improvement is None:
        return "- No evaluable prediction targets were available in this run."
    if float(improvement) < 0:
        return (
            "- The lane-aware mean FDE is higher in this run, which is useful: "
            "it exposes cases where nearest-lane following is too naive."
        )
    return (
        "- Positive mean FDE improvement means the lane-aware baseline reduced "
        "final displacement error across evaluated targets in this run."
    )


def _required_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping field: {key}")
    return value


def _required_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}")
    return value


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
