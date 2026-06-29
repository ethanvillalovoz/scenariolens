from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot, isfinite
from pathlib import Path

from scenariolens.baseline_compare import fallback_reason_counts
from scenariolens.baseline_compare_study import BASELINE_COMPARISON_STUDY_FORMAT
from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    load_failure_study_input,
)
from scenariolens.prediction import (
    LANE_MATCH_THRESHOLD_M,
    MIN_LANE_AWARE_SPEED_MPS,
    PredictionBaselineComparison,
    PredictionTrackResult,
    _anchor_index,
    _lane_polylines,
    _nearest_lane_projection,
    compare_prediction_baselines,
    constant_velocity_baseline,
    lane_aware_baseline,
)
from scenariolens.schema import AgentTrack, Scenario, State
from scenariolens.visualize import scenario_svg

BASELINE_DEBUG_FORMAT = "scenariolens.baseline_debug.v1"
BASELINE_DEBUG_INPUT_FORMATS = FAILURE_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class BaselineDebugResult:
    """Files produced by a local-first baseline debugging casebook."""

    ready: bool
    case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_baseline_debug_casebook(
    output_dir: str | Path,
    input_path: str | Path | None = None,
    scenario_ids: tuple[str, ...] = (),
    input_format: str = "native",
    max_scenarios: int | None = 25,
    study_manifest_path: str | Path | None = None,
    case_count: int = 3,
    public_report_path: str | Path | None = None,
) -> BaselineDebugResult:
    """Generate local SVG/debug artifacts plus an optional public-safe summary."""

    if input_format not in BASELINE_DEBUG_INPUT_FORMATS:
        raise ValueError(
            "Unsupported baseline-debug input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(BASELINE_DEBUG_INPUT_FORMATS)}"
        )
    if case_count < 1:
        raise ValueError("case-count must be at least 1.")
    if study_manifest_path is None and input_path is None:
        raise ValueError("Provide either --study-manifest or --input.")

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    if study_manifest_path is not None:
        payload = _payload_from_study_manifest(
            study_manifest_path=Path(study_manifest_path),
            output_dir=target,
            case_count=case_count,
        )
    else:
        assert input_path is not None
        payload = _payload_from_direct_input(
            input_path=Path(input_path),
            output_dir=target,
            scenario_ids=scenario_ids,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )

    local_report = baseline_debug_casebook_markdown(payload, public_safe=False)
    public_report = baseline_debug_casebook_markdown(payload, public_safe=True)
    _write_json(manifest_path, payload)
    report_path.write_text(local_report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(public_report, encoding="utf-8")

    return BaselineDebugResult(
        ready=bool(payload["ready"]),
        case_count=len(_required_list(payload, "cases")),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def baseline_debug_casebook_markdown(
    payload: dict[str, object],
    public_safe: bool = True,
) -> str:
    """Return a Markdown casebook for selected baseline-debug scenarios."""

    cases = _required_list(payload, "cases")
    lines = [
        "# ScenarioLens Baseline Debug Casebook",
        "",
        "This casebook explains selected constant-velocity vs lane-aware "
        "prediction outcomes. It is meant to turn the aggregate study into "
        "debuggable evidence: where maps help, where naive lane following "
        "regresses, and where the lane-aware baseline intentionally falls back.",
        "",
        "## Scope",
        "",
        f"- Source: `{payload['source']}`",
        f"- Input format: `{payload['input_format']}`",
        f"- Ready for analysis: {payload['ready']}",
        f"- Cases selected: {len(cases)}",
        "- Raw Waymo files committed: no",
        "- Raw trajectories, local SVG overlays, and per-case debug manifests committed: no",
        "",
    ]
    if public_safe:
        lines.append(
            "The public copy reports scenario IDs, metric summaries, fallback "
            "reasons, and interpretation only. Local SVGs and per-track debug "
            "manifests stay under ignored `data/processed/` paths."
        )
    else:
        lines.append(
            "The local copy links to rendered SVG overlays and per-case manifests "
            "under the ignored output directory."
        )

    lines.extend(
        [
            "",
            "## Selected Cases",
            "",
            "| Case | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback |"
            + ("" if public_safe else " Local SVG |"),
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"
            + ("" if public_safe else " --- |"),
        ]
    )
    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        row = (
            "| "
            f"{case['case_label']} | "
            f"`{case['source_name']}` | "
            f"`{case['scenario_id']}` | "
            f"{summary['evaluated_target_count']} | "
            f"{_meter_text(summary['constant_velocity_fde_m'])} | "
            f"{_meter_text(summary['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(summary['fde_improvement_m'])} | "
            f"{summary['map_used_count']} | "
            f"{summary['fallback_count']} | "
            f"`{summary['top_fallback_reason']}` |"
        )
        if not public_safe:
            row += f" [{case['svg_path']}]({case['svg_path']}) |"
        lines.append(row)

    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        tracks = _required_list(case, "track_diagnostics")
        lines.extend(
            [
                "",
                f"## {case['case_label']}: `{case['scenario_id']}`",
                "",
                f"- Source: `{case['source_input']}`",
                f"- Why selected: {case['selection_reason']}",
                f"- Constant-velocity FDE: {_meter_text(summary['constant_velocity_fde_m'])}",
                f"- Lane-aware FDE: {_meter_text(summary['lane_aware_fde_m'])}",
                f"- FDE improvement: {_signed_meter_text(summary['fde_improvement_m'])}",
                f"- Map-used / fallback targets: {summary['map_used_count']} / {summary['fallback_count']}",
            ]
        )
        if not public_safe:
            lines.append(f"- Local SVG overlay: `{case['svg_path']}`")
            lines.append(f"- Local case manifest: `{case['manifest_path']}`")

        lines.extend(
            [
                "",
                "| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |",
                "| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            lane = _required_mapping(track, "lane_match")
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"`{track['agent_type']}` | "
                f"{_meter_text(track['constant_velocity_fde_m'])} | "
                f"{_meter_text(track['lane_aware_fde_m'])} | "
                f"{_signed_meter_text(track['fde_improvement_m'])} | "
                f"{track['lane_map_used']} | "
                f"`{track['lane_fallback_reason'] or 'none'}` | "
                f"{_meter_text(lane['nearest_lane_distance_m'])} | "
                f"{_meter_text(track['constant_velocity_last_error_m'])} | "
                f"{_meter_text(track['lane_aware_last_error_m'])} |"
            )

        if not public_safe:
            lines.extend(["", "Metric-only error timeline:"])
            for track in tracks:
                assert isinstance(track, dict)
                cv_series = _series_text(_required_list(track, "constant_velocity_errors"))
                lane_series = _series_text(_required_list(track, "lane_aware_errors"))
                lines.append(
                    f"- `{track['track_id']}` CV `{cv_series}`; lane-aware `{lane_series}`"
                )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The improvement case shows where map-conditioned motion can reduce a simple forecast error.",
            "- The regression case is the useful warning: nearest-lane following can be wrong when lane choice, direction, or intent is ambiguous.",
            "- The fallback-heavy case shows production-minded behavior for a diagnostic baseline: when inputs are not trustworthy, it records why and returns to the safer baseline.",
            "- This is still an evaluation/debugging framework, not a production prediction model or Waymo benchmark claim.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _payload_from_study_manifest(
    study_manifest_path: Path,
    output_dir: Path,
    case_count: int,
) -> dict[str, object]:
    study_payload = json.loads(study_manifest_path.read_text(encoding="utf-8"))
    if study_payload.get("format") != BASELINE_COMPARISON_STUDY_FORMAT:
        raise ValueError(
            "Expected a baseline-compare-study manifest with format "
            f"{BASELINE_COMPARISON_STUDY_FORMAT}."
        )

    specs = _case_specs_from_study(study_payload, case_count=case_count)
    cases = []
    ready = bool(study_payload.get("ready", False))
    for spec in specs:
        case = _case_from_spec(
            spec=spec,
            input_format=str(study_payload.get("input_format", "native")),
            max_scenarios=_optional_int(study_payload.get("max_scenarios_per_input")),
            output_dir=output_dir,
        )
        cases.append(case)
        ready = ready and bool(case["ready"])
    ready = ready and bool(cases)

    return {
        "format": BASELINE_DEBUG_FORMAT,
        "source": str(study_manifest_path),
        "source_kind": "baseline_compare_study",
        "input_format": str(study_payload.get("input_format", "native")),
        "max_scenarios": study_payload.get("max_scenarios_per_input"),
        "ready": ready,
        "output_dir": str(output_dir),
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
    }


def _payload_from_direct_input(
    input_path: Path,
    output_dir: Path,
    scenario_ids: tuple[str, ...],
    input_format: str,
    max_scenarios: int | None,
) -> dict[str, object]:
    ready, preflight, scenarios = load_failure_study_input(
        source=input_path,
        input_format=input_format,
        max_scenarios=max_scenarios,
    )
    selected_ids = scenario_ids or ((scenarios[0].scenario_id,) if scenarios else ())
    selection_reason = (
        "Requested with --scenario."
        if scenario_ids
        else "Defaulted to the first loaded scenario."
    )
    cases = []
    for index, scenario_id in enumerate(selected_ids, start=1):
        case = _case_from_loaded_scenarios(
            scenarios=scenarios,
            source_input=input_path,
            input_format=input_format,
            output_dir=output_dir,
            scenario_id=scenario_id,
            case_label=f"Direct case {index}",
            selection_reason=selection_reason,
            source_index=1,
            scenario_index=index,
            preflight=preflight,
            input_ready=ready,
        )
        cases.append(case)
        ready = ready and bool(case["ready"])
    ready = ready and bool(cases)

    return {
        "format": BASELINE_DEBUG_FORMAT,
        "source": str(input_path),
        "source_kind": "direct_input",
        "input_format": input_format,
        "max_scenarios": max_scenarios,
        "ready": ready,
        "output_dir": str(output_dir),
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
    }


def _case_specs_from_study(
    study_payload: dict[str, object],
    case_count: int,
) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    def add_case(label: str, reason: str, rows: object) -> None:
        if len(specs) >= case_count or not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = (str(row.get("source_input", "")), str(row.get("scenario_id", "")))
            if key in seen or not key[0] or not key[1]:
                continue
            specs.append({**row, "case_label": label, "selection_reason": reason})
            seen.add(key)
            return

    add_case(
        "Largest improvement",
        "Highest positive FDE improvement from the baseline comparison study.",
        study_payload.get("top_improvements"),
    )
    add_case(
        "Largest regression",
        "Most negative FDE delta from the baseline comparison study.",
        study_payload.get("top_regressions"),
    )
    add_case(
        "Fallback-heavy case",
        "Most lane-aware fallback-heavy scenario in the comparison study.",
        study_payload.get("top_fallbacks"),
    )

    for label, key in (
        ("Additional improvement", "top_improvements"),
        ("Additional regression", "top_regressions"),
        ("Additional fallback case", "top_fallbacks"),
    ):
        rows = study_payload.get(key)
        if len(specs) >= case_count or not isinstance(rows, list):
            continue
        for row in rows:
            if len(specs) >= case_count or not isinstance(row, dict):
                continue
            key_value = (
                str(row.get("source_input", "")),
                str(row.get("scenario_id", "")),
            )
            if key_value in seen or not key_value[0] or not key_value[1]:
                continue
            specs.append(
                {
                    **row,
                    "case_label": label,
                    "selection_reason": f"Additional selected row from `{key}`.",
                }
            )
            seen.add(key_value)

    return specs[:case_count]


def _case_from_spec(
    spec: dict[str, object],
    input_format: str,
    max_scenarios: int | None,
    output_dir: Path,
) -> dict[str, object]:
    source = Path(str(spec["source_input"]))
    ready, preflight, scenarios = load_failure_study_input(
        source=source,
        input_format=input_format,
        max_scenarios=max_scenarios,
    )
    return _case_from_loaded_scenarios(
        scenarios=scenarios,
        source_input=source,
        input_format=input_format,
        output_dir=output_dir,
        scenario_id=str(spec["scenario_id"]),
        case_label=str(spec["case_label"]),
        selection_reason=str(spec["selection_reason"]),
        source_index=_optional_int(spec.get("source_index")) or 1,
        scenario_index=_optional_int(spec.get("scenario_index")) or 1,
        preflight=preflight,
        input_ready=ready,
    )


def _case_from_loaded_scenarios(
    scenarios: tuple[Scenario, ...],
    source_input: Path,
    input_format: str,
    output_dir: Path,
    scenario_id: str,
    case_label: str,
    selection_reason: str,
    source_index: int,
    scenario_index: int,
    preflight: dict[str, object] | None,
    input_ready: bool,
) -> dict[str, object]:
    scenario = _find_scenario(scenarios, scenario_id)
    case_slug = _safe_slug(f"{case_label}-{source_index}-{scenario_index}-{scenario_id}")
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = case_dir / "manifest.json"
    svg_path = case_dir / "trajectory_comparison.svg"
    relative_manifest = manifest_path.relative_to(output_dir)
    relative_svg = svg_path.relative_to(output_dir)

    if scenario is None:
        case = {
            "ready": False,
            "case_label": case_label,
            "selection_reason": selection_reason,
            "source_input": str(source_input),
            "source_name": source_input.name,
            "input_format": input_format,
            "scenario_id": scenario_id,
            "source_index": source_index,
            "scenario_index": scenario_index,
            "preflight": preflight or {},
            "error": "scenario_not_found",
            "summary": _empty_summary(),
            "track_diagnostics": [],
            "manifest_path": str(relative_manifest),
            "svg_path": str(relative_svg),
        }
        _write_json(manifest_path, case)
        return case

    comparison = compare_prediction_baselines(scenario)
    constant_summary = constant_velocity_baseline(scenario)
    lane_summary = lane_aware_baseline(scenario)
    track_diagnostics = _track_diagnostics(
        scenario=scenario,
        comparison=comparison,
        constant_results=constant_summary.track_results,
        lane_results=lane_summary.track_results,
    )
    case = {
        "ready": bool(input_ready),
        "case_label": case_label,
        "selection_reason": selection_reason,
        "source_input": str(source_input),
        "source_name": source_input.name,
        "input_format": input_format,
        "scenario_id": scenario.scenario_id,
        "source_index": source_index,
        "scenario_index": scenario_index,
        "preflight": preflight or {},
        "summary": _comparison_summary(comparison),
        "track_diagnostics": track_diagnostics,
        "manifest_path": str(relative_manifest),
        "svg_path": str(relative_svg),
    }
    _write_json(manifest_path, case)
    svg_path.write_text(
        scenario_svg(scenario, show_lane_aware_baseline=True),
        encoding="utf-8",
    )
    return case


def _track_diagnostics(
    scenario: Scenario,
    comparison: PredictionBaselineComparison,
    constant_results: tuple[PredictionTrackResult, ...],
    lane_results: tuple[PredictionTrackResult, ...],
) -> list[dict[str, object]]:
    tracks_by_id = {track.agent_id: track for track in scenario.tracks}
    constant_by_id = {result.track_id: result for result in constant_results}
    lane_by_id = {result.track_id: result for result in lane_results}
    rows = []
    for row in comparison.track_results:
        track = tracks_by_id.get(row.track_id)
        constant = constant_by_id.get(row.track_id)
        lane = lane_by_id.get(row.track_id)
        if track is None or constant is None or lane is None:
            continue
        constant_errors = _error_series(track=track, scenario=scenario, result=constant)
        lane_errors = _error_series(track=track, scenario=scenario, result=lane)
        rows.append(
            {
                "track_id": row.track_id,
                "agent_type": row.agent_type,
                "constant_velocity_ade_m": row.constant_velocity_ade_m,
                "constant_velocity_fde_m": row.constant_velocity_fde_m,
                "lane_aware_ade_m": row.lane_aware_ade_m,
                "lane_aware_fde_m": row.lane_aware_fde_m,
                "fde_improvement_m": row.fde_improvement_m,
                "lane_map_used": row.lane_map_used,
                "lane_fallback_reason": row.lane_fallback_reason,
                "anchor_time_s": constant.anchor_time_s,
                "horizon_s": constant.horizon_s,
                "future_state_count": constant.future_state_count,
                "constant_velocity_errors": constant_errors,
                "lane_aware_errors": lane_errors,
                "constant_velocity_last_error_m": _last_error(constant_errors),
                "lane_aware_last_error_m": _last_error(lane_errors),
                "lane_match": _lane_match_diagnostic(track, scenario),
            }
        )
    return rows


def _comparison_summary(comparison: PredictionBaselineComparison) -> dict[str, object]:
    reasons = fallback_reason_counts((comparison,))
    top_reason = "none"
    if reasons:
        reason, count = next(iter(reasons.items()))
        top_reason = f"{reason} ({count})"
    return {
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


def _lane_match_diagnostic(
    track: AgentTrack,
    scenario: Scenario,
    lane_match_threshold_m: float = LANE_MATCH_THRESHOLD_M,
) -> dict[str, object]:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return _lane_match_status("insufficient_track_states")
    anchor = states[_anchor_index(states, scenario)]
    anchor_speed = hypot(anchor.vx, anchor.vy)
    lanes = _lane_polylines(scenario)
    if not lanes:
        return _lane_match_status(
            "no_lane_map_features",
            anchor_speed_mps=anchor_speed,
        )
    projection = _nearest_lane_projection(anchor.x, anchor.y, lanes)
    if projection is None:
        return _lane_match_status(
            "no_usable_lane_polyline",
            anchor_speed_mps=anchor_speed,
        )
    if not isfinite(anchor_speed) or anchor_speed < MIN_LANE_AWARE_SPEED_MPS:
        status = "low_or_invalid_anchor_speed"
    elif projection.distance_m > lane_match_threshold_m:
        status = "target_too_far_from_lane"
    else:
        status = "lane_matched"
    return {
        "status": status,
        "nearest_lane_distance_m": round(projection.distance_m, 3),
        "lane_match_threshold_m": lane_match_threshold_m,
        "anchor_speed_mps": round(anchor_speed, 3) if isfinite(anchor_speed) else None,
        "lane_segment_index": projection.segment_index,
        "lane_point_count": len(projection.lane),
    }


def _lane_match_status(
    status: str,
    anchor_speed_mps: float | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "nearest_lane_distance_m": None,
        "lane_match_threshold_m": LANE_MATCH_THRESHOLD_M,
        "anchor_speed_mps": (
            round(anchor_speed_mps, 3)
            if anchor_speed_mps is not None and isfinite(anchor_speed_mps)
            else None
        ),
        "lane_segment_index": None,
        "lane_point_count": 0,
    }


def _error_series(
    track: AgentTrack,
    scenario: Scenario,
    result: PredictionTrackResult,
) -> list[dict[str, object]]:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    anchor_index = _anchor_index(states, scenario)
    future_by_time = {
        round(state.t, 6): state
        for state in states[anchor_index + 1 :]
        if state.t > states[anchor_index].t
    }
    rows = []
    for predicted in result.predicted_states[1:]:
        actual = future_by_time.get(round(predicted.t, 6))
        if actual is None:
            continue
        rows.append(
            {
                "t": round(actual.t, 3),
                "error_m": round(_state_error(predicted, actual), 3),
            }
        )
    return rows


def _last_error(rows: list[dict[str, object]]) -> float | None:
    if not rows:
        return None
    return float(rows[-1]["error_m"])


def _state_error(predicted: State, actual: State) -> float:
    return hypot(predicted.x - actual.x, predicted.y - actual.y)


def _find_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str,
) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _empty_summary() -> dict[str, object]:
    return {
        "target_source": "n/a",
        "requested_target_count": 0,
        "evaluated_target_count": 0,
        "constant_velocity_ade_m": None,
        "constant_velocity_fde_m": None,
        "constant_velocity_miss_rate": None,
        "lane_aware_ade_m": None,
        "lane_aware_fde_m": None,
        "lane_aware_miss_rate": None,
        "fde_improvement_m": None,
        "map_used_count": 0,
        "fallback_count": 0,
        "top_fallback_reason": "none",
    }


def _series_text(rows: list[object]) -> str:
    values = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        values.append(f"t={row['t']}: {_meter_text(row['error_m'])}")
    return ", ".join(values) if values else "n/a"


def _safe_slug(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {"-", "_", " "}:
            safe.append("-")
    return "-".join("".join(safe).split("-"))[:120] or "case"


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
