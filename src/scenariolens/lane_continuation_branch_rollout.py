from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_selection import (
    _chain_text,
    _meter_text,
    _optional_float,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)

LANE_CONTINUATION_BRANCH_ROLLOUT_FORMAT = (
    "scenariolens.lane_continuation_branch_rollout_gate.v1"
)

_PROMOTE_DECISION = "promote_for_broader_selector_eval"
_HOLD_ROUTE_CONTEXT_DECISION = "hold_for_route_context_margin"
_HOLD_SELECTOR_STABILITY_DECISION = "hold_for_selector_stability"
_HOLD_ROUTE_AND_SELECTOR_DECISION = "hold_for_route_and_selector_context"
_HOLD_MANUAL_REVIEW_DECISION = "hold_for_manual_review"
_NOT_EVALUABLE_DECISION = "not_evaluable"


@dataclass(frozen=True)
class LaneContinuationBranchRolloutResult:
    """Files produced by a branch rollout gate diagnostic run."""

    ready: bool
    case_count: int
    promoted_case_count: int
    held_route_context_case_count: int
    held_selector_stability_case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_branch_rollout_gate(
    branch_replay_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationBranchRolloutResult:
    """Generate a public-safe promote/hold gate from branch replay evidence."""

    source = Path(branch_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_branch_rollout_payload(
        branch_replay_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_branch_rollout_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationBranchRolloutResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        promoted_case_count=int(aggregate["promoted_case_count"]),
        held_route_context_case_count=int(
            aggregate["held_route_context_case_count"]
        ),
        held_selector_stability_case_count=int(
            aggregate["held_selector_stability_case_count"]
        ),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_branch_rollout_payload(
    branch_replay_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return rollout gate decisions for branch replay cases."""

    branch_replay = json.loads(branch_replay_manifest_path.read_text(encoding="utf-8"))
    if branch_replay.get("format") != LANE_CONTINUATION_BRANCH_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation branch-replay manifest with format "
            f"{LANE_CONTINUATION_BRANCH_REPLAY_FORMAT}."
        )

    cases = [
        _rollout_case(case)
        for case in _required_list(branch_replay, "cases")
        if isinstance(case, dict)
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_BRANCH_ROLLOUT_FORMAT,
        "branch_replay_manifest": str(branch_replay_manifest_path),
        "branch_replay_format": branch_replay.get("format"),
        "branch_selection_manifest": branch_replay.get("branch_selection_manifest"),
        "replay_manifest": branch_replay.get("replay_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(branch_replay.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "promotion_gate": (
            "Promote only cases whose branch replay accepted the "
            "motion-context selector for broader rollout. Hold stable "
            "thin-margin cases for route-context work and unstable choices "
            "for selector-stability work."
        ),
        "source_scope": {
            "branch_replay_case_count": branch_replay.get("case_count"),
            "replayed_case_count": _required_mapping(
                branch_replay,
                "aggregate",
            ).get("replayed_case_count"),
            "perturbation_trial_count": _required_mapping(
                branch_replay,
                "aggregate",
            ).get("perturbation_trial_count"),
            "minimum_stable_gain_m": branch_replay.get("minimum_stable_gain_m"),
        },
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The rollout gate is an evidence triage artifact over open-loop "
            "branch replay diagnostics. It is not a route planner, not a "
            "closed-loop simulator, not a production release process, and not "
            "a Waymo benchmark claim."
        ),
    }


def lane_continuation_branch_rollout_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for branch rollout gate decisions."""

    aggregate = _required_mapping(payload, "aggregate")
    source_scope = _required_mapping(payload, "source_scope")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Branch Rollout Gate",
        "",
        "This report converts the motion-context branch replay diagnostic into "
        "a promote/hold decision table. A case is promoted only when the "
        "branch replay accepted it for broader selector evaluation; thin "
        "route-context margins and selector instability stay held with their "
        "next engineering action.",
        "",
        "The gate is intentionally conservative. It is useful because it shows "
        "how ScenarioLens can move from metric reporting to release-style "
        "evidence triage without claiming to be a planner or a benchmark. "
        "It is not a route planner.",
        "",
        "## Scope",
        "",
        f"- Branch replay manifest: `{payload['branch_replay_manifest']}`",
        f"- Branch selection manifest: `{payload['branch_selection_manifest']}`",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Ready for rollout triage: {payload['ready']}",
        f"- Replay cases: {source_scope['branch_replay_case_count']}",
        f"- Replayed cases: {source_scope['replayed_case_count']}",
        f"- Perturbation trials: {source_scope['perturbation_trial_count']}",
        f"- Minimum stable gain: {_meter_text(source_scope['minimum_stable_gain_m'])}",
        f"- Gate: {payload['promotion_gate']}",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Rollout Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Replayed cases | {aggregate['replayed_case_count']} |",
        f"| Promoted candidates | {aggregate['promoted_case_count']} |",
        f"| Held for route context | {aggregate['held_route_context_case_count']} |",
        f"| Held for selector stability | {aggregate['held_selector_stability_case_count']} |",
        f"| Held for route and selector context | {aggregate['held_route_and_selector_case_count']} |",
        f"| Manual-review holds | {aggregate['manual_review_case_count']} |",
        f"| Not evaluable | {aggregate['not_evaluable_case_count']} |",
        f"| Speed-minus margin holds | {aggregate['speed_minus_margin_hold_count']} |",
        f"| Speed-prior resolved holds | {aggregate['speed_prior_resolved_hold_count']} |",
        f"| Oracle-matched holds | {aggregate['oracle_matched_hold_count']} |",
        f"| Mean promoted margin | {_signed_meter_text(aggregate['mean_promoted_margin_m'])} |",
        f"| Min promoted margin | {_signed_meter_text(aggregate['min_promoted_margin_m'])} |",
        f"| Max hold priority | {_number_text(aggregate['max_hold_priority_score'])} |",
        f"| Max hold gap to gate | {_signed_meter_text(aggregate['max_hold_gap_to_gate_m'])} |",
        "",
        "## Decisions",
        "",
        "| Rank | Scenario | Track | Decision | Acceptance | Route context | Margin | Speed-prior margin | First next action |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['decision']}` | "
            f"`{case['acceptance_label']}` | "
            f"`{case['route_context_label']}` | "
            f"{_signed_meter_text(case.get('robustness_margin_m'))} | "
            f"{_signed_meter_text(case.get('history_speed_prior_margin_m'))} | "
            f"{case['first_next_action']} |"
        )

    promoted = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("decision") == _PROMOTE_DECISION
    ]
    held = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("decision") != _PROMOTE_DECISION
    ]
    lines.extend(
        [
            "",
            "## Promote Queue",
            "",
        ]
    )
    if not promoted:
        lines.append("- No cases currently clear the branch rollout gate.")
    for case in promoted:
        assert isinstance(case, dict)
        lines.append(
            "- "
            f"`{case['scenario_id']}` track `{case['track_id']}`: "
            f"{_signed_meter_text(case.get('robustness_margin_m'))} margin, "
            f"default chain {_chain_text(case.get('default_chain'))}, "
            f"motion-context chain {_chain_text(case.get('motion_context_chain'))}."
        )

    lines.extend(
        [
            "",
            "## Hold Queue",
            "",
        ]
    )
    if not held:
        lines.append("- No cases are held by this rollout gate.")
    for case in held:
        assert isinstance(case, dict)
        lines.append(
            "- "
            f"`{case['scenario_id']}` track `{case['track_id']}`: "
            f"**{case['decision']}** because {case['decision_reason']} "
            f"First action: {case['first_next_action']}"
        )

    for case in cases:
        assert isinstance(case, dict)
        actions = _required_list(case, "next_actions")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Decision: **{case['decision']}**",
                f"- Decision reason: {case['decision_reason']}",
                f"- Acceptance: **{case['acceptance_label']}**",
                f"- Stability: **{case['stability_label']}**",
                f"- Route-context diagnostic: **{case['route_context_label']}**",
                f"- History speed-prior acceptance: **{case['history_speed_prior_acceptance_label']}**",
                f"- Nominal recoverable FDE: {_signed_meter_text(case.get('nominal_gain_m'))}",
                f"- Minimum perturbed recoverable FDE: {_signed_meter_text(case.get('min_gain_m'))}",
                f"- Robustness margin: {_signed_meter_text(case.get('robustness_margin_m'))}",
                f"- Route-context gap to gate: {_signed_meter_text(case.get('robustness_gap_to_gate_m'))}",
                f"- Route-context priority: {_number_text(case.get('route_context_priority_score'))}",
                f"- Selected route matches diagnostic oracle: {case['selected_matches_oracle']}",
                "",
                "Next actions:",
                "",
                *[f"- {action}" for action in actions],
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The promote queue is a candidate set for broader selector "
            "evaluation, not a production release.",
            "- The hold queue is the interesting research queue: it names where "
            "the current branch selector needs route context, selector margin, "
            "or replay readiness work.",
            "- Publishing both promoted and held cases keeps the evidence honest "
            "and makes regressions useful rather than embarrassing.",
            "- Public outputs stay aggregate and case-summary oriented; raw "
            "Waymo TFRecords and local per-case packets remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _rollout_case(case: dict[str, object]) -> dict[str, object]:
    stability = _mapping_or_empty(case.get("perturbation_stability"))
    acceptance = _mapping_or_empty(case.get("acceptance_decision"))
    speed_prior_acceptance = _mapping_or_empty(
        case.get("history_speed_prior_acceptance_decision")
    )
    speed_prior_stability = _mapping_or_empty(
        case.get("history_speed_prior_stability")
    )
    route_context = _mapping_or_empty(case.get("route_context_margin_diagnostic"))
    decision, decision_reason = _rollout_decision(
        ready=bool(case.get("ready")),
        acceptance_label=str(acceptance.get("label", "not_evaluable")),
        route_context_label=str(route_context.get("label", "not_evaluable")),
        stability_label=str(stability.get("label", "not_evaluable")),
    )
    next_actions = _next_actions(
        decision=decision,
        acceptance=acceptance,
        route_context=route_context,
    )
    return {
        "rank": int(case.get("rank", 0) or 0),
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "source_name": str(case.get("source_name", "")),
        "ready": bool(case.get("ready")),
        "decision": decision,
        "promotion_ready": decision == _PROMOTE_DECISION,
        "decision_reason": decision_reason,
        "acceptance_label": str(acceptance.get("label", "not_evaluable")),
        "route_context_label": str(route_context.get("label", "not_evaluable")),
        "stability_label": str(stability.get("label", "not_evaluable")),
        "history_speed_prior_acceptance_label": str(
            speed_prior_acceptance.get("label", "not_evaluable")
        ),
        "default_chain": case.get("default_chain", []),
        "motion_context_chain": case.get("motion_context_chain", []),
        "nominal_gain_m": _rounded(case.get("nominal_motion_context_gain_m")),
        "min_gain_m": _rounded(stability.get("min_gain_m")),
        "robustness_margin_m": _rounded(stability.get("robustness_margin_m")),
        "history_speed_prior_margin_m": _rounded(
            speed_prior_stability.get("robustness_margin_m")
        ),
        "route_context_priority_score": _rounded(
            route_context.get("priority_score")
        ),
        "robustness_gap_to_gate_m": _rounded(
            route_context.get("robustness_gap_to_gate_m")
        ),
        "selected_matches_oracle": bool(
            route_context.get("selected_matches_oracle")
        ),
        "speed_prior_resolved_margin": bool(
            route_context.get("speed_prior_resolved_margin")
        ),
        "first_next_action": next_actions[0],
        "next_actions": next_actions,
    }


def _rollout_decision(
    ready: bool,
    acceptance_label: str,
    route_context_label: str,
    stability_label: str,
) -> tuple[str, str]:
    if not ready:
        return _NOT_EVALUABLE_DECISION, "the branch replay case was not evaluable."
    if acceptance_label == "accepted_for_selector_rollout":
        return (
            _PROMOTE_DECISION,
            "the branch preserved its choice and cleared the recoverable-FDE gate.",
        )
    if route_context_label in {
        "speed_minus_route_context_margin",
        "route_context_margin",
    }:
        return (
            _HOLD_ROUTE_CONTEXT_DECISION,
            "the branch is stable but its route-context recoverable-FDE margin "
            "is too thin.",
        )
    if route_context_label == "selector_stability_context_margin":
        return (
            _HOLD_SELECTOR_STABILITY_DECISION,
            "the selector choice changes under perturbation.",
        )
    if route_context_label == "route_and_selector_context_margin":
        return (
            _HOLD_ROUTE_AND_SELECTOR_DECISION,
            "both route-context margin and selector stability need follow-up.",
        )
    if stability_label in {
        "branch_stable_gain_sensitive",
        "history_speed_prior_branch_stable_gain_sensitive",
    }:
        return (
            _HOLD_ROUTE_CONTEXT_DECISION,
            "the branch is stable but at least one perturbation loses margin.",
        )
    if acceptance_label in {
        "needs_selector_stability",
        "needs_route_and_selector_followup",
    }:
        return (
            _HOLD_SELECTOR_STABILITY_DECISION,
            "the replay did not preserve a stable branch choice.",
        )
    return (
        _HOLD_MANUAL_REVIEW_DECISION,
        "the replay decision needs manual review before promotion.",
    )


def _next_actions(
    decision: str,
    acceptance: dict[str, object],
    route_context: dict[str, object],
) -> list[str]:
    route_actions = [
        str(action)
        for action in route_context.get("next_actions", [])
        if str(action).strip()
    ]
    acceptance_action = str(acceptance.get("next_action", "")).strip()
    if decision == _PROMOTE_DECISION:
        actions = []
        if acceptance_action:
            actions.append(acceptance_action)
        actions.extend(route_actions)
        return actions or [
            "Evaluate this selector behavior on a broader branchable queue.",
        ]
    if route_actions:
        return route_actions
    if acceptance_action:
        return [acceptance_action]
    return [
        "Keep this case held until the replay packet has a concrete follow-up.",
    ]


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    promoted = [
        case for case in cases if case.get("decision") == _PROMOTE_DECISION
    ]
    holds = [
        case
        for case in cases
        if case.get("decision") not in {_PROMOTE_DECISION, _NOT_EVALUABLE_DECISION}
    ]
    promoted_margins = [
        margin
        for case in promoted
        if (margin := _optional_float(case.get("robustness_margin_m"))) is not None
    ]
    hold_priorities = [
        priority
        for case in holds
        if (priority := _optional_float(case.get("route_context_priority_score")))
        is not None
    ]
    hold_gaps = [
        gap
        for case in holds
        if (gap := _optional_float(case.get("robustness_gap_to_gate_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "replayed_case_count": sum(bool(case.get("ready")) for case in cases),
        "promoted_case_count": len(promoted),
        "held_route_context_case_count": sum(
            case.get("decision") == _HOLD_ROUTE_CONTEXT_DECISION
            for case in cases
        ),
        "held_selector_stability_case_count": sum(
            case.get("decision") == _HOLD_SELECTOR_STABILITY_DECISION
            for case in cases
        ),
        "held_route_and_selector_case_count": sum(
            case.get("decision") == _HOLD_ROUTE_AND_SELECTOR_DECISION
            for case in cases
        ),
        "manual_review_case_count": sum(
            case.get("decision") == _HOLD_MANUAL_REVIEW_DECISION
            for case in cases
        ),
        "not_evaluable_case_count": sum(
            case.get("decision") == _NOT_EVALUABLE_DECISION for case in cases
        ),
        "speed_minus_margin_hold_count": sum(
            case.get("route_context_label") == "speed_minus_route_context_margin"
            for case in cases
        ),
        "speed_prior_resolved_hold_count": sum(
            bool(case.get("speed_prior_resolved_margin"))
            and case.get("decision") != _PROMOTE_DECISION
            for case in cases
        ),
        "oracle_matched_hold_count": sum(
            bool(case.get("selected_matches_oracle"))
            and case.get("decision") != _PROMOTE_DECISION
            for case in cases
        ),
        "mean_promoted_margin_m": _mean(promoted_margins),
        "min_promoted_margin_m": (
            round(min(promoted_margins), 3) if promoted_margins else None
        ),
        "max_hold_priority_score": (
            round(max(hold_priorities), 3) if hold_priorities else None
        ),
        "max_hold_gap_to_gate_m": round(max(hold_gaps), 3) if hold_gaps else None,
    }


def _mapping_or_empty(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _rounded(value: object) -> float | None:
    number = _optional_float(value)
    return round(number, 3) if number is not None else None


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _number_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number:.3f}"
