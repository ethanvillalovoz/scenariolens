from __future__ import annotations

import json
from dataclasses import dataclass
from math import acos, degrees, hypot, isfinite
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.prediction import (
    HEADING_AWARE_ALIGNMENT_PENALTY_M,
    HEADING_AWARE_MIN_ALIGNMENT,
    LANE_MATCH_THRESHOLD_M,
    _anchor_index,
    _feature_points,
    _lane_direction,
    _lane_heading_alignment,
    _lane_length,
    _project_to_lane,
    constant_velocity_baseline,
    heading_aware_lane_baseline,
    lane_aware_baseline,
)
from scenariolens.replay_prototype import REPLAY_PROTOTYPE_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State

ROUTE_INTENT_AUDIT_FORMAT = "scenariolens.route_intent_audit.v1"


@dataclass(frozen=True)
class RouteIntentAuditResult:
    """Files produced by a route/intent diagnostic run."""

    ready: bool
    case_count: int
    audited_track_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_route_intent_audit(
    replay_manifest_path: str | Path,
    output_dir: str | Path,
    case_count: int = 3,
    public_report_path: str | Path | None = None,
) -> RouteIntentAuditResult:
    """Generate a public-safe route/intent audit from replay-prototype output."""

    source = Path(replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = route_intent_audit_payload(
        replay_manifest_path=source,
        output_dir=target,
        case_count=case_count,
    )
    report = route_intent_audit_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return RouteIntentAuditResult(
        ready=bool(payload["ready"]),
        case_count=len(_required_list(payload, "cases")),
        audited_track_count=int(aggregate["audited_track_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def route_intent_audit_payload(
    replay_manifest_path: Path,
    output_dir: Path,
    case_count: int,
) -> dict[str, object]:
    """Return deterministic diagnostics for stable replay regression cases."""

    if case_count < 1:
        raise ValueError("case-count must be at least 1.")

    replay_payload = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay_payload.get("format") != REPLAY_PROTOTYPE_FORMAT:
        raise ValueError(
            "Expected a replay-prototype manifest with format "
            f"{REPLAY_PROTOTYPE_FORMAT}."
        )

    selected = _selected_regression_cases(
        _required_list(replay_payload, "cases"),
    )[:case_count]
    cases = [
        _audit_case(
            replay_case=case,
            output_dir=output_dir,
            rank=index,
        )
        for index, case in enumerate(selected, start=1)
    ]
    aggregate = _aggregate_cases(cases)
    ready = bool(replay_payload.get("ready")) and any(
        bool(case.get("ready")) for case in cases
    )

    return {
        "format": ROUTE_INTENT_AUDIT_FORMAT,
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay_payload.get("format"),
        "source_kind": replay_payload.get("source_kind"),
        "output_dir": str(output_dir),
        "ready": ready,
        "requested_case_count": case_count,
        "selected_case_count": len(selected),
        "case_count": len(cases),
        "default_lane_match_threshold_m": LANE_MATCH_THRESHOLD_M,
        "heading_min_alignment": HEADING_AWARE_MIN_ALIGNMENT,
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
        "scope_note": (
            "Route/intent diagnostic only; this does not infer an official route "
            "plan, change the baseline, run closed-loop simulation, or claim a "
            "Waymo benchmark result."
        ),
    }


def route_intent_audit_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a route/intent audit payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    lines = [
        "# ScenarioLens Route/Intent Audit",
        "",
        "This report follows the stable context replay regression one step "
        "deeper. It reloads replayed local scenarios, compares constant-velocity, "
        "nearest-lane, and heading-aware open-loop rollouts, and asks whether "
        "the lane-aware failure looks like route/intent ambiguity rather than a "
        "simple threshold issue.",
        "",
        "It is intentionally scoped: this is not a route planner, not a matcher "
        "change, not closed-loop simulation, and not a Waymo benchmark claim. "
        "Raw Waymo files and local per-case packets stay out of git.",
        "",
        "## Scope",
        "",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Source kind: `{payload.get('source_kind', 'unknown')}`",
        f"- Ready for audit: {payload['ready']}",
        f"- Cases audited: {payload['case_count']}",
        f"- Default lane-match threshold: {_meter_text(payload['default_lane_match_threshold_m'])}",
        "- Raw Waymo files committed: no",
        "- Local route/intent packets committed: no",
        "",
        "## Audit Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Audited cases | {aggregate['audited_case_count']} |",
        f"| Audited tracks | {aggregate['audited_track_count']} |",
        f"| Stable replay regression cases | {aggregate['stable_regression_case_count']} |",
        f"| Nearest-lane regression tracks | {aggregate['nearest_regression_track_count']} |",
        f"| Heading-fix candidate tracks | {aggregate['heading_fix_candidate_count']} |",
        f"| Route/intent diagnostic tracks | {aggregate['route_intent_candidate_count']} |",
        f"| Lane-continuity risk tracks | {aggregate['lane_continuity_risk_count']} |",
        "",
    ]

    if not cases:
        lines.extend(
            [
                "No stable replay regression cases were found in the replay "
                "prototype manifest.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Case Summary",
            "",
            "| Rank | Scenario | Case | Tracks | CV FDE | Nearest FDE | Heading FDE | Worst delta | Main diagnosis |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        diagnosis = _required_mapping(case, "primary_diagnosis")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"{case['case_label']} | "
            f"{summary['audited_track_count']} | "
            f"{_meter_text(summary['constant_velocity_fde_m'])} | "
            f"{_meter_text(summary['nearest_lane_fde_m'])} | "
            f"{_meter_text(summary['heading_lane_fde_m'])} | "
            f"{_signed_meter_text(summary['worst_nearest_delta_m'])} | "
            f"`{diagnosis['label']}` |"
        )

    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        route_context = _required_mapping(case, "route_context")
        diagnosis = _required_mapping(case, "primary_diagnosis")
        tracks = _required_list(case, "track_audits")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}`",
                "",
                f"- Case: {case['case_label']}",
                f"- Source: `{case['source_name']}`",
                f"- Replay stability: `{case['replay_stability_label']}`",
                f"- Primary diagnosis: **{diagnosis['label']}**",
                f"- Why: {diagnosis['reason']}",
                f"- Recommended next action: {diagnosis['next_action']}",
                f"- Scenario route links: {route_context['route_link_count']} "
                f"(entry {route_context['entry_link_count']}, exit "
                f"{route_context['exit_link_count']}, neighbors "
                f"{route_context['neighbor_link_count']})",
                f"- Local audit packet: `{case['local_packet_path']}`",
                "",
                "Track diagnostics:",
                "",
                "| Track | CV FDE | Nearest FDE | Heading FDE | Nearest delta | Heading vs nearest | Lane dist | Future dist to lane | Future-lane align | Route hints | Diagnosis |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            nearest = _required_mapping(track, "nearest_lane")
            track_diagnosis = _required_mapping(track, "diagnosis")
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"{_meter_text(track['constant_velocity_fde_m'])} | "
                f"{_meter_text(track['nearest_lane_fde_m'])} | "
                f"{_meter_text(track['heading_lane_fde_m'])} | "
                f"{_signed_meter_text(track['nearest_vs_constant_fde_delta_m'])} | "
                f"{_signed_meter_text(track['heading_vs_nearest_fde_delta_m'])} | "
                f"{_meter_text(nearest['anchor_lane_distance_m'])} | "
                f"{_meter_text(nearest['actual_final_distance_to_lane_m'])} | "
                f"{_number_text(nearest['actual_future_alignment_to_horizon_tangent'])} | "
                f"{nearest['route_hint_count']} | "
                f"`{track_diagnosis['label']}` |"
            )

        lines.extend(
            [
                "",
                "Case metrics:",
                "",
                f"- Constant-velocity FDE: {_meter_text(summary['constant_velocity_fde_m'])}",
                f"- Nearest-lane FDE: {_meter_text(summary['nearest_lane_fde_m'])}",
                f"- Heading-aware FDE: {_meter_text(summary['heading_lane_fde_m'])}",
                f"- Stable replay sign: {summary['stable_replay_sign_preserved']}",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A stable replay regression means the warning persisted under small anchor-state perturbations; it does not prove the map baseline is generally bad.",
            "- If heading-aware selection fixes the nearest-lane regression, lane selection should be improved before heavier simulation work.",
            "- If both nearest-lane and heading-aware rollouts fail while route/topology hints exist, the likely next step is route or intent conditioning rather than a wider lane-match radius.",
            "- Lane-continuity and curvature warnings identify cases where following the selected lane centerline through the horizon can diverge from the target's actual future motion.",
            "- This audit keeps the public artifact honest: it explains a replayed failure mode without changing the default scoring baseline.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _selected_regression_cases(cases: list[object]) -> list[dict[str, object]]:
    regression_cases = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        nominal = _required_mapping(case, "nominal")
        if str(case.get("readiness")) != "ready_for_regression_replay":
            continue
        delta = _optional_float(nominal.get("fde_improvement_m"))
        if delta is None or delta >= 0.0:
            continue
        regression_cases.append(case)

    stable = [
        case
        for case in regression_cases
        if _required_mapping(case, "perturbation_stability").get("label")
        == "stable_regression_warning"
    ]
    selected = stable or regression_cases
    return sorted(
        selected,
        key=lambda case: (
            float(_required_mapping(case, "nominal").get("fde_improvement_m") or 0.0),
            str(case.get("scenario_id", "")),
        ),
    )


def _audit_case(
    replay_case: dict[str, object],
    output_dir: Path,
    rank: int,
) -> dict[str, object]:
    source_input = Path(str(replay_case["source_input"]))
    input_format = str(replay_case.get("input_format", "native"))
    input_ready, preflight, scenarios = load_failure_study_input(
        source=source_input,
        input_format=input_format,
        max_scenarios=None,
    )
    scenario = _find_scenario(scenarios, str(replay_case["scenario_id"]))
    case_slug = _safe_slug(
        f"{rank}-{replay_case.get('case_label', 'case')}-{replay_case['scenario_id']}"
    )
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    packet_path = case_dir / "route_intent_audit.json"

    if scenario is None:
        case_payload = {
            "ready": False,
            "rank": rank,
            "case_label": replay_case.get("case_label", "Case"),
            "scenario_id": replay_case.get("scenario_id", ""),
            "source_name": replay_case.get("source_name", source_input.name),
            "error": "scenario_not_found",
            "input_ready": input_ready,
            "preflight": preflight or {},
            "route_context": _empty_route_context(),
            "summary": _empty_summary(),
            "primary_diagnosis": _diagnosis(
                "not_evaluable",
                "Scenario could not be reloaded from the local source.",
                "Confirm local raw data is present, then rerun the audit.",
            ),
            "track_audits": [],
            "local_packet_path": str(packet_path),
        }
        _write_json(packet_path, case_payload)
        return case_payload

    constant = constant_velocity_baseline(scenario)
    nearest = lane_aware_baseline(scenario)
    heading = heading_aware_lane_baseline(scenario)
    track_audits = _track_audits(
        replay_case=replay_case,
        scenario=scenario,
        constant_results=constant.track_results,
        nearest_results=nearest.track_results,
        heading_results=heading.track_results,
    )
    summary = _case_summary(
        replay_case=replay_case,
        constant_fde=constant.fde_m,
        nearest_fde=nearest.fde_m,
        heading_fde=heading.fde_m,
        track_audits=track_audits,
    )
    primary = _primary_diagnosis(track_audits)
    case_payload = {
        "ready": bool(input_ready),
        "rank": rank,
        "case_label": replay_case.get("case_label", "Case"),
        "scenario_id": scenario.scenario_id,
        "source_input": str(source_input),
        "source_name": replay_case.get("source_name", source_input.name),
        "input_format": input_format,
        "input_ready": input_ready,
        "preflight": preflight or {},
        "replay_readiness": replay_case.get("readiness"),
        "replay_stability_label": _required_mapping(
            replay_case,
            "perturbation_stability",
        ).get("label"),
        "route_context": _route_context(scenario),
        "summary": summary,
        "primary_diagnosis": primary,
        "track_audits": track_audits,
        "local_packet_path": str(packet_path),
    }
    _write_json(packet_path, case_payload)
    return case_payload


def _track_audits(
    replay_case: dict[str, object],
    scenario: Scenario,
    constant_results: tuple[object, ...],
    nearest_results: tuple[object, ...],
    heading_results: tuple[object, ...],
) -> list[dict[str, object]]:
    tracks_by_id = {track.agent_id: track for track in scenario.tracks}
    constant_by_id = {getattr(result, "track_id"): result for result in constant_results}
    nearest_by_id = {getattr(result, "track_id"): result for result in nearest_results}
    heading_by_id = {getattr(result, "track_id"): result for result in heading_results}
    selected_ids = _regression_track_ids(replay_case)
    rows = []
    for track_id in selected_ids:
        track = tracks_by_id.get(track_id)
        constant = constant_by_id.get(track_id)
        nearest = nearest_by_id.get(track_id)
        heading = heading_by_id.get(track_id)
        if track is None or constant is None or nearest is None or heading is None:
            continue
        nearest_diag = _lane_choice_diagnostic(track, scenario, selection="nearest")
        heading_diag = _lane_choice_diagnostic(track, scenario, selection="heading")
        row = {
            "track_id": track_id,
            "agent_type": track.agent_type,
            "constant_velocity_fde_m": getattr(constant, "fde_m"),
            "nearest_lane_fde_m": getattr(nearest, "fde_m"),
            "heading_lane_fde_m": getattr(heading, "fde_m"),
            "nearest_vs_constant_fde_delta_m": _optional_delta(
                getattr(constant, "fde_m"),
                getattr(nearest, "fde_m"),
            ),
            "heading_vs_nearest_fde_delta_m": _optional_delta(
                getattr(nearest, "fde_m"),
                getattr(heading, "fde_m"),
            ),
            "heading_vs_constant_fde_delta_m": _optional_delta(
                getattr(constant, "fde_m"),
                getattr(heading, "fde_m"),
            ),
            "nearest_lane_map_used": getattr(nearest, "map_used"),
            "heading_lane_map_used": getattr(heading, "map_used"),
            "nearest_lane": nearest_diag,
            "heading_lane": heading_diag,
        }
        row["diagnosis"] = _track_diagnosis(row)
        rows.append(row)
    return rows


def _regression_track_ids(replay_case: dict[str, object]) -> tuple[str, ...]:
    selected = []
    for track in _required_list(replay_case, "track_replays"):
        if not isinstance(track, dict):
            continue
        delta = _optional_float(track.get("fde_improvement_m"))
        if delta is not None and delta < 0.0 and bool(track.get("lane_map_used")):
            selected.append(str(track["track_id"]))
    if selected:
        return tuple(selected)
    return tuple(
        str(track["track_id"])
        for track in _required_list(replay_case, "track_replays")
        if isinstance(track, dict) and bool(track.get("lane_map_used"))
    )


def _lane_choice_diagnostic(
    track: AgentTrack,
    scenario: Scenario,
    selection: str,
) -> dict[str, object]:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return _empty_lane_choice("insufficient_track_states")
    anchor = states[_anchor_index(states, scenario)]
    future_states = tuple(state for state in states if state.t > anchor.t)
    if not future_states:
        return _empty_lane_choice("no_future_states")
    final_actual = future_states[-1]
    anchor_speed = hypot(anchor.vx, anchor.vy)
    if not isfinite(anchor_speed) or anchor_speed <= 0.0:
        return _empty_lane_choice("low_or_invalid_anchor_speed")

    choice = _select_lane_feature(anchor, scenario, selection=selection)
    if choice is None:
        return _empty_lane_choice("no_usable_lane_polyline")
    projection = choice["projection"]
    assert hasattr(projection, "distance_m")
    if float(projection.distance_m) > LANE_MATCH_THRESHOLD_M:
        return _lane_choice_payload(
            status="target_too_far_from_lane",
            choice=choice,
            anchor=anchor,
            final_actual=final_actual,
            anchor_speed=anchor_speed,
        )
    if selection == "heading" and float(choice["heading_alignment"]) < HEADING_AWARE_MIN_ALIGNMENT:
        return _lane_choice_payload(
            status="lane_heading_misaligned",
            choice=choice,
            anchor=anchor,
            final_actual=final_actual,
            anchor_speed=anchor_speed,
        )
    return _lane_choice_payload(
        status="lane_matched",
        choice=choice,
        anchor=anchor,
        final_actual=final_actual,
        anchor_speed=anchor_speed,
    )


def _select_lane_feature(
    anchor: State,
    scenario: Scenario,
    selection: str,
) -> dict[str, object] | None:
    choices = _lane_feature_projections(anchor, scenario)
    if not choices:
        return None
    if selection == "nearest":
        return min(choices, key=lambda item: float(item["distance_m"]))
    if selection != "heading":
        raise ValueError(f"Unsupported lane selection: {selection}")
    in_range = [
        item for item in choices if float(item["distance_m"]) <= LANE_MATCH_THRESHOLD_M
    ]
    aligned = [
        item
        for item in in_range
        if float(item["heading_alignment"]) >= HEADING_AWARE_MIN_ALIGNMENT
    ]
    if not aligned:
        return min(choices, key=lambda item: float(item["distance_m"]))
    return min(
        aligned,
        key=lambda item: float(item["distance_m"])
        + HEADING_AWARE_ALIGNMENT_PENALTY_M
        * (1.0 - float(item["heading_alignment"])),
    )


def _lane_feature_projections(
    anchor: State,
    scenario: Scenario,
) -> list[dict[str, object]]:
    features = scenario.metadata.get("waymo_map_features", ())
    if not isinstance(features, list):
        return []
    choices = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("kind") != "lane":
            continue
        lane = _feature_points(feature)
        if len(lane) < 2:
            continue
        projection = _project_to_lane(anchor.x, anchor.y, lane)
        if projection is None:
            continue
        choices.append(
            {
                "feature": feature,
                "lane": lane,
                "projection": projection,
                "distance_m": round(projection.distance_m, 3),
                "heading_alignment": round(
                    _lane_heading_alignment(anchor, projection),
                    3,
                ),
            }
        )
    return choices


def _lane_choice_payload(
    status: str,
    choice: dict[str, object],
    anchor: State,
    final_actual: State,
    anchor_speed: float,
) -> dict[str, object]:
    feature = _required_mapping(choice, "feature")
    lane = choice["lane"]
    projection = choice["projection"]
    assert isinstance(lane, tuple)
    direction = _lane_direction(anchor, projection)  # type: ignore[arg-type]
    lane_length = _lane_length(lane)
    horizon_s = final_actual.t - anchor.t
    travel_m = max(0.0, anchor_speed * horizon_s)
    remaining_m = (
        lane_length - projection.arc_length_m
        if direction >= 0.0
        else projection.arc_length_m
    )
    target_s = max(
        0.0,
        min(lane_length, projection.arc_length_m + (travel_m * direction)),
    )
    final_projection = _project_to_lane(final_actual.x, final_actual.y, lane)
    start_tangent = _travel_tangent(projection, direction)
    horizon_tangent = _tangent_at_arc(lane, target_s, direction)
    actual_vector = (final_actual.x - anchor.x, final_actual.y - anchor.y)
    return {
        "status": status,
        "feature_id": feature.get("feature_id"),
        "feature_type": feature.get("feature_type"),
        "speed_limit_mph": feature.get("speed_limit_mph"),
        "anchor_lane_distance_m": round(float(projection.distance_m), 3),
        "anchor_heading_alignment": round(float(choice["heading_alignment"]), 3),
        "actual_future_alignment_to_anchor_tangent": _vector_alignment(
            actual_vector,
            start_tangent,
        ),
        "actual_future_alignment_to_horizon_tangent": _vector_alignment(
            actual_vector,
            horizon_tangent,
        ),
        "lane_tangent_change_deg": _angle_between(start_tangent, horizon_tangent),
        "actual_final_distance_to_lane_m": (
            round(final_projection.distance_m, 3)
            if final_projection is not None
            else None
        ),
        "anchor_speed_mps": round(anchor_speed, 3),
        "horizon_s": round(horizon_s, 3),
        "travel_m": round(travel_m, 3),
        "remaining_lane_m": round(max(remaining_m, 0.0), 3),
        "lane_end_clamp_risk": travel_m >= max(remaining_m - 0.001, 0.0),
        "route_hint_count": _route_hint_count(feature),
        "entry_lane_count": len(_as_list(feature.get("entry_lanes"))),
        "exit_lane_count": len(_as_list(feature.get("exit_lanes"))),
        "neighbor_count": int(feature.get("left_neighbor_count", 0) or 0)
        + int(feature.get("right_neighbor_count", 0) or 0),
        "lane_point_count": len(lane),
        "lane_segment_index": projection.segment_index,
    }


def _track_diagnosis(row: dict[str, object]) -> dict[str, object]:
    nearest_delta = _optional_float(row.get("nearest_vs_constant_fde_delta_m"))
    heading_vs_nearest = _optional_float(row.get("heading_vs_nearest_fde_delta_m"))
    heading_vs_constant = _optional_float(row.get("heading_vs_constant_fde_delta_m"))
    nearest = _required_mapping(row, "nearest_lane")
    if nearest_delta is None or nearest_delta >= 0.0:
        return _diagnosis(
            "not_a_nearest_lane_regression",
            "The audited track is not worse than constant velocity under nearest-lane following.",
            "Keep this as context, but prioritize true replay regressions first.",
        )
    if (
        heading_vs_nearest is not None
        and heading_vs_nearest > 1.0
        and heading_vs_constant is not None
        and heading_vs_constant >= 0.0
    ):
        return _diagnosis(
            "heading_selector_fix_candidate",
            "Heading-aware lane selection removes the nearest-lane regression on this track.",
            "Promote this case into the heading-aware selector validation set.",
        )
    if bool(nearest.get("lane_end_clamp_risk")):
        return _diagnosis(
            "lane_continuity_or_route_link_needed",
            "The target would run beyond the selected lane polyline during the forecast horizon.",
            "Inspect lane continuation links before trusting a lane-following rollout.",
        )
    tangent_change = _optional_float(nearest.get("lane_tangent_change_deg")) or 0.0
    future_alignment = _optional_float(
        nearest.get("actual_future_alignment_to_horizon_tangent")
    )
    route_hints = int(nearest.get("route_hint_count", 0) or 0)
    final_lane_distance = _optional_float(nearest.get("actual_final_distance_to_lane_m"))
    if (
        route_hints > 0
        and (
            (future_alignment is not None and future_alignment < 0.35)
            or tangent_change >= 35.0
            or (final_lane_distance is not None and final_lane_distance > 10.0)
        )
    ):
        return _diagnosis(
            "route_intent_prior_needed",
            "The selected lane is locally plausible, but the target's future motion diverges from that lane through the horizon.",
            "Add route/intent checks before treating lane-following as a stronger predictor.",
        )
    if route_hints == 0:
        return _diagnosis(
            "map_topology_gap",
            "The selected lane has no parsed entry, exit, or neighbor hints in this lightweight reader.",
            "Improve parsed topology coverage before adding route-conditioned logic.",
        )
    return _diagnosis(
        "manual_route_intent_review",
        "The regression is not explained by heading selection, lane continuity, or obvious route-hint gaps.",
        "Review the local overlay and per-track packet before changing baseline behavior.",
    )


def _primary_diagnosis(track_audits: list[dict[str, object]]) -> dict[str, object]:
    if not track_audits:
        return _diagnosis(
            "not_evaluable",
            "No map-used regression tracks were available for audit.",
            "Regenerate the replay prototype or inspect fallback-heavy cases instead.",
        )
    priority = {
        "route_intent_prior_needed": 0,
        "lane_continuity_or_route_link_needed": 1,
        "heading_selector_fix_candidate": 2,
        "map_topology_gap": 3,
        "manual_route_intent_review": 4,
        "not_a_nearest_lane_regression": 5,
    }
    return min(
        (_required_mapping(track, "diagnosis") for track in track_audits),
        key=lambda diagnosis: priority.get(str(diagnosis.get("label")), 99),
    )


def _case_summary(
    replay_case: dict[str, object],
    constant_fde: float | None,
    nearest_fde: float | None,
    heading_fde: float | None,
    track_audits: list[dict[str, object]],
) -> dict[str, object]:
    deltas = [
        float(track["nearest_vs_constant_fde_delta_m"])
        for track in track_audits
        if track.get("nearest_vs_constant_fde_delta_m") is not None
    ]
    stability = _required_mapping(replay_case, "perturbation_stability")
    return {
        "audited_track_count": len(track_audits),
        "constant_velocity_fde_m": constant_fde,
        "nearest_lane_fde_m": nearest_fde,
        "heading_lane_fde_m": heading_fde,
        "worst_nearest_delta_m": min(deltas) if deltas else None,
        "stable_replay_sign_preserved": (
            stability.get("label") == "stable_regression_warning"
        ),
    }


def _route_context(scenario: Scenario) -> dict[str, object]:
    summary = scenario.metadata.get("waymo_map_summary", {})
    if not isinstance(summary, dict):
        return _empty_route_context()
    return {
        "lane_count": int(summary.get("lane_count", 0) or 0),
        "entry_link_count": int(summary.get("entry_link_count", 0) or 0),
        "exit_link_count": int(summary.get("exit_link_count", 0) or 0),
        "neighbor_link_count": int(summary.get("neighbor_link_count", 0) or 0),
        "route_link_count": int(summary.get("route_link_count", 0) or 0),
        "has_route_context": bool(summary.get("has_route_context")),
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    audited = [case for case in cases if bool(case.get("ready"))]
    tracks = [
        track
        for case in audited
        for track in _required_list(case, "track_audits")
        if isinstance(track, dict)
    ]
    diagnoses = [_required_mapping(track, "diagnosis") for track in tracks]
    return {
        "audited_case_count": len(audited),
        "audited_track_count": len(tracks),
        "stable_regression_case_count": sum(
            str(case.get("replay_stability_label")) == "stable_regression_warning"
            for case in audited
        ),
        "nearest_regression_track_count": sum(
            (_optional_float(track.get("nearest_vs_constant_fde_delta_m")) or 0.0)
            < 0.0
            for track in tracks
        ),
        "heading_fix_candidate_count": _diagnosis_count(
            diagnoses,
            "heading_selector_fix_candidate",
        ),
        "route_intent_candidate_count": _diagnosis_count(
            diagnoses,
            "route_intent_prior_needed",
        ),
        "lane_continuity_risk_count": _diagnosis_count(
            diagnoses,
            "lane_continuity_or_route_link_needed",
        ),
    }


def _diagnosis_count(
    diagnoses: list[dict[str, object]],
    label: str,
) -> int:
    return sum(str(diagnosis.get("label")) == label for diagnosis in diagnoses)


def _empty_lane_choice(status: str) -> dict[str, object]:
    return {
        "status": status,
        "feature_id": None,
        "feature_type": None,
        "speed_limit_mph": None,
        "anchor_lane_distance_m": None,
        "anchor_heading_alignment": None,
        "actual_future_alignment_to_anchor_tangent": None,
        "actual_future_alignment_to_horizon_tangent": None,
        "lane_tangent_change_deg": None,
        "actual_final_distance_to_lane_m": None,
        "anchor_speed_mps": None,
        "horizon_s": None,
        "travel_m": None,
        "remaining_lane_m": None,
        "lane_end_clamp_risk": False,
        "route_hint_count": 0,
        "entry_lane_count": 0,
        "exit_lane_count": 0,
        "neighbor_count": 0,
        "lane_point_count": 0,
        "lane_segment_index": None,
    }


def _empty_route_context() -> dict[str, object]:
    return {
        "lane_count": 0,
        "entry_link_count": 0,
        "exit_link_count": 0,
        "neighbor_link_count": 0,
        "route_link_count": 0,
        "has_route_context": False,
    }


def _empty_summary() -> dict[str, object]:
    return {
        "audited_track_count": 0,
        "constant_velocity_fde_m": None,
        "nearest_lane_fde_m": None,
        "heading_lane_fde_m": None,
        "worst_nearest_delta_m": None,
        "stable_replay_sign_preserved": False,
    }


def _diagnosis(label: str, reason: str, next_action: str) -> dict[str, object]:
    return {
        "label": label,
        "reason": reason,
        "next_action": next_action,
    }


def _travel_tangent(projection: object, direction: float) -> tuple[float, float]:
    dx = float(getattr(projection, "segment_dx"))
    dy = float(getattr(projection, "segment_dy"))
    length = float(getattr(projection, "segment_length_m"))
    if length <= 0.0:
        return (0.0, 0.0)
    return ((dx / length) * direction, (dy / length) * direction)


def _tangent_at_arc(
    lane: tuple[tuple[float, float], ...],
    arc_length_m: float,
    direction: float,
) -> tuple[float, float]:
    accumulated = 0.0
    for (x1, y1), (x2, y2) in zip(lane, lane[1:]):
        dx = x2 - x1
        dy = y2 - y1
        length = hypot(dx, dy)
        if length <= 0.0:
            continue
        if accumulated + length >= arc_length_m:
            return ((dx / length) * direction, (dy / length) * direction)
        accumulated += length
    if len(lane) >= 2:
        x1, y1 = lane[-2]
        x2, y2 = lane[-1]
        length = hypot(x2 - x1, y2 - y1)
        if length > 0.0:
            return (((x2 - x1) / length) * direction, ((y2 - y1) / length) * direction)
    return (0.0, 0.0)


def _vector_alignment(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float | None:
    left_norm = hypot(left[0], left[1])
    right_norm = hypot(right[0], right[1])
    if left_norm <= 0.0 or right_norm <= 0.0:
        return None
    x_alignment = (left[0] / left_norm) * (right[0] / right_norm)
    y_alignment = (left[1] / left_norm) * (right[1] / right_norm)
    return round(x_alignment + y_alignment, 3)


def _angle_between(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float | None:
    alignment = _vector_alignment(left, right)
    if alignment is None:
        return None
    clamped = max(-1.0, min(1.0, alignment))
    return round(degrees(acos(clamped)), 3)


def _route_hint_count(feature: dict[str, object]) -> int:
    return (
        len(_as_list(feature.get("entry_lanes")))
        + len(_as_list(feature.get("exit_lanes")))
        + int(feature.get("left_neighbor_count", 0) or 0)
        + int(feature.get("right_neighbor_count", 0) or 0)
    )


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _find_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str,
) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _optional_delta(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 3)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    return f"{number:.3f} m"


def _signed_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _number_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    return f"{number:.3f}"


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
