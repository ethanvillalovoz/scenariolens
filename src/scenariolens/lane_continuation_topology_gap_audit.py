from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenariolens.failure_study import load_failure_study_input
from scenariolens.ingest.waymo_motion import (
    MAX_MAP_FEATURES_PER_SCENARIO,
    NATIVE_JSON_SUFFIXES,
    NATIVE_JSONL_SUFFIXES,
    NATIVE_PROTO_SUFFIXES,
    NATIVE_TFRECORD_SUFFIXES,
    _iter_tfrecord_records,
    _map_feature_from_mapping,
    _scenario_mapping_from_proto_bytes,
    _scenario_mappings_from_payload,
    native_motion_format_label,
)
from scenariolens.lane_continuation import (
    _feature_id,
    _lane_features,
    _lane_features_by_id,
    _link_ids,
    _nearest_lane_feature,
)
from scenariolens.lane_continuation_branch_selection import (
    _meter_text,
    _optional_float,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.prediction import _anchor_index, _lane_direction
from scenariolens.schema import AgentTrack, Scenario

LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT = (
    "scenariolens.lane_continuation_topology_gap_audit.v1"
)

_TOPOLOGY_BUCKET = "topology_audit"
_TOPOLOGY_STATUSES = {
    "linked_feature_missing",
    "no_exit_lanes",
    "no_entry_lanes",
}


@dataclass(frozen=True)
class LaneContinuationTopologyGapAuditResult:
    """Files produced by a lane-continuation topology gap audit."""

    ready: bool
    case_count: int
    cap_recovered_count: int
    cap_recoverable_count: int
    terminal_confirmed_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_topology_gap_audit(
    replay_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTopologyGapAuditResult:
    """Generate a public-safe audit of lane-link topology blocker cases."""

    source = Path(replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_topology_gap_audit_payload(
        replay_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_topology_gap_audit_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTopologyGapAuditResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        cap_recovered_count=int(aggregate["cap_recovered_case_count"]),
        cap_recoverable_count=int(aggregate["cap_recoverable_case_count"]),
        terminal_confirmed_count=int(aggregate["terminal_confirmed_case_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_topology_gap_audit_payload(
    replay_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return topology gap diagnostics from a lane-continuation replay manifest."""

    replay = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay.get("format") != LANE_CONTINUATION_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation replay manifest with format "
            f"{LANE_CONTINUATION_REPLAY_FORMAT}."
        )

    selected = [
        case
        for case in replay.get("cases", [])
        if isinstance(case, dict) and _is_topology_gap_case(case)
    ]
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ] = {}
    max_scenarios = _optional_int(replay.get("max_scenarios_per_source"))
    raw_cache = _raw_inventory_cache(
        replay_cases=selected,
        max_scenarios=max_scenarios,
    )
    cases = [
        _audit_case(
            replay_case=case,
            source_cache=source_cache,
            raw_cache=raw_cache,
            replay_max_scenarios=max_scenarios,
        )
        for case in selected
    ]
    aggregate = _aggregate_cases(cases)
    aggregate["raw_source_pass_count"] = len(
        {
            (
                str(case.get("source_input", "")),
                str(case.get("input_format", "native")),
            )
            for case in selected
        }
    )
    aggregate["raw_scenario_inventory_count"] = len(raw_cache)
    return {
        "format": LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay.get("format"),
        "candidate_manifest": replay.get("candidate_manifest"),
        "study_manifest": replay.get("study_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(replay.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "map_feature_cap": MAX_MAP_FEATURES_PER_SCENARIO,
        "case_count": len(cases),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The topology gap audit reloads each local source once to compare "
            "capped ScenarioLens map features with raw parsed map-feature ids. "
            "It publishes derived link-presence summaries, not raw Waymo map "
            "geometry, not a route planner, and not a benchmark claim."
        ),
    }


def lane_continuation_topology_gap_audit_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for topology gap diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = payload.get("cases", [])
    assert isinstance(cases, list)

    lines = [
        "# ScenarioLens Lane-Continuation Topology Gap Audit",
        "",
        "This audit works down the branch coverage queue's topology/parser "
        "blockers. For each topology-audit replay case, ScenarioLens reloads "
        "the local source slice, compares the capped ScenarioLens map features "
        "against raw parsed map-feature ids, and asks whether missing lane-link "
        "targets are recoverable by improving map materialization.",
        "",
        "The report is intentionally narrow: it does not change the default "
        "baseline, does not publish raw map geometry, and is not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Candidate manifest: `{payload.get('candidate_manifest')}`",
        f"- Study manifest: `{payload.get('study_manifest')}`",
        f"- Ready: {payload['ready']}",
        f"- Map feature cap: {payload['map_feature_cap']}",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Audit Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases audited | {aggregate['case_count']} |",
        f"| Ready cases | {aggregate['ready_case_count']} |",
        f"| Cap-recovered cases | {aggregate['cap_recovered_case_count']} |",
        f"| Still cap-recoverable cases | {aggregate['cap_recoverable_case_count']} |",
        f"| Terminal lanes confirmed | {aggregate['terminal_confirmed_case_count']} |",
        f"| Raw target still missing | {aggregate['raw_target_missing_case_count']} |",
        f"| Selected feature missing in capped map | {aggregate['selected_feature_missing_case_count']} |",
        f"| Capped maps at feature cap | {aggregate['capped_map_at_limit_count']} |",
        f"| Batched raw-source passes | {aggregate['raw_source_pass_count']} |",
        f"| Raw scenario inventories requested | {aggregate['raw_scenario_inventory_count']} |",
        f"| Mean route gap to horizon | {_signed_meter_text(aggregate['mean_route_gap_to_horizon_m'])} |",
        "",
        "## Decisions",
        "",
        "| Rank | Scenario | Track | Status | Selected lane | Link field | Link targets | Raw lanes | Capped lanes | Diagnosis | First next action |",
        "| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
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
            f"`{case['lane_link_status']}` | "
            f"`{case['selected_feature_id']}` | "
            f"`{case['link_field']}` | "
            f"{_target_text(case)} | "
            f"{case['raw_lane_feature_count']} | "
            f"{case['capped_lane_feature_count']} | "
            f"`{case['diagnosis_label']}` | "
            f"{case['first_next_action']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        targets = case.get("link_target_presence", [])
        assert isinstance(targets, list)
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Diagnosis: **{case['diagnosis_label']}**",
                f"- Selected feature: `{case['selected_feature_id']}`",
                f"- Link field: `{case['link_field']}`",
                f"- Lane-link status: `{case['lane_link_status']}`",
                f"- Raw/capped map features: {case['raw_map_feature_count']} / {case['capped_map_feature_count']}",
                f"- Raw/capped lane features: {case['raw_lane_feature_count']} / {case['capped_lane_feature_count']}",
                f"- Capped map at feature cap: {case['capped_map_at_limit']}",
                f"- Horizon / route remaining: {_meter_text(case.get('horizon_travel_m'))} / {_meter_text(case.get('route_remaining_m'))}",
                f"- Route gap to horizon: {_signed_meter_text(case.get('route_gap_to_horizon_m'))}",
                f"- Reason: {case['diagnosis_reason']}",
                "",
                "Link target presence:",
                "",
                "| Target | In capped map | In raw map | Raw index | Beyond cap |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        if not targets:
            lines.append("| n/a | n/a | n/a | n/a | n/a |")
        for target in targets:
            assert isinstance(target, dict)
            lines.append(
                "| "
                f"`{target['target_id']}` | "
                f"{target['present_in_capped_map']} | "
                f"{target['present_in_raw_map']} | "
                f"{target['raw_feature_index'] if target['raw_feature_index'] is not None else 'n/a'} | "
                f"{target['beyond_cap']} |"
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
            "- Cap-recovered cases mean a referenced lane target from beyond the raw feature cap is now available in the capped ScenarioLens map feature set.",
            "- Cap-recoverable cases mean the referenced lane target exists in the raw parsed map but was not available inside the capped ScenarioLens map feature set.",
            "- Terminal-lane confirmations mean the selected lane has no parsed continuation in either the capped or raw parsed map; these need selected-lane or topology-neighborhood work rather than a simple cap increase.",
            "- Raw-missing targets stay parser/proto-source audits until the referenced id can be found.",
            "- Raw map inventories are collected in one sequential pass per source rather than rescanning a shard for every case.",
            "- This audit turns topology blockers into engineering tasks before expanding branch-selection and route-context guard claims.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_topology_gap_case(case: dict[str, object]) -> bool:
    if str(case.get("bucket")) != _TOPOLOGY_BUCKET:
        return False
    nominal = case.get("nominal")
    if not isinstance(nominal, dict):
        return False
    return str(nominal.get("lane_link_status")) in _TOPOLOGY_STATUSES


def _audit_case(
    replay_case: dict[str, object],
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
    raw_cache: dict[tuple[str, str, str, int | None], dict[str, object]],
    replay_max_scenarios: int | None,
) -> dict[str, object]:
    nominal = _required_mapping(replay_case, "nominal")
    source_input = Path(str(replay_case.get("source_input", "")))
    input_format = str(replay_case.get("input_format", "native"))
    scenario_id = str(replay_case.get("scenario_id", ""))
    track_id = str(replay_case.get("track_id", ""))
    selected_feature_id = str(nominal.get("selected_feature_id", ""))
    lane_link_status = str(nominal.get("lane_link_status", "unknown"))
    base = {
        "rank": int(replay_case.get("rank", 0) or 0),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source_input),
        "source_name": str(replay_case.get("source_name", source_input.name)),
        "input_format": input_format,
        "ready": False,
        "lane_link_status": lane_link_status,
        "selected_feature_id": selected_feature_id,
        "link_field": "unknown",
        "link_target_ids": [],
        "link_target_presence": [],
        "capped_map_feature_count": 0,
        "capped_lane_feature_count": 0,
        "raw_lane_feature_count": 0,
        "capped_map_at_limit": False,
        "horizon_travel_m": _optional_float(nominal.get("horizon_travel_m")),
        "route_remaining_m": _optional_float(nominal.get("route_remaining_m")),
        "route_gap_to_horizon_m": _route_gap(nominal),
        "diagnosis_label": "not_evaluable",
        "diagnosis_reason": "The local scenario could not be audited.",
        "first_next_action": "Confirm local source data is present, then rerun the audit.",
        "next_actions": [
            "Confirm local source data is present, then rerun the audit.",
        ],
    }

    source_key = (str(source_input), input_format, replay_max_scenarios)
    if source_key not in source_cache:
        source_cache[source_key] = load_failure_study_input(
            source=source_input,
            input_format=input_format,
            max_scenarios=replay_max_scenarios,
        )
    input_ready, preflight, scenarios = source_cache[source_key]
    scenario = _find_scenario(scenarios, scenario_id)
    if scenario is None:
        base["input_ready"] = input_ready
        base["preflight"] = preflight or {}
        base["error"] = "scenario_not_found_in_loaded_source"
        return base

    capped_map_features = _map_features(scenario)
    capped_features = _lane_features(scenario)
    capped_by_id = _lane_features_by_id(scenario)
    capped_feature = capped_by_id.get(selected_feature_id)
    link_field = _link_field(
        scenario=scenario,
        track_id=track_id,
        lane_link_status=lane_link_status,
    )
    capped_targets = (
        list(_link_ids(capped_feature.get(link_field)))
        if capped_feature is not None
        else []
    )

    raw_key = (str(source_input), input_format, scenario_id, replay_max_scenarios)
    raw_inventory = raw_cache.get(
        raw_key,
        _empty_raw_inventory("scenario_not_requested_in_raw_inventory_batch"),
    )
    raw_by_id = raw_inventory.get("features_by_id", {})
    raw_index_by_id = raw_inventory.get("feature_index_by_id", {})
    raw_selected = raw_by_id.get(selected_feature_id) if isinstance(raw_by_id, dict) else None
    raw_targets = (
        list(_link_ids(raw_selected.get(link_field)))
        if isinstance(raw_selected, dict)
        else []
    )
    target_ids = tuple(dict.fromkeys([*capped_targets, *raw_targets]))
    target_presence = [
        _target_presence(
            target_id=target_id,
            capped_by_id=capped_by_id,
            raw_by_id=raw_by_id if isinstance(raw_by_id, dict) else {},
            raw_index_by_id=(
                raw_index_by_id if isinstance(raw_index_by_id, dict) else {}
            ),
        )
        for target_id in target_ids
    ]
    diagnosis = _diagnosis(
        lane_link_status=lane_link_status,
        selected_feature_id=selected_feature_id,
        capped_feature=capped_feature,
        raw_selected=raw_selected if isinstance(raw_selected, dict) else None,
        capped_targets=capped_targets,
        raw_targets=raw_targets,
        target_presence=target_presence,
        capped_map_at_limit=len(capped_map_features) >= MAX_MAP_FEATURES_PER_SCENARIO,
    )
    base.update(
        {
            "ready": True,
            "input_ready": input_ready,
            "preflight": preflight or {},
            "link_field": link_field,
            "link_target_ids": list(target_ids),
            "link_target_presence": target_presence,
            "capped_map_feature_count": len(capped_map_features),
            "capped_lane_feature_count": len(capped_features),
            "raw_lane_feature_count": int(raw_inventory.get("lane_feature_count", 0) or 0),
            "raw_map_feature_count": int(raw_inventory.get("map_feature_count", 0) or 0),
            "capped_map_at_limit": len(capped_map_features) >= MAX_MAP_FEATURES_PER_SCENARIO,
            **diagnosis,
        }
    )
    return base


def _raw_inventory_cache(
    replay_cases: list[dict[str, object]],
    max_scenarios: int | None,
) -> dict[tuple[str, str, str, int | None], dict[str, object]]:
    requested: dict[tuple[str, str], set[str]] = {}
    for case in replay_cases:
        source = str(case.get("source_input", ""))
        input_format = str(case.get("input_format", "native"))
        scenario_id = str(case.get("scenario_id", ""))
        requested.setdefault((source, input_format), set()).add(scenario_id)

    cache: dict[tuple[str, str, str, int | None], dict[str, object]] = {}
    for (source, input_format), scenario_ids in requested.items():
        inventories = _raw_map_inventories(
            source=Path(source),
            input_format=input_format,
            scenario_ids=scenario_ids,
            max_scenarios=max_scenarios,
        )
        for scenario_id in scenario_ids:
            cache[(source, input_format, scenario_id, max_scenarios)] = inventories[
                scenario_id
            ]
    return cache


def _raw_map_inventories(
    source: Path,
    input_format: str,
    scenario_ids: set[str],
    max_scenarios: int | None,
) -> dict[str, dict[str, object]]:
    if input_format != "native":
        return {
            scenario_id: _empty_raw_inventory(
                "unsupported_input_format_for_raw_map_audit"
            )
            for scenario_id in scenario_ids
        }
    try:
        mappings = _raw_scenario_mappings(
            source=source,
            scenario_ids=scenario_ids,
            max_scenarios=max_scenarios,
        )
    except (OSError, ValueError) as exc:
        return {
            scenario_id: _empty_raw_inventory(f"raw_source_read_failed: {exc}")
            for scenario_id in scenario_ids
        }
    return {
        scenario_id: (
            _raw_map_inventory_from_mapping(mappings[scenario_id])
            if scenario_id in mappings
            else _empty_raw_inventory("scenario_not_found_in_raw_source")
        )
        for scenario_id in scenario_ids
    }


def _raw_scenario_mappings(
    source: Path,
    scenario_ids: set[str],
    max_scenarios: int | None,
) -> dict[str, dict[str, Any]]:
    if not scenario_ids:
        return {}
    label = native_motion_format_label(source)
    if label in NATIVE_JSON_SUFFIXES:
        payload = json.loads(source.read_text(encoding="utf-8"))
        mappings = _scenario_mappings_from_payload(payload, source)
        return _requested_mappings(mappings[:max_scenarios], scenario_ids)
    if label in NATIVE_JSONL_SUFFIXES:
        return _jsonl_requested_mappings(
            source=source,
            scenario_ids=scenario_ids,
            max_scenarios=max_scenarios,
        )
    if label in NATIVE_PROTO_SUFFIXES:
        mapping = _scenario_mapping_from_proto_bytes(source.read_bytes())
        return _requested_mappings([mapping], scenario_ids)
    if label in NATIVE_TFRECORD_SUFFIXES:
        found: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(_iter_tfrecord_records(source), start=1):
            if max_scenarios is not None and index > max_scenarios:
                break
            mapping = _scenario_mapping_from_proto_bytes(record)
            scenario_id = _mapping_scenario_id(mapping)
            if scenario_id in scenario_ids:
                found[scenario_id] = mapping
                if len(found) == len(scenario_ids):
                    break
        return found
    return {}


def _jsonl_requested_mappings(
    source: Path,
    scenario_ids: set[str],
    max_scenarios: int | None,
) -> dict[str, dict[str, Any]]:
    loaded = 0
    found: dict[str, dict[str, Any]] = {}
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            for mapping in _scenario_mappings_from_payload(payload, source):
                loaded += 1
                scenario_id = _mapping_scenario_id(mapping)
                if scenario_id in scenario_ids:
                    found[scenario_id] = mapping
                    if len(found) == len(scenario_ids):
                        return found
                if max_scenarios is not None and loaded >= max_scenarios:
                    return found
    return found


def _requested_mappings(
    mappings: list[dict[str, Any]],
    scenario_ids: set[str],
) -> dict[str, dict[str, Any]]:
    return {
        scenario_id: mapping
        for mapping in mappings
        if (scenario_id := _mapping_scenario_id(mapping)) in scenario_ids
    }


def _mapping_scenario_id(mapping: dict[str, Any]) -> str:
    return str(mapping.get("scenario_id", mapping.get("scenarioId", "")))


def _raw_map_inventory_from_mapping(
    mapping: dict[str, Any],
) -> dict[str, object]:
    raw_payload = mapping.get("map_features")
    if raw_payload is None:
        raw_payload = mapping.get("mapFeatures")
    if not isinstance(raw_payload, list):
        raw_payload = []
    features = [
        feature
        for item in raw_payload
        if isinstance(item, dict)
        if (feature := _map_feature_from_mapping(item)) is not None
    ]
    lane_features = [
        feature
        for feature in features
        if feature.get("kind") == "lane" and _feature_id(feature)
    ]
    by_id = {
        _feature_id(feature): feature
        for feature in features
        if _feature_id(feature)
    }
    index_by_id = {
        _feature_id(feature): index
        for index, feature in enumerate(features, start=1)
        if _feature_id(feature)
    }
    return {
        "ready": True,
        "error": None,
        "map_feature_count": len(features),
        "lane_feature_count": len(lane_features),
        "features_by_id": by_id,
        "feature_index_by_id": index_by_id,
    }


def _empty_raw_inventory(error: str) -> dict[str, object]:
    return {
        "ready": False,
        "error": error,
        "map_feature_count": 0,
        "lane_feature_count": 0,
        "features_by_id": {},
        "feature_index_by_id": {},
    }


def _target_presence(
    target_id: str,
    capped_by_id: dict[str, dict[str, object]],
    raw_by_id: dict[str, object],
    raw_index_by_id: dict[str, object],
) -> dict[str, object]:
    raw_index = _optional_int(raw_index_by_id.get(target_id))
    return {
        "target_id": target_id,
        "present_in_capped_map": target_id in capped_by_id,
        "present_in_raw_map": target_id in raw_by_id,
        "raw_feature_index": raw_index,
        "beyond_cap": raw_index is not None
        and raw_index > MAX_MAP_FEATURES_PER_SCENARIO,
    }


def _diagnosis(
    lane_link_status: str,
    selected_feature_id: str,
    capped_feature: dict[str, object] | None,
    raw_selected: dict[str, object] | None,
    capped_targets: list[str],
    raw_targets: list[str],
    target_presence: list[dict[str, object]],
    capped_map_at_limit: bool,
) -> dict[str, object]:
    cap_recoverable_targets = [
        target
        for target in target_presence
        if not bool(target["present_in_capped_map"])
        and bool(target["present_in_raw_map"])
    ]
    cap_recovered_targets = [
        target
        for target in target_presence
        if bool(target["present_in_capped_map"])
        and bool(target["present_in_raw_map"])
        and bool(target["beyond_cap"])
    ]
    raw_missing_targets = [
        target
        for target in target_presence
        if not bool(target["present_in_raw_map"])
    ]
    if capped_feature is None:
        label = "selected_feature_missing_in_capped_map"
        reason = (
            "The selected lane feature is missing from the capped ScenarioLens "
            "map feature set, so link expansion cannot start."
        )
        actions = [
            "Audit selected-lane materialization before changing branch selection.",
            "Compare raw map feature ids against capped ScenarioLens features.",
        ]
    elif cap_recoverable_targets:
        label = "cap_recoverable_link_target"
        reason = (
            "At least one referenced link target exists in the raw parsed map "
            "but is absent from the capped ScenarioLens map feature set."
        )
        actions = [
            "Materialize closure features referenced by selected lane links before applying the map-feature cap.",
            "Rerun lane-continuation replay and branch coverage after link-closure loading.",
        ]
    elif cap_recovered_targets:
        label = "cap_recovered_link_target"
        reason = (
            "A referenced link target from beyond the raw feature cap is now "
            "available in the capped ScenarioLens map feature set."
        )
        actions = [
            "Rerun lane-continuation replay and branch coverage with link-closure materialization enabled.",
            "Confirm the former topology blocker moves into replay or branch-selection evidence.",
        ]
    elif not capped_targets and not raw_targets and raw_selected is not None:
        label = "terminal_lane_confirmed"
        reason = (
            "The selected lane has no parsed continuation in either capped or "
            "raw parsed map features."
        )
        actions = [
            "Audit selected-lane quality and nearby alternate lanes before expanding branch selection.",
            "Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.",
        ]
    elif raw_missing_targets:
        label = "raw_link_target_missing"
        reason = (
            "A referenced lane target is missing from the raw parsed map "
            "inventory, so this remains parser/proto-source follow-up."
        )
        actions = [
            "Inspect raw map proto parsing for referenced lane ids.",
            "Keep the case held until the target id can be materialized or explained.",
        ]
    elif lane_link_status in {"no_exit_lanes", "no_entry_lanes"}:
        label = "terminal_or_directional_link_gap"
        reason = (
            "The replay saw no usable directional link from the selected lane; "
            "raw targets did not reveal a simple cap recovery."
        )
        actions = [
            "Check selected-lane direction and nearby lane alternatives.",
            "Rerun topology audit after selected-lane or direction logic changes.",
        ]
    else:
        label = "unresolved_topology_gap"
        reason = (
            "The topology blocker could not be explained by cap recovery or "
            "terminal-lane evidence."
        )
        actions = [
            "Inspect selected lane links, raw map feature ids, and nearby lane geometry.",
        ]
    return {
        "diagnosis_label": label,
        "diagnosis_reason": reason,
        "cap_recovered": label == "cap_recovered_link_target",
        "cap_recoverable": label == "cap_recoverable_link_target",
        "terminal_confirmed": label == "terminal_lane_confirmed",
        "raw_target_missing": label == "raw_link_target_missing",
        "selected_feature_missing": label == "selected_feature_missing_in_capped_map",
        "capped_map_at_limit": capped_map_at_limit,
        "first_next_action": actions[0],
        "next_actions": actions,
    }


def _link_field(
    scenario: Scenario,
    track_id: str,
    lane_link_status: str,
) -> str:
    if lane_link_status == "no_entry_lanes":
        return "entry_lanes"
    if lane_link_status == "no_exit_lanes":
        return "exit_lanes"
    track = _find_track(scenario, track_id)
    if track is None:
        return "exit_lanes"
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return "exit_lanes"
    anchor = states[_anchor_index(states, scenario)]
    choice = _nearest_lane_feature(anchor, _lane_features(scenario))
    if choice is None:
        return "exit_lanes"
    direction = _lane_direction(anchor, choice["projection"])  # type: ignore[arg-type]
    return "exit_lanes" if direction >= 0.0 else "entry_lanes"


def _map_features(scenario: Scenario) -> list[dict[str, object]]:
    raw_features = scenario.metadata.get("waymo_map_features", ())
    if not isinstance(raw_features, list):
        return []
    return [feature for feature in raw_features if isinstance(feature, dict)]


def _find_scenario(scenarios: tuple[Scenario, ...], scenario_id: str) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _find_track(scenario: Scenario, track_id: str) -> AgentTrack | None:
    for track in scenario.tracks:
        if track.agent_id == track_id:
            return track
    return None


def _route_gap(nominal: dict[str, object]) -> float | None:
    horizon = _optional_float(nominal.get("horizon_travel_m"))
    remaining = _optional_float(nominal.get("route_remaining_m"))
    if horizon is None or remaining is None:
        return None
    return round(horizon - remaining, 3)


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    route_gaps = [
        gap
        for case in ready
        if (gap := _optional_float(case.get("route_gap_to_horizon_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "cap_recovered_case_count": sum(
            bool(case.get("cap_recovered")) for case in ready
        ),
        "cap_recoverable_case_count": sum(
            bool(case.get("cap_recoverable")) for case in ready
        ),
        "terminal_confirmed_case_count": sum(
            bool(case.get("terminal_confirmed")) for case in ready
        ),
        "raw_target_missing_case_count": sum(
            bool(case.get("raw_target_missing")) for case in ready
        ),
        "selected_feature_missing_case_count": sum(
            bool(case.get("selected_feature_missing")) for case in ready
        ),
        "capped_map_at_limit_count": sum(
            bool(case.get("capped_map_at_limit")) for case in ready
        ),
        "mean_route_gap_to_horizon_m": _mean(route_gaps),
    }


def _target_text(case: dict[str, object]) -> str:
    targets = case.get("link_target_ids")
    if not isinstance(targets, list) or not targets:
        return "none"
    return ", ".join(f"`{target}`" for target in targets)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _optional_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
