from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot, isfinite
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.ingest.waymo_motion import MAX_MAP_FEATURES_PER_SCENARIO
from scenariolens.prediction import (
    DEFAULT_MISS_THRESHOLD_M,
    LANE_MATCH_THRESHOLD_M,
    MIN_LANE_AWARE_SPEED_MPS,
    PredictionBaselineSummary,
    PredictionTrackResult,
    _advance_along_lane,
    _anchor_index,
    _evaluate_track,
    _feature_points,
    _lane_direction,
    _lane_heading_alignment,
    _lane_length,
    _prediction_target_ids,
    _project_to_lane,
    _state_error,
    _summarize_results,
    constant_velocity_baseline,
    heading_aware_lane_baseline,
    lane_aware_baseline,
)
from scenariolens.route_intent_audit import ROUTE_INTENT_AUDIT_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State

LANE_CONTINUATION_FORMAT = "scenariolens.lane_continuation_prototype.v1"


@dataclass(frozen=True)
class LaneContinuationPrototypeResult:
    """Files produced by a lane-link continuation prototype run."""

    ready: bool
    case_count: int
    evaluated_track_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


@dataclass(frozen=True)
class _LinkedLaneRoute:
    points: tuple[tuple[float, float], ...]
    feature_ids: tuple[str, ...]
    link_count: int
    status: str
    start_s: float
    base_remaining_m: float
    route_remaining_m: float


def lane_link_baseline(
    scenario: Scenario,
    miss_threshold_m: float = DEFAULT_MISS_THRESHOLD_M,
    lane_match_threshold_m: float = LANE_MATCH_THRESHOLD_M,
    max_hops: int = 2,
) -> PredictionBaselineSummary:
    """Evaluate a prototype baseline that follows parsed lane exit links.

    This is intentionally separate from the default lane-aware scorer. It tests
    whether a lane-continuity diagnosis can be explained by following parsed
    entry/exit links for a small number of hops.
    """

    summary, _ = _lane_link_baseline_with_details(
        scenario=scenario,
        miss_threshold_m=miss_threshold_m,
        lane_match_threshold_m=lane_match_threshold_m,
        max_hops=max_hops,
    )
    return summary


def generate_lane_continuation_prototype(
    audit_manifest_path: str | Path,
    output_dir: str | Path,
    case_count: int = 3,
    public_report_path: str | Path | None = None,
) -> LaneContinuationPrototypeResult:
    """Generate a public-safe lane-link continuation prototype report."""

    source = Path(audit_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_payload(
        audit_manifest_path=source,
        output_dir=target,
        case_count=case_count,
    )
    report = lane_continuation_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationPrototypeResult(
        ready=bool(payload["ready"]),
        case_count=len(_required_list(payload, "cases")),
        evaluated_track_count=int(aggregate["evaluated_track_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_payload(
    audit_manifest_path: Path,
    output_dir: Path,
    case_count: int,
) -> dict[str, object]:
    """Return deterministic lane-link continuation evidence."""

    if case_count < 1:
        raise ValueError("case-count must be at least 1.")

    audit_payload = json.loads(audit_manifest_path.read_text(encoding="utf-8"))
    if audit_payload.get("format") != ROUTE_INTENT_AUDIT_FORMAT:
        raise ValueError(
            "Expected a route-intent audit manifest with format "
            f"{ROUTE_INTENT_AUDIT_FORMAT}."
        )

    selected = _selected_lane_continuity_cases(
        _required_list(audit_payload, "cases"),
    )[:case_count]
    cases = [
        _prototype_case(
            audit_case=case,
            output_dir=output_dir,
            rank=index,
        )
        for index, case in enumerate(selected, start=1)
    ]
    aggregate = _aggregate_cases(cases)
    ready = bool(audit_payload.get("ready")) and any(
        bool(case.get("ready")) for case in cases
    )

    return {
        "format": LANE_CONTINUATION_FORMAT,
        "audit_manifest": str(audit_manifest_path),
        "audit_format": audit_payload.get("format"),
        "source_kind": audit_payload.get("source_kind"),
        "output_dir": str(output_dir),
        "ready": ready,
        "requested_case_count": case_count,
        "selected_case_count": len(selected),
        "case_count": len(cases),
        "max_lane_link_hops": 2,
        "lane_match_threshold_m": LANE_MATCH_THRESHOLD_M,
        "map_feature_cap": MAX_MAP_FEATURES_PER_SCENARIO,
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
        "scope_note": (
            "Lane-link continuation prototype only; this is not route planning, "
            "not closed-loop simulation, not a default scorer change, and not a "
            "Waymo benchmark claim."
        ),
    }


def lane_continuation_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a lane-link continuation payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    lines = [
        "# ScenarioLens Lane-Link Continuation Prototype",
        "",
        "This report follows the route/intent audit's lane-continuity warning "
        "with a small executable prototype. It reloads the audited local "
        "scenario, compares constant-velocity, nearest-lane, heading-aware, "
        "and lane-link continuation rollouts, then reports whether parsed "
        "entry/exit lane links reduce the stable regression.",
        "",
        "It is intentionally scoped: this is not route planning, not a default "
        "scorer change, not closed-loop simulation, and not a Waymo benchmark "
        "claim. Raw Waymo files and local per-case packets stay out of git.",
        "",
        "## Scope",
        "",
        f"- Route/intent audit manifest: `{payload['audit_manifest']}`",
        f"- Ready for prototype: {payload['ready']}",
        f"- Cases evaluated: {payload['case_count']}",
        f"- Max lane-link hops: {payload['max_lane_link_hops']}",
        f"- Lane-match threshold: {_meter_text(payload['lane_match_threshold_m'])}",
        f"- Waymo map feature cap: {payload['map_feature_cap']}",
        "- Raw Waymo files committed: no",
        "- Local lane-link packets committed: no",
        "",
        "## Prototype Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Evaluated cases | {aggregate['evaluated_case_count']} |",
        f"| Evaluated tracks | {aggregate['evaluated_track_count']} |",
        f"| Tracks using linked lanes | {aggregate['linked_lane_track_count']} |",
        f"| Tracks improved over nearest lane | {aggregate['improved_over_nearest_count']} |",
        f"| Tracks still clamped after links | {aggregate['still_clamped_count']} |",
        f"| Mean nearest FDE | {_meter_text(aggregate['mean_nearest_fde_m'])} |",
        f"| Mean lane-link FDE | {_meter_text(aggregate['mean_lane_link_fde_m'])} |",
        f"| Mean lane-link improvement over nearest | {_signed_meter_text(aggregate['mean_lane_link_improvement_m'])} |",
        "",
    ]

    if not cases:
        lines.extend(
            [
                "No lane-continuity audit cases were found in the route/intent "
                "manifest.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Case Summary",
            "",
            "| Rank | Scenario | Tracks | CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link improvement | Main result |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        conclusion = _required_mapping(case, "primary_conclusion")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"{summary['evaluated_track_count']} | "
            f"{_meter_text(summary['constant_velocity_fde_m'])} | "
            f"{_meter_text(summary['nearest_lane_fde_m'])} | "
            f"{_meter_text(summary['heading_lane_fde_m'])} | "
            f"{_meter_text(summary['lane_link_fde_m'])} | "
            f"{_signed_meter_text(summary['lane_link_improvement_over_nearest_m'])} | "
            f"`{conclusion['label']}` |"
        )

    for case in cases:
        assert isinstance(case, dict)
        summary = _required_mapping(case, "summary")
        conclusion = _required_mapping(case, "primary_conclusion")
        tracks = _required_list(case, "track_results")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}`",
                "",
                f"- Case: {case['case_label']}",
                f"- Source: `{case['source_name']}`",
                f"- Primary result: **{conclusion['label']}**",
                f"- Why: {conclusion['reason']}",
                f"- Recommended next action: {conclusion['next_action']}",
                f"- Local prototype packet: `{case['local_packet_path']}`",
                "",
                "Track results:",
                "",
                "| Track | CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            link = _required_mapping(track, "lane_link")
            track_conclusion = _required_mapping(track, "conclusion")
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"{_meter_text(track['constant_velocity_fde_m'])} | "
                f"{_meter_text(track['nearest_lane_fde_m'])} | "
                f"{_meter_text(track['heading_lane_fde_m'])} | "
                f"{_meter_text(track['lane_link_fde_m'])} | "
                f"{_signed_meter_text(track['lane_link_improvement_over_nearest_m'])} | "
                f"{_feature_chain_text(link)} | "
                f"{_meter_text(link['base_remaining_m'])} / {_meter_text(link['route_remaining_m'])} | "
                f"`{track_conclusion['label']}` |"
            )

        lines.extend(
            [
                "",
                "Case metrics:",
                "",
                f"- Constant-velocity FDE: {_meter_text(summary['constant_velocity_fde_m'])}",
                f"- Nearest-lane FDE: {_meter_text(summary['nearest_lane_fde_m'])}",
                f"- Heading-aware FDE: {_meter_text(summary['heading_lane_fde_m'])}",
                f"- Lane-link FDE: {_meter_text(summary['lane_link_fde_m'])}",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A lane-link improvement supports the audit finding: the nearest-lane failure was partly a lane-continuity artifact.",
            "- A remaining regression does not invalidate the framework; it points to route choice, map topology quality, speed modeling, or richer prediction logic.",
            "- This prototype keeps the default scoring baseline unchanged and treats linked-lane following as a follow-up experiment.",
            "- Public artifacts stay aggregate and diagnostic; local per-case packets and raw Waymo TFRecords remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _lane_link_baseline_with_details(
    scenario: Scenario,
    miss_threshold_m: float,
    lane_match_threshold_m: float,
    max_hops: int,
) -> tuple[PredictionBaselineSummary, dict[str, dict[str, object]]]:
    target_ids, target_source = _prediction_target_ids(scenario)
    tracks_by_id = {track.agent_id: track for track in scenario.tracks}
    results: list[PredictionTrackResult] = []
    details: dict[str, dict[str, object]] = {}
    map_used_count = 0
    fallback_count = 0

    for track_id in target_ids:
        track = tracks_by_id.get(track_id)
        if track is None:
            continue
        result, detail = _evaluate_lane_link_track(
            track=track,
            scenario=scenario,
            miss_threshold_m=miss_threshold_m,
            lane_match_threshold_m=lane_match_threshold_m,
            max_hops=max_hops,
        )
        if result is None:
            fallback_reason = str(detail.get("status", "lane_link_not_available"))
            fallback = _evaluate_track(
                track=track,
                scenario=scenario,
                miss_threshold_m=miss_threshold_m,
                baseline_name="lane_link_continuation",
                map_used=False,
                fallback_reason=fallback_reason,
            )
            if fallback is None:
                continue
            result = fallback
            fallback_count += 1
            detail["fallback_reason"] = fallback_reason
        elif result.map_used:
            map_used_count += 1
        results.append(result)
        details[track_id] = detail

    summary = _summarize_results(
        target_source=target_source,
        requested_target_count=len(target_ids),
        results=tuple(results),
        baseline_name="lane_link_continuation",
        map_used_count=map_used_count,
        fallback_count=fallback_count,
    )
    return summary, details


def _evaluate_lane_link_track(
    track: AgentTrack,
    scenario: Scenario,
    miss_threshold_m: float,
    lane_match_threshold_m: float,
    max_hops: int,
) -> tuple[PredictionTrackResult | None, dict[str, object]]:
    if track.agent_type not in {"vehicle", "cyclist"}:
        return None, _empty_lane_link_detail("non_vehicle_or_cyclist_target")

    features = _lane_features(scenario)
    if not features:
        return None, _empty_lane_link_detail("no_lane_map_features")

    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return None, _empty_lane_link_detail("insufficient_track_states")

    anchor_index = _anchor_index(states, scenario)
    anchor = states[anchor_index]
    future_states = tuple(
        state for state in states[anchor_index + 1 :] if state.t > anchor.t
    )
    if not future_states:
        return None, _empty_lane_link_detail("no_future_states")

    anchor_speed = hypot(anchor.vx, anchor.vy)
    if not isfinite(anchor_speed) or anchor_speed < MIN_LANE_AWARE_SPEED_MPS:
        return None, _empty_lane_link_detail("low_or_invalid_anchor_speed")

    choice = _nearest_lane_feature(anchor, features)
    if choice is None:
        return None, _empty_lane_link_detail("no_usable_lane_polyline")
    projection = choice["projection"]
    assert hasattr(projection, "distance_m")
    if float(projection.distance_m) > lane_match_threshold_m:
        detail = _empty_lane_link_detail("target_too_far_from_lane")
        detail["anchor_lane_distance_m"] = round(float(projection.distance_m), 3)
        return None, detail

    feature = _required_mapping(choice, "feature")
    direction = _lane_direction(anchor, projection)  # type: ignore[arg-type]
    route = _linked_lane_route(
        feature=feature,
        projection=projection,
        direction=direction,
        scenario=scenario,
        max_hops=max_hops,
    )
    predictions = tuple(
        _advance_along_lane(
            route.points,
            start_s=route.start_s,
            travel_m=anchor_speed * (actual.t - anchor.t),
            target_time_s=actual.t,
            speed_mps=anchor_speed,
        )
        for actual in future_states
    )
    errors = tuple(
        _state_error(predicted, actual)
        for predicted, actual in zip(predictions, future_states)
    )
    if not errors:
        return None, _empty_lane_link_detail("no_prediction_errors")

    horizon_travel_m = anchor_speed * (future_states[-1].t - anchor.t)
    detail = {
        "status": route.status,
        "selected_feature_id": _feature_id(feature),
        "feature_chain": list(route.feature_ids),
        "link_count": route.link_count,
        "anchor_lane_distance_m": round(float(projection.distance_m), 3),
        "anchor_heading_alignment": round(_lane_heading_alignment(anchor, projection), 3),
        "anchor_speed_mps": round(anchor_speed, 3),
        "horizon_s": round(future_states[-1].t - anchor.t, 3),
        "horizon_travel_m": round(horizon_travel_m, 3),
        "base_remaining_m": round(route.base_remaining_m, 3),
        "route_remaining_m": round(route.route_remaining_m, 3),
        "lane_end_clamp_risk_before": horizon_travel_m >= route.base_remaining_m,
        "lane_end_clamp_risk_after": horizon_travel_m >= route.route_remaining_m,
        "route_length_m": round(_lane_length(route.points), 3),
        "map_used": True,
    }
    fde = errors[-1]
    return (
        PredictionTrackResult(
            track_id=track.agent_id,
            agent_type=track.agent_type,
            anchor_time_s=round(anchor.t, 3),
            horizon_s=round(future_states[-1].t - anchor.t, 3),
            future_state_count=len(future_states),
            ade_m=round(sum(errors) / len(errors), 3),
            fde_m=round(fde, 3),
            miss=fde > miss_threshold_m,
            predicted_states=(anchor, *predictions),
            baseline_name="lane_link_continuation",
            map_used=True,
            fallback_reason=None,
        ),
        detail,
    )


def _linked_lane_route(
    feature: dict[str, object],
    projection: object,
    direction: float,
    scenario: Scenario,
    max_hops: int,
) -> _LinkedLaneRoute:
    base_lane = _feature_points(feature)
    if direction >= 0.0:
        route_points = list(base_lane)
        start_s = float(getattr(projection, "arc_length_m"))
        base_remaining = _lane_length(base_lane) - start_s
        link_field = "exit_lanes"
    else:
        route_points = list(reversed(base_lane))
        start_s = _lane_length(base_lane) - float(getattr(projection, "arc_length_m"))
        base_remaining = start_s
        link_field = "entry_lanes"

    features_by_id = _lane_features_by_id(scenario)
    current = feature
    feature_ids = [_feature_id(feature)]
    visited = set(feature_ids)
    status = "no_lane_links"
    link_count = 0

    for _ in range(max_hops):
        next_ids = _link_ids(current.get(link_field))
        if not next_ids:
            status = f"no_{link_field}"
            break
        candidate = _best_link_candidate(
            route_points=tuple(route_points),
            next_ids=next_ids,
            features_by_id=features_by_id,
            reverse=direction < 0.0,
            visited=visited,
        )
        if candidate is None:
            status = "linked_feature_missing"
            break
        next_feature, oriented_points = candidate
        next_id = _feature_id(next_feature)
        route_points = _append_lane_points(route_points, oriented_points)
        feature_ids.append(next_id)
        visited.add(next_id)
        current = next_feature
        status = "linked_lane_chain"
        link_count += 1

    route = tuple(route_points)
    route_remaining = max(_lane_length(route) - start_s, 0.0)
    return _LinkedLaneRoute(
        points=route,
        feature_ids=tuple(feature_ids),
        link_count=link_count,
        status=status,
        start_s=start_s,
        base_remaining_m=max(base_remaining, 0.0),
        route_remaining_m=route_remaining,
    )


def _prototype_case(
    audit_case: dict[str, object],
    output_dir: Path,
    rank: int,
) -> dict[str, object]:
    source_input = Path(str(audit_case["source_input"]))
    input_format = str(audit_case.get("input_format", "native"))
    input_ready, preflight, scenarios = load_failure_study_input(
        source=source_input,
        input_format=input_format,
        max_scenarios=None,
    )
    scenario = _find_scenario(scenarios, str(audit_case["scenario_id"]))
    case_slug = _safe_slug(
        f"{rank}-{audit_case.get('case_label', 'case')}-{audit_case['scenario_id']}"
    )
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    packet_path = case_dir / "lane_continuation_prototype.json"

    if scenario is None:
        case_payload = {
            "ready": False,
            "rank": rank,
            "case_label": audit_case.get("case_label", "Case"),
            "scenario_id": audit_case.get("scenario_id", ""),
            "source_name": audit_case.get("source_name", source_input.name),
            "error": "scenario_not_found",
            "input_ready": input_ready,
            "preflight": preflight or {},
            "summary": _empty_summary(),
            "primary_conclusion": _conclusion(
                "not_evaluable",
                "Scenario could not be reloaded from the local source.",
                "Confirm local raw data is present, then rerun the prototype.",
            ),
            "track_results": [],
            "local_packet_path": str(packet_path),
        }
        _write_json(packet_path, case_payload)
        return case_payload

    constant = constant_velocity_baseline(scenario)
    nearest = lane_aware_baseline(scenario)
    heading = heading_aware_lane_baseline(scenario)
    lane_link, lane_link_details = _lane_link_baseline_with_details(
        scenario=scenario,
        miss_threshold_m=DEFAULT_MISS_THRESHOLD_M,
        lane_match_threshold_m=LANE_MATCH_THRESHOLD_M,
        max_hops=2,
    )
    track_results = _selected_track_results(
        audit_case=audit_case,
        constant_results=constant.track_results,
        nearest_results=nearest.track_results,
        heading_results=heading.track_results,
        lane_link_results=lane_link.track_results,
        lane_link_details=lane_link_details,
    )
    summary = _case_summary(
        constant_fde=constant.fde_m,
        nearest_fde=nearest.fde_m,
        heading_fde=heading.fde_m,
        lane_link_fde=lane_link.fde_m,
        track_results=track_results,
    )
    primary = _primary_conclusion(track_results)
    case_payload = {
        "ready": bool(input_ready),
        "rank": rank,
        "case_label": audit_case.get("case_label", "Case"),
        "scenario_id": scenario.scenario_id,
        "source_input": str(source_input),
        "source_name": audit_case.get("source_name", source_input.name),
        "input_format": input_format,
        "input_ready": input_ready,
        "preflight": preflight or {},
        "route_intent_diagnosis": _required_mapping(
            audit_case,
            "primary_diagnosis",
        ).get("label"),
        "summary": summary,
        "primary_conclusion": primary,
        "track_results": track_results,
        "local_packet_path": str(packet_path),
    }
    _write_json(packet_path, case_payload)
    return case_payload


def _selected_track_results(
    audit_case: dict[str, object],
    constant_results: tuple[PredictionTrackResult, ...],
    nearest_results: tuple[PredictionTrackResult, ...],
    heading_results: tuple[PredictionTrackResult, ...],
    lane_link_results: tuple[PredictionTrackResult, ...],
    lane_link_details: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    constant_by_id = {result.track_id: result for result in constant_results}
    nearest_by_id = {result.track_id: result for result in nearest_results}
    heading_by_id = {result.track_id: result for result in heading_results}
    lane_link_by_id = {result.track_id: result for result in lane_link_results}
    rows = []
    for track_id in _lane_continuity_track_ids(audit_case):
        constant = constant_by_id.get(track_id)
        nearest = nearest_by_id.get(track_id)
        heading = heading_by_id.get(track_id)
        lane_link = lane_link_by_id.get(track_id)
        if (
            constant is None
            or nearest is None
            or heading is None
            or lane_link is None
        ):
            continue
        row = {
            "track_id": track_id,
            "agent_type": constant.agent_type,
            "constant_velocity_fde_m": constant.fde_m,
            "nearest_lane_fde_m": nearest.fde_m,
            "heading_lane_fde_m": heading.fde_m,
            "lane_link_fde_m": lane_link.fde_m,
            "lane_link_improvement_over_nearest_m": _optional_delta(
                nearest.fde_m,
                lane_link.fde_m,
            ),
            "lane_link_improvement_over_constant_m": _optional_delta(
                constant.fde_m,
                lane_link.fde_m,
            ),
            "lane_link_map_used": lane_link.map_used,
            "lane_link_fallback_reason": lane_link.fallback_reason,
            "lane_link": lane_link_details.get(
                track_id,
                _empty_lane_link_detail("missing_lane_link_detail"),
            ),
        }
        row["conclusion"] = _track_conclusion(row)
        rows.append(row)
    return rows


def _selected_lane_continuity_cases(cases: list[object]) -> list[dict[str, object]]:
    selected = []
    for case in cases:
        if not isinstance(case, dict) or not bool(case.get("ready")):
            continue
        if _lane_continuity_track_ids(case):
            selected.append(case)
    return sorted(
        selected,
        key=lambda case: (int(case.get("rank", 9999) or 9999), str(case.get("scenario_id", ""))),
    )


def _lane_continuity_track_ids(case: dict[str, object]) -> tuple[str, ...]:
    track_ids = []
    for track in _required_list(case, "track_audits"):
        if not isinstance(track, dict):
            continue
        diagnosis = _required_mapping(track, "diagnosis")
        if str(diagnosis.get("label")) == "lane_continuity_or_route_link_needed":
            track_ids.append(str(track["track_id"]))
    return tuple(track_ids)


def _track_conclusion(row: dict[str, object]) -> dict[str, object]:
    link = _required_mapping(row, "lane_link")
    improvement = _optional_float(row.get("lane_link_improvement_over_nearest_m"))
    if not bool(row.get("lane_link_map_used")):
        return _conclusion(
            "lane_link_not_available",
            "The prototype could not use a lane-link rollout for this target.",
            "Inspect parsed map features and fallback reason before extending the baseline.",
        )
    if int(link.get("link_count", 0) or 0) <= 0:
        return _conclusion(
            "topology_gap",
            "No usable linked lane was available from the selected map feature.",
            "Improve parsed lane topology before treating this as a route-link candidate.",
        )
    if improvement is not None and improvement > 1.0:
        return _conclusion(
            "lane_link_improvement",
            "Following parsed lane links reduced FDE versus the clamped nearest-lane rollout.",
            "Promote this case into a lane-continuation validation set.",
        )
    if bool(link.get("lane_end_clamp_risk_after")):
        return _conclusion(
            "route_horizon_still_exceeds_chain",
            "The target still travels beyond the linked lane chain within the horizon.",
            "Parse more continuation links or shorten the prototype horizon before tuning behavior.",
        )
    if improvement is not None and improvement < -1.0:
        return _conclusion(
            "continuation_regression",
            "Following parsed lane links made FDE worse than nearest-lane clamping.",
            "Inspect route choice and lane geometry before using linked-lane rollouts.",
        )
    return _conclusion(
        "neutral_continuation",
        "Linked-lane following changed little for this target.",
        "Keep the case as context, but prioritize larger linked-lane improvements or regressions.",
    )


def _primary_conclusion(track_results: list[dict[str, object]]) -> dict[str, object]:
    if not track_results:
        return _conclusion(
            "not_evaluable",
            "No lane-continuity tracks were available for this prototype.",
            "Regenerate the route/intent audit and rerun this command.",
        )
    priority = {
        "lane_link_improvement": 0,
        "continuation_regression": 1,
        "route_horizon_still_exceeds_chain": 2,
        "topology_gap": 3,
        "neutral_continuation": 4,
        "lane_link_not_available": 5,
    }
    return min(
        (_required_mapping(track, "conclusion") for track in track_results),
        key=lambda conclusion: priority.get(str(conclusion.get("label")), 99),
    )


def _case_summary(
    constant_fde: float | None,
    nearest_fde: float | None,
    heading_fde: float | None,
    lane_link_fde: float | None,
    track_results: list[dict[str, object]],
) -> dict[str, object]:
    improvements = [
        float(track["lane_link_improvement_over_nearest_m"])
        for track in track_results
        if track.get("lane_link_improvement_over_nearest_m") is not None
    ]
    return {
        "evaluated_track_count": len(track_results),
        "constant_velocity_fde_m": constant_fde,
        "nearest_lane_fde_m": nearest_fde,
        "heading_lane_fde_m": heading_fde,
        "lane_link_fde_m": lane_link_fde,
        "lane_link_improvement_over_nearest_m": (
            round(sum(improvements) / len(improvements), 3)
            if improvements
            else None
        ),
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    evaluated = [case for case in cases if bool(case.get("ready"))]
    tracks = [
        track
        for case in evaluated
        for track in _required_list(case, "track_results")
        if isinstance(track, dict)
    ]
    nearest_fdes = _numbers(track.get("nearest_lane_fde_m") for track in tracks)
    link_fdes = _numbers(track.get("lane_link_fde_m") for track in tracks)
    improvements = _numbers(
        track.get("lane_link_improvement_over_nearest_m") for track in tracks
    )
    return {
        "evaluated_case_count": len(evaluated),
        "evaluated_track_count": len(tracks),
        "linked_lane_track_count": sum(
            int(_required_mapping(track, "lane_link").get("link_count", 0) or 0) > 0
            for track in tracks
        ),
        "improved_over_nearest_count": sum(
            (_optional_float(track.get("lane_link_improvement_over_nearest_m")) or 0.0)
            > 1.0
            for track in tracks
        ),
        "still_clamped_count": sum(
            bool(_required_mapping(track, "lane_link").get("lane_end_clamp_risk_after"))
            for track in tracks
        ),
        "mean_nearest_fde_m": _mean(nearest_fdes),
        "mean_lane_link_fde_m": _mean(link_fdes),
        "mean_lane_link_improvement_m": _mean(improvements),
    }


def _lane_features(scenario: Scenario) -> list[dict[str, object]]:
    raw_features = scenario.metadata.get("waymo_map_features", ())
    if not isinstance(raw_features, list):
        return []
    features = []
    for feature in raw_features:
        if not isinstance(feature, dict) or feature.get("kind") != "lane":
            continue
        if len(_feature_points(feature)) < 2:
            continue
        features.append(feature)
    return features


def _lane_features_by_id(scenario: Scenario) -> dict[str, dict[str, object]]:
    return {
        _feature_id(feature): feature
        for feature in _lane_features(scenario)
        if _feature_id(feature)
    }


def _nearest_lane_feature(
    anchor: State,
    features: list[dict[str, object]],
) -> dict[str, object] | None:
    choices = []
    for feature in features:
        lane = _feature_points(feature)
        projection = _project_to_lane(anchor.x, anchor.y, lane)
        if projection is None:
            continue
        choices.append(
            {
                "feature": feature,
                "lane": lane,
                "projection": projection,
                "distance_m": projection.distance_m,
            }
        )
    if not choices:
        return None
    return min(choices, key=lambda choice: float(choice["distance_m"]))


def _best_link_candidate(
    route_points: tuple[tuple[float, float], ...],
    next_ids: tuple[str, ...],
    features_by_id: dict[str, dict[str, object]],
    reverse: bool,
    visited: set[str],
) -> tuple[dict[str, object], tuple[tuple[float, float], ...]] | None:
    candidates = []
    for next_id in next_ids:
        if next_id in visited:
            continue
        feature = features_by_id.get(next_id)
        if feature is None:
            continue
        points = _feature_points(feature)
        if reverse:
            points = tuple(reversed(points))
        if len(points) < 2:
            continue
        connection_distance = hypot(
            route_points[-1][0] - points[0][0],
            route_points[-1][1] - points[0][1],
        )
        continuity_penalty = 1.0 - _tangent_alignment(
            _last_tangent(route_points),
            _first_tangent(points),
        )
        candidates.append(
            (
                connection_distance + max(continuity_penalty, 0.0),
                feature,
                points,
            )
        )
    if not candidates:
        return None
    _, feature, points = min(candidates, key=lambda item: item[0])
    return feature, points


def _append_lane_points(
    route_points: list[tuple[float, float]],
    next_points: tuple[tuple[float, float], ...],
) -> list[tuple[float, float]]:
    if not next_points:
        return route_points
    start = 1 if hypot(
        route_points[-1][0] - next_points[0][0],
        route_points[-1][1] - next_points[0][1],
    ) < 0.25 else 0
    return [*route_points, *next_points[start:]]


def _feature_id(feature: dict[str, object]) -> str:
    value = feature.get("feature_id")
    return "" if value is None else str(value)


def _link_ids(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if item is not None)


def _first_tangent(points: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    if len(points) < 2:
        return (0.0, 0.0)
    return (points[1][0] - points[0][0], points[1][1] - points[0][1])


def _last_tangent(points: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    if len(points) < 2:
        return (0.0, 0.0)
    return (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])


def _tangent_alignment(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float:
    left_norm = hypot(left[0], left[1])
    right_norm = hypot(right[0], right[1])
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 0.0
    return ((left[0] / left_norm) * (right[0] / right_norm)) + (
        (left[1] / left_norm) * (right[1] / right_norm)
    )


def _empty_lane_link_detail(status: str) -> dict[str, object]:
    return {
        "status": status,
        "selected_feature_id": None,
        "feature_chain": [],
        "link_count": 0,
        "anchor_lane_distance_m": None,
        "anchor_heading_alignment": None,
        "anchor_speed_mps": None,
        "horizon_s": None,
        "horizon_travel_m": None,
        "base_remaining_m": None,
        "route_remaining_m": None,
        "lane_end_clamp_risk_before": False,
        "lane_end_clamp_risk_after": False,
        "route_length_m": None,
        "map_used": False,
    }


def _empty_summary() -> dict[str, object]:
    return {
        "evaluated_track_count": 0,
        "constant_velocity_fde_m": None,
        "nearest_lane_fde_m": None,
        "heading_lane_fde_m": None,
        "lane_link_fde_m": None,
        "lane_link_improvement_over_nearest_m": None,
    }


def _conclusion(label: str, reason: str, next_action: str) -> dict[str, object]:
    return {
        "label": label,
        "reason": reason,
        "next_action": next_action,
    }


def _feature_chain_text(link: dict[str, object]) -> str:
    chain = link.get("feature_chain")
    if not isinstance(chain, list) or not chain:
        return "n/a"
    return " -> ".join(str(item) for item in chain)


def _numbers(values: object) -> tuple[float, ...]:
    numbers = []
    for value in values:
        number = _optional_float(value)
        if number is not None:
            numbers.append(number)
    return tuple(numbers)


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


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
