from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_selection import (
    _meter_text,
    _optional_float,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector import (
    DEFAULT_MAX_ALTERNATE_DISTANCE_M,
    DEFAULT_MIN_HEADING_ALIGNMENT,
    DEFAULT_MIN_ROUTE_EXTENSION_M,
    _aggregate_cases,
    _selector_case,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_calibration.v1"
)

DEFAULT_MAX_ALTERNATE_DISTANCE_GATES_M = (3.0, DEFAULT_MAX_ALTERNATE_DISTANCE_M)
DEFAULT_MIN_HEADING_ALIGNMENT_GATES = (
    DEFAULT_MIN_HEADING_ALIGNMENT,
    0.90,
    0.70,
)
DEFAULT_MIN_ROUTE_EXTENSION_GATES_M = (
    10.0,
    25.0,
    40.0,
    DEFAULT_MIN_ROUTE_EXTENSION_M,
    75.0,
)


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorCalibrationResult:
    """Files produced by a terminal-neighborhood selector calibration run."""

    ready: bool
    case_count: int
    policy_count: int
    current_false_hold_count: int
    recommended_false_hold_count: int
    recommended_false_promote_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_calibration(
    terminal_neighborhood_replay_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorCalibrationResult:
    """Generate a public-safe selector threshold calibration sweep."""

    source = Path(terminal_neighborhood_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_selector_calibration_payload(
        terminal_neighborhood_replay_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_terminal_neighborhood_selector_calibration_markdown(
        payload
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    recommendation = _required_mapping(payload, "recommended_policy")
    return LaneContinuationTerminalNeighborhoodSelectorCalibrationResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        policy_count=int(aggregate["policy_count"]),
        current_false_hold_count=int(aggregate["current_false_hold_count"]),
        recommended_false_hold_count=int(recommendation["false_hold_count"]),
        recommended_false_promote_count=int(recommendation["false_promote_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_calibration_payload(
    terminal_neighborhood_replay_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return calibration sweep diagnostics for terminal-neighborhood selector gates."""

    replay = json.loads(
        terminal_neighborhood_replay_manifest_path.read_text(encoding="utf-8")
    )
    if replay.get("format") != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT:
        raise ValueError(
            "Expected a terminal-neighborhood replay manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT}."
        )

    replay_cases = [
        case for case in _required_list(replay, "cases") if isinstance(case, dict)
    ]
    current_policy = {
        "max_alternate_distance_m": DEFAULT_MAX_ALTERNATE_DISTANCE_M,
        "min_heading_alignment": DEFAULT_MIN_HEADING_ALIGNMENT,
        "min_route_extension_m": DEFAULT_MIN_ROUTE_EXTENSION_M,
        "require_chain_extension": True,
    }
    policies = _policy_sweep(replay_cases)
    current_result = _current_policy_result(
        policies=policies,
        current_policy=current_policy,
        replay_cases=replay_cases,
    )
    recommendation = _recommended_policy(
        policies=policies,
        current_policy=current_policy,
        current_result=current_result,
    )
    aggregate = _aggregate(
        cases=_required_list(current_result, "cases"),
        policies=policies,
        current_result=current_result,
        recommendation=recommendation,
    )
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
        "terminal_neighborhood_replay_manifest": str(
            terminal_neighborhood_replay_manifest_path
        ),
        "terminal_neighborhood_replay_format": replay.get("format"),
        "terminal_neighborhood_audit_manifest": replay.get(
            "terminal_neighborhood_manifest"
        ),
        "topology_manifest": replay.get("topology_manifest"),
        "replay_manifest": replay.get("replay_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(replay.get("ready")) and bool(replay_cases),
        "current_policy": current_policy,
        "search_grid": {
            "max_alternate_distance_gates_m": list(
                DEFAULT_MAX_ALTERNATE_DISTANCE_GATES_M
            ),
            "min_heading_alignment_gates": list(DEFAULT_MIN_HEADING_ALIGNMENT_GATES),
            "min_route_extension_gates_m": list(DEFAULT_MIN_ROUTE_EXTENSION_GATES_M),
        },
        "source_scope": {
            "replay_case_count": _required_mapping(replay, "aggregate").get(
                "case_count"
            ),
            "replayed_case_count": _required_mapping(replay, "aggregate").get(
                "replayed_case_count"
            ),
            "accepted_case_count": _required_mapping(replay, "aggregate").get(
                "accepted_case_count"
            ),
            "held_case_count": _required_mapping(replay, "aggregate").get(
                "held_case_count"
            ),
            "perturbation_trial_count": _required_mapping(replay, "aggregate").get(
                "perturbation_trial_count"
            ),
        },
        "aggregate": aggregate,
        "current_policy_result": current_result,
        "recommended_policy": recommendation,
        "policy_candidates": policies,
        "cases": _case_impacts(
            cases=_required_list(current_result, "cases"),
            current_result=current_result,
            recommendation=recommendation,
        ),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Terminal-neighborhood selector calibration is a diagnostic "
            "threshold sweep over already-derived replay labels. It does not "
            "change the default selector, default scorer, map adapter, or any "
            "replay artifact. It is not a route planner or Waymo benchmark claim."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_calibration_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for a selector calibration sweep."""

    aggregate = _required_mapping(payload, "aggregate")
    current = _required_mapping(payload, "current_policy_result")
    recommended = _required_mapping(payload, "recommended_policy")
    current_policy = _required_mapping(payload, "current_policy")
    search = _required_mapping(payload, "search_grid")
    source_scope = _required_mapping(payload, "source_scope")
    policies = _required_list(payload, "policy_candidates")
    cases = _required_list(payload, "cases")
    current_false_holds = int(current.get("false_hold_count", 0) or 0)
    replay_held_count = int(aggregate.get("replay_gate_held_count", 0) or 0)

    recommended_false_holds = int(recommended.get("false_hold_count", 0) or 0)
    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Calibration",
        "",
        _opening_summary(
            current_false_hold_count=current_false_holds,
            recommended_false_hold_count=recommended_false_holds,
            replay_held_count=replay_held_count,
        ),
        "",
        "The calibration is intentionally narrow. It is not a route planner, "
        "not a learned policy, not a default scorer change, and not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Terminal-neighborhood replay manifest: `{payload['terminal_neighborhood_replay_manifest']}`",
        f"- Terminal-neighborhood audit manifest: `{payload['terminal_neighborhood_audit_manifest']}`",
        f"- Topology manifest: `{payload['topology_manifest']}`",
        f"- Ready for calibration: {payload['ready']}",
        f"- Replay cases: {source_scope['replay_case_count']}",
        f"- Replayed cases: {source_scope['replayed_case_count']}",
        f"- Replay-gate accepted cases: {source_scope['accepted_case_count']}",
        f"- Replay-gate held cases: {source_scope['held_case_count']}",
        f"- Perturbation trials behind replay labels: {source_scope['perturbation_trial_count']}",
        f"- Current max alternate distance: {_meter_text(current_policy['max_alternate_distance_m'])}",
        f"- Current minimum heading alignment: {_score_text(current_policy['min_heading_alignment'])}",
        f"- Current minimum route extension: {_meter_text(current_policy['min_route_extension_m'])}",
        f"- Distance gate search: {', '.join(_meter_text(value) for value in _required_list(search, 'max_alternate_distance_gates_m'))}",
        f"- Heading gate search: {', '.join(_score_text(value) for value in _required_list(search, 'min_heading_alignment_gates'))}",
        f"- Route-extension gate search: {', '.join(_meter_text(value) for value in _required_list(search, 'min_route_extension_gates_m'))}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Calibration Summary",
        "",
        "| Metric | Current | Recommended |",
        "| --- | ---: | ---: |",
        f"| Max alternate distance | {_meter_text(current['max_alternate_distance_m'])} | {_meter_text(recommended['max_alternate_distance_m'])} |",
        f"| Minimum heading alignment | {_score_text(current['min_heading_alignment'])} | {_score_text(recommended['min_heading_alignment'])} |",
        f"| Minimum route extension | {_meter_text(current['min_route_extension_m'])} | {_meter_text(recommended['min_route_extension_m'])} |",
        f"| Promoted candidates | {current['selector_promote_count']} | {recommended['selector_promote_count']} |",
        f"| Held candidates | {current['selector_hold_count']} | {recommended['selector_hold_count']} |",
        f"| Replay-gate matches | {current['selector_replay_gate_match_count']} | {recommended['selector_replay_gate_match_count']} |",
        f"| False promotions | {current['false_promote_count']} | {recommended['false_promote_count']} |",
        f"| False holds | {current['false_hold_count']} | {recommended['false_hold_count']} |",
        f"| Mean promoted replay gain | {_signed_meter_text(current['mean_promoted_replay_gain_m'])} | {_signed_meter_text(recommended['mean_promoted_replay_gain_m'])} |",
        "",
        "Recommended action:",
        "",
        f"- {recommended['recommendation']}",
        "",
        "## Policy Sweep",
        "",
        "| Max distance | Heading gate | Route gate | Promotes | Holds | Matches | False promotes | False holds | Mean promoted gain |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in policies:
        assert isinstance(policy, dict)
        lines.append(
            "| "
            f"{_meter_text(policy['max_alternate_distance_m'])} | "
            f"{_score_text(policy['min_heading_alignment'])} | "
            f"{_meter_text(policy['min_route_extension_m'])} | "
            f"{policy['selector_promote_count']} | "
            f"{policy['selector_hold_count']} | "
            f"{policy['selector_replay_gate_match_count']} | "
            f"{policy['false_promote_count']} | "
            f"{policy['false_hold_count']} | "
            f"{_signed_meter_text(policy['mean_promoted_replay_gain_m'])} |"
        )

    lines.extend(
        [
            "",
            "## Case Impact",
            "",
            "| Rank | Scenario | Track | Replay gate | Alternate distance | Heading min | Route extension | Current decision | Recommended decision | Changed | Replay gain |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |",
        ]
    )
    if not cases:
        lines.append(
            "| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
        )
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['replay_gate_label']}` | "
            f"{_meter_text(case.get('alternate_lane_distance_m'))} | "
            f"{_score_text(case.get('minimum_heading_alignment'))} | "
            f"{_meter_text(case.get('route_extension_m'))} | "
            f"`{case['current_decision']}` | "
            f"`{case['recommended_decision']}` | "
            f"{case['changed_by_recommendation']} | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            _current_policy_interpretation(current_false_holds),
            "- The recommended selector gates are calibration candidates, not an automatic default-policy change.",
            _negative_control_interpretation(replay_held_count),
            "- The next stronger validation step is to rerun this sweep after broadening terminal-neighborhood replay cases across more shards.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _opening_summary(
    current_false_hold_count: int,
    recommended_false_hold_count: int,
    replay_held_count: int,
) -> str:
    if current_false_hold_count > 0 and recommended_false_hold_count == 0:
        return (
            "This report calibrates the conservative terminal-neighborhood "
            "selector that held replay-accepted nearby-lane candidates. It "
            "sweeps small distance, heading, and route-extension gate grids, "
            "compares each policy against replay-gate labels, and recommends "
            "the least-relaxed policy that removes the current false holds on "
            "this queue without adding false promotions."
        )
    if current_false_hold_count > 0:
        return (
            "This report stress-tests the conservative terminal-neighborhood "
            "selector on a broader nearby-lane replay queue. It sweeps small "
            "distance, heading, and route-extension gate grids, then reports "
            "the best zero-false-promotion calibration candidate it found "
            "while making clear that false holds remain."
        )
    if replay_held_count > 0:
        return (
            "This report validates the terminal-neighborhood selector against "
            "an expanded nearby-lane replay queue that includes both "
            "replay-accepted and replay-held cases. It sweeps small geometry "
            "gate grids and checks whether the current gates still avoid false "
            "holds and false promotions on this queue."
        )
    return (
        "This report calibrates the terminal-neighborhood selector against the "
        "current nearby-lane replay queue. It sweeps small geometry gate grids "
        "and checks whether candidate policies avoid false holds and false "
        "promotions on the available replay labels."
    )


def _current_policy_interpretation(current_false_hold_count: int) -> str:
    if current_false_hold_count == 0:
        return (
            "- The current selector has 0 false holds on this queue; the "
            "calibration sweep is a validation check, not a default-policy "
            "change."
        )
    return (
        "- The current selector is intentionally conservative and creates "
        f"{current_false_hold_count} false {_plural('hold', current_false_hold_count)} "
        "on this queue."
    )


def _negative_control_interpretation(replay_held_count: int) -> str:
    if replay_held_count == 0:
        return (
            "- The current real queue has no replay-rejected negative controls, "
            "so zero false promotions here is evidence of agreement on this "
            "queue, not proof of broad safety."
        )
    return (
        f"- The current queue includes {replay_held_count} replay-held negative "
        f"{_plural('control', replay_held_count)}, so false-promotion counts "
        "are measured on this queue; broader safety still requires more "
        "terminal-neighborhood negatives across shards."
    )


def _policy_sweep(replay_cases: list[dict[str, object]]) -> list[dict[str, object]]:
    policies: list[dict[str, object]] = []
    for max_distance in DEFAULT_MAX_ALTERNATE_DISTANCE_GATES_M:
        for min_heading in DEFAULT_MIN_HEADING_ALIGNMENT_GATES:
            for min_route_extension in DEFAULT_MIN_ROUTE_EXTENSION_GATES_M:
                policies.append(
                    _evaluate_policy(
                        replay_cases=replay_cases,
                        max_alternate_distance_m=max_distance,
                        min_heading_alignment=min_heading,
                        min_route_extension_m=min_route_extension,
                    )
                )
    return policies


def _evaluate_policy(
    replay_cases: list[dict[str, object]],
    max_alternate_distance_m: float,
    min_heading_alignment: float,
    min_route_extension_m: float,
) -> dict[str, object]:
    cases = [
        _selector_case(
            replay_case=case,
            max_alternate_distance_m=max_alternate_distance_m,
            min_heading_alignment=min_heading_alignment,
            min_route_extension_m=min_route_extension_m,
        )
        for case in replay_cases
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "max_alternate_distance_m": round(max_alternate_distance_m, 3),
        "min_heading_alignment": round(min_heading_alignment, 3),
        "min_route_extension_m": round(min_route_extension_m, 3),
        "selector_promote_count": aggregate["selector_promote_count"],
        "selector_hold_count": aggregate["selector_hold_count"],
        "selector_replay_gate_match_count": aggregate[
            "selector_replay_gate_match_count"
        ],
        "false_promote_count": aggregate["selector_false_promote_count"],
        "false_hold_count": aggregate["selector_false_hold_count"],
        "mean_promoted_replay_gain_m": aggregate["mean_promoted_replay_gain_m"],
        "mean_held_replay_gain_m": aggregate["mean_held_replay_gain_m"],
        "mean_promoted_route_extension_m": aggregate[
            "mean_promoted_route_extension_m"
        ],
        "cases": cases,
    }


def _current_policy_result(
    policies: list[dict[str, object]],
    current_policy: dict[str, object],
    replay_cases: list[dict[str, object]],
) -> dict[str, object]:
    current_distance = _optional_float(current_policy.get("max_alternate_distance_m"))
    current_heading = _optional_float(current_policy.get("min_heading_alignment"))
    current_route = _optional_float(current_policy.get("min_route_extension_m"))
    if current_distance is None or current_heading is None or current_route is None:
        return policies[0] if policies else {}
    for policy in policies:
        if (
            _optional_float(policy.get("max_alternate_distance_m")) == current_distance
            and _optional_float(policy.get("min_heading_alignment")) == current_heading
            and _optional_float(policy.get("min_route_extension_m")) == current_route
        ):
            return policy
    return _evaluate_policy(
        replay_cases=replay_cases,
        max_alternate_distance_m=current_distance,
        min_heading_alignment=current_heading,
        min_route_extension_m=current_route,
    )


def _recommended_policy(
    policies: list[dict[str, object]],
    current_policy: dict[str, object],
    current_result: dict[str, object],
) -> dict[str, object]:
    current_false_hold = int(current_result.get("false_hold_count", 0) or 0)
    current_false_promote = int(current_result.get("false_promote_count", 0) or 0)
    if current_false_hold == 0 and current_false_promote == 0:
        recommended = dict(current_result)
        recommended["recommendation"] = (
            "Keep the current selector gates as the provisional calibration "
            "target for this queue; use the sweep as validation evidence."
        )
        return recommended

    exact_candidates = [
        policy
        for policy in policies
        if int(policy.get("false_hold_count", 0) or 0) == 0
        and int(policy.get("false_promote_count", 0) or 0) == 0
    ]
    if exact_candidates:
        recommended = dict(
            sorted(
                exact_candidates,
                key=lambda policy: _policy_distance(policy, current_policy),
            )[0]
        )
        recommended["recommendation"] = (
            "Use this as a provisional calibration target for the next "
            "expanded terminal-neighborhood queue; do not change the default "
            "selector until negative coverage improves."
        )
        return recommended

    zero_false_promote = [
        policy
        for policy in policies
        if int(policy.get("false_promote_count", 0) or 0) == 0
    ]
    candidates = zero_false_promote if zero_false_promote else policies
    recommended = dict(
        sorted(
            candidates,
            key=lambda policy: (
                int(policy.get("false_promote_count", 0) or 0),
                int(policy.get("false_hold_count", 0) or 0),
                -int(policy.get("selector_replay_gate_match_count", 0) or 0),
                _policy_distance(policy, current_policy),
            ),
        )[0]
        if candidates
        else {}
    )
    recommended["recommendation"] = (
        "Use this only as a diagnostic calibration candidate for the next "
        "expanded queue; do not change the default selector because no grid "
        "candidate cleared both false holds and false promotions."
    )
    return recommended


def _policy_distance(
    policy: dict[str, object],
    current_policy: dict[str, object],
) -> tuple[float, float, float, float, float, float]:
    policy_distance = _optional_float(policy.get("max_alternate_distance_m")) or 0.0
    policy_heading = _optional_float(policy.get("min_heading_alignment")) or 0.0
    policy_route = _optional_float(policy.get("min_route_extension_m")) or 0.0
    current_distance = (
        _optional_float(current_policy.get("max_alternate_distance_m")) or 0.0
    )
    current_heading = _optional_float(current_policy.get("min_heading_alignment")) or 0.0
    current_route = _optional_float(current_policy.get("min_route_extension_m")) or 0.0
    return (
        abs(policy_distance - current_distance),
        abs(policy_heading - current_heading),
        abs(policy_route - current_route),
        -policy_route,
        -policy_heading,
        policy_distance,
    )


def _aggregate(
    cases: list[object],
    policies: list[dict[str, object]],
    current_result: dict[str, object],
    recommendation: dict[str, object],
) -> dict[str, object]:
    ready = [case for case in cases if isinstance(case, dict) and bool(case.get("ready"))]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "policy_count": len(policies),
        "replay_gate_accepted_count": sum(
            bool(case.get("replay_gate_accepted")) for case in ready
        ),
        "replay_gate_held_count": sum(
            not bool(case.get("replay_gate_accepted")) for case in ready
        ),
        "current_false_hold_count": int(current_result.get("false_hold_count", 0) or 0),
        "current_false_promote_count": int(
            current_result.get("false_promote_count", 0) or 0
        ),
        "recommended_false_hold_count": int(
            recommendation.get("false_hold_count", 0) or 0
        ),
        "recommended_false_promote_count": int(
            recommendation.get("false_promote_count", 0) or 0
        ),
    }


def _case_impacts(
    cases: list[object],
    current_result: dict[str, object],
    recommendation: dict[str, object],
) -> list[dict[str, object]]:
    current_decisions = _decision_index(current_result)
    recommended_decisions = _decision_index(recommendation)
    impacts = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        key = (str(case.get("scenario_id")), str(case.get("track_id")))
        current = current_decisions.get(key, {})
        recommended = recommended_decisions.get(key, {})
        current_decision = str(current.get("selector_label", "not_evaluable"))
        recommended_decision = str(recommended.get("selector_label", "not_evaluable"))
        impacts.append(
            {
                **case,
                "current_decision": current_decision,
                "recommended_decision": recommended_decision,
                "current_match_label": current.get("selector_gate_match_label"),
                "recommended_match_label": recommended.get("selector_gate_match_label"),
                "changed_by_recommendation": current_decision != recommended_decision,
            }
        )
    return impacts


def _decision_index(policy: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    index = {}
    for decision in _required_list(policy, "cases"):
        if isinstance(decision, dict):
            index[
                (str(decision.get("scenario_id")), str(decision.get("track_id")))
            ] = decision
    return index


def _plural(word: str, count: int) -> str:
    return word if count == 1 else f"{word}s"


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"
