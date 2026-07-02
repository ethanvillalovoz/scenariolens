from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
    _chain_text,
    _meter_text,
    _optional_float,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)

LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT = (
    "scenariolens.lane_continuation_route_context_guard.v1"
)

_ENDPOINT_ALIGNMENT_DELTA_GATE = -0.05
_SPEED_LIMIT_DROP_DELTA_GATE = 0.10
_ROUTE_FIT_DELTA_GATE = 0.0


@dataclass(frozen=True)
class LaneContinuationRouteContextGuardResult:
    """Files produced by a route-context branch promotion guard study."""

    ready: bool
    case_count: int
    promoted_case_count: int
    held_case_count: int
    replay_gate_match_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_route_context_guard(
    branch_selection_manifest_path: str | Path,
    branch_replay_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationRouteContextGuardResult:
    """Generate a public-safe route-context promotion guard study."""

    selection_source = Path(branch_selection_manifest_path)
    replay_source = Path(branch_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_route_context_guard_payload(
        branch_selection_manifest_path=selection_source,
        branch_replay_manifest_path=replay_source,
        output_dir=target,
    )
    report = lane_continuation_route_context_guard_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationRouteContextGuardResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        promoted_case_count=int(aggregate["guard_promote_count"]),
        held_case_count=int(aggregate["guard_hold_count"]),
        replay_gate_match_count=int(aggregate["guard_replay_gate_match_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_route_context_guard_payload(
    branch_selection_manifest_path: Path,
    branch_replay_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return route-context guard decisions for motion-context branch candidates."""

    branch_selection = json.loads(
        branch_selection_manifest_path.read_text(encoding="utf-8")
    )
    if branch_selection.get("format") != LANE_CONTINUATION_BRANCH_SELECTION_FORMAT:
        raise ValueError(
            "Expected a lane-continuation branch-selection manifest with format "
            f"{LANE_CONTINUATION_BRANCH_SELECTION_FORMAT}."
        )

    branch_replay = json.loads(branch_replay_manifest_path.read_text(encoding="utf-8"))
    if branch_replay.get("format") != LANE_CONTINUATION_BRANCH_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation branch-replay manifest with format "
            f"{LANE_CONTINUATION_BRANCH_REPLAY_FORMAT}."
        )

    replay_cases = {
        (str(case.get("scenario_id")), str(case.get("track_id"))): case
        for case in _required_list(branch_replay, "cases")
        if isinstance(case, dict)
    }
    cases = [
        _guard_case(
            branch_case=case,
            replay_case=replay_cases.get(
                (str(case.get("scenario_id")), str(case.get("track_id")))
            ),
        )
        for case in _required_list(branch_selection, "cases")
        if isinstance(case, dict) and _is_motion_context_candidate(case)
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
        "branch_selection_manifest": str(branch_selection_manifest_path),
        "branch_selection_format": branch_selection.get("format"),
        "branch_replay_manifest": str(branch_replay_manifest_path),
        "branch_replay_format": branch_replay.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(branch_selection.get("ready"))
        and bool(branch_replay.get("ready"))
        and any(bool(case.get("ready")) for case in cases),
        "guard_policy": {
            "description": (
                "Promote a motion-context branch candidate only when it improves "
                "route fit without adding a large endpoint-alignment penalty or "
                "a downstream speed-limit-drop cue. Otherwise hold it for richer "
                "route context before selector rollout."
            ),
            "route_fit_delta_gate": _ROUTE_FIT_DELTA_GATE,
            "endpoint_alignment_delta_gate": _ENDPOINT_ALIGNMENT_DELTA_GATE,
            "speed_limit_drop_delta_gate": _SPEED_LIMIT_DROP_DELTA_GATE,
        },
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The route-context guard is a diagnostic promotion policy over "
            "branch-selection and branch-replay summaries. It is not a route "
            "planner, not closed-loop simulation, not a learned model, and not "
            "a Waymo benchmark claim."
        ),
    }


def lane_continuation_route_context_guard_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for a route-context guard study."""

    aggregate = _required_mapping(payload, "aggregate")
    policy = _required_mapping(payload, "guard_policy")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Route-Context Guard Study",
        "",
        "This study follows the branch rollout gate by testing a stricter "
        "non-oracle promotion guard for motion-context branch candidates. The "
        "guard asks whether a branch improvement also has enough route-context "
        "support to be promoted for broader selector evaluation.",
        "",
        "The guard does not replace ScenarioLens scoring or the existing "
        "motion-context selector. It is a laptop-safe diagnostic: route "
        "features decide the guard, while branch replay outcomes are used only "
        "to check whether the guard agrees with the current replay gate.",
        "",
        "## Scope",
        "",
        f"- Branch-selection manifest: `{payload['branch_selection_manifest']}`",
        f"- Branch-replay manifest: `{payload['branch_replay_manifest']}`",
        f"- Ready for route-context guard study: {payload['ready']}",
        f"- Route-fit delta gate: `{policy['route_fit_delta_gate']}`",
        f"- Endpoint-alignment delta gate: `{policy['endpoint_alignment_delta_gate']}`",
        f"- Speed-limit-drop delta gate: `{policy['speed_limit_drop_delta_gate']}`",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Guard Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Ready cases | {aggregate['ready_case_count']} |",
        f"| Guard promotions | {aggregate['guard_promote_count']} |",
        f"| Guard holds | {aggregate['guard_hold_count']} |",
        f"| Replay gate accepted | {aggregate['replay_gate_accepted_count']} |",
        f"| Replay route-context holds | {aggregate['replay_route_context_hold_count']} |",
        f"| Guard/replay gate matches | {aggregate['guard_replay_gate_match_count']} |",
        f"| Guard false promotions | {aggregate['guard_false_promote_count']} |",
        f"| Guard false holds | {aggregate['guard_false_hold_count']} |",
        f"| Speed-minus margin cases held | {aggregate['speed_minus_margin_held_count']} |",
        f"| Mean promoted nominal gain | {_signed_meter_text(aggregate['mean_promoted_nominal_gain_m'])} |",
        f"| Mean held nominal gain | {_signed_meter_text(aggregate['mean_held_nominal_gain_m'])} |",
        "",
        "## Guard Decisions",
        "",
        "| Rank | Scenario | Track | Guard | Replay gate | Route context | Motion gain | Endpoint delta | Speed-limit delta | Route-fit delta | First next action |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
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
            f"`{case['guard_label']}` | "
            f"`{case['replay_acceptance_label']}` | "
            f"`{case['replay_route_context_label']}` | "
            f"{_signed_meter_text(case.get('motion_context_gain_m'))} | "
            f"{_signed_score_text(case.get('endpoint_alignment_delta'))} | "
            f"{_signed_score_text(case.get('speed_limit_drop_delta'))} | "
            f"{_signed_score_text(case.get('route_fit_delta'))} | "
            f"{case['first_next_action']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        checks = _required_mapping(case, "guard_checks")
        flags = _required_list(case, "route_context_flags")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Guard label: **{case['guard_label']}**",
                f"- Guard reason: {case['guard_reason']}",
                f"- Replay acceptance: **{case['replay_acceptance_label']}**",
                f"- Replay route-context label: **{case['replay_route_context_label']}**",
                f"- Guard matched replay gate: {case['guard_matches_replay_gate']}",
                f"- Default chain: {_chain_text(case.get('default_chain'))}",
                f"- Motion-context chain: {_chain_text(case.get('motion_context_chain'))}",
                f"- Guard-selected chain: {_chain_text(case.get('guard_selected_chain'))}",
                f"- Nominal recoverable FDE: {_signed_meter_text(case.get('motion_context_gain_m'))}",
                f"- Route-context flags: {', '.join(str(flag) for flag in flags) if flags else 'none'}",
                "",
                "Guard checks:",
                "",
                "| Check | Value | Passed |",
                "| --- | ---: | --- |",
                f"| Route-fit delta | {_signed_score_text(checks.get('route_fit_delta'))} | {checks['route_fit_pass']} |",
                f"| Endpoint-alignment delta | {_signed_score_text(checks.get('endpoint_alignment_delta'))} | {checks['endpoint_alignment_pass']} |",
                f"| Speed-limit-drop delta | {_signed_score_text(checks.get('speed_limit_drop_delta'))} | {checks['speed_limit_drop_pass']} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A guard promotion means the current motion-context branch has "
            "route-fit support without obvious endpoint or downstream speed "
            "context warnings.",
            "- A guard hold is still valuable evidence: it turns a marginal "
            "nominal improvement into a concrete route-context follow-up before "
            "broader selector rollout.",
            "- The replay gate remains the stricter evidence source. This guard "
            "is a candidate policy to test on a larger branchable queue, not a "
            "route planner, production release policy, or benchmark result.",
            "- Public outputs stay summary-oriented; raw Waymo TFRecords and "
            "local replay packets remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_motion_context_candidate(case: dict[str, object]) -> bool:
    return (
        bool(case.get("ready"))
        and bool(case.get("branchable"))
        and str(case.get("verdict")) == "motion_context_selector_improves"
    )


def _guard_case(
    branch_case: dict[str, object],
    replay_case: dict[str, object] | None,
) -> dict[str, object]:
    default_route = _route_with_flag(branch_case, "is_default")
    motion_route = _route_with_flag(branch_case, "is_motion_context_selected")
    if default_route is None or motion_route is None:
        return _not_ready_case(branch_case, "missing_default_or_motion_context_route")

    deltas = _route_deltas(default_route=default_route, motion_route=motion_route)
    checks = _guard_checks(deltas)
    replay_acceptance = (
        _required_mapping(replay_case, "acceptance_decision")
        if replay_case is not None
        else {}
    )
    replay_route_context = (
        _required_mapping(replay_case, "route_context_margin_diagnostic")
        if replay_case is not None
        else {}
    )
    promote = all(
        bool(checks[key])
        for key in (
            "route_fit_pass",
            "endpoint_alignment_pass",
            "speed_limit_drop_pass",
        )
    )
    guard_label = (
        "promote_motion_context_candidate"
        if promote
        else "hold_for_route_context_evidence"
    )
    replay_accepted = (
        str(replay_acceptance.get("label")) == "accepted_for_selector_rollout"
    )
    route_context_label = str(replay_route_context.get("label", "not_replayed"))
    actions = _next_actions(
        guard_label=guard_label,
        route_context_label=route_context_label,
    )
    return {
        "rank": int(branch_case.get("rank", 0) or 0),
        "scenario_id": str(branch_case.get("scenario_id", "")),
        "track_id": str(branch_case.get("track_id", "")),
        "source_name": str(branch_case.get("source_name", "")),
        "ready": True,
        "branch_selection_verdict": str(branch_case.get("verdict", "unknown")),
        "guard_label": guard_label,
        "guard_promotes_motion_context": promote,
        "guard_reason": _guard_reason(
            promote=promote,
            flags=_route_context_flags(deltas),
        ),
        "guard_matches_replay_gate": promote == replay_accepted,
        "replay_acceptance_label": str(
            replay_acceptance.get("label", "not_replayed")
        ),
        "replay_route_context_label": route_context_label,
        "default_chain": branch_case.get("default_chain", []),
        "motion_context_chain": branch_case.get("motion_context_chain", []),
        "guard_selected_chain": (
            branch_case.get("motion_context_chain", [])
            if promote
            else branch_case.get("default_chain", [])
        ),
        "default_fde_m": _rounded(branch_case.get("default_fde_m")),
        "motion_context_fde_m": _rounded(branch_case.get("motion_context_fde_m")),
        "motion_context_gain_m": _rounded(
            branch_case.get("motion_context_recoverable_fde_m")
        ),
        "route_fit_delta": deltas["route_fit_delta"],
        "endpoint_alignment_delta": deltas["endpoint_alignment_delta"],
        "speed_limit_drop_delta": deltas["speed_limit_drop_delta"],
        "route_remaining_delta_m": deltas["route_remaining_delta_m"],
        "motion_context_score_delta": deltas["motion_context_score_delta"],
        "route_context_flags": _route_context_flags(deltas),
        "guard_checks": checks,
        "first_next_action": actions[0],
        "next_actions": actions,
    }


def _not_ready_case(
    branch_case: dict[str, object],
    reason: str,
) -> dict[str, object]:
    return {
        "rank": int(branch_case.get("rank", 0) or 0),
        "scenario_id": str(branch_case.get("scenario_id", "")),
        "track_id": str(branch_case.get("track_id", "")),
        "source_name": str(branch_case.get("source_name", "")),
        "ready": False,
        "branch_selection_verdict": str(branch_case.get("verdict", "unknown")),
        "guard_label": "not_evaluable",
        "guard_promotes_motion_context": False,
        "guard_reason": reason,
        "guard_matches_replay_gate": False,
        "replay_acceptance_label": "not_evaluable",
        "replay_route_context_label": "not_evaluable",
        "default_chain": branch_case.get("default_chain", []),
        "motion_context_chain": branch_case.get("motion_context_chain", []),
        "guard_selected_chain": branch_case.get("default_chain", []),
        "motion_context_gain_m": None,
        "route_fit_delta": None,
        "endpoint_alignment_delta": None,
        "speed_limit_drop_delta": None,
        "route_remaining_delta_m": None,
        "motion_context_score_delta": None,
        "route_context_flags": [],
        "guard_checks": {
            "route_fit_delta": None,
            "route_fit_pass": False,
            "endpoint_alignment_delta": None,
            "endpoint_alignment_pass": False,
            "speed_limit_drop_delta": None,
            "speed_limit_drop_pass": False,
        },
        "first_next_action": "Rerun branch selection with route candidate details.",
        "next_actions": ["Rerun branch selection with route candidate details."],
    }


def _route_with_flag(
    branch_case: dict[str, object],
    flag: str,
) -> dict[str, object] | None:
    for route in _required_list(branch_case, "route_candidates"):
        if isinstance(route, dict) and bool(route.get(flag)):
            return route
    return None


def _route_deltas(
    default_route: dict[str, object],
    motion_route: dict[str, object],
) -> dict[str, float | None]:
    def delta(field: str) -> float | None:
        selected = _optional_float(motion_route.get(field))
        default = _optional_float(default_route.get(field))
        if selected is None or default is None:
            return None
        return round(selected - default, 6)

    return {
        "route_fit_delta": delta("motion_context_route_fit"),
        "endpoint_alignment_delta": delta("motion_context_endpoint_alignment"),
        "speed_limit_drop_delta": delta("motion_context_speed_limit_drop"),
        "route_remaining_delta_m": delta("route_remaining_m"),
        "motion_context_score_delta": delta("motion_context_score"),
    }


def _guard_checks(deltas: dict[str, float | None]) -> dict[str, object]:
    route_fit = deltas["route_fit_delta"]
    endpoint = deltas["endpoint_alignment_delta"]
    speed_drop = deltas["speed_limit_drop_delta"]
    return {
        "route_fit_delta": route_fit,
        "route_fit_pass": route_fit is not None and route_fit > _ROUTE_FIT_DELTA_GATE,
        "endpoint_alignment_delta": endpoint,
        "endpoint_alignment_pass": endpoint is not None
        and endpoint >= _ENDPOINT_ALIGNMENT_DELTA_GATE,
        "speed_limit_drop_delta": speed_drop,
        "speed_limit_drop_pass": speed_drop is not None
        and speed_drop <= _SPEED_LIMIT_DROP_DELTA_GATE,
    }


def _route_context_flags(deltas: dict[str, float | None]) -> list[str]:
    flags: list[str] = []
    endpoint = deltas["endpoint_alignment_delta"]
    speed_drop = deltas["speed_limit_drop_delta"]
    route_fit = deltas["route_fit_delta"]
    if route_fit is not None and route_fit <= _ROUTE_FIT_DELTA_GATE:
        flags.append("weak_route_fit")
    if endpoint is not None and endpoint < _ENDPOINT_ALIGNMENT_DELTA_GATE:
        flags.append("endpoint_alignment_drop")
    if speed_drop is not None and speed_drop > _SPEED_LIMIT_DROP_DELTA_GATE:
        flags.append("downstream_speed_limit_drop")
    return flags


def _guard_reason(promote: bool, flags: list[str]) -> str:
    if promote:
        return (
            "The motion-context branch improves route fit without triggering "
            "the endpoint-alignment or downstream speed-limit guardrails."
        )
    if flags:
        return (
            "The branch has nominal recoverable FDE, but route-context "
            f"guardrails fired: {', '.join(flags)}."
        )
    return "The branch did not clear all route-context guardrails."


def _next_actions(guard_label: str, route_context_label: str) -> list[str]:
    if guard_label == "promote_motion_context_candidate":
        return [
            "Keep this branch in the broader selector-evaluation queue.",
            "Use it as a positive control when expanding route-context guard coverage.",
        ]
    if route_context_label == "speed_minus_route_context_margin":
        return [
            "Add turn-lane, downstream topology, and traffic-control context before selector rollout.",
            "Keep the motion-context branch held until the replay margin clears the gate.",
            "Test this guard on more branchable cases before changing selector defaults.",
        ]
    return [
        "Collect richer route-context evidence before promoting this branch.",
        "Rerun branch replay after the guard feature set changes.",
    ]


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    promoted = [
        case for case in ready if bool(case.get("guard_promotes_motion_context"))
    ]
    held = [
        case for case in ready if not bool(case.get("guard_promotes_motion_context"))
    ]
    promoted_gains = [
        gain
        for case in promoted
        if (gain := _optional_float(case.get("motion_context_gain_m"))) is not None
    ]
    held_gains = [
        gain
        for case in held
        if (gain := _optional_float(case.get("motion_context_gain_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "guard_promote_count": len(promoted),
        "guard_hold_count": len(held),
        "replay_gate_accepted_count": sum(
            str(case.get("replay_acceptance_label"))
            == "accepted_for_selector_rollout"
            for case in ready
        ),
        "replay_route_context_hold_count": sum(
            str(case.get("replay_acceptance_label")) == "needs_route_context_margin"
            for case in ready
        ),
        "guard_replay_gate_match_count": sum(
            bool(case.get("guard_matches_replay_gate")) for case in ready
        ),
        "guard_false_promote_count": sum(
            bool(case.get("guard_promotes_motion_context"))
            and str(case.get("replay_acceptance_label"))
            != "accepted_for_selector_rollout"
            for case in ready
        ),
        "guard_false_hold_count": sum(
            not bool(case.get("guard_promotes_motion_context"))
            and str(case.get("replay_acceptance_label"))
            == "accepted_for_selector_rollout"
            for case in ready
        ),
        "speed_minus_margin_held_count": sum(
            not bool(case.get("guard_promotes_motion_context"))
            and str(case.get("replay_route_context_label"))
            == "speed_minus_route_context_margin"
            for case in ready
        ),
        "mean_promoted_nominal_gain_m": _mean(promoted_gains),
        "mean_held_nominal_gain_m": _mean(held_gains),
    }


def _rounded(value: object) -> float | None:
    number = _optional_float(value)
    return round(number, 3) if number is not None else None


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
