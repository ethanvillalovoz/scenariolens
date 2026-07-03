from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot, isfinite
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.lane_continuation import (
    _feature_id,
    _lane_features_by_id,
    _linked_lane_route,
)
from scenariolens.lane_continuation_branch_selection import (
    _chain_text,
    _meter_text,
    _optional_float,
    _optional_int,
    _required_list,
    _required_mapping,
    _route_result,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_replay import (
    _PERTURBATIONS,
    _perturb_anchor_velocity,
)
from scenariolens.lane_continuation_terminal_neighborhood_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
)
from scenariolens.prediction import (
    MIN_LANE_AWARE_SPEED_MPS,
    _anchor_index,
    _feature_points,
    _lane_direction,
    _lane_heading_alignment,
    _project_to_lane,
)
from scenariolens.schema import AgentTrack, Scenario

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_replay.v1"
)

DEFAULT_MIN_STABLE_GAIN_M = 1.0
DEFAULT_TOP = 5


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodReplayResult:
    """Files produced by a terminal-neighborhood replay/gate run."""

    ready: bool
    case_count: int
    replayed_case_count: int
    accepted_case_count: int
    held_case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_replay(
    terminal_neighborhood_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = DEFAULT_TOP,
    minimum_stable_gain_m: float = DEFAULT_MIN_STABLE_GAIN_M,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodReplayResult:
    """Generate public-safe replay evidence for terminal-neighborhood recovery."""

    source = Path(terminal_neighborhood_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_replay_payload(
        terminal_neighborhood_manifest_path=source,
        output_dir=target,
        top=top,
        minimum_stable_gain_m=minimum_stable_gain_m,
    )
    report = lane_continuation_terminal_neighborhood_replay_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodReplayResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        replayed_case_count=int(aggregate["replayed_case_count"]),
        accepted_case_count=int(aggregate["accepted_case_count"]),
        held_case_count=int(aggregate["held_case_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_replay_payload(
    terminal_neighborhood_manifest_path: Path,
    output_dir: Path,
    top: int = DEFAULT_TOP,
    minimum_stable_gain_m: float = DEFAULT_MIN_STABLE_GAIN_M,
) -> dict[str, object]:
    """Return replay/gate diagnostics for nearby terminal-lane recovery cases."""

    if top < 1:
        raise ValueError("top must be at least 1.")
    if minimum_stable_gain_m <= 0.0:
        raise ValueError("minimum-stable-gain-m must be positive.")

    audit = json.loads(terminal_neighborhood_manifest_path.read_text(encoding="utf-8"))
    if audit.get("format") != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT:
        raise ValueError(
            "Expected a terminal-neighborhood audit manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT}."
        )

    selected = [
        case
        for case in _required_list(audit, "cases")
        if isinstance(case, dict) and _is_replay_candidate(case)
    ][:top]
    max_scenarios = _optional_int(audit.get("max_scenarios_per_source"))
    max_hops = _optional_int(audit.get("max_hops")) or 2
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ] = {}
    cases = [
        _replay_case(
            audit_case=case,
            source_cache=source_cache,
            max_scenarios_per_source=max_scenarios,
            max_hops=max_hops,
            minimum_stable_gain_m=minimum_stable_gain_m,
        )
        for case in selected
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
        "terminal_neighborhood_manifest": str(terminal_neighborhood_manifest_path),
        "terminal_neighborhood_format": audit.get("format"),
        "topology_manifest": audit.get("topology_manifest"),
        "replay_manifest": audit.get("replay_manifest"),
        "candidate_manifest": audit.get("candidate_manifest"),
        "study_manifest": audit.get("study_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(audit.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "top": top,
        "max_scenarios_per_source": max_scenarios,
        "max_hops": max_hops,
        "minimum_stable_gain_m": round(minimum_stable_gain_m, 3),
        "selected_candidate_count": len(selected),
        "source_terminal_case_count": int(
            audit.get("selected_terminal_case_count", 0) or 0
        ),
        "perturbations": list(_PERTURBATIONS),
        "acceptance_gate": (
            "Accept a terminal-neighborhood recovery candidate only when the "
            "forced alternate lane improves selected-lane FDE by at least "
            f"{minimum_stable_gain_m:.1f} m nominally and every valid "
            "perturbation preserves the alternate chain with the same minimum gain."
        ),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Terminal-neighborhood replay is an open-loop diagnostic over "
            "candidate lanes proposed by the terminal-neighborhood audit. It "
            "does not change default scoring, branch selection, or map matching; "
            "it publishes only derived replay/gate summaries."
        ),
    }


def lane_continuation_terminal_neighborhood_replay_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for terminal-neighborhood replay/gating."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    perturbations = _required_list(payload, "perturbations")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Replay Gate",
        "",
        "This report follows the terminal-neighborhood audit by force-replaying "
        "the proposed nearby lane alternatives against their selected terminal "
        "lanes. The goal is to decide whether each alternate lane is ready for "
        "broader selector experiments or should stay held as diagnostic evidence.",
        "",
        "The replay is intentionally narrow: it does not change the default "
        "ScenarioLens scorer, does not publish raw map geometry, and is not a "
        "Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Terminal-neighborhood manifest: `{payload['terminal_neighborhood_manifest']}`",
        f"- Topology manifest: `{payload.get('topology_manifest')}`",
        f"- Replay manifest: `{payload.get('replay_manifest')}`",
        f"- Ready: {payload['ready']}",
        f"- Max scenarios per source: {payload['max_scenarios_per_source']}",
        f"- Max lane-link hops: {payload['max_hops']}",
        f"- Selected candidates: {payload['selected_candidate_count']}",
        f"- Minimum stable gain: {_meter_text(payload['minimum_stable_gain_m'])}",
        f"- Acceptance gate: {payload['acceptance_gate']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Replay Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Replayed cases | {aggregate['replayed_case_count']} |",
        f"| Accepted recovery candidates | {aggregate['accepted_case_count']} |",
        f"| Held candidates | {aggregate['held_case_count']} |",
        f"| Nominal improvement cases | {aggregate['nominal_improvement_case_count']} |",
        f"| Nominal regression cases | {aggregate['nominal_regression_case_count']} |",
        f"| Perturbation trials | {aggregate['perturbation_trial_count']} |",
        f"| Chain-preserving trials | {aggregate['chain_preserving_trial_count']} |",
        f"| Stable-gain trials | {aggregate['stable_gain_trial_count']} |",
        f"| Mean nominal gain | {_signed_meter_text(aggregate['mean_nominal_gain_m'])} |",
        f"| Mean perturbed gain | {_signed_meter_text(aggregate['mean_trial_gain_m'])} |",
        f"| Min perturbed gain | {_signed_meter_text(aggregate['min_trial_gain_m'])} |",
        f"| Max perturbed gain | {_signed_meter_text(aggregate['max_trial_gain_m'])} |",
        "",
        "## Perturbations",
        "",
    ]
    for perturbation in perturbations:
        assert isinstance(perturbation, dict)
        lines.append(f"- `{perturbation['label']}`: {perturbation['description']}")

    lines.extend(
        [
            "",
            "## Gate Decisions",
            "",
            "| Rank | Scenario | Track | Selected lane | Alternate lane | Selected FDE | Alternate FDE | Gain | Stable trials | Decision | First next action |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0/0 | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        stability = _required_mapping(case, "perturbation_stability")
        decision = _required_mapping(case, "gate_decision")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{_chain_text(case.get('selected_chain'))} | "
            f"{_chain_text(case.get('alternate_chain'))} | "
            f"{_meter_text(case.get('selected_fde_m'))} | "
            f"{_meter_text(case.get('alternate_fde_m'))} | "
            f"{_signed_meter_text(case.get('nominal_gain_m'))} | "
            f"{stability['stable_gain_trial_count']}/{stability['valid_trial_count']} | "
            f"`{decision['label']}` | "
            f"{decision['next_action']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        decision = _required_mapping(case, "gate_decision")
        stability = _required_mapping(case, "perturbation_stability")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Ready: {case['ready']}",
                f"- Decision: **{decision['label']}**",
                f"- Reason: {decision['reason']}",
                f"- Recommended next action: {decision['next_action']}",
                f"- Selected feature: `{case['selected_feature_id']}`",
                f"- Alternate feature: `{case['alternate_feature_id']}`",
                f"- Selected chain: {_chain_text(case.get('selected_chain'))}",
                f"- Alternate chain: {_chain_text(case.get('alternate_chain'))}",
                f"- Selected route status/count: `{case['selected_route_status']}` / {case['selected_link_count']}",
                f"- Alternate route status/count: `{case['alternate_route_status']}` / {case['alternate_link_count']}",
                f"- Selected/alternate lane distance: {_meter_text(case.get('selected_lane_distance_m'))} / {_meter_text(case.get('alternate_lane_distance_m'))}",
                f"- Selected/alternate heading alignment: {case.get('selected_heading_alignment')} / {case.get('alternate_heading_alignment')}",
                f"- Selected/alternate route remaining: {_meter_text(case.get('selected_route_remaining_m'))} / {_meter_text(case.get('alternate_route_remaining_m'))}",
                f"- Selected/alternate FDE: {_meter_text(case.get('selected_fde_m'))} / {_meter_text(case.get('alternate_fde_m'))}",
                f"- Nominal gain: {_signed_meter_text(case.get('nominal_gain_m'))}",
                f"- Stable trials: {stability['stable_gain_trial_count']}/{stability['valid_trial_count']}",
                f"- Chain-preserving trials: {stability['chain_preserving_trial_count']}/{stability['valid_trial_count']}",
                f"- Worst trial: `{stability['worst_trial_label']}`",
                f"- Min/mean/max perturbed gain: {_signed_meter_text(stability.get('min_gain_m'))} / {_signed_meter_text(stability.get('mean_gain_m'))} / {_signed_meter_text(stability.get('max_gain_m'))}",
                "",
                "Perturbation trials:",
                "",
                "| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |",
                "| --- | --- | --- | ---: | --- | --- | --- |",
            ]
        )
        for trial in _required_list(case, "perturbation_trials"):
            assert isinstance(trial, dict)
            lines.append(
                "| "
                f"`{trial['label']}` | "
                f"{_chain_text(trial.get('selected_chain'))} | "
                f"{_chain_text(trial.get('alternate_chain'))} | "
                f"{_signed_meter_text(trial.get('gain_m'))} | "
                f"{trial['chain_preserved']} | "
                f"{trial['stable_gain']} | "
                f"`{trial['verdict']}` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Accepted recovery candidates are not default behavior; they are next-pass selector candidates with replay evidence.",
            "- Held candidates remain useful: they explain why a nearby lane looked plausible in topology but was not robust enough under open-loop replay.",
            "- The gate requires both chain preservation and a positive FDE margin under deterministic speed and heading perturbations.",
            "- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_replay_candidate(case: dict[str, object]) -> bool:
    alternate = case.get("best_alternate_feature_id")
    return (
        bool(case.get("ready"))
        and str(case.get("diagnosis_label")) == "nearby_alternate_lane_recovery"
        and alternate not in (None, "")
    )


def _replay_case(
    audit_case: dict[str, object],
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
    max_scenarios_per_source: int | None,
    max_hops: int,
    minimum_stable_gain_m: float,
) -> dict[str, object]:
    source_input = Path(str(audit_case.get("source_input", "")))
    input_format = str(audit_case.get("input_format", "native"))
    scenario_id = str(audit_case.get("scenario_id", ""))
    track_id = str(audit_case.get("track_id", ""))
    selected_feature_id = str(audit_case.get("selected_feature_id", ""))
    alternate_feature_id = str(audit_case.get("best_alternate_feature_id", ""))
    base = {
        "rank": int(audit_case.get("rank", 0) or 0),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source_input),
        "source_name": str(audit_case.get("source_name", source_input.name)),
        "input_format": input_format,
        "ready": False,
        "selected_feature_id": selected_feature_id,
        "alternate_feature_id": alternate_feature_id,
        "selected_chain": [],
        "alternate_chain": [],
        "selected_fde_m": None,
        "alternate_fde_m": None,
        "nominal_gain_m": None,
        "perturbation_trials": [],
        "perturbation_stability": _empty_stability(),
        "gate_decision": _gate_decision(
            ready=False,
            nominal_gain=None,
            stability=_empty_stability(),
            minimum_stable_gain_m=minimum_stable_gain_m,
        ),
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

    nominal = _forced_replay_pair(
        scenario=scenario,
        track_id=track_id,
        selected_feature_id=selected_feature_id,
        alternate_feature_id=alternate_feature_id,
        max_hops=max_hops,
    )
    if not bool(nominal.get("ready")):
        stability = _empty_stability()
        base.update(
            {
                "input_ready": input_ready,
                "preflight": preflight or {},
                **nominal,
                "perturbation_stability": stability,
                "gate_decision": _gate_decision(
                    ready=False,
                    nominal_gain=nominal.get("nominal_gain_m"),
                    stability=stability,
                    minimum_stable_gain_m=minimum_stable_gain_m,
                ),
            }
        )
        return base

    expected_chain = tuple(str(item) for item in nominal.get("alternate_chain", []))
    trials = [
        _perturbation_trial(
            scenario=scenario,
            track_id=track_id,
            selected_feature_id=selected_feature_id,
            alternate_feature_id=alternate_feature_id,
            max_hops=max_hops,
            expected_chain=expected_chain,
            minimum_stable_gain_m=minimum_stable_gain_m,
            perturbation=perturbation,
        )
        for perturbation in _PERTURBATIONS
    ]
    stability = _perturbation_stability(
        trials=trials,
        minimum_stable_gain_m=minimum_stable_gain_m,
    )
    decision = _gate_decision(
        ready=True,
        nominal_gain=nominal.get("nominal_gain_m"),
        stability=stability,
        minimum_stable_gain_m=minimum_stable_gain_m,
    )
    base.update(
        {
            "ready": True,
            "input_ready": input_ready,
            "preflight": preflight or {},
            **nominal,
            "perturbation_trials": trials,
            "perturbation_stability": stability,
            "gate_decision": decision,
        }
    )
    return base


def _forced_replay_pair(
    scenario: Scenario,
    track_id: str,
    selected_feature_id: str,
    alternate_feature_id: str,
    max_hops: int,
) -> dict[str, object]:
    track = _find_track(scenario, track_id)
    if track is None:
        return _not_ready("track_not_found")
    selected = _forced_route_result(
        scenario=scenario,
        track=track,
        feature_id=selected_feature_id,
        max_hops=max_hops,
    )
    alternate = _forced_route_result(
        scenario=scenario,
        track=track,
        feature_id=alternate_feature_id,
        max_hops=max_hops,
    )
    if not bool(selected.get("ready")):
        return _not_ready(f"selected_route_not_ready:{selected.get('error')}")
    if not bool(alternate.get("ready")):
        return _not_ready(f"alternate_route_not_ready:{alternate.get('error')}")
    selected_fde = _optional_float(selected.get("fde_m"))
    alternate_fde = _optional_float(alternate.get("fde_m"))
    gain = (
        round(selected_fde - alternate_fde, 3)
        if selected_fde is not None and alternate_fde is not None
        else None
    )
    return {
        "ready": True,
        "selected_lane_distance_m": selected.get("lane_distance_m"),
        "alternate_lane_distance_m": alternate.get("lane_distance_m"),
        "selected_heading_alignment": selected.get("heading_alignment"),
        "alternate_heading_alignment": alternate.get("heading_alignment"),
        "selected_chain": selected.get("feature_chain", []),
        "alternate_chain": alternate.get("feature_chain", []),
        "selected_link_count": selected.get("link_count", 0),
        "alternate_link_count": alternate.get("link_count", 0),
        "selected_route_status": selected.get("status"),
        "alternate_route_status": alternate.get("status"),
        "selected_route_remaining_m": selected.get("route_remaining_m"),
        "alternate_route_remaining_m": alternate.get("route_remaining_m"),
        "selected_base_remaining_m": selected.get("base_remaining_m"),
        "alternate_base_remaining_m": alternate.get("base_remaining_m"),
        "selected_fde_m": selected_fde,
        "alternate_fde_m": alternate_fde,
        "selected_ade_m": selected.get("ade_m"),
        "alternate_ade_m": alternate.get("ade_m"),
        "nominal_gain_m": gain,
        "horizon_travel_m": selected.get("horizon_travel_m"),
    }


def _forced_route_result(
    scenario: Scenario,
    track: AgentTrack,
    feature_id: str,
    max_hops: int,
) -> dict[str, object]:
    if track.agent_type not in {"vehicle", "cyclist"}:
        return _not_ready("non_vehicle_or_cyclist_target")
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return _not_ready("insufficient_track_states")
    anchor_index = _anchor_index(states, scenario)
    anchor = states[anchor_index]
    history_states = states[: anchor_index + 1]
    future_states = tuple(
        state for state in states[anchor_index + 1 :] if state.t > anchor.t
    )
    if not future_states:
        return _not_ready("no_future_states")
    anchor_speed = hypot(anchor.vx, anchor.vy)
    if not isfinite(anchor_speed) or anchor_speed < MIN_LANE_AWARE_SPEED_MPS:
        return _not_ready("low_or_invalid_anchor_speed")

    feature = _lane_features_by_id(scenario).get(feature_id)
    if feature is None:
        return _not_ready("feature_not_found")
    lane = _feature_points(feature)
    projection = _project_to_lane(anchor.x, anchor.y, lane)
    if projection is None:
        return _not_ready("projection_unavailable")
    direction = _lane_direction(anchor, projection)
    route = _linked_lane_route(
        feature=feature,
        projection=projection,
        direction=direction,
        scenario=scenario,
        max_hops=max_hops,
    )
    result = _route_result(
        route=route,
        anchor=anchor,
        history_states=history_states,
        future_states=future_states,
        anchor_speed=anchor_speed,
        default_chain=tuple(route.feature_ids),
        features_by_id=_lane_features_by_id(scenario),
    )
    return {
        "ready": True,
        "feature_id": _feature_id(feature),
        "lane_distance_m": round(float(getattr(projection, "distance_m")), 3),
        "heading_alignment": round(
            _lane_heading_alignment(anchor, projection), 3  # type: ignore[arg-type]
        ),
        "direction": "forward" if direction >= 0.0 else "reverse",
        **result,
    }


def _perturbation_trial(
    scenario: Scenario,
    track_id: str,
    selected_feature_id: str,
    alternate_feature_id: str,
    max_hops: int,
    expected_chain: tuple[str, ...],
    minimum_stable_gain_m: float,
    perturbation: dict[str, object],
) -> dict[str, object]:
    perturbed = _perturb_anchor_velocity(
        scenario=scenario,
        track_id=track_id,
        speed_scale=float(perturbation["speed_scale"]),
        heading_delta_deg=float(perturbation["heading_delta_deg"]),
    )
    replay = _forced_replay_pair(
        scenario=perturbed,
        track_id=track_id,
        selected_feature_id=selected_feature_id,
        alternate_feature_id=alternate_feature_id,
        max_hops=max_hops,
    )
    gain = _optional_float(replay.get("nominal_gain_m"))
    alternate_chain = tuple(str(item) for item in replay.get("alternate_chain", []))
    chain_preserved = bool(replay.get("ready")) and alternate_chain == expected_chain
    stable_gain = gain is not None and gain >= minimum_stable_gain_m
    if not bool(replay.get("ready")):
        verdict = str(replay.get("error", "not_evaluable"))
    elif chain_preserved and stable_gain:
        verdict = "stable_recovery"
    elif not chain_preserved:
        verdict = "alternate_chain_changed"
    elif gain is not None and gain > 0.0:
        verdict = "thin_positive_margin"
    else:
        verdict = "alternate_regressed"
    return {
        "label": perturbation["label"],
        "speed_scale": perturbation["speed_scale"],
        "heading_delta_deg": perturbation["heading_delta_deg"],
        "ready": bool(replay.get("ready")),
        "selected_chain": replay.get("selected_chain", []),
        "alternate_chain": replay.get("alternate_chain", []),
        "selected_fde_m": replay.get("selected_fde_m"),
        "alternate_fde_m": replay.get("alternate_fde_m"),
        "gain_m": gain,
        "chain_preserved": chain_preserved,
        "stable_gain": stable_gain,
        "verdict": verdict,
    }


def _perturbation_stability(
    trials: list[dict[str, object]],
    minimum_stable_gain_m: float,
) -> dict[str, object]:
    valid = [trial for trial in trials if bool(trial.get("ready"))]
    gains = [
        gain
        for trial in valid
        if (gain := _optional_float(trial.get("gain_m"))) is not None
    ]
    chain_preserving = sum(bool(trial.get("chain_preserved")) for trial in valid)
    stable = sum(bool(trial.get("stable_gain")) for trial in valid)
    worst = (
        min(
            valid,
            key=lambda trial: _optional_float(trial.get("gain_m")) or -999999.0,
        )
        if valid
        else None
    )
    if not valid:
        label = "not_evaluable"
    elif chain_preserving == len(valid) and stable == len(valid):
        label = "stable_recovery"
    elif stable > 0:
        label = "sensitive_recovery"
    elif gains and max(gains) > 0.0:
        label = "thin_margin"
    else:
        label = "recovery_regressed"
    return {
        "label": label,
        "valid_trial_count": len(valid),
        "chain_preserving_trial_count": chain_preserving,
        "stable_gain_trial_count": stable,
        "minimum_stable_gain_m": round(minimum_stable_gain_m, 3),
        "min_gain_m": round(min(gains), 3) if gains else None,
        "mean_gain_m": _mean(gains),
        "max_gain_m": round(max(gains), 3) if gains else None,
        "worst_trial_label": worst.get("label") if worst else None,
    }


def _gate_decision(
    ready: bool,
    nominal_gain: object,
    stability: dict[str, object],
    minimum_stable_gain_m: float,
) -> dict[str, object]:
    gain = _optional_float(nominal_gain)
    valid_count = int(stability.get("valid_trial_count", 0) or 0)
    stable_count = int(stability.get("stable_gain_trial_count", 0) or 0)
    chain_count = int(stability.get("chain_preserving_trial_count", 0) or 0)
    if not ready or valid_count == 0:
        return {
            "label": "not_evaluable",
            "accepted": False,
            "reason": "The forced selected/alternate route pair could not be replayed.",
            "next_action": "Confirm local source data and rerun the replay gate.",
        }
    if (
        gain is not None
        and gain >= minimum_stable_gain_m
        and stable_count == valid_count
        and chain_count == valid_count
    ):
        return {
            "label": "accept_for_selector_experiment",
            "accepted": True,
            "reason": (
                "The alternate lane beats the selected terminal lane nominally "
                "and under every deterministic perturbation."
            ),
            "next_action": "Promote this alternate-lane recovery into the next bounded selector experiment.",
        }
    if gain is not None and gain > 0.0:
        return {
            "label": "hold_for_margin_or_stability",
            "accepted": False,
            "reason": (
                "The alternate lane helps nominally, but the gain or chain "
                "stability is not strong enough for the replay gate."
            ),
            "next_action": "Keep the case as a replay diagnostic and add route-context features before promotion.",
        }
    return {
        "label": "hold_recovery_regressed",
        "accepted": False,
        "reason": (
            "The alternate lane does not beat the selected terminal-lane replay "
            "on this open-loop check."
        ),
        "next_action": "Do not promote this alternate; inspect selected-lane quality and local topology manually.",
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    decisions = [
        _required_mapping(case, "gate_decision")
        for case in ready
        if isinstance(case.get("gate_decision"), dict)
    ]
    trial_rows = [
        trial
        for case in ready
        for trial in _required_list(case, "perturbation_trials")
        if isinstance(trial, dict) and bool(trial.get("ready"))
    ]
    nominal_gains = [
        gain
        for case in ready
        if (gain := _optional_float(case.get("nominal_gain_m"))) is not None
    ]
    trial_gains = [
        gain
        for trial in trial_rows
        if (gain := _optional_float(trial.get("gain_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "replayed_case_count": len(ready),
        "accepted_case_count": sum(
            bool(decision.get("accepted")) for decision in decisions
        ),
        "held_case_count": sum(
            not bool(decision.get("accepted")) for decision in decisions
        ),
        "nominal_improvement_case_count": sum(gain > 0.0 for gain in nominal_gains),
        "nominal_regression_case_count": sum(gain <= 0.0 for gain in nominal_gains),
        "perturbation_trial_count": len(trial_rows),
        "chain_preserving_trial_count": sum(
            bool(trial.get("chain_preserved")) for trial in trial_rows
        ),
        "stable_gain_trial_count": sum(
            bool(trial.get("stable_gain")) for trial in trial_rows
        ),
        "mean_nominal_gain_m": _mean(nominal_gains),
        "mean_trial_gain_m": _mean(trial_gains),
        "min_trial_gain_m": round(min(trial_gains), 3) if trial_gains else None,
        "max_trial_gain_m": round(max(trial_gains), 3) if trial_gains else None,
    }


def _not_ready(error: str) -> dict[str, object]:
    return {"ready": False, "error": error}


def _empty_stability() -> dict[str, object]:
    return {
        "label": "not_evaluable",
        "valid_trial_count": 0,
        "chain_preserving_trial_count": 0,
        "stable_gain_trial_count": 0,
        "minimum_stable_gain_m": DEFAULT_MIN_STABLE_GAIN_M,
        "min_gain_m": None,
        "mean_gain_m": None,
        "max_gain_m": None,
        "worst_trial_label": None,
    }


def _find_scenario(scenarios: tuple[Scenario, ...], scenario_id: str) -> Scenario | None:
    return next(
        (scenario for scenario in scenarios if scenario.scenario_id == scenario_id),
        None,
    )


def _find_track(scenario: Scenario, track_id: str) -> AgentTrack | None:
    return next((track for track in scenario.tracks if track.agent_id == track_id), None)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)
