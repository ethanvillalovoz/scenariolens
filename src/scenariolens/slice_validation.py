from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    inspect_waymo_motion_slice,
    load_waymo_motion,
    waymo_motion_slice_ready,
)
from scenariolens.io import save_scenarios
from scenariolens.report import markdown_report, ranked_scores, score_reasons
from scenariolens.visualize import scenario_svg

VALIDATION_FORMAT = "scenariolens.waymo_motion_validation.v1"


@dataclass(frozen=True)
class WaymoMotionValidationResult:
    """Files produced by a local Waymo Motion validation run."""

    ready: bool
    scenario_count: int
    reported_count: int
    output_dir: Path
    preflight_path: Path
    manifest_path: Path
    summary_path: Path
    case_study_path: Path | None
    scenarios_path: Path | None
    report_path: Path | None
    assets_dir: Path | None


def validate_waymo_motion_slice(
    input_path: str | Path,
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 5,
) -> WaymoMotionValidationResult:
    """Preflight, ingest, score, report, and render a local Waymo Motion slice."""

    source = Path(input_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    preflight = inspect_waymo_motion_slice(source)
    preflight_path = target / "preflight.json"
    _write_json(preflight_path, asdict(preflight))

    if not waymo_motion_slice_ready(preflight):
        manifest = _manifest(
            input_path=source,
            output_dir=target,
            max_scenarios=max_scenarios,
            top=top,
            ready=False,
            preflight=preflight,
            scenarios=(),
            outputs={"preflight": preflight_path.name},
        )
        manifest_path = target / "manifest.json"
        summary_path = target / "README.md"
        _write_json(manifest_path, manifest)
        summary_path.write_text(_summary_markdown(manifest), encoding="utf-8")
        return WaymoMotionValidationResult(
            ready=False,
            scenario_count=0,
            reported_count=0,
            output_dir=target,
            preflight_path=preflight_path,
            manifest_path=manifest_path,
            summary_path=summary_path,
            case_study_path=None,
            scenarios_path=None,
            report_path=None,
            assets_dir=None,
        )

    scenarios = load_waymo_motion(source, max_scenarios=max_scenarios)
    scenarios_path = target / "scenarios.json"
    report_path = target / "report.md"
    case_study_path = target / "case_study.md"
    assets_dir = target / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    save_scenarios(scenarios_path, scenarios)
    report_path.write_text(markdown_report(scenarios, limit=top), encoding="utf-8")

    top_scores = ranked_scores(scenarios)[:top]
    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    for score in top_scores:
        scenario = scenario_by_id[score.scenario_id]
        (assets_dir / f"{score.scenario_id}.svg").write_text(
            scenario_svg(scenario),
            encoding="utf-8",
        )

    manifest = _manifest(
        input_path=source,
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        ready=True,
        preflight=preflight,
        scenarios=scenarios,
        outputs={
            "preflight": preflight_path.name,
            "scenarios": scenarios_path.name,
            "report": report_path.name,
            "case_study": case_study_path.name,
            "assets_dir": assets_dir.name,
        },
    )
    manifest_path = target / "manifest.json"
    summary_path = target / "README.md"
    _write_json(manifest_path, manifest)
    summary_path.write_text(_summary_markdown(manifest), encoding="utf-8")
    case_study_path.write_text(case_study_markdown(manifest), encoding="utf-8")

    return WaymoMotionValidationResult(
        ready=True,
        scenario_count=len(scenarios),
        reported_count=len(top_scores),
        output_dir=target,
        preflight_path=preflight_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        case_study_path=case_study_path,
        scenarios_path=scenarios_path,
        report_path=report_path,
        assets_dir=assets_dir,
    )


def _manifest(
    input_path: Path,
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    ready: bool,
    preflight,
    scenarios,
    outputs: dict[str, str],
) -> dict[str, object]:
    all_scores = ranked_scores(tuple(scenarios)) if scenarios else ()
    scores = all_scores[:top]
    return {
        "format": VALIDATION_FORMAT,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "max_scenarios": max_scenarios,
        "top": top,
        "ready": ready,
        "scenario_count": len(scenarios),
        "reported_count": len(scores),
        "preflight": asdict(preflight),
        "aggregate_metrics": _aggregate_metrics(all_scores),
        "outputs": outputs,
        "top_scenarios": [
            {
                "rank": rank,
                "scenario_id": score.scenario_id,
                "score": round(score.interaction_score, 3),
                "tags": list(score.tags),
                "reasons": list(score_reasons(score)),
            }
            for rank, score in enumerate(scores, start=1)
        ],
    }


def case_study_markdown(manifest: dict[str, object]) -> str:
    """Return a public-safe real-slice case study from a validation manifest."""

    preflight = _required_mapping(manifest, "preflight")
    aggregate = _required_mapping(manifest, "aggregate_metrics")
    score_distribution = _required_mapping(aggregate, "score_distribution")
    agent_summary = _required_mapping(aggregate, "agent_summary")
    vru_summary = _required_mapping(aggregate, "vru_summary")
    waymo_summary = _required_mapping(aggregate, "waymo_metadata")
    baseline_summary = _required_mapping(aggregate, "prediction_baseline")
    top_scenarios = manifest["top_scenarios"]
    if not isinstance(top_scenarios, list):
        raise TypeError("manifest top_scenarios must be a list")

    lines = [
        "# Waymo Motion Real-Data Case Study",
        "",
        "This case study summarizes one local ScenarioLens smoke run against a "
        "downloaded Waymo Open Dataset Motion validation shard. It is designed "
        "to be public-safe: raw Waymo files, normalized scenario JSON, and SVGs "
        "from the shard remain local ignored artifacts.",
        "",
        "## Run Scope",
        "",
        f"- Dataset path: `{manifest['input_path']}`",
        f"- Supported files: {preflight['supported_file_count']}",
        f"- Supported bytes scanned: {preflight['total_bytes']:,}",
        f"- Scenarios analyzed: {manifest['scenario_count']}",
        f"- Top scenarios reported: {manifest['reported_count']}",
        "- Raw dataset files committed: no",
        "",
        "## Aggregate Findings",
        "",
        "| Category | Metric | Value |",
        "| --- | --- | ---: |",
        f"| Score | min / median / mean / max | {_range_text(score_distribution)} |",
        f"| Tracks | avg raw agents | {_float_text(agent_summary['mean_raw_agents'])} |",
        f"| Tracks | avg scored agents | {_float_text(agent_summary['mean_scored_agents'])} |",
        f"| Tracks | avg excluded tracks | {_float_text(agent_summary['mean_excluded_tracks'])} |",
        f"| Tracks | low-quality track rate | {_percent_text(agent_summary['low_quality_track_rate'])} |",
        f"| VRUs | scenarios with VRUs | {vru_summary['scenarios_with_vrus']} |",
        f"| VRUs | avg raw VRUs | {_float_text(vru_summary['mean_raw_vrus'])} |",
        f"| Waymo metadata | scenarios with SDC track | {waymo_summary['scenarios_with_sdc_track']} |",
        f"| Waymo metadata | total prediction targets | {waymo_summary['prediction_target_total']} |",
        f"| Waymo metadata | total objects of interest | {waymo_summary['object_of_interest_total']} |",
        f"| Waymo metadata | scenarios with parsed map features | {waymo_summary['scenarios_with_map_features']} |",
        f"| Prediction baseline | evaluated targets | {baseline_summary['evaluated_target_total']} |",
        f"| Prediction baseline | mean ADE / FDE | {_float_text(baseline_summary['mean_ade_m'])} m / {_float_text(baseline_summary['mean_fde_m'])} m |",
        f"| Prediction baseline | max FDE | {_float_text(baseline_summary['max_fde_m'])} m |",
        f"| Prediction baseline | weighted miss rate | {_percent_text(baseline_summary['weighted_miss_rate'])} |",
        "",
        "## Top Ranked Scenarios",
        "",
        "| Rank | Scenario | Score | Main Reason |",
        "| ---: | --- | ---: | --- |",
    ]
    for scenario in top_scenarios:
        reasons = scenario.get("reasons", [])
        reason = reasons[0] if reasons else "included for review"
        lines.append(
            f"| {scenario['rank']} | `{scenario['scenario_id']}` | "
            f"{scenario['score']:.3f} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The scores are screening heuristics for review prioritization, not certified safety metrics.",
            "- The run demonstrates that ScenarioLens can ingest a real Motion TFRecord shard with a dependency-free reader.",
            "- The aggregate section is safe to publish because it contains counts and summary statistics only.",
            "- The next useful expansion is to compare these interaction and baseline-failure distributions across more validation shards.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _summary_markdown(manifest: dict[str, object]) -> str:
    preflight = manifest["preflight"]
    if not isinstance(preflight, dict):
        raise TypeError("manifest preflight must be a dictionary")
    outputs = manifest["outputs"]
    if not isinstance(outputs, dict):
        raise TypeError("manifest outputs must be a dictionary")
    top_scenarios = manifest["top_scenarios"]
    if not isinstance(top_scenarios, list):
        raise TypeError("manifest top_scenarios must be a list")
    aggregate = manifest.get("aggregate_metrics")
    if aggregate is not None and not isinstance(aggregate, dict):
        raise TypeError("manifest aggregate_metrics must be a dictionary")

    lines = [
        "# Waymo Motion Slice Validation",
        "",
        f"- Input: `{manifest['input_path']}`",
        f"- Ready for ingestion: {manifest['ready']}",
        f"- Files scanned: {preflight['file_count']}",
        f"- Supported files: {preflight['supported_file_count']}",
        f"- Scenario count: {manifest['scenario_count']}",
        f"- Reported top scenarios: {manifest['reported_count']}",
        "",
        "## Outputs",
        "",
    ]
    for label, path in outputs.items():
        lines.append(f"- {label}: `{path}`")

    if aggregate:
        agent_summary = _required_mapping(aggregate, "agent_summary")
        vru_summary = _required_mapping(aggregate, "vru_summary")
        waymo_summary = _required_mapping(aggregate, "waymo_metadata")
        baseline_summary = _required_mapping(aggregate, "prediction_baseline")
        lines.extend(
            [
                "",
                "## Aggregate Metrics",
                "",
                f"- Average raw agents: {_float_text(agent_summary['mean_raw_agents'])}",
                f"- Average scored agents: {_float_text(agent_summary['mean_scored_agents'])}",
                f"- Low-quality track rate: {_percent_text(agent_summary['low_quality_track_rate'])}",
                f"- Scenarios with VRUs: {vru_summary['scenarios_with_vrus']}",
                f"- Prediction targets: {waymo_summary['prediction_target_total']}",
                f"- Objects of interest: {waymo_summary['object_of_interest_total']}",
                f"- Scenarios with parsed map features: {waymo_summary['scenarios_with_map_features']}",
                f"- Baseline targets evaluated: {baseline_summary['evaluated_target_total']}",
                f"- Mean baseline FDE: {_float_text(baseline_summary['mean_fde_m'])} m",
                f"- Weighted baseline miss rate: {_percent_text(baseline_summary['weighted_miss_rate'])}",
            ]
        )

    notes = preflight.get("notes", ())
    if notes:
        lines.extend(["", "## Preflight Notes", ""])
        for note in notes:
            lines.append(f"- {note}")

    if top_scenarios:
        lines.extend(["", "## Top Scenarios", ""])
        lines.extend(["| Rank | Scenario | Score | Why |", "| ---: | --- | ---: | --- |"])
        for scenario in top_scenarios:
            reasons = scenario.get("reasons", [])
            reason = reasons[0] if reasons else "included for review"
            lines.append(
                f"| {scenario['rank']} | `{scenario['scenario_id']}` | "
                f"{scenario['score']:.3f} | {reason} |"
            )
    else:
        lines.extend(
            [
                "",
                "## Next Action",
                "",
                "Fix the input path or optional dependencies, then rerun the validation command.",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _aggregate_metrics(scores) -> dict[str, object]:
    scores = tuple(scores)
    if not scores:
        return {
            "score_distribution": _numeric_summary(()),
            "agent_summary": {
                "mean_raw_agents": 0.0,
                "mean_scored_agents": 0.0,
                "mean_excluded_tracks": 0.0,
                "excluded_track_rate": 0.0,
                "low_quality_track_rate": 0.0,
            },
            "vru_summary": {
                "scenarios_with_vrus": 0,
                "mean_raw_vrus": 0.0,
                "mean_scored_vrus": 0.0,
                "max_raw_vrus": 0,
            },
            "waymo_metadata": {
                "scenarios_with_sdc_track": 0,
                "prediction_target_total": 0,
                "object_of_interest_total": 0,
                "scenarios_with_map_features": 0,
            },
            "prediction_baseline": {
                "scenarios_with_evaluated_targets": 0,
                "evaluated_target_total": 0,
                "mean_ade_m": 0.0,
                "mean_fde_m": 0.0,
                "max_fde_m": 0.0,
                "weighted_miss_rate": 0.0,
                "mean_failure_score": 0.0,
            },
            "top_tags": [],
        }

    raw_agents = tuple(score.agent_count for score in scores)
    scored_agents = tuple(score.scoring_agent_count for score in scores)
    excluded_tracks = tuple(score.excluded_track_count for score in scores)
    low_quality_tracks = tuple(score.low_quality_track_count for score in scores)
    raw_vrus = tuple(score.vulnerable_road_user_count for score in scores)
    scored_vrus = tuple(score.scoring_vulnerable_road_user_count for score in scores)
    baseline_scores = tuple(
        score for score in scores if score.prediction_target_evaluated_count > 0
    )
    baseline_ades = tuple(
        score.baseline_ade_m for score in baseline_scores if score.baseline_ade_m is not None
    )
    baseline_fdes = tuple(
        score.baseline_fde_m for score in baseline_scores if score.baseline_fde_m is not None
    )
    evaluated_targets = sum(
        score.prediction_target_evaluated_count for score in baseline_scores
    )
    weighted_misses = sum(
        (score.baseline_miss_rate or 0.0) * score.prediction_target_evaluated_count
        for score in baseline_scores
    )
    tag_counts: dict[str, int] = {}
    for score in scores:
        for tag in score.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    raw_agent_total = sum(raw_agents)
    return {
        "score_distribution": _numeric_summary(
            tuple(score.interaction_score for score in scores)
        ),
        "agent_summary": {
            "mean_raw_agents": round(_mean(raw_agents), 3),
            "mean_scored_agents": round(_mean(scored_agents), 3),
            "mean_excluded_tracks": round(_mean(excluded_tracks), 3),
            "excluded_track_rate": _rate(sum(excluded_tracks), raw_agent_total),
            "low_quality_track_rate": _rate(sum(low_quality_tracks), raw_agent_total),
        },
        "vru_summary": {
            "scenarios_with_vrus": sum(1 for value in raw_vrus if value > 0),
            "mean_raw_vrus": round(_mean(raw_vrus), 3),
            "mean_scored_vrus": round(_mean(scored_vrus), 3),
            "max_raw_vrus": max(raw_vrus),
        },
        "waymo_metadata": {
            "scenarios_with_sdc_track": sum(1 for score in scores if score.sdc_track_present),
            "prediction_target_total": sum(score.prediction_target_count for score in scores),
            "object_of_interest_total": sum(score.object_of_interest_count for score in scores),
            "scenarios_with_map_features": sum(
                1 for score in scores if "map_context" in score.tags
            ),
        },
        "prediction_baseline": {
            "scenarios_with_evaluated_targets": len(baseline_scores),
            "evaluated_target_total": evaluated_targets,
            "mean_ade_m": round(_mean(baseline_ades), 3),
            "mean_fde_m": round(_mean(baseline_fdes), 3),
            "max_fde_m": round(max(baseline_fdes), 3) if baseline_fdes else 0.0,
            "weighted_miss_rate": _float_rate(weighted_misses, evaluated_targets),
            "mean_failure_score": round(
                _mean(tuple(score.baseline_failure_score for score in baseline_scores)),
                3,
            ),
        },
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in sorted(
                tag_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:8]
        ],
    }


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


def _mean(values: tuple[float, ...] | tuple[int, ...]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def _median(sorted_values: tuple[float, ...]) -> float:
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)


def _float_rate(numerator: float, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)


def _required_mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping[key]
    if not isinstance(value, dict):
        raise TypeError(f"manifest {key} must be a dictionary")
    return value


def _float_text(value: object) -> str:
    return f"{float(value):.2f}"


def _percent_text(value: object) -> str:
    return f"{float(value) * 100:.2f}%"


def _range_text(summary: dict[str, object]) -> str:
    return (
        f"{_float_text(summary['min'])} / {_float_text(summary['median'])} / "
        f"{_float_text(summary['mean'])} / {_float_text(summary['max'])}"
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
