from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from scenariolens.baseline_debug import BASELINE_DEBUG_FORMAT
from scenariolens.failure_study import load_failure_study_input
from scenariolens.prediction import (
    LANE_MATCH_THRESHOLD_M,
    constant_velocity_baseline,
    lane_aware_baseline,
)
from scenariolens.schema import Scenario

MAP_MATCH_AUDIT_FORMAT = "scenariolens.map_match_audit.v1"
DEFAULT_AUDIT_THRESHOLDS_M = (3.5, 5.0, 10.0, 25.0, 50.0, 100.0, 150.0)


@dataclass(frozen=True)
class MapMatchAuditResult:
    """Files produced by a lane-map matching audit run."""

    ready: bool
    case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_map_match_audit(
    debug_manifest_path: str | Path,
    output_dir: str | Path,
    thresholds_m: tuple[float, ...] = DEFAULT_AUDIT_THRESHOLDS_M,
    case_count: int = 3,
    public_report_path: str | Path | None = None,
) -> MapMatchAuditResult:
    """Generate a public-safe audit for lane-match fallback behavior."""

    source = Path(debug_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = map_match_audit_payload(
        debug_manifest_path=source,
        output_dir=target,
        thresholds_m=thresholds_m,
        case_count=case_count,
    )
    report = map_match_audit_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return MapMatchAuditResult(
        ready=bool(payload["ready"]),
        case_count=len(_required_list(payload, "cases")),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def map_match_audit_payload(
    debug_manifest_path: Path,
    output_dir: Path,
    thresholds_m: tuple[float, ...],
    case_count: int,
) -> dict[str, object]:
    """Return deterministic lane-match threshold-audit metadata."""

    thresholds = _clean_thresholds(thresholds_m)
    if case_count < 1:
        raise ValueError("case-count must be at least 1.")

    debug_payload = json.loads(debug_manifest_path.read_text(encoding="utf-8"))
    if debug_payload.get("format") != BASELINE_DEBUG_FORMAT:
        raise ValueError(
            "Expected a baseline-debug manifest with format "
            f"{BASELINE_DEBUG_FORMAT}."
        )

    selected = _fallback_cases(_required_list(debug_payload, "cases"))[:case_count]
    cases = [
        _audit_case(
            debug_case=case,
            output_dir=output_dir,
            thresholds_m=thresholds,
            max_scenarios=_optional_int(debug_payload.get("max_scenarios")),
            rank=index,
        )
        for index, case in enumerate(selected, start=1)
    ]
    aggregate = _aggregate_cases(cases)
    ready = bool(debug_payload.get("ready")) and any(
        bool(case.get("ready")) for case in cases
    )

    return {
        "format": MAP_MATCH_AUDIT_FORMAT,
        "debug_manifest": str(debug_manifest_path),
        "debug_format": debug_payload.get("format"),
        "output_dir": str(output_dir),
        "ready": ready,
        "default_lane_match_threshold_m": LANE_MATCH_THRESHOLD_M,
        "thresholds_m": list(thresholds),
        "selected_case_count": len(selected),
        "case_count": len(cases),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
        "scope_note": (
            "Threshold sweep audit only; this does not change the default "
            "lane-aware baseline and does not claim a production map matcher."
        ),
    }


def map_match_audit_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a map-match audit payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    thresholds = _required_list(payload, "thresholds_m")
    lines = [
        "# ScenarioLens Map-Match Audit",
        "",
        "This report audits lane-aware fallback behavior before changing the "
        "matcher. It reloads selected fallback-heavy debug cases, sweeps lane "
        "match thresholds, and checks whether simply accepting farther lane "
        "matches improves or worsens final displacement error.",
        "",
        "It is intentionally scoped: this is a threshold-sensitivity diagnostic, "
        "not a matcher change, not a Waymo benchmark claim, and not a production "
        "map-matching system.",
        "",
        "## Scope",
        "",
        f"- Debug manifest: `{payload['debug_manifest']}`",
        f"- Ready for audit: {payload['ready']}",
        f"- Cases audited: {payload['case_count']}",
        f"- Default lane-match threshold: {_meter_text(payload['default_lane_match_threshold_m'])}",
        f"- Threshold sweep: {', '.join(_meter_text(value) for value in thresholds)}",
        "- Raw Waymo files committed: no",
        "- Local audit packets committed: no",
        "",
        "## Audit Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Audited cases | {aggregate['audited_case_count']} |",
        f"| Audited targets | {aggregate['audited_target_count']} |",
        f"| Default map-used targets | {aggregate['default_map_used_count']} |",
        f"| Default fallback targets | {aggregate['default_fallback_count']} |",
        f"| Best threshold map-used targets | {aggregate['best_threshold_map_used_count']} |",
        f"| Best threshold FDE delta | {_signed_meter_text(aggregate['best_threshold_fde_improvement_m'])} |",
        f"| Cases where widening worsened FDE | {aggregate['widening_worse_case_count']} |",
        "",
    ]

    if not cases:
        lines.extend(
            [
                "No fallback-heavy cases were found in the debug manifest.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Case Summary",
            "",
            "| Rank | Scenario | Case | Targets | Default map used | Default fallbacks | Nearest-lane range | Recommendation |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for case in cases:
        assert isinstance(case, dict)
        distance_summary = _required_mapping(case, "lane_distance_summary")
        recommendation = _required_mapping(case, "recommendation")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"{case['case_label']} | "
            f"{case['evaluated_target_count']} | "
            f"{case['default_map_used_count']} | "
            f"{case['default_fallback_count']} | "
            f"{_distance_range_text(distance_summary)} | "
            f"{recommendation['label']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        recommendation = _required_mapping(case, "recommendation")
        tracks = _required_list(case, "track_audit")
        sweeps = _required_list(case, "threshold_sweep")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}`",
                "",
                f"- Case: {case['case_label']}",
                f"- Source: `{case['source_name']}`",
                f"- Default target handling: {case['default_map_used_count']} map-used / {case['default_fallback_count']} fallback",
                f"- Recommendation: **{recommendation['label']}**",
                f"- Why: {recommendation['reason']}",
                f"- Local audit packet: `{case['local_packet_path']}`",
                "",
                "Target lane-distance audit:",
                "",
                "| Track | Type | Nearest lane | Anchor speed | Default fallback | First matched threshold | CV FDE |",
                "| --- | --- | ---: | ---: | --- | ---: | ---: |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"`{track['agent_type']}` | "
                f"{_meter_text(track['nearest_lane_distance_m'])} | "
                f"{_mps_text(track['anchor_speed_mps'])} | "
                f"`{track['default_fallback_reason'] or 'none'}` | "
                f"{_meter_text(track['first_matched_threshold_m'])} | "
                f"{_meter_text(track['constant_velocity_fde_m'])} |"
            )

        lines.extend(
            [
                "",
                "Threshold sweep:",
                "",
                "| Threshold | Map used | Fallbacks | Lane FDE | FDE delta | Label | Fallback reasons |",
                "| ---: | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for sweep in sweeps:
            assert isinstance(sweep, dict)
            reasons = _required_mapping(sweep, "fallback_reasons")
            reason_text = ", ".join(f"`{key}`: {value}" for key, value in reasons.items())
            lines.append(
                "| "
                f"{_meter_text(sweep['threshold_m'])} | "
                f"{sweep['map_used_count']} | "
                f"{sweep['fallback_count']} | "
                f"{_meter_text(sweep['lane_aware_fde_m'])} | "
                f"{_signed_meter_text(sweep['fde_improvement_m'])} | "
                f"`{sweep['label']}` | "
                f"{reason_text or 'none'} |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The default threshold is a guardrail: when targets are far from parsed lanes, ScenarioLens falls back to constant velocity instead of trusting a bad map match.",
            "- If wider thresholds make FDE worse, the fix is not a larger radius; it is better lane selection, coordinate-frame auditing, route/intent priors, or richer map context.",
            "- If a wider threshold improves FDE on a case, that threshold is still only a hypothesis and should be validated against more scenarios before becoming default behavior.",
            "- This report keeps the public artifact honest by separating map-match coverage problems from replay-ready model evidence.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _audit_case(
    debug_case: dict[str, object],
    output_dir: Path,
    thresholds_m: tuple[float, ...],
    max_scenarios: int | None,
    rank: int,
) -> dict[str, object]:
    source_input = Path(str(debug_case["source_input"]))
    input_format = str(debug_case.get("input_format", "native"))
    input_ready, preflight, scenarios = load_failure_study_input(
        source=source_input,
        input_format=input_format,
        max_scenarios=max_scenarios,
    )
    scenario = _find_scenario(scenarios, str(debug_case["scenario_id"]))
    case_slug = _safe_slug(
        f"{rank}-{debug_case.get('case_label', 'case')}-{debug_case['scenario_id']}"
    )
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    packet_path = case_dir / "map_match_audit.json"

    if scenario is None:
        case_payload = {
            "ready": False,
            "rank": rank,
            "case_label": debug_case.get("case_label", "Case"),
            "scenario_id": debug_case.get("scenario_id", ""),
            "source_name": debug_case.get("source_name", source_input.name),
            "error": "scenario_not_found",
            "input_ready": input_ready,
            "preflight": preflight or {},
            "evaluated_target_count": 0,
            "default_map_used_count": 0,
            "default_fallback_count": 0,
            "lane_distance_summary": _distance_summary([]),
            "track_audit": [],
            "threshold_sweep": [],
            "recommendation": {
                "label": "not_evaluable",
                "reason": "Scenario could not be reloaded from the local source.",
            },
            "local_packet_path": str(packet_path),
        }
        _write_json(packet_path, case_payload)
        return case_payload

    constant = constant_velocity_baseline(scenario)
    sweeps = [
        _threshold_sweep_row(
            scenario=scenario,
            threshold_m=threshold,
            constant_fde_m=constant.fde_m,
        )
        for threshold in thresholds_m
    ]
    track_audit = _track_audit_rows(debug_case, sweeps)
    default_sweep = sweeps[0]
    case_payload = {
        "ready": bool(input_ready),
        "rank": rank,
        "case_label": debug_case.get("case_label", "Case"),
        "scenario_id": scenario.scenario_id,
        "source_input": str(source_input),
        "source_name": debug_case.get("source_name", source_input.name),
        "input_format": input_format,
        "input_ready": input_ready,
        "preflight": preflight or {},
        "evaluated_target_count": constant.evaluated_track_count,
        "constant_velocity_fde_m": constant.fde_m,
        "default_map_used_count": default_sweep["map_used_count"],
        "default_fallback_count": default_sweep["fallback_count"],
        "lane_distance_summary": _distance_summary(
            [
                _optional_float(track.get("nearest_lane_distance_m"))
                for track in track_audit
            ]
        ),
        "track_audit": track_audit,
        "threshold_sweep": sweeps,
        "recommendation": _recommendation(sweeps, track_audit),
        "local_packet_path": str(packet_path),
    }
    _write_json(packet_path, case_payload)
    return case_payload


def _threshold_sweep_row(
    scenario: Scenario,
    threshold_m: float,
    constant_fde_m: float | None,
) -> dict[str, object]:
    lane = lane_aware_baseline(scenario, lane_match_threshold_m=threshold_m)
    improvement = _optional_delta(constant_fde_m, lane.fde_m)
    return {
        "threshold_m": threshold_m,
        "lane_aware_ade_m": lane.ade_m,
        "lane_aware_fde_m": lane.fde_m,
        "lane_aware_miss_rate": lane.miss_rate,
        "fde_improvement_m": improvement,
        "map_used_count": lane.map_used_count,
        "fallback_count": lane.fallback_count,
        "fallback_reasons": _fallback_reason_counts(lane.track_results),
        "map_used_track_ids": [
            result.track_id for result in lane.track_results if result.map_used
        ],
        "label": _sweep_label(
            map_used_count=lane.map_used_count,
            fallback_count=lane.fallback_count,
            fde_improvement_m=improvement,
        ),
    }


def _track_audit_rows(
    debug_case: dict[str, object],
    sweeps: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for track in _required_list(debug_case, "track_diagnostics"):
        if not isinstance(track, dict):
            continue
        lane = _required_mapping(track, "lane_match")
        track_id = str(track["track_id"])
        rows.append(
            {
                "track_id": track_id,
                "agent_type": track.get("agent_type", "unknown"),
                "nearest_lane_distance_m": lane.get("nearest_lane_distance_m"),
                "anchor_speed_mps": lane.get("anchor_speed_mps"),
                "default_fallback_reason": track.get("lane_fallback_reason"),
                "default_lane_match_status": lane.get("status"),
                "first_matched_threshold_m": _first_matched_threshold(track_id, sweeps),
                "constant_velocity_fde_m": track.get("constant_velocity_fde_m"),
                "lane_aware_fde_m": track.get("lane_aware_fde_m"),
            }
        )
    return rows


def _fallback_cases(cases: list[object]) -> list[dict[str, object]]:
    selected = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        summary = _required_mapping(case, "summary")
        fallback_count = _optional_int(summary.get("fallback_count")) or 0
        if fallback_count <= 0:
            continue
        selected.append(case)
    return sorted(
        selected,
        key=lambda case: (
            -(_optional_int(_required_mapping(case, "summary").get("fallback_count")) or 0),
            _optional_int(_required_mapping(case, "summary").get("map_used_count")) or 0,
            str(case.get("scenario_id", "")),
        ),
    )


def _recommendation(
    sweeps: list[dict[str, object]],
    tracks: list[dict[str, object]],
) -> dict[str, object]:
    if not sweeps:
        return {
            "label": "not_evaluable",
            "reason": "No threshold sweep rows were produced.",
        }
    default = sweeps[0]
    usable = [sweep for sweep in sweeps if sweep.get("fde_improvement_m") is not None]
    best = max(
        usable,
        key=lambda row: float(row["fde_improvement_m"]),
        default=default,
    )
    max_distance = max(
        (
            float(distance)
            for distance in (
                track.get("nearest_lane_distance_m") for track in tracks
            )
            if distance is not None
        ),
        default=None,
    )
    if int(default["map_used_count"]) == 0 and float(best["fde_improvement_m"] or 0.0) <= 0.0:
        if max_distance is not None and max_distance > 50.0:
            return {
                "label": "audit_coordinate_frame_or_lane_set",
                "reason": (
                    "Default matching falls back for every target, and widening "
                    "the threshold does not improve FDE. Several targets are far "
                    "from parsed lane polylines, so coordinate frames, lane "
                    "coverage, and lane-selection logic should be audited first."
                ),
            }
        return {
            "label": "keep_default_threshold",
            "reason": (
                "Widening the threshold does not improve FDE, so accepting "
                "farther lane matches would reduce diagnostic quality."
            ),
        }
    if float(best["fde_improvement_m"] or 0.0) > 0.0:
        return {
            "label": "candidate_threshold_needs_validation",
            "reason": (
                f"The best sweep threshold ({_meter_text(best['threshold_m'])}) "
                "improves FDE on this case, but it should be validated across "
                "more scenarios before changing the default matcher."
            ),
        }
    return {
        "label": "manual_map_match_review",
        "reason": "The sweep is mixed or inconclusive and needs case-level review.",
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    audited = [case for case in cases if bool(case.get("ready"))]
    default_map_used = sum(int(case["default_map_used_count"]) for case in audited)
    default_fallbacks = sum(int(case["default_fallback_count"]) for case in audited)
    best_rows = []
    for case in audited:
        sweeps = _required_list(case, "threshold_sweep")
        usable = [
            sweep
            for sweep in sweeps
            if isinstance(sweep, dict) and sweep.get("fde_improvement_m") is not None
        ]
        if usable:
            best_rows.append(
                max(usable, key=lambda row: float(row["fde_improvement_m"]))
            )
    best_improvement = (
        round(sum(float(row["fde_improvement_m"]) for row in best_rows), 3)
        if best_rows
        else None
    )
    return {
        "audited_case_count": len(audited),
        "audited_target_count": sum(
            int(case["evaluated_target_count"]) for case in audited
        ),
        "default_map_used_count": default_map_used,
        "default_fallback_count": default_fallbacks,
        "best_threshold_map_used_count": sum(
            int(row["map_used_count"]) for row in best_rows
        ),
        "best_threshold_fde_improvement_m": best_improvement,
        "widening_worse_case_count": sum(
            any(
                isinstance(sweep, dict)
                and float(sweep.get("threshold_m", 0.0)) > LANE_MATCH_THRESHOLD_M
                and (sweep.get("fde_improvement_m") is not None)
                and float(sweep["fde_improvement_m"]) < 0.0
                for sweep in _required_list(case, "threshold_sweep")
            )
            for case in audited
        ),
    }


def _clean_thresholds(thresholds_m: tuple[float, ...]) -> tuple[float, ...]:
    values = {float(value) for value in thresholds_m if isfinite(float(value))}
    values.add(LANE_MATCH_THRESHOLD_M)
    if any(value <= 0 for value in values):
        raise ValueError("All lane-match thresholds must be positive.")
    return tuple(sorted(values))


def _first_matched_threshold(
    track_id: str,
    sweeps: list[dict[str, object]],
) -> float | None:
    for sweep in sweeps:
        ids = sweep.get("map_used_track_ids", [])
        if isinstance(ids, list) and track_id in ids:
            return float(sweep["threshold_m"])
    return None


def _fallback_reason_counts(results: tuple[object, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        reason = getattr(result, "fallback_reason", None)
        if reason:
            counts[str(reason)] = counts.get(str(reason), 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _sweep_label(
    map_used_count: int,
    fallback_count: int,
    fde_improvement_m: float | None,
) -> str:
    if map_used_count == 0 and fallback_count > 0:
        return "all_targets_fallback"
    if fde_improvement_m is None:
        return "not_evaluable"
    if fde_improvement_m < 0:
        return "worse_than_constant_velocity"
    if fde_improvement_m > 0:
        return "improves_over_constant_velocity"
    return "same_as_constant_velocity"


def _distance_summary(values: list[float | None]) -> dict[str, object]:
    distances = [float(value) for value in values if value is not None]
    if not distances:
        return {"min_m": None, "max_m": None, "mean_m": None}
    return {
        "min_m": round(min(distances), 3),
        "max_m": round(max(distances), 3),
        "mean_m": round(sum(distances) / len(distances), 3),
    }


def _find_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str,
) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _optional_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 3)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _distance_range_text(summary: dict[str, object]) -> str:
    if summary.get("min_m") is None or summary.get("max_m") is None:
        return "n/a"
    return f"{_meter_text(summary['min_m'])} - {_meter_text(summary['max_m'])}"


def _meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    return f"{number:.3f} m"


def _mps_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    return f"{number:.3f} m/s"


def _signed_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _safe_slug(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {"-", "_", " "}:
            safe.append("-")
    return "-".join("".join(safe).split("-"))[:120] or "case"


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
