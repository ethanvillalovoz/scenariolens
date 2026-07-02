from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot, isfinite
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.lane_continuation import (
    _append_lane_points,
    _feature_id,
    _feature_points,
    _lane_features,
    _lane_features_by_id,
    _lane_length,
    _link_ids,
    _nearest_lane_feature,
)
from scenariolens.lane_continuation_diagnostics import (
    LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.prediction import (
    DEFAULT_MISS_THRESHOLD_M,
    LANE_MATCH_THRESHOLD_M,
    MIN_LANE_AWARE_SPEED_MPS,
    _advance_along_lane,
    _anchor_index,
    _lane_direction,
    _state_error,
)
from scenariolens.schema import AgentTrack, Scenario, State

LANE_CONTINUATION_BRANCH_SELECTION_FORMAT = (
    "scenariolens.lane_continuation_branch_selection.v1"
)

_REGRESSION_BUCKET = "regression_replay_debug"
_ACTIONABLE_LABELS = {
    "stable_route_choice_regression",
    "route_horizon_limit",
    "linked_route_worse_than_constant_velocity",
    "route_choice_or_speed_prior_audit",
}


@dataclass(frozen=True)
class LaneContinuationBranchSelectionResult:
    """Files produced by a lane-continuation branch-selection diagnostic run."""

    ready: bool
    case_count: int
    branchable_count: int
    motion_context_improved_count: int
    oracle_improved_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


@dataclass(frozen=True)
class _BranchRoute:
    feature_ids: tuple[str, ...]
    points: tuple[tuple[float, float], ...]
    link_count: int
    status: str
    start_s: float
    base_remaining_m: float
    route_remaining_m: float


def generate_lane_continuation_branch_selection(
    diagnostics_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = 5,
    max_hops: int = 2,
    public_report_path: str | Path | None = None,
) -> LaneContinuationBranchSelectionResult:
    """Generate a public-safe branch-selection diagnostic packet."""

    source = Path(diagnostics_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_branch_selection_payload(
        diagnostics_manifest_path=source,
        output_dir=target,
        top=top,
        max_hops=max_hops,
    )
    report = lane_continuation_branch_selection_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationBranchSelectionResult(
        ready=bool(payload["ready"]),
        case_count=int(payload["case_count"]),
        branchable_count=int(aggregate["branchable_case_count"]),
        motion_context_improved_count=int(
            aggregate["motion_context_improved_case_count"]
        ),
        oracle_improved_count=int(aggregate["oracle_improved_case_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_branch_selection_payload(
    diagnostics_manifest_path: Path,
    output_dir: Path,
    top: int,
    max_hops: int,
) -> dict[str, object]:
    """Return branch-selection diagnostics from route-diagnostic cases."""

    if top < 1:
        raise ValueError("top must be at least 1.")
    if max_hops < 1:
        raise ValueError("max-hops must be at least 1.")

    diagnostics = json.loads(diagnostics_manifest_path.read_text(encoding="utf-8"))
    if diagnostics.get("format") != LANE_CONTINUATION_DIAGNOSTICS_FORMAT:
        raise ValueError(
            "Expected a lane-continuation route-diagnostics manifest with format "
            f"{LANE_CONTINUATION_DIAGNOSTICS_FORMAT}."
        )

    replay_manifest_path = _resolve_path(
        diagnostics.get("replay_manifest"),
        diagnostics_manifest_path,
    )
    replay = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay.get("format") != LANE_CONTINUATION_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation replay manifest with format "
            f"{LANE_CONTINUATION_REPLAY_FORMAT}."
        )

    replay_cases = {
        (str(case.get("scenario_id")), str(case.get("track_id"))): case
        for case in _required_list(replay, "cases")
        if isinstance(case, dict)
    }
    selected = [
        diagnostic
        for diagnostic in _required_list(diagnostics, "diagnostics")
        if isinstance(diagnostic, dict)
        and diagnostic.get("bucket") == _REGRESSION_BUCKET
        and str(diagnostic.get("diagnosis_label")) in _ACTIONABLE_LABELS
    ][:top]

    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ] = {}
    cases = [
        _branch_case(
            diagnostic=diagnostic,
            replay_case=replay_cases.get(
                (str(diagnostic.get("scenario_id")), str(diagnostic.get("track_id")))
            ),
            max_hops=max_hops,
            source_cache=source_cache,
            replay_max_scenarios=_optional_int(replay.get("max_scenarios_per_source")),
        )
        for diagnostic in selected
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
        "diagnostics_manifest": str(diagnostics_manifest_path),
        "diagnostics_format": diagnostics.get("format"),
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(diagnostics.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "top": top,
        "max_lane_link_hops": max_hops,
        "case_count": len(cases),
        "source_diagnostic_count": len(_required_list(diagnostics, "diagnostics")),
        "selected_diagnostic_count": len(selected),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Branch-selection diagnostics only; the oracle branch is an "
            "observed-future upper bound for debugging and is not a deployable "
            "planner, not closed-loop simulation, not Waymax/JAX execution, "
            "and not a Waymo benchmark claim."
        ),
    }


def lane_continuation_branch_selection_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for branch-selection diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Lane-Continuation Branch Selection Diagnostic",
        "",
        "This report follows the route-diagnostics casebook with a branch sweep: "
        "for each replayed continuation regression, ScenarioLens reloads the "
        "local scenario, enumerates parsed linked-lane alternatives, and "
        "compares the current geometric route against three diagnostic selectors.",
        "",
        "The `anchor_heading` selector uses only the anchor velocity and parsed "
        "route geometry. The `motion_context` selector adds a non-oracle route "
        "prior from recent target speed, known forecast horizon, route-chain "
        "length, and downstream lane speed limits. The `oracle_upper_bound` "
        "selector is an oracle upper bound that uses the observed future "
        "trajectory only to quantify whether choosing another parsed branch "
        "could explain the failure. It is intentionally not a route planner, "
        "not closed-loop simulation, not Waymax/JAX execution, and not a "
        "Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Diagnostics manifest: `{payload['diagnostics_manifest']}`",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Ready for branch diagnostics: {payload['ready']}",
        f"- Cases analyzed: {payload['case_count']}",
        f"- Max lane-link hops: {payload['max_lane_link_hops']}",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Branch Sweep Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Evaluable cases | {aggregate['evaluable_case_count']} |",
        f"| Branchable cases | {aggregate['branchable_case_count']} |",
        f"| Single-chain cases | {aggregate['single_chain_case_count']} |",
        f"| Oracle upper-bound improvements | {aggregate['oracle_improved_case_count']} |",
        f"| Anchor-heading selector improvements | {aggregate['anchor_heading_improved_case_count']} |",
        f"| Anchor-heading selector changed route | {aggregate['anchor_heading_changed_case_count']} |",
        f"| Motion-context selector improvements | {aggregate['motion_context_improved_case_count']} |",
        f"| Motion-context selector changed route | {aggregate['motion_context_changed_case_count']} |",
        f"| Motion-context matched oracle on branchable cases | {aggregate['motion_context_oracle_match_branchable_count']} |",
        f"| Mean motion-context recoverable FDE | {_signed_meter_text(aggregate['mean_motion_context_recoverable_fde_m'])} |",
        f"| Max motion-context recoverable FDE | {_signed_meter_text(aggregate['max_motion_context_recoverable_fde_m'])} |",
        f"| Default route still best | {aggregate['default_best_case_count']} |",
        f"| Mean oracle recoverable FDE | {_signed_meter_text(aggregate['mean_oracle_recoverable_fde_m'])} |",
        f"| Max oracle recoverable FDE | {_signed_meter_text(aggregate['max_oracle_recoverable_fde_m'])} |",
        "",
        "## Case Results",
        "",
        "| Rank | Scenario | Track | Diagnosis | Routes | Default chain | Motion-context chain | Oracle chain | Motion gain | Oracle gain | Verdict |",
        "| ---: | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['diagnosis_label']}` | "
            f"{case['route_candidate_count']} | "
            f"{_chain_text(case.get('default_chain'))} | "
            f"{_chain_text(case.get('motion_context_chain'))} | "
            f"{_chain_text(case.get('oracle_chain'))} | "
            f"{_signed_meter_text(case.get('motion_context_recoverable_fde_m'))} | "
            f"{_signed_meter_text(case.get('oracle_recoverable_fde_m'))} | "
            f"`{case['verdict']}` |"
        )

    for case in cases:
        assert isinstance(case, dict)
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Diagnosis source: `{case['diagnosis_label']}`",
                f"- Source: `{case['source_name']}`",
                f"- Ready: {case['ready']}",
                f"- Verdict: **{case['verdict']}**",
                f"- Why it matters: {case['why_it_matters']}",
                f"- Default linked-route FDE: {_meter_text(case.get('default_fde_m'))}",
                f"- Anchor-heading route FDE: {_meter_text(case.get('anchor_heading_fde_m'))}",
                f"- Motion-context route FDE: {_meter_text(case.get('motion_context_fde_m'))}",
                f"- Oracle upper-bound route FDE: {_meter_text(case.get('oracle_fde_m'))}",
                f"- Motion-context recoverable FDE: {_signed_meter_text(case.get('motion_context_recoverable_fde_m'))}",
                f"- Oracle recoverable FDE: {_signed_meter_text(case.get('oracle_recoverable_fde_m'))}",
                f"- Motion-context estimated travel: {_meter_text(case.get('motion_context_estimated_travel_m'))}",
                f"- Route candidate count: {case['route_candidate_count']}",
                "",
                "Route candidates:",
                "",
                "| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |",
                "| --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        route_candidates = _required_list(case, "route_candidates")
        if not route_candidates:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a |")
        for route in route_candidates:
            assert isinstance(route, dict)
            flags = []
            if route.get("is_default"):
                flags.append("default")
            if route.get("is_anchor_heading_selected"):
                flags.append("anchor_heading")
            if route.get("is_motion_context_selected"):
                flags.append("motion_context")
            if route.get("is_oracle_selected"):
                flags.append("oracle_upper_bound")
            lines.append(
                "| "
                f"{_chain_text(route.get('feature_chain'))} | "
                f"`{route['status']}` | "
                f"{_score_text(route.get('anchor_heading_score'))} | "
                f"{_score_text(route.get('motion_context_score'))} | "
                f"{_meter_text(route.get('fde_m'))} | "
                f"{_signed_meter_text(route.get('gain_vs_default_m'))} | "
                f"{', '.join(flags) if flags else 'n/a'} |"
            )
        actions = _required_list(case, "next_actions")
        if actions:
            lines.extend(["", "Recommended next actions:"])
            lines.extend(f"- {action}" for action in actions)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Branchable cases show where the parsed map topology exposes more than one continuation from the selected lane.",
            "- Motion-context improvements are non-oracle evidence that recent speed, horizon length, and downstream lane speed limits can choose a better parsed branch on some cases.",
            "- Oracle upper-bound improvements prove that a different parsed branch can reduce open-loop error, but they are not deployable predictor results because they use observed future motion.",
            "- If motion-context still misses an oracle-improvable route, the next step is richer context such as turn-lane semantics, signal state, route context, or a learned candidate scorer.",
            "- Single-chain cases need longer topology, parser coverage, or a different selected lane before branch selection can help.",
            "- Public outputs stay diagnostic; raw Waymo TFRecords and local packets remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _branch_case(
    diagnostic: dict[str, object],
    replay_case: dict[str, object] | None,
    max_hops: int,
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
    replay_max_scenarios: int | None,
) -> dict[str, object]:
    rank = int(diagnostic.get("rank", 0) or 0)
    scenario_id = str(diagnostic.get("scenario_id", ""))
    track_id = str(diagnostic.get("track_id", ""))
    base = {
        "rank": rank,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "diagnosis_label": str(diagnostic.get("diagnosis_label", "unknown")),
        "source_name": str(diagnostic.get("source_name", "")),
        "ready": False,
        "route_candidate_count": 0,
        "route_candidates": [],
        "default_chain": [],
        "anchor_heading_chain": [],
        "motion_context_chain": [],
        "oracle_chain": [],
        "default_fde_m": None,
        "anchor_heading_fde_m": None,
        "motion_context_fde_m": None,
        "oracle_fde_m": None,
        "motion_context_recoverable_fde_m": None,
        "oracle_recoverable_fde_m": None,
        "motion_context_estimated_travel_m": None,
        "verdict": "not_evaluable",
        "why_it_matters": "The case could not be reloaded for branch diagnostics.",
        "next_actions": [
            "Confirm the replay manifest and local source data are available.",
        ],
    }
    if replay_case is None:
        base["error"] = "replay_case_not_found"
        return base

    source_input = Path(str(replay_case.get("source_input", "")))
    input_format = str(replay_case.get("input_format", "native"))
    max_scenarios = replay_max_scenarios
    source_key = (str(source_input), input_format, max_scenarios)
    if source_key not in source_cache:
        source_cache[source_key] = load_failure_study_input(
            source=source_input,
            input_format=input_format,
            max_scenarios=max_scenarios,
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
        base["error"] = "track_not_found"
        return base

    evaluation = _evaluate_branch_routes(
        scenario=scenario,
        track=track,
        replay_case=replay_case,
        max_hops=max_hops,
    )
    base.update(evaluation)
    base["source_input"] = str(source_input)
    base["source_name"] = str(replay_case.get("source_name", source_input.name))
    base["input_format"] = input_format
    base["input_ready"] = input_ready
    base["preflight"] = preflight or {}
    return base


def _evaluate_branch_routes(
    scenario: Scenario,
    track: AgentTrack,
    replay_case: dict[str, object],
    max_hops: int,
) -> dict[str, object]:
    if track.agent_type not in {"vehicle", "cyclist"}:
        return _not_evaluable("non_vehicle_or_cyclist_target")

    features = _lane_features(scenario)
    if not features:
        return _not_evaluable("no_lane_map_features")

    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return _not_evaluable("insufficient_track_states")

    anchor_index = _anchor_index(states, scenario)
    anchor = states[anchor_index]
    history_states = states[: anchor_index + 1]
    future_states = tuple(
        state for state in states[anchor_index + 1 :] if state.t > anchor.t
    )
    if not future_states:
        return _not_evaluable("no_future_states")

    anchor_speed = hypot(anchor.vx, anchor.vy)
    if not isfinite(anchor_speed) or anchor_speed < MIN_LANE_AWARE_SPEED_MPS:
        return _not_evaluable("low_or_invalid_anchor_speed")

    choice = _nearest_lane_feature(anchor, features)
    if choice is None:
        return _not_evaluable("no_usable_lane_polyline")
    projection = choice["projection"]
    if float(getattr(projection, "distance_m")) > LANE_MATCH_THRESHOLD_M:
        return _not_evaluable("target_too_far_from_lane")

    feature = _required_mapping(choice, "feature")
    direction = _lane_direction(anchor, projection)  # type: ignore[arg-type]
    route_candidates = _enumerate_branch_routes(
        feature=feature,
        projection=projection,
        direction=direction,
        scenario=scenario,
        max_hops=max_hops,
    )
    if not route_candidates:
        return _not_evaluable("no_route_candidates")

    nominal = _required_mapping(replay_case, "nominal")
    default_chain = tuple(str(item) for item in nominal.get("feature_chain", []))
    features_by_id = _lane_features_by_id(scenario)
    evaluated = [
        _route_result(
            route=route,
            anchor=anchor,
            history_states=history_states,
            future_states=future_states,
            anchor_speed=anchor_speed,
            default_chain=default_chain,
            features_by_id=features_by_id,
        )
        for route in route_candidates
    ]
    default = _select_default_route(evaluated, default_chain)
    anchor_heading = max(
        evaluated,
        key=lambda row: (
            float(row["anchor_heading_score"]),
            -float(row["fde_m"]),
            _chain_text(row["feature_chain"]),
        ),
    )
    motion_context = max(
        evaluated,
        key=lambda row: (
            float(row["motion_context_score"]),
            float(row["anchor_heading_score"]),
            -float(row["fde_m"]),
            _chain_text(row["feature_chain"]),
        ),
    )
    oracle = min(
        evaluated,
        key=lambda row: (float(row["fde_m"]), _chain_text(row["feature_chain"])),
    )
    for row in evaluated:
        row["is_default"] = row is default
        row["is_anchor_heading_selected"] = row is anchor_heading
        row["is_motion_context_selected"] = row is motion_context
        row["is_oracle_selected"] = row is oracle
        row["gain_vs_default_m"] = round(
            float(default["fde_m"]) - float(row["fde_m"]),
            3,
        )
        row["history_speed_prior_gain_vs_default_m"] = round(
            float(default["fde_m"]) - float(row["history_speed_prior_fde_m"]),
            3,
        )

    branchable = len(evaluated) > 1
    oracle_gain = round(float(default["fde_m"]) - float(oracle["fde_m"]), 3)
    anchor_gain = round(float(default["fde_m"]) - float(anchor_heading["fde_m"]), 3)
    motion_context_gain = round(
        float(default["fde_m"]) - float(motion_context["fde_m"]),
        3,
    )
    verdict = _case_verdict(
        branchable=branchable,
        oracle_gain=oracle_gain,
        anchor_gain=anchor_gain,
        motion_context_gain=motion_context_gain,
        anchor_changed=anchor_heading is not default,
        motion_context_changed=motion_context is not default,
        oracle_changed=oracle is not default,
    )
    nearest_fde = _optional_float(nominal.get("nearest_lane_fde_m"))
    default_fde = _optional_float(nominal.get("lane_link_fde_m"))
    if default_fde is None:
        default_fde = float(default["fde_m"])

    return {
        "ready": True,
        "selected_feature_id": _feature_id(feature),
        "anchor_speed_mps": round(anchor_speed, 3),
        "anchor_lane_distance_m": round(float(getattr(projection, "distance_m")), 3),
        "horizon_s": round(future_states[-1].t - anchor.t, 3),
        "horizon_travel_m": round(anchor_speed * (future_states[-1].t - anchor.t), 3),
        "nearest_lane_fde_m": nearest_fde,
        "replay_default_lane_link_fde_m": default_fde,
        "route_candidate_count": len(evaluated),
        "branchable": branchable,
        "default_chain": list(default["feature_chain"]),
        "anchor_heading_chain": list(anchor_heading["feature_chain"]),
        "motion_context_chain": list(motion_context["feature_chain"]),
        "oracle_chain": list(oracle["feature_chain"]),
        "default_fde_m": float(default["fde_m"]),
        "anchor_heading_fde_m": float(anchor_heading["fde_m"]),
        "motion_context_fde_m": float(motion_context["fde_m"]),
        "oracle_fde_m": float(oracle["fde_m"]),
        "oracle_recoverable_fde_m": oracle_gain,
        "anchor_heading_recoverable_fde_m": anchor_gain,
        "motion_context_recoverable_fde_m": motion_context_gain,
        "motion_context_estimated_travel_m": motion_context.get(
            "motion_context_estimated_travel_m"
        ),
        "anchor_heading_changed_route": anchor_heading is not default,
        "motion_context_changed_route": motion_context is not default,
        "oracle_changed_route": oracle is not default,
        "default_is_oracle_best": oracle is default,
        "motion_context_is_oracle_best": oracle is motion_context,
        "verdict": verdict,
        "why_it_matters": _why_it_matters(verdict),
        "next_actions": _next_actions(verdict),
        "route_candidates": sorted(
            evaluated,
            key=lambda row: (
                not bool(row["is_default"]),
                -float(row["gain_vs_default_m"]),
                _chain_text(row["feature_chain"]),
            ),
        ),
    }


def _enumerate_branch_routes(
    feature: dict[str, object],
    projection: object,
    direction: float,
    scenario: Scenario,
    max_hops: int,
) -> list[_BranchRoute]:
    base_lane = _feature_points(feature)
    if direction >= 0.0:
        route_points = list(base_lane)
        start_s = float(getattr(projection, "arc_length_m"))
        base_remaining = _lane_length(base_lane) - start_s
        link_field = "exit_lanes"
        reverse = False
    else:
        route_points = list(reversed(base_lane))
        start_s = _lane_length(base_lane) - float(getattr(projection, "arc_length_m"))
        base_remaining = start_s
        link_field = "entry_lanes"
        reverse = True

    features_by_id = _lane_features_by_id(scenario)
    start_id = _feature_id(feature)
    routes: list[_BranchRoute] = []

    def walk(
        current: dict[str, object],
        points: list[tuple[float, float]],
        feature_ids: list[str],
        visited: set[str],
        depth: int,
        status: str,
    ) -> None:
        if depth >= max_hops:
            routes.append(
                _route_from_points(
                    points=points,
                    feature_ids=feature_ids,
                    link_count=depth,
                    status=status,
                    start_s=start_s,
                    base_remaining=base_remaining,
                )
            )
            return

        next_ids = _link_ids(current.get(link_field))
        if not next_ids:
            routes.append(
                _route_from_points(
                    points=points,
                    feature_ids=feature_ids,
                    link_count=depth,
                    status=f"no_{link_field}",
                    start_s=start_s,
                    base_remaining=base_remaining,
                )
            )
            return

        progressed = False
        for next_id in next_ids:
            if next_id in visited:
                continue
            next_feature = features_by_id.get(next_id)
            if next_feature is None:
                continue
            next_points = _feature_points(next_feature)
            if reverse:
                next_points = tuple(reversed(next_points))
            if len(next_points) < 2:
                continue
            progressed = True
            walk(
                current=next_feature,
                points=_append_lane_points(points, next_points),
                feature_ids=[*feature_ids, next_id],
                visited={*visited, next_id},
                depth=depth + 1,
                status="linked_lane_chain",
            )

        if not progressed:
            routes.append(
                _route_from_points(
                    points=points,
                    feature_ids=feature_ids,
                    link_count=depth,
                    status="linked_feature_missing",
                    start_s=start_s,
                    base_remaining=base_remaining,
                )
            )

    walk(
        current=feature,
        points=route_points,
        feature_ids=[start_id],
        visited={start_id},
        depth=0,
        status="no_lane_links",
    )
    return sorted(
        routes,
        key=lambda route: (
            -route.link_count,
            _chain_text(route.feature_ids),
        ),
    )


def _route_from_points(
    points: list[tuple[float, float]],
    feature_ids: list[str],
    link_count: int,
    status: str,
    start_s: float,
    base_remaining: float,
) -> _BranchRoute:
    route_points = tuple(points)
    route_remaining = max(_lane_length(route_points) - start_s, 0.0)
    return _BranchRoute(
        feature_ids=tuple(feature_ids),
        points=route_points,
        link_count=link_count,
        status=status,
        start_s=start_s,
        base_remaining_m=max(base_remaining, 0.0),
        route_remaining_m=route_remaining,
    )


def _route_result(
    route: _BranchRoute,
    anchor: State,
    history_states: tuple[State, ...],
    future_states: tuple[State, ...],
    anchor_speed: float,
    default_chain: tuple[str, ...],
    features_by_id: dict[str, dict[str, object]],
) -> dict[str, object]:
    errors = _route_errors(
        route=route,
        anchor=anchor,
        future_states=future_states,
        speed_mps=anchor_speed,
    )
    fde = errors[-1] if errors else 0.0
    horizon_travel = anchor_speed * (future_states[-1].t - anchor.t)
    history_speed_prior = _history_blended_speed_prior_mps(
        anchor_speed=anchor_speed,
        history_states=history_states,
    )
    history_prior_errors = _route_errors(
        route=route,
        anchor=anchor,
        future_states=future_states,
        speed_mps=history_speed_prior,
    )
    history_prior_fde = history_prior_errors[-1] if history_prior_errors else 0.0
    history_prior_horizon_travel = history_speed_prior * (
        future_states[-1].t - anchor.t
    )
    heading_score = _anchor_heading_score(
        anchor=anchor,
        route=route,
        horizon_travel_m=horizon_travel,
    )
    motion_context = _motion_context_score(
        anchor=anchor,
        history_states=history_states,
        route=route,
        horizon_s=future_states[-1].t - anchor.t,
        horizon_travel_m=horizon_travel,
        features_by_id=features_by_id,
    )
    return {
        "feature_chain": list(route.feature_ids),
        "status": route.status,
        "link_count": route.link_count,
        "ade_m": round(sum(errors) / len(errors), 3) if errors else None,
        "fde_m": round(fde, 3),
        "miss": fde > DEFAULT_MISS_THRESHOLD_M,
        "history_speed_prior_mps": round(history_speed_prior, 3),
        "history_speed_prior_ade_m": (
            round(sum(history_prior_errors) / len(history_prior_errors), 3)
            if history_prior_errors
            else None
        ),
        "history_speed_prior_fde_m": round(history_prior_fde, 3),
        "history_speed_prior_miss": history_prior_fde > DEFAULT_MISS_THRESHOLD_M,
        "history_speed_prior_horizon_travel_m": round(
            history_prior_horizon_travel,
            3,
        ),
        "anchor_heading_score": round(heading_score, 6),
        "motion_context_score": round(float(motion_context["score"]), 6),
        "motion_context_estimated_travel_m": round(
            float(motion_context["estimated_travel_m"]),
            3,
        ),
        "motion_context_route_fit": round(float(motion_context["route_fit"]), 6),
        "motion_context_speed_limit_drop": round(
            float(motion_context["speed_limit_drop"]),
            6,
        ),
        "motion_context_endpoint_alignment": round(
            float(motion_context["endpoint_alignment"]),
            6,
        ),
        "route_remaining_m": round(route.route_remaining_m, 3),
        "base_remaining_m": round(route.base_remaining_m, 3),
        "horizon_travel_m": round(horizon_travel, 3),
        "lane_end_clamp_risk_after": horizon_travel >= route.route_remaining_m,
        "is_default_chain_match": tuple(route.feature_ids) == default_chain,
    }


def _route_errors(
    route: _BranchRoute,
    anchor: State,
    future_states: tuple[State, ...],
    speed_mps: float,
) -> tuple[float, ...]:
    predictions = tuple(
        _advance_along_lane(
            route.points,
            start_s=route.start_s,
            travel_m=speed_mps * (actual.t - anchor.t),
            target_time_s=actual.t,
            speed_mps=speed_mps,
        )
        for actual in future_states
    )
    return tuple(
        _state_error(predicted, actual)
        for predicted, actual in zip(predictions, future_states)
    )


def _anchor_heading_score(
    anchor: State,
    route: _BranchRoute,
    horizon_travel_m: float,
) -> float:
    if not route.points:
        return -999.0
    alignment = _endpoint_alignment(anchor, route)
    clamp_penalty = max(horizon_travel_m - route.route_remaining_m, 0.0) / max(
        horizon_travel_m,
        1.0,
    )
    link_bonus = min(route.link_count, 2) * 0.01
    return alignment - clamp_penalty + link_bonus


def _motion_context_score(
    anchor: State,
    history_states: tuple[State, ...],
    route: _BranchRoute,
    horizon_s: float,
    horizon_travel_m: float,
    features_by_id: dict[str, dict[str, object]],
) -> dict[str, float]:
    estimated_speed = min(
        hypot(anchor.vx, anchor.vy),
        _recent_speed_mps(history_states),
    )
    estimated_travel = max(estimated_speed * max(horizon_s, 0.0), 0.0)
    endpoint_alignment = _endpoint_alignment(anchor, route)
    route_fit = -abs(route.route_remaining_m - estimated_travel) / max(
        horizon_travel_m,
        1.0,
    )
    speed_limit_drop = _route_speed_limit_drop(route, features_by_id)
    link_bonus = min(route.link_count, 2) * 0.01
    return {
        "score": (0.40 * endpoint_alignment)
        + (0.85 * route_fit)
        + (1.00 * speed_limit_drop)
        + link_bonus,
        "estimated_travel_m": estimated_travel,
        "route_fit": route_fit,
        "speed_limit_drop": speed_limit_drop,
        "endpoint_alignment": endpoint_alignment,
    }


def _endpoint_alignment(anchor: State, route: _BranchRoute) -> float:
    if not route.points:
        return 0.0
    velocity_norm = hypot(anchor.vx, anchor.vy)
    endpoint_dx = route.points[-1][0] - anchor.x
    endpoint_dy = route.points[-1][1] - anchor.y
    endpoint_norm = hypot(endpoint_dx, endpoint_dy)
    if velocity_norm <= 0.0 or endpoint_norm <= 0.0:
        return 0.0
    return ((anchor.vx / velocity_norm) * (endpoint_dx / endpoint_norm)) + (
        (anchor.vy / velocity_norm) * (endpoint_dy / endpoint_norm)
    )


def _recent_speed_mps(history_states: tuple[State, ...]) -> float:
    if not history_states:
        return 0.0
    recent = history_states[-5:]
    speeds = [hypot(state.vx, state.vy) for state in recent]
    valid = [speed for speed in speeds if isfinite(speed)]
    if not valid:
        return 0.0
    return sum(valid) / len(valid)


def _history_blended_speed_prior_mps(
    anchor_speed: float,
    history_states: tuple[State, ...],
) -> float:
    recent_speed = _recent_speed_mps(history_states)
    if not isfinite(recent_speed) or recent_speed < MIN_LANE_AWARE_SPEED_MPS:
        return anchor_speed
    blended = (0.35 * anchor_speed) + (0.65 * recent_speed)
    return max(blended, MIN_LANE_AWARE_SPEED_MPS)


def _route_speed_limit_drop(
    route: _BranchRoute,
    features_by_id: dict[str, dict[str, object]],
) -> float:
    if len(route.feature_ids) < 2:
        return 0.0
    base = _feature_speed_limit_mph(features_by_id.get(route.feature_ids[0], {}))
    downstream = [
        value
        for feature_id in route.feature_ids[1:]
        if (
            value := _feature_speed_limit_mph(features_by_id.get(feature_id, {}))
        )
        is not None
    ]
    if base is None or not downstream or base <= 0.0:
        return 0.0
    return max(base - min(downstream), 0.0) / base


def _feature_speed_limit_mph(feature: dict[str, object]) -> float | None:
    value = feature.get("speed_limit_mph")
    number = _optional_float(value)
    return number if number is not None and number > 0.0 else None


def _select_default_route(
    routes: list[dict[str, object]],
    default_chain: tuple[str, ...],
) -> dict[str, object]:
    for route in routes:
        if tuple(str(item) for item in route["feature_chain"]) == default_chain:
            return route
    return max(
        routes,
        key=lambda row: (
            float(row["anchor_heading_score"]),
            -float(row["fde_m"]),
            _chain_text(row["feature_chain"]),
        ),
    )


def _case_verdict(
    branchable: bool,
    oracle_gain: float,
    anchor_gain: float,
    motion_context_gain: float,
    anchor_changed: bool,
    motion_context_changed: bool,
    oracle_changed: bool,
) -> str:
    if not branchable:
        return "single_chain_no_branch_choice"
    if anchor_changed and anchor_gain > 1.0:
        return "anchor_heading_selector_improves"
    if motion_context_changed and motion_context_gain > 1.0:
        return "motion_context_selector_improves"
    if oracle_changed and oracle_gain > 1.0:
        return "oracle_branch_upper_bound_improves"
    if oracle_gain > 1.0:
        return "default_chain_mismatch_or_upper_bound_improves"
    return "branch_sweep_no_better_route"


def _why_it_matters(verdict: str) -> str:
    if verdict == "anchor_heading_selector_improves":
        return "A simple anchor-heading route prior changes the parsed branch and reduces open-loop error on this diagnostic case."
    if verdict == "motion_context_selector_improves":
        return "A non-oracle motion-context prior changes the parsed branch and reduces open-loop error using recent speed, route length, and downstream speed limits."
    if verdict == "oracle_branch_upper_bound_improves":
        return "Another parsed branch fits the observed future better, proving branch choice is a plausible source of the continuation regression."
    if verdict == "single_chain_no_branch_choice":
        return "The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help."
    if verdict == "branch_sweep_no_better_route":
        return "The current linked route is already the best parsed branch under open-loop replay, so the regression is likely speed, horizon, or topology quality rather than first-hop branch choice."
    return "The branch sweep found recoverable error, but the default chain could not be matched exactly against enumerated route candidates."


def _next_actions(verdict: str) -> list[str]:
    if verdict == "anchor_heading_selector_improves":
        return [
            "Promote the anchor-heading route prior into the next replay pass.",
            "Keep the default geometric route side by side as the control.",
            "Verify the selector across the broader continuation candidate queue.",
        ]
    if verdict == "motion_context_selector_improves":
        return [
            "Replay the motion-context selected branch under deterministic anchor perturbations.",
            "Compare the selector across the broader continuation candidate queue.",
            "Keep the oracle upper bound as a diagnostic ceiling, not a deployable result.",
        ]
    if verdict == "oracle_branch_upper_bound_improves":
        return [
            "Add a richer non-oracle route prior using turn-lane semantics, traffic controls, or near-term intent cues.",
            "Use the oracle branch only as an upper-bound diagnostic, not as a deployed predictor.",
            "Rerun perturbation checks after adding the non-oracle prior.",
        ]
    if verdict == "single_chain_no_branch_choice":
        return [
            "Audit lane topology depth, missing links, and selected-lane quality.",
            "Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.",
            "Keep this case separate from branch-selector performance claims.",
        ]
    return [
        "Inspect speed priors, route horizon, and map topology quality before changing branch logic.",
        "Keep the branch sweep as evidence that not every linked-lane regression is a first-hop branch issue.",
    ]


def _not_evaluable(reason: str) -> dict[str, object]:
    return {
        "ready": False,
        "route_candidate_count": 0,
        "route_candidates": [],
        "branchable": False,
        "default_chain": [],
        "anchor_heading_chain": [],
        "motion_context_chain": [],
        "oracle_chain": [],
        "default_fde_m": None,
        "anchor_heading_fde_m": None,
        "motion_context_fde_m": None,
        "oracle_fde_m": None,
        "motion_context_recoverable_fde_m": None,
        "oracle_recoverable_fde_m": None,
        "motion_context_estimated_travel_m": None,
        "verdict": reason,
        "why_it_matters": "The case cannot support branch selection until the blocker is resolved.",
        "next_actions": [
            "Resolve the evaluator blocker, then rerun branch-selection diagnostics.",
        ],
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    oracle_gains = [
        gain
        for case in ready
        if (gain := _optional_float(case.get("oracle_recoverable_fde_m"))) is not None
    ]
    motion_context_gains = [
        gain
        for case in ready
        if (gain := _optional_float(case.get("motion_context_recoverable_fde_m")))
        is not None
    ]
    positive_oracle_gains = [gain for gain in oracle_gains if gain > 1.0]
    positive_motion_context_gains = [
        gain for gain in motion_context_gains if gain > 1.0
    ]
    return {
        "case_count": len(cases),
        "evaluable_case_count": len(ready),
        "branchable_case_count": sum(bool(case.get("branchable")) for case in ready),
        "single_chain_case_count": sum(
            bool(case.get("ready")) and not bool(case.get("branchable"))
            for case in cases
        ),
        "oracle_improved_case_count": len(positive_oracle_gains),
        "anchor_heading_improved_case_count": sum(
            (_optional_float(case.get("anchor_heading_recoverable_fde_m")) or 0.0)
            > 1.0
            for case in ready
        ),
        "anchor_heading_changed_case_count": sum(
            bool(case.get("anchor_heading_changed_route")) for case in ready
        ),
        "motion_context_improved_case_count": len(positive_motion_context_gains),
        "motion_context_changed_case_count": sum(
            bool(case.get("motion_context_changed_route")) for case in ready
        ),
        "motion_context_oracle_match_count": sum(
            bool(case.get("motion_context_is_oracle_best")) for case in ready
        ),
        "motion_context_oracle_match_branchable_count": sum(
            bool(case.get("branchable"))
            and bool(case.get("motion_context_is_oracle_best"))
            for case in ready
        ),
        "mean_motion_context_recoverable_fde_m": _mean(
            tuple(positive_motion_context_gains)
        ),
        "max_motion_context_recoverable_fde_m": (
            round(max(positive_motion_context_gains), 3)
            if positive_motion_context_gains
            else None
        ),
        "default_best_case_count": sum(
            bool(case.get("default_is_oracle_best")) for case in ready
        ),
        "mean_oracle_recoverable_fde_m": _mean(tuple(positive_oracle_gains)),
        "max_oracle_recoverable_fde_m": (
            round(max(positive_oracle_gains), 3) if positive_oracle_gains else None
        ),
    }


def _find_scenario(scenarios: tuple[Scenario, ...], scenario_id: str) -> Scenario | None:
    return next(
        (scenario for scenario in scenarios if scenario.scenario_id == scenario_id),
        None,
    )


def _find_track(scenario: Scenario, track_id: str) -> AgentTrack | None:
    return next((track for track in scenario.tracks if track.agent_id == track_id), None)


def _resolve_path(value: object, source: Path) -> Path:
    path = Path(str(value or ""))
    if path.is_absolute() or path.exists():
        return path
    return source.parent / path


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


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _meter_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number:.3f} m"


def _signed_meter_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _score_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number:.3f}"


def _chain_text(value: object) -> str:
    if isinstance(value, tuple):
        items = value
    elif isinstance(value, list):
        items = tuple(value)
    else:
        return "n/a"
    if not items:
        return "n/a"
    return " -> ".join(str(item) for item in items)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
