from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_selection import (
    _optional_float,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_route_context_guard import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
)

LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_CALIBRATION_FORMAT = (
    "scenariolens.lane_continuation_route_context_guard_calibration.v1"
)

DEFAULT_ROUTE_FIT_DELTA_GATES = (0.0,)
DEFAULT_ENDPOINT_ALIGNMENT_DELTA_GATES = (
    0.0,
    -0.05,
    -0.10,
    -0.15,
    -0.20,
    -0.25,
    -0.30,
)
DEFAULT_SPEED_LIMIT_DROP_DELTA_GATES = (0.10,)

_ACCEPTED_LABEL = "accepted_for_selector_rollout"


@dataclass(frozen=True)
class LaneContinuationRouteContextGuardCalibrationResult:
    """Files produced by a route-context guard calibration run."""

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


def generate_lane_continuation_route_context_guard_calibration(
    route_context_guard_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationRouteContextGuardCalibrationResult:
    """Generate a public-safe calibration sweep for route-context guard gates."""

    source = Path(route_context_guard_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_route_context_guard_calibration_payload(
        route_context_guard_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_route_context_guard_calibration_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    recommendation = _required_mapping(payload, "recommended_policy")
    return LaneContinuationRouteContextGuardCalibrationResult(
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


def lane_continuation_route_context_guard_calibration_payload(
    route_context_guard_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return calibration sweep diagnostics for a route-context guard manifest."""

    guard = json.loads(route_context_guard_manifest_path.read_text(encoding="utf-8"))
    if guard.get("format") != LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT:
        raise ValueError(
            "Expected a route-context guard manifest with format "
            f"{LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT}."
        )

    current_policy = _required_mapping(guard, "guard_policy")
    cases = [
        _calibration_case(case)
        for case in _required_list(guard, "cases")
        if isinstance(case, dict)
    ]
    policies = _policy_sweep(cases)
    current_result = _current_policy_result(
        policies=policies,
        current_policy=current_policy,
        cases=cases,
    )
    recommendation = _recommended_policy(
        policies=policies,
        current_policy=current_policy,
    )
    aggregate = _aggregate(
        cases=cases,
        policies=policies,
        current_result=current_result,
        recommendation=recommendation,
    )
    return {
        "format": LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_CALIBRATION_FORMAT,
        "route_context_guard_manifest": str(route_context_guard_manifest_path),
        "route_context_guard_format": guard.get("format"),
        "branch_selection_manifest": guard.get("branch_selection_manifest"),
        "branch_replay_manifest": guard.get("branch_replay_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(guard.get("ready")) and bool(cases),
        "current_policy": {
            "route_fit_delta_gate": _rounded(
                current_policy.get("route_fit_delta_gate")
            ),
            "endpoint_alignment_delta_gate": _rounded(
                current_policy.get("endpoint_alignment_delta_gate")
            ),
            "speed_limit_drop_delta_gate": _rounded(
                current_policy.get("speed_limit_drop_delta_gate")
            ),
        },
        "search_grid": {
            "route_fit_delta_gates": list(DEFAULT_ROUTE_FIT_DELTA_GATES),
            "endpoint_alignment_delta_gates": list(
                DEFAULT_ENDPOINT_ALIGNMENT_DELTA_GATES
            ),
            "speed_limit_drop_delta_gates": list(
                DEFAULT_SPEED_LIMIT_DROP_DELTA_GATES
            ),
        },
        "aggregate": aggregate,
        "current_policy_result": current_result,
        "recommended_policy": recommendation,
        "policy_candidates": policies,
        "cases": _case_impacts(cases, current_result, recommendation),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Route-context guard calibration is a diagnostic threshold sweep "
            "over already-derived guard summaries. It does not change the "
            "default guard, default scorer, branch selector, or any replay "
            "artifact. It is not a route planner or Waymo benchmark claim."
        ),
    }


def lane_continuation_route_context_guard_calibration_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for a route-context guard calibration sweep."""

    aggregate = _required_mapping(payload, "aggregate")
    current = _required_mapping(payload, "current_policy_result")
    recommended = _required_mapping(payload, "recommended_policy")
    current_policy = _required_mapping(payload, "current_policy")
    search = _required_mapping(payload, "search_grid")
    policies = _required_list(payload, "policy_candidates")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Route-Context Guard Calibration",
        "",
        "This report calibrates the conservative route-context guard that held "
        "one branch replay candidate despite replay acceptance. It sweeps a "
        "small endpoint-alignment gate grid, compares each policy against "
        "branch-replay labels, and recommends the least-relaxed policy that "
        "removes the current false hold on this queue.",
        "",
        "The calibration is intentionally narrow. It is not a route planner, "
        "not a learned policy, not a default scorer change, and not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Route-context guard manifest: `{payload['route_context_guard_manifest']}`",
        f"- Branch-selection manifest: `{payload['branch_selection_manifest']}`",
        f"- Branch-replay manifest: `{payload['branch_replay_manifest']}`",
        f"- Ready for calibration: {payload['ready']}",
        f"- Cases analyzed: {aggregate['case_count']}",
        f"- Replay accepted cases: {aggregate['replay_accepted_count']}",
        f"- Replay held cases: {aggregate['replay_held_count']}",
        f"- Current route-fit gate: {_signed_score_text(current_policy['route_fit_delta_gate'])}",
        f"- Current endpoint-alignment gate: {_signed_score_text(current_policy['endpoint_alignment_delta_gate'])}",
        f"- Current speed-limit-drop gate: {_signed_score_text(current_policy['speed_limit_drop_delta_gate'])}",
        f"- Endpoint gate search: {', '.join(_signed_score_text(value) for value in _required_list(search, 'endpoint_alignment_delta_gates'))}",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Calibration Summary",
        "",
        "| Metric | Current | Recommended |",
        "| --- | ---: | ---: |",
        f"| Endpoint-alignment gate | {_signed_score_text(current['endpoint_alignment_delta_gate'])} | {_signed_score_text(recommended['endpoint_alignment_delta_gate'])} |",
        f"| Promoted candidates | {current['promote_count']} | {recommended['promote_count']} |",
        f"| Held candidates | {current['hold_count']} | {recommended['hold_count']} |",
        f"| Replay-gate matches | {current['match_count']} | {recommended['match_count']} |",
        f"| False promotions | {current['false_promote_count']} | {recommended['false_promote_count']} |",
        f"| False holds | {current['false_hold_count']} | {recommended['false_hold_count']} |",
        f"| Mean promoted gain | {_signed_meter_text(current['mean_promoted_gain_m'])} | {_signed_meter_text(recommended['mean_promoted_gain_m'])} |",
        "",
        "Recommended action:",
        "",
        f"- {recommended['recommendation']}",
        "",
        "## Policy Sweep",
        "",
        "| Endpoint gate | Promotes | Holds | Matches | False promotes | False holds | Mean promoted gain |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in policies:
        assert isinstance(policy, dict)
        lines.append(
            "| "
            f"{_signed_score_text(policy['endpoint_alignment_delta_gate'])} | "
            f"{policy['promote_count']} | "
            f"{policy['hold_count']} | "
            f"{policy['match_count']} | "
            f"{policy['false_promote_count']} | "
            f"{policy['false_hold_count']} | "
            f"{_signed_meter_text(policy['mean_promoted_gain_m'])} |"
        )

    lines.extend(
        [
            "",
            "## Case Impact",
            "",
            "| Rank | Scenario | Track | Replay label | Endpoint delta | Current decision | Recommended decision | Changed | Motion gain |",
            "| ---: | --- | --- | --- | ---: | --- | --- | --- | ---: |",
        ]
    )
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['replay_acceptance_label']}` | "
            f"{_signed_score_text(case.get('endpoint_alignment_delta'))} | "
            f"`{case['current_decision']}` | "
            f"`{case['recommended_decision']}` | "
            f"{case['changed_by_recommendation']} | "
            f"{_signed_meter_text(case.get('motion_context_gain_m'))} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The current guard is intentionally conservative and creates one false hold on this branch queue.",
            "- The recommended endpoint gate is a calibration candidate, not an automatic default change.",
            "- The current real queue has no replay-rejected negative controls, so zero false promotions here is evidence of agreement on this queue, not proof of broad safety.",
            "- The next stronger validation step is to rerun this calibration after expanding the branchable queue across more shards.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _calibration_case(case: dict[str, object]) -> dict[str, object]:
    return {
        "rank": int(case.get("rank", 0) or 0),
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "source_name": str(case.get("source_name", "")),
        "ready": bool(case.get("ready")),
        "replay_acceptance_label": str(case.get("replay_acceptance_label", "")),
        "replay_accepted": str(case.get("replay_acceptance_label")) == _ACCEPTED_LABEL,
        "route_fit_delta": _rounded(case.get("route_fit_delta")),
        "endpoint_alignment_delta": _rounded(case.get("endpoint_alignment_delta")),
        "speed_limit_drop_delta": _rounded(case.get("speed_limit_drop_delta")),
        "motion_context_gain_m": _rounded(case.get("motion_context_gain_m")),
        "current_guard_label": str(case.get("guard_label", "")),
    }


def _policy_sweep(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    policies: list[dict[str, object]] = []
    for route_fit_gate in DEFAULT_ROUTE_FIT_DELTA_GATES:
        for speed_gate in DEFAULT_SPEED_LIMIT_DROP_DELTA_GATES:
            for endpoint_gate in DEFAULT_ENDPOINT_ALIGNMENT_DELTA_GATES:
                policies.append(
                    _evaluate_policy(
                        cases=cases,
                        route_fit_delta_gate=route_fit_gate,
                        endpoint_alignment_delta_gate=endpoint_gate,
                        speed_limit_drop_delta_gate=speed_gate,
                    )
                )
    return policies


def _evaluate_policy(
    cases: list[dict[str, object]],
    route_fit_delta_gate: float,
    endpoint_alignment_delta_gate: float,
    speed_limit_drop_delta_gate: float,
) -> dict[str, object]:
    decisions = [
        _case_decision(
            case=case,
            route_fit_delta_gate=route_fit_delta_gate,
            endpoint_alignment_delta_gate=endpoint_alignment_delta_gate,
            speed_limit_drop_delta_gate=speed_limit_drop_delta_gate,
        )
        for case in cases
        if bool(case.get("ready"))
    ]
    promoted = [decision for decision in decisions if bool(decision["promote"])]
    false_promotes = [
        decision
        for decision in decisions
        if bool(decision["promote"]) and not bool(decision["replay_accepted"])
    ]
    false_holds = [
        decision
        for decision in decisions
        if not bool(decision["promote"]) and bool(decision["replay_accepted"])
    ]
    return {
        "route_fit_delta_gate": round(route_fit_delta_gate, 6),
        "endpoint_alignment_delta_gate": round(endpoint_alignment_delta_gate, 6),
        "speed_limit_drop_delta_gate": round(speed_limit_drop_delta_gate, 6),
        "promote_count": len(promoted),
        "hold_count": len(decisions) - len(promoted),
        "match_count": sum(bool(decision["matches_replay"]) for decision in decisions),
        "false_promote_count": len(false_promotes),
        "false_hold_count": len(false_holds),
        "mean_promoted_gain_m": _mean(
            [
                gain
                for decision in promoted
                if (gain := _optional_float(decision.get("motion_context_gain_m")))
                is not None
            ]
        ),
        "decisions": decisions,
    }


def _case_decision(
    case: dict[str, object],
    route_fit_delta_gate: float,
    endpoint_alignment_delta_gate: float,
    speed_limit_drop_delta_gate: float,
) -> dict[str, object]:
    route_fit = _optional_float(case.get("route_fit_delta"))
    endpoint = _optional_float(case.get("endpoint_alignment_delta"))
    speed_drop = _optional_float(case.get("speed_limit_drop_delta"))
    promote = (
        route_fit is not None
        and route_fit > route_fit_delta_gate
        and endpoint is not None
        and endpoint >= endpoint_alignment_delta_gate
        and speed_drop is not None
        and speed_drop <= speed_limit_drop_delta_gate
    )
    replay_accepted = bool(case.get("replay_accepted"))
    return {
        "scenario_id": case.get("scenario_id"),
        "track_id": case.get("track_id"),
        "promote": promote,
        "decision": (
            "promote_motion_context_candidate"
            if promote
            else "hold_for_route_context_evidence"
        ),
        "replay_accepted": replay_accepted,
        "matches_replay": promote == replay_accepted,
        "motion_context_gain_m": case.get("motion_context_gain_m"),
    }


def _current_policy_result(
    policies: list[dict[str, object]],
    current_policy: dict[str, object],
    cases: list[dict[str, object]],
) -> dict[str, object]:
    route_fit_gate = _optional_float(current_policy.get("route_fit_delta_gate"))
    endpoint_gate = _optional_float(current_policy.get("endpoint_alignment_delta_gate"))
    speed_gate = _optional_float(current_policy.get("speed_limit_drop_delta_gate"))
    if route_fit_gate is None or endpoint_gate is None or speed_gate is None:
        return policies[0] if policies else {}
    for policy in policies:
        if (
            _optional_float(policy.get("route_fit_delta_gate")) == route_fit_gate
            and _optional_float(policy.get("endpoint_alignment_delta_gate"))
            == endpoint_gate
            and _optional_float(policy.get("speed_limit_drop_delta_gate")) == speed_gate
        ):
            return policy
    return _evaluate_policy(
        cases=cases,
        route_fit_delta_gate=route_fit_gate,
        endpoint_alignment_delta_gate=endpoint_gate,
        speed_limit_drop_delta_gate=speed_gate,
    )


def _recommended_policy(
    policies: list[dict[str, object]],
    current_policy: dict[str, object],
) -> dict[str, object]:
    current_endpoint = _optional_float(current_policy.get("endpoint_alignment_delta_gate"))
    candidates = [
        policy
        for policy in policies
        if int(policy.get("false_hold_count", 0) or 0) == 0
        and int(policy.get("false_promote_count", 0) or 0) == 0
    ]
    if candidates:
        candidates = sorted(
            candidates,
            key=lambda policy: (
                abs(
                    (_optional_float(policy.get("endpoint_alignment_delta_gate")) or 0.0)
                    - (current_endpoint or 0.0)
                ),
                -(_optional_float(policy.get("endpoint_alignment_delta_gate")) or 0.0),
            ),
        )
        recommended = dict(candidates[0])
        recommended["recommendation"] = (
            "Use this as a provisional calibration target for the next expanded "
            "branchable queue; do not change the default guard until negative "
            "coverage improves."
        )
        return recommended
    fallback = dict(policies[0]) if policies else {}
    fallback["recommendation"] = (
        "No candidate cleared false holds and false promotions on this queue; "
        "keep the current guard and expand evidence."
    )
    return fallback


def _aggregate(
    cases: list[dict[str, object]],
    policies: list[dict[str, object]],
    current_result: dict[str, object],
    recommendation: dict[str, object],
) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "policy_count": len(policies),
        "replay_accepted_count": sum(bool(case.get("replay_accepted")) for case in ready),
        "replay_held_count": sum(not bool(case.get("replay_accepted")) for case in ready),
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
    cases: list[dict[str, object]],
    current_result: dict[str, object],
    recommendation: dict[str, object],
) -> list[dict[str, object]]:
    current_decisions = _decision_index(current_result)
    recommended_decisions = _decision_index(recommendation)
    impacts = []
    for case in cases:
        key = (str(case.get("scenario_id")), str(case.get("track_id")))
        current = current_decisions.get(key, {})
        recommended = recommended_decisions.get(key, {})
        impacts.append(
            {
                **case,
                "current_decision": current.get("decision", "not_evaluable"),
                "recommended_decision": recommended.get("decision", "not_evaluable"),
                "changed_by_recommendation": current.get("decision")
                != recommended.get("decision"),
            }
        )
    return impacts


def _decision_index(policy: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    index = {}
    for decision in _required_list(policy, "decisions"):
        if isinstance(decision, dict):
            index[
                (str(decision.get("scenario_id")), str(decision.get("track_id")))
            ] = decision
    return index


def _rounded(value: object) -> float | None:
    number = _optional_float(value)
    return round(number, 6) if number is not None else None


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _signed_score_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f}"
