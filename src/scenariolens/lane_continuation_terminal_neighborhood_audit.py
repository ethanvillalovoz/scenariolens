from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.lane_continuation import (
    _feature_id,
    _lane_features,
    _lane_features_by_id,
    _link_ids,
    _linked_lane_route,
)
from scenariolens.lane_continuation_branch_selection import (
    _meter_text,
    _optional_float,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_topology_gap_audit import (
    LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
)
from scenariolens.prediction import (
    _anchor_index,
    _feature_points,
    _lane_direction,
    _lane_heading_alignment,
    _project_to_lane,
)
from scenariolens.schema import AgentTrack, Scenario, State

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_audit.v1"
)

DEFAULT_NEIGHBORHOOD_RADIUS_M = 6.0
DEFAULT_HEADING_ALIGNMENT_MIN = 0.65
DEFAULT_MAX_HOPS = 2
MAX_NEIGHBOR_ROWS_PER_CASE = 6

_TERMINAL_DIAGNOSES = {
    "terminal_lane_confirmed",
    "terminal_or_directional_link_gap",
}
_DIRECTIONAL_LINK_FIELDS = ("entry_lanes", "exit_lanes")


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodAuditResult:
    """Files produced by a terminal-lane neighborhood audit."""

    ready: bool
    case_count: int
    nearby_recovery_count: int
    directional_gap_count: int
    true_terminal_count: int
    selected_lane_issue_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_audit(
    topology_manifest_path: str | Path,
    output_dir: str | Path,
    neighborhood_radius_m: float = DEFAULT_NEIGHBORHOOD_RADIUS_M,
    heading_alignment_min: float = DEFAULT_HEADING_ALIGNMENT_MIN,
    max_hops: int = DEFAULT_MAX_HOPS,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodAuditResult:
    """Generate a public-safe audit of selected terminal-lane neighborhoods."""

    source = Path(topology_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_audit_payload(
        topology_manifest_path=source,
        output_dir=target,
        neighborhood_radius_m=neighborhood_radius_m,
        heading_alignment_min=heading_alignment_min,
        max_hops=max_hops,
    )
    report = lane_continuation_terminal_neighborhood_audit_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodAuditResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        nearby_recovery_count=int(aggregate["nearby_recovery_case_count"]),
        directional_gap_count=int(aggregate["directional_gap_case_count"]),
        true_terminal_count=int(aggregate["true_terminal_case_count"]),
        selected_lane_issue_count=int(aggregate["selected_lane_issue_case_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_audit_payload(
    topology_manifest_path: Path,
    output_dir: Path,
    neighborhood_radius_m: float = DEFAULT_NEIGHBORHOOD_RADIUS_M,
    heading_alignment_min: float = DEFAULT_HEADING_ALIGNMENT_MIN,
    max_hops: int = DEFAULT_MAX_HOPS,
) -> dict[str, object]:
    """Return terminal-lane neighborhood diagnostics from topology blockers."""

    if neighborhood_radius_m <= 0.0:
        raise ValueError("neighborhood-radius-m must be positive.")
    if not 0.0 <= heading_alignment_min <= 1.0:
        raise ValueError("heading-alignment-min must be between 0 and 1.")
    if max_hops < 1:
        raise ValueError("max-hops must be at least 1.")

    topology = json.loads(topology_manifest_path.read_text(encoding="utf-8"))
    if topology.get("format") != LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT:
        raise ValueError(
            "Expected a lane-continuation topology gap audit manifest with "
            f"format {LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT}."
        )

    terminal_cases = [
        case
        for case in topology.get("cases", [])
        if isinstance(case, dict) and _is_terminal_neighborhood_case(case)
    ]
    replay_max_scenarios = _replay_max_scenarios(
        topology=topology,
        topology_manifest_path=topology_manifest_path,
    )
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ] = {}
    cases = [
        _audit_case(
            topology_case=case,
            source_cache=source_cache,
            max_scenarios_per_source=replay_max_scenarios,
            neighborhood_radius_m=neighborhood_radius_m,
            heading_alignment_min=heading_alignment_min,
            max_hops=max_hops,
        )
        for case in terminal_cases
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
        "topology_manifest": str(topology_manifest_path),
        "topology_format": topology.get("format"),
        "replay_manifest": topology.get("replay_manifest"),
        "candidate_manifest": topology.get("candidate_manifest"),
        "study_manifest": topology.get("study_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(topology.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "max_scenarios_per_source": replay_max_scenarios,
        "neighborhood_radius_m": round(neighborhood_radius_m, 3),
        "heading_alignment_min": round(heading_alignment_min, 3),
        "max_hops": max_hops,
        "source_topology_case_count": int(topology.get("case_count", 0) or 0),
        "selected_terminal_case_count": len(terminal_cases),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The terminal-neighborhood audit reloads local source slices only "
            "to inspect derived lane-link availability around selected terminal "
            "lanes. It publishes counts, feature ids, distances, and decisions; "
            "it does not publish raw Waymo map geometry, route plans, or "
            "benchmark claims."
        ),
    }


def lane_continuation_terminal_neighborhood_audit_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for terminal-lane neighborhood diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = payload.get("cases", [])
    assert isinstance(cases, list)

    lines = [
        "# ScenarioLens Lane-Continuation Terminal Neighborhood Audit",
        "",
        "This report takes the topology-gap audit's terminal/directional "
        "blockers and asks whether the selected lane is truly terminal, "
        "directionally ambiguous, or recoverable by considering nearby aligned "
        "lanes before expanding branch selection.",
        "",
        "The report is intentionally narrow: it does not change the default "
        "prediction baseline, does not publish raw map geometry, and is not a "
        "Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Topology manifest: `{payload['topology_manifest']}`",
        f"- Replay manifest: `{payload.get('replay_manifest')}`",
        f"- Candidate manifest: `{payload.get('candidate_manifest')}`",
        f"- Study manifest: `{payload.get('study_manifest')}`",
        f"- Ready: {payload['ready']}",
        f"- Max scenarios per source: {payload['max_scenarios_per_source']}",
        f"- Neighborhood radius: {_meter_text(payload['neighborhood_radius_m'])}",
        f"- Heading alignment minimum: {payload['heading_alignment_min']}",
        f"- Max lane-link hops: {payload['max_hops']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Audit Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Source topology cases | {payload['source_topology_case_count']} |",
        f"| Terminal/directional cases selected | {payload['selected_terminal_case_count']} |",
        f"| Cases audited | {aggregate['case_count']} |",
        f"| Ready cases | {aggregate['ready_case_count']} |",
        f"| Nearby alternate-lane recovery candidates | {aggregate['nearby_recovery_case_count']} |",
        f"| Directional-link mismatch candidates | {aggregate['directional_gap_case_count']} |",
        f"| True terminal / map-boundary cases | {aggregate['true_terminal_case_count']} |",
        f"| Selected-lane issue candidates | {aggregate['selected_lane_issue_case_count']} |",
        f"| Mean nearby lane candidates | {aggregate['mean_nearby_candidate_count']} |",
        f"| Mean linked alternate count | {aggregate['mean_linked_alternate_count']} |",
        f"| Mean route gap to horizon | {_signed_meter_text(aggregate['mean_route_gap_to_horizon_m'])} |",
        "",
        "## Decisions",
        "",
        "| Rank | Scenario | Track | Selected lane | Link field | Decision | Selected distance | Nearby lanes | Linked alternates | Best alternate | First next action |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['selected_feature_id']}` | "
            f"`{case['link_field']}` | "
            f"`{case['diagnosis_label']}` | "
            f"{_meter_text(case.get('selected_lane_distance_m'))} | "
            f"{case['nearby_candidate_count']} | "
            f"{case['linked_alternate_count']} | "
            f"{_best_alternate_text(case)} | "
            f"{case['first_next_action']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        neighbors = case.get("nearby_lanes", [])
        assert isinstance(neighbors, list)
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Diagnosis: **{case['diagnosis_label']}**",
                f"- Reason: {case['diagnosis_reason']}",
                f"- Selected feature: `{case['selected_feature_id']}`",
                f"- Lane-link status: `{case['lane_link_status']}`",
                f"- Link field: `{case['link_field']}`",
                f"- Selected distance / alignment: {_meter_text(case.get('selected_lane_distance_m'))} / {case.get('selected_heading_alignment', 'n/a')}",
                f"- Selected directional/opposite links: {case['selected_directional_link_count']} / {case['selected_opposite_link_count']}",
                f"- Horizon / selected route remaining: {_meter_text(case.get('horizon_travel_m'))} / {_meter_text(case.get('selected_route_remaining_m'))}",
                f"- Route gap to horizon: {_signed_meter_text(case.get('route_gap_to_horizon_m'))}",
                f"- Nearby aligned lanes / linked alternates: {case['aligned_nearby_count']} / {case['linked_alternate_count']}",
                "",
                "Nearby lane candidates:",
                "",
                "| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |",
                "| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |",
            ]
        )
        if not neighbors:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
        for neighbor in neighbors:
            assert isinstance(neighbor, dict)
            lines.append(
                "| "
                f"`{neighbor['feature_id']}` | "
                f"{neighbor['is_selected']} | "
                f"{_meter_text(neighbor.get('distance_m'))} | "
                f"{neighbor.get('heading_alignment', 'n/a')} | "
                f"`{neighbor['link_field']}` | "
                f"{neighbor['directional_link_count']} | "
                f"`{neighbor['route_status']}` | "
                f"{_meter_text(neighbor.get('route_remaining_m'))} | "
                f"{neighbor['recovery_candidate']} |"
            )
        actions = case.get("next_actions", [])
        assert isinstance(actions, list)
        lines.extend(["", "Recommended next actions:"])
        lines.extend(f"- {action}" for action in actions)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Nearby alternate-lane recovery candidates mean the selected lane was terminal, but another close, heading-aligned lane has parsed continuation that could seed a bounded neighborhood search.",
            "- Directional-link mismatch candidates mean the selected lane has links only opposite the inferred travel direction; those cases need direction/anchor validation before adding branches.",
            "- True terminal/map-boundary cases are held as map-boundary or topology-source follow-up rather than promoted into branch-selection claims.",
            "- This is still a diagnostic framework, not a production planner: the next implementation step is to gate any alternate-lane recovery through replay evidence before changing default behavior.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_terminal_neighborhood_case(case: dict[str, object]) -> bool:
    if not bool(case.get("ready")):
        return False
    diagnosis = str(case.get("diagnosis_label", ""))
    status = str(case.get("lane_link_status", ""))
    if diagnosis in _TERMINAL_DIAGNOSES:
        return True
    return status in {"no_exit_lanes", "no_entry_lanes"} and diagnosis not in {
        "cap_recoverable_link_target",
        "cap_recovered_link_target",
    }


def _audit_case(
    topology_case: dict[str, object],
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
    max_scenarios_per_source: int | None,
    neighborhood_radius_m: float,
    heading_alignment_min: float,
    max_hops: int,
) -> dict[str, object]:
    source_input = Path(str(topology_case.get("source_input", "")))
    input_format = str(topology_case.get("input_format", "native"))
    scenario_id = str(topology_case.get("scenario_id", ""))
    track_id = str(topology_case.get("track_id", ""))
    selected_feature_id = str(topology_case.get("selected_feature_id", ""))
    link_field = _normal_link_field(topology_case.get("link_field"))
    lane_link_status = str(topology_case.get("lane_link_status", "unknown"))
    base = {
        "rank": int(topology_case.get("rank", 0) or 0),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source_input),
        "source_name": str(topology_case.get("source_name", source_input.name)),
        "input_format": input_format,
        "ready": False,
        "lane_link_status": lane_link_status,
        "topology_diagnosis_label": topology_case.get("diagnosis_label"),
        "selected_feature_id": selected_feature_id,
        "link_field": link_field,
        "horizon_travel_m": _optional_float(topology_case.get("horizon_travel_m")),
        "selected_lane_distance_m": None,
        "selected_heading_alignment": None,
        "selected_directional_link_count": 0,
        "selected_opposite_link_count": 0,
        "selected_route_remaining_m": None,
        "route_gap_to_horizon_m": _optional_float(
            topology_case.get("route_gap_to_horizon_m")
        ),
        "nearby_candidate_count": 0,
        "aligned_nearby_count": 0,
        "linked_alternate_count": 0,
        "best_alternate_feature_id": None,
        "best_alternate_route_remaining_m": None,
        "nearby_lanes": [],
        "diagnosis_label": "not_evaluable",
        "diagnosis_reason": "The local scenario could not be audited.",
        "first_next_action": "Confirm local source data is present, then rerun the audit.",
        "next_actions": [
            "Confirm local source data is present, then rerun the audit.",
        ],
    }

    source_key = (str(source_input), input_format, max_scenarios_per_source)
    if source_key not in source_cache:
        source_cache[source_key] = load_failure_study_input(
            source=source_input,
            input_format=input_format,
            max_scenarios=max_scenarios_per_source,
        )
    input_ready, preflight, scenarios = source_cache[source_key]
    scenario = _find_scenario(scenarios, scenario_id)
    if scenario is None:
        base["input_ready"] = input_ready
        base["preflight"] = preflight or {}
        base["error"] = "scenario_not_found_in_loaded_source"
        return base

    track = _find_track(scenario, track_id)
    if track is None:
        base.update(
            {
                "input_ready": input_ready,
                "preflight": preflight or {},
                "error": "track_not_found_in_loaded_scenario",
            }
        )
        return base

    anchor = _track_anchor(track=track, scenario=scenario)
    if anchor is None:
        base.update(
            {
                "input_ready": input_ready,
                "preflight": preflight or {},
                "error": "track_anchor_not_available",
            }
        )
        return base

    features_by_id = _lane_features_by_id(scenario)
    selected = features_by_id.get(selected_feature_id)
    if selected is None:
        diagnosis = _case_diagnosis(
            label="selected_feature_missing",
            reason=(
                "The selected lane feature is not available in the ScenarioLens "
                "map feature set, so neighborhood inspection cannot start."
            ),
            actions=(
                "Audit selected-lane materialization before changing neighborhood selection.",
                "Rerun the topology-gap audit after map-feature loading changes.",
            ),
        )
        base.update(
            {
                "ready": True,
                "input_ready": input_ready,
                "preflight": preflight or {},
                **diagnosis,
            }
        )
        return base

    neighbors = _nearby_lane_rows(
        scenario=scenario,
        anchor=anchor,
        selected_feature_id=selected_feature_id,
        requested_link_field=link_field,
        neighborhood_radius_m=neighborhood_radius_m,
        heading_alignment_min=heading_alignment_min,
        max_hops=max_hops,
    )
    selected_row = next(
        (row for row in neighbors if row["feature_id"] == selected_feature_id),
        None,
    )
    if selected_row is None:
        selected_row = _selected_lane_row(
            scenario=scenario,
            anchor=anchor,
            selected=selected,
            selected_feature_id=selected_feature_id,
            requested_link_field=link_field,
            heading_alignment_min=heading_alignment_min,
            max_hops=max_hops,
        )
    linked_alternates = [
        row
        for row in neighbors
        if not bool(row["is_selected"]) and bool(row["recovery_candidate"])
    ]
    best_alternate = linked_alternates[0] if linked_alternates else None
    horizon = _case_horizon(topology_case, track, anchor)
    selected_route_remaining = _optional_float(selected_row.get("route_remaining_m"))
    route_gap = (
        round(horizon - selected_route_remaining, 3)
        if horizon is not None and selected_route_remaining is not None
        else _optional_float(topology_case.get("route_gap_to_horizon_m"))
    )
    diagnosis = _diagnose_case(
        selected_row=selected_row,
        linked_alternates=linked_alternates,
        heading_alignment_min=heading_alignment_min,
        neighborhood_radius_m=neighborhood_radius_m,
    )
    base.update(
        {
            "ready": True,
            "input_ready": input_ready,
            "preflight": preflight or {},
            "horizon_travel_m": horizon,
            "selected_lane_distance_m": selected_row.get("distance_m"),
            "selected_heading_alignment": selected_row.get("heading_alignment"),
            "selected_directional_link_count": selected_row.get(
                "directional_link_count",
                0,
            ),
            "selected_opposite_link_count": selected_row.get("opposite_link_count", 0),
            "selected_route_remaining_m": selected_route_remaining,
            "route_gap_to_horizon_m": route_gap,
            "nearby_candidate_count": len(neighbors),
            "aligned_nearby_count": sum(
                bool(row.get("heading_aligned")) for row in neighbors
            ),
            "linked_alternate_count": len(linked_alternates),
            "best_alternate_feature_id": (
                best_alternate.get("feature_id") if best_alternate else None
            ),
            "best_alternate_route_remaining_m": (
                best_alternate.get("route_remaining_m") if best_alternate else None
            ),
            "nearby_lanes": neighbors[:MAX_NEIGHBOR_ROWS_PER_CASE],
            **diagnosis,
        }
    )
    return base


def _nearby_lane_rows(
    scenario: Scenario,
    anchor: State,
    selected_feature_id: str,
    requested_link_field: str,
    neighborhood_radius_m: float,
    heading_alignment_min: float,
    max_hops: int,
) -> list[dict[str, object]]:
    rows = []
    for feature in _lane_features(scenario):
        feature_id = _feature_id(feature)
        if not feature_id:
            continue
        lane = _feature_points(feature)
        projection = _project_to_lane(anchor.x, anchor.y, lane)
        if projection is None or projection.distance_m > neighborhood_radius_m:
            continue
        rows.append(
            _lane_row(
                scenario=scenario,
                anchor=anchor,
                feature=feature,
                feature_id=feature_id,
                projection=projection,
                is_selected=feature_id == selected_feature_id,
                requested_link_field=requested_link_field,
                heading_alignment_min=heading_alignment_min,
                max_hops=max_hops,
            )
        )
    return sorted(
        rows,
        key=lambda row: (
            not bool(row["recovery_candidate"]),
            not bool(row["heading_aligned"]),
            bool(row["is_selected"]),
            float(row["distance_m"]),
            -float(row["route_remaining_m"] or 0.0),
        ),
    )


def _selected_lane_row(
    scenario: Scenario,
    anchor: State,
    selected: dict[str, object],
    selected_feature_id: str,
    requested_link_field: str,
    heading_alignment_min: float,
    max_hops: int,
) -> dict[str, object]:
    lane = _feature_points(selected)
    projection = _project_to_lane(anchor.x, anchor.y, lane)
    if projection is None:
        return {
            "feature_id": selected_feature_id,
            "is_selected": True,
            "distance_m": None,
            "heading_alignment": None,
            "heading_aligned": False,
            "direction": "unknown",
            "link_field": requested_link_field,
            "opposite_link_field": _opposite_link_field(requested_link_field),
            "directional_link_count": len(_link_ids(selected.get(requested_link_field))),
            "opposite_link_count": len(
                _link_ids(selected.get(_opposite_link_field(requested_link_field)))
            ),
            "route_status": "projection_unavailable",
            "link_count": 0,
            "route_remaining_m": None,
            "base_remaining_m": None,
            "recovery_candidate": False,
        }
    return _lane_row(
        scenario=scenario,
        anchor=anchor,
        feature=selected,
        feature_id=selected_feature_id,
        projection=projection,
        is_selected=True,
        requested_link_field=requested_link_field,
        heading_alignment_min=heading_alignment_min,
        max_hops=max_hops,
    )


def _lane_row(
    scenario: Scenario,
    anchor: State,
    feature: dict[str, object],
    feature_id: str,
    projection: object,
    is_selected: bool,
    requested_link_field: str,
    heading_alignment_min: float,
    max_hops: int,
) -> dict[str, object]:
    direction = _lane_direction(anchor, projection)  # type: ignore[arg-type]
    link_field = requested_link_field if is_selected else _link_field_for_direction(direction)
    opposite_link_field = _opposite_link_field(link_field)
    route = _linked_lane_route(
        feature=feature,
        projection=projection,
        direction=direction,
        scenario=scenario,
        max_hops=max_hops,
    )
    alignment = round(_lane_heading_alignment(anchor, projection), 3)  # type: ignore[arg-type]
    directional_link_count = len(_link_ids(feature.get(link_field)))
    opposite_link_count = len(_link_ids(feature.get(opposite_link_field)))
    heading_aligned = alignment >= heading_alignment_min
    recovery_candidate = (
        not is_selected
        and heading_aligned
        and directional_link_count > 0
        and route.link_count > 0
    )
    return {
        "feature_id": feature_id,
        "is_selected": is_selected,
        "distance_m": round(float(getattr(projection, "distance_m")), 3),
        "heading_alignment": alignment,
        "heading_aligned": heading_aligned,
        "direction": "forward" if direction >= 0.0 else "reverse",
        "link_field": link_field,
        "opposite_link_field": opposite_link_field,
        "directional_link_count": directional_link_count,
        "opposite_link_count": opposite_link_count,
        "route_status": route.status,
        "link_count": route.link_count,
        "route_remaining_m": round(route.route_remaining_m, 3),
        "base_remaining_m": round(route.base_remaining_m, 3),
        "recovery_candidate": recovery_candidate,
    }


def _diagnose_case(
    selected_row: dict[str, object],
    linked_alternates: list[dict[str, object]],
    heading_alignment_min: float,
    neighborhood_radius_m: float,
) -> dict[str, object]:
    selected_distance = _optional_float(selected_row.get("distance_m"))
    selected_alignment = _optional_float(selected_row.get("heading_alignment"))
    if linked_alternates:
        best = linked_alternates[0]
        return _case_diagnosis(
            label="nearby_alternate_lane_recovery",
            reason=(
                "The selected lane is terminal for the requested direction, "
                "but a nearby heading-aligned lane has parsed directional "
                "continuation."
            ),
            actions=(
                "Add a bounded selected-lane neighborhood search before branch selection.",
                f"Replay alternate lane `{best['feature_id']}` before changing default scoring behavior.",
            ),
            nearby_recovery=True,
            selected_lane_issue=True,
        )
    if (
        selected_distance is not None
        and selected_distance > neighborhood_radius_m
    ) or (
        selected_alignment is not None
        and selected_alignment < heading_alignment_min
    ):
        return _case_diagnosis(
            label="selected_lane_quality_issue",
            reason=(
                "The selected lane is too far from the anchor or poorly aligned "
                "with the target heading."
            ),
            actions=(
                "Prefer heading/continuity-aware lane selection before evaluating terminal topology.",
                "Hold this case out of branch-selection evidence until the selected lane is stable.",
            ),
            selected_lane_issue=True,
        )
    if (
        int(selected_row.get("directional_link_count", 0) or 0) == 0
        and int(selected_row.get("opposite_link_count", 0) or 0) > 0
    ):
        return _case_diagnosis(
            label="directional_link_mismatch",
            reason=(
                "The selected lane has links only opposite the inferred travel "
                "direction, so the blocker may be direction or anchor-context "
                "sensitive."
            ),
            actions=(
                "Audit anchor heading, lane direction, and entry/exit semantics for this case.",
                "Require replay evidence before allowing opposite-direction link recovery.",
            ),
            directional_gap=True,
        )
    return _case_diagnosis(
        label="true_terminal_or_map_boundary",
        reason=(
            "No close, heading-aligned lane with parsed continuation was found "
            "around the selected terminal lane."
        ),
        actions=(
            "Keep this case as a map-boundary/topology-source blocker.",
            "Do not promote it into branch selection without new map context.",
        ),
        true_terminal=True,
    )


def _case_diagnosis(
    label: str,
    reason: str,
    actions: tuple[str, ...],
    nearby_recovery: bool = False,
    directional_gap: bool = False,
    true_terminal: bool = False,
    selected_lane_issue: bool = False,
) -> dict[str, object]:
    return {
        "diagnosis_label": label,
        "diagnosis_reason": reason,
        "nearby_recovery": nearby_recovery,
        "directional_gap": directional_gap,
        "true_terminal": true_terminal,
        "selected_lane_issue": selected_lane_issue,
        "first_next_action": actions[0],
        "next_actions": list(actions),
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    nearby_counts = [
        float(case["nearby_candidate_count"])
        for case in ready
        if case.get("nearby_candidate_count") is not None
    ]
    linked_counts = [
        float(case["linked_alternate_count"])
        for case in ready
        if case.get("linked_alternate_count") is not None
    ]
    route_gaps = [
        gap
        for case in ready
        if (gap := _optional_float(case.get("route_gap_to_horizon_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "nearby_recovery_case_count": sum(
            bool(case.get("nearby_recovery")) for case in ready
        ),
        "directional_gap_case_count": sum(
            bool(case.get("directional_gap")) for case in ready
        ),
        "true_terminal_case_count": sum(
            bool(case.get("true_terminal")) for case in ready
        ),
        "selected_lane_issue_case_count": sum(
            bool(case.get("selected_lane_issue")) for case in ready
        ),
        "mean_nearby_candidate_count": _mean(nearby_counts),
        "mean_linked_alternate_count": _mean(linked_counts),
        "mean_route_gap_to_horizon_m": _mean(route_gaps),
    }


def _track_anchor(track: AgentTrack, scenario: Scenario) -> State | None:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return None
    return states[_anchor_index(states, scenario)]


def _case_horizon(
    topology_case: dict[str, object],
    track: AgentTrack,
    anchor: State,
) -> float | None:
    case_horizon = _optional_float(topology_case.get("horizon_travel_m"))
    if case_horizon is not None:
        return case_horizon
    states = tuple(sorted(track.states, key=lambda state: state.t))
    future = tuple(state for state in states if state.t > anchor.t)
    if not future:
        return None
    return round(hypot(anchor.vx, anchor.vy) * (future[-1].t - anchor.t), 3)


def _replay_max_scenarios(
    topology: dict[str, object],
    topology_manifest_path: Path,
) -> int | None:
    replay_value = topology.get("replay_manifest")
    if not replay_value:
        return None
    replay_path = _resolve_path(replay_value, topology_manifest_path)
    if not replay_path.exists():
        return None
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    value = replay.get("max_scenarios_per_source")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _resolve_path(value: object, source_path: Path) -> Path:
    path = Path(str(value))
    if path.is_absolute() or path.exists():
        return path
    return source_path.parent / path


def _find_scenario(scenarios: tuple[Scenario, ...], scenario_id: str) -> Scenario | None:
    return next(
        (scenario for scenario in scenarios if scenario.scenario_id == scenario_id),
        None,
    )


def _find_track(scenario: Scenario, track_id: str) -> AgentTrack | None:
    return next((track for track in scenario.tracks if track.agent_id == track_id), None)


def _normal_link_field(value: object) -> str:
    field = str(value)
    return field if field in _DIRECTIONAL_LINK_FIELDS else "exit_lanes"


def _link_field_for_direction(direction: float) -> str:
    return "exit_lanes" if direction >= 0.0 else "entry_lanes"


def _opposite_link_field(link_field: str) -> str:
    return "entry_lanes" if link_field == "exit_lanes" else "exit_lanes"


def _best_alternate_text(case: dict[str, object]) -> str:
    feature_id = case.get("best_alternate_feature_id")
    if feature_id in (None, ""):
        return "none"
    remaining = _meter_text(case.get("best_alternate_route_remaining_m"))
    return f"`{feature_id}` ({remaining})"


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)
