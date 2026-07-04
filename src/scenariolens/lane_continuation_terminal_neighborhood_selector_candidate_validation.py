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
from scenariolens.lane_continuation_terminal_neighborhood_selector_route_context_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_candidate_validation.v1"
)

_PROMOTE = "promote_terminal_neighborhood_alternate"
_HOLD = "hold_for_terminal_neighborhood_context"
_HEADING_CANDIDATE = "heading_relaxation_candidate"
_ROUTE_CONTEXT_HOLD = "route_context_hold"


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorCandidateValidationResult:
    """Files produced by a diagnostic selector-candidate validation run."""

    ready: bool
    case_count: int
    candidate_match_count: int
    candidate_false_promote_count: int
    candidate_false_hold_count: int
    recovered_false_hold_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_candidate_validation(
    selector_transfer_manifest_path: str | Path,
    selector_route_context_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorCandidateValidationResult:
    """Generate a public-safe diagnostic selector candidate validation."""

    source = Path(selector_transfer_manifest_path)
    context_source = Path(selector_route_context_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_selector_candidate_validation_payload(
        selector_transfer_manifest_path=source,
        selector_route_context_manifest_path=context_source,
        output_dir=target,
    )
    report = lane_continuation_terminal_neighborhood_selector_candidate_validation_markdown(
        payload
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodSelectorCandidateValidationResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        candidate_match_count=int(aggregate["candidate_match_count"]),
        candidate_false_promote_count=int(aggregate["candidate_false_promote_count"]),
        candidate_false_hold_count=int(aggregate["candidate_false_hold_count"]),
        recovered_false_hold_count=int(aggregate["recovered_false_hold_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_candidate_validation_payload(
    selector_transfer_manifest_path: Path,
    selector_route_context_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return validation data for a diagnostic context-aware selector candidate."""

    transfer = json.loads(selector_transfer_manifest_path.read_text(encoding="utf-8"))
    if (
        transfer.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector transfer manifest with "
            f"format {LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT}."
        )
    route_context = json.loads(
        selector_route_context_manifest_path.read_text(encoding="utf-8")
    )
    if (
        route_context.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector route/context audit "
            "manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT}."
        )

    transfer_result = _required_mapping(transfer, "transfer_policy_result")
    transfer_cases = [
        case
        for case in _required_list(transfer_result, "cases")
        if isinstance(case, dict)
    ]
    context_cases = {
        _case_key(case): case
        for case in _required_list(route_context, "cases")
        if isinstance(case, dict)
    }
    cases = [
        _candidate_case(case, context_cases.get(_case_key(case)))
        for case in transfer_cases
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": (
            LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT
        ),
        "selector_transfer_manifest": str(selector_transfer_manifest_path),
        "selector_transfer_format": transfer.get("format"),
        "selector_route_context_manifest": str(selector_route_context_manifest_path),
        "selector_route_context_format": route_context.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(transfer.get("ready"))
        and bool(route_context.get("ready"))
        and bool(cases),
        "source_scope": {
            "training_scope": transfer.get("training_scope", {}),
            "validation_scope": transfer.get("validation_scope", {}),
            "route_context_aggregate": route_context.get("aggregate", {}),
        },
        "candidate_policy": {
            "policy_label": "context_aware_heading_candidate",
            "inherits_transfer_policy": True,
            "extra_promote_condition": (
                "Promote only transfer false holds classified by the "
                "route/context audit as heading_relaxation_candidate."
            ),
            "default_selector_changed": False,
            "raw_map_geometry_used": False,
            "scope": "diagnostic validation queue only",
        },
        "aggregate": aggregate,
        "cases": cases,
        "recommendation": _recommendation(aggregate),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Selector candidate validation uses only derived transfer labels "
            "and route/context classifications. It does not publish raw Waymo "
            "records, trajectory points, or map polylines, and it does not "
            "change ScenarioLens default selector behavior."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_candidate_validation_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for diagnostic selector candidate validation."""

    aggregate = _required_mapping(payload, "aggregate")
    policy = _required_mapping(payload, "candidate_policy")
    source_scope = _required_mapping(payload, "source_scope")
    validation_scope = _required_mapping(source_scope, "validation_scope")
    route_context_aggregate = _required_mapping(
        source_scope, "route_context_aggregate"
    )
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Candidate Validation",
        "",
        "This report tests a narrow diagnostic selector candidate after the "
        "route/context audit. It keeps the transferred selector policy intact "
        "and adds exactly one public-safe promotion rule: recover false holds "
        "only when the route/context audit classifies them as "
        "`heading_relaxation_candidate`.",
        "",
        "The candidate is intentionally narrow. It is not a default selector "
        "change, not a route planner, not a learned model, not closed-loop "
        "simulation, and not a Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Selector transfer manifest: `{payload['selector_transfer_manifest']}`",
        f"- Route/context audit manifest: `{payload['selector_route_context_manifest']}`",
        f"- Ready for candidate validation: {payload['ready']}",
        f"- Validation cases: {validation_scope.get('validation_case_count')}",
        f"- Route/context false holds available: {route_context_aggregate.get('false_hold_count')}",
        f"- Candidate policy: `{policy['policy_label']}`",
        f"- Default selector changed: {policy['default_selector_changed']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Validation Summary",
        "",
        "| Metric | Transfer policy | Candidate policy |",
        "| --- | ---: | ---: |",
        f"| Replay-gate matches | {aggregate['transfer_match_count']} | {aggregate['candidate_match_count']} |",
        f"| False promotions | {aggregate['transfer_false_promote_count']} | {aggregate['candidate_false_promote_count']} |",
        f"| False holds | {aggregate['transfer_false_hold_count']} | {aggregate['candidate_false_hold_count']} |",
        f"| Promoted cases | {aggregate['transfer_promote_count']} | {aggregate['candidate_promote_count']} |",
        f"| Held cases | {aggregate['transfer_hold_count']} | {aggregate['candidate_hold_count']} |",
        "",
        "Additional checks:",
        "",
        f"- Recovered transfer false holds: {aggregate['recovered_false_hold_count']}",
        f"- Replay-held negatives preserved: {aggregate['preserved_negative_control_count']} / {aggregate['replay_held_count']}",
        f"- Route/context holds retained: {aggregate['retained_route_context_hold_count']}",
        "",
        "## Candidate Outcomes",
        "",
        "| Rank | Split | Scenario | Track | Replay label | Transfer | Candidate | Candidate match | Context class | Gain | Rationale |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"{_split_label(case['validation_split'])} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{case['replay_label']} | "
            f"{case['transfer_decision']} | "
            f"{case['candidate_decision']} | "
            f"{case['candidate_match_label']} | "
            f"{case['route_context_classification']} | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{case['candidate_rationale']} |"
        )

    changed_cases = [
        case
        for case in cases
        if isinstance(case, dict) and bool(case.get("changed_by_candidate"))
    ]
    negative_controls = [
        case
        for case in cases
        if isinstance(case, dict) and not bool(case.get("replay_gate_accepted"))
    ]
    lines.extend(
        [
            "",
            "## Recovered Cases",
            "",
            "| Rank | Scenario | Track | Context labels | Heading selected/alternate | Route extension | Next validation step |",
            "| ---: | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    if not changed_cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in changed_cases:
        assert isinstance(case, dict)
        context_labels = ", ".join(
            str(label) for label in _required_list(case, "context_labels")
        )
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{context_labels if context_labels else 'none'} | "
            f"{_score_text(case.get('selected_heading_alignment'))} / {_score_text(case.get('alternate_heading_alignment'))} | "
            f"{_meter_text(case.get('route_extension_m'))} | "
            f"{case['next_validation_step']} |"
        )

    lines.extend(
        [
            "",
            "## Negative Controls",
            "",
            "| Rank | Scenario | Track | Replay gain | Candidate decision | Reason held |",
            "| ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    if not negative_controls:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in negative_controls:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{case['candidate_decision']} | "
            f"{case['candidate_rationale']} |"
        )

    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            str(payload["recommendation"]),
            "",
            "## Interpretation",
            "",
            "- This candidate is evaluated against the existing replay-label queue; it is not trained on raw trajectory data.",
            "- Preserving replay-held negative controls matters more than recovering every replay-accepted alternate.",
            "- The severe route/context hold remains held, so this is still diagnostic evidence rather than selector adoption.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _candidate_case(
    transfer_case: dict[str, object],
    route_context_case: dict[str, object] | None,
) -> dict[str, object]:
    replay_accepted = bool(transfer_case.get("replay_gate_accepted"))
    transfer_promotes = bool(transfer_case.get("selector_promotes"))
    context_classification = (
        str(route_context_case.get("classification"))
        if route_context_case is not None
        else "not_a_false_hold"
    )
    context_labels = (
        [
            str(label)
            for label in route_context_case.get("context_labels", [])
            if isinstance(label, str)
        ]
        if route_context_case is not None
        else []
    )
    candidate_promotes = transfer_promotes or (
        context_classification == _HEADING_CANDIDATE
    )
    changed = candidate_promotes != transfer_promotes
    candidate_match_label = _match_label(candidate_promotes, replay_accepted)
    return {
        "rank": int(transfer_case.get("rank", 0) or 0),
        "validation_split": str(transfer_case.get("validation_split", "")),
        "scenario_id": str(transfer_case.get("scenario_id", "")),
        "track_id": str(transfer_case.get("track_id", "")),
        "source_name": str(transfer_case.get("source_name", "")),
        "replay_gate_accepted": replay_accepted,
        "replay_label": "accepted" if replay_accepted else "held",
        "transfer_promotes": transfer_promotes,
        "candidate_promotes": candidate_promotes,
        "transfer_decision": _PROMOTE if transfer_promotes else _HOLD,
        "candidate_decision": _PROMOTE if candidate_promotes else _HOLD,
        "transfer_match_label": str(transfer_case.get("selector_gate_match_label", "")),
        "candidate_match_label": candidate_match_label,
        "changed_by_candidate": changed,
        "route_context_classification": context_classification,
        "context_labels": context_labels,
        "replay_gain_m": _optional_float(transfer_case.get("replay_gain_m")),
        "selected_heading_alignment": _optional_float(
            transfer_case.get("selected_heading_alignment")
        ),
        "alternate_heading_alignment": _optional_float(
            transfer_case.get("alternate_heading_alignment")
        ),
        "route_extension_m": _optional_float(transfer_case.get("route_extension_m")),
        "candidate_rationale": _candidate_rationale(
            replay_accepted=replay_accepted,
            transfer_promotes=transfer_promotes,
            context_classification=context_classification,
        ),
        "next_validation_step": _next_validation_step(context_classification),
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    replay_held = [case for case in cases if not bool(case.get("replay_gate_accepted"))]
    transfer_matches = [
        case for case in cases if case.get("transfer_match_label") not in _ERROR_LABELS
    ]
    candidate_matches = [
        case for case in cases if case.get("candidate_match_label") not in _ERROR_LABELS
    ]
    transfer_false_promotes = [
        case for case in cases if case.get("transfer_match_label") == "false_promote"
    ]
    transfer_false_holds = [
        case for case in cases if case.get("transfer_match_label") == "false_hold"
    ]
    candidate_false_promotes = [
        case for case in cases if case.get("candidate_match_label") == "false_promote"
    ]
    candidate_false_holds = [
        case for case in cases if case.get("candidate_match_label") == "false_hold"
    ]
    return {
        "case_count": len(cases),
        "replay_accepted_count": sum(
            bool(case.get("replay_gate_accepted")) for case in cases
        ),
        "replay_held_count": len(replay_held),
        "transfer_match_count": len(transfer_matches),
        "candidate_match_count": len(candidate_matches),
        "match_delta": len(candidate_matches) - len(transfer_matches),
        "transfer_false_promote_count": len(transfer_false_promotes),
        "candidate_false_promote_count": len(candidate_false_promotes),
        "transfer_false_hold_count": len(transfer_false_holds),
        "candidate_false_hold_count": len(candidate_false_holds),
        "transfer_promote_count": sum(
            bool(case.get("transfer_promotes")) for case in cases
        ),
        "candidate_promote_count": sum(
            bool(case.get("candidate_promotes")) for case in cases
        ),
        "transfer_hold_count": sum(
            not bool(case.get("transfer_promotes")) for case in cases
        ),
        "candidate_hold_count": sum(
            not bool(case.get("candidate_promotes")) for case in cases
        ),
        "recovered_false_hold_count": sum(
            case.get("transfer_match_label") == "false_hold"
            and case.get("candidate_match_label") == "true_positive_recovery"
            for case in cases
        ),
        "preserved_negative_control_count": sum(
            not bool(case.get("replay_gate_accepted"))
            and not bool(case.get("candidate_promotes"))
            for case in cases
        ),
        "retained_route_context_hold_count": sum(
            case.get("route_context_classification") == _ROUTE_CONTEXT_HOLD
            and not bool(case.get("candidate_promotes"))
            for case in cases
        ),
    }


def _recommendation(aggregate: dict[str, object]) -> str:
    recovered = int(aggregate.get("recovered_false_hold_count", 0) or 0)
    false_promotes = int(aggregate.get("candidate_false_promote_count", 0) or 0)
    retained_context = int(aggregate.get("retained_route_context_hold_count", 0) or 0)
    if recovered and false_promotes == 0 and retained_context:
        return (
            "Keep the default selector unchanged, but carry the "
            "context-aware heading candidate into the next validation queue. "
            "It recovers one transfer false hold, preserves replay-held "
            "negative controls, and keeps the severe route/context case held."
        )
    if false_promotes:
        return (
            "Do not advance this candidate. It introduces false promotions, "
            "so the next step is stricter route/context evidence."
        )
    return (
        "Keep this as a diagnostic record only. The candidate does not recover "
        "a false hold on the current queue."
    )


def _candidate_rationale(
    replay_accepted: bool,
    transfer_promotes: bool,
    context_classification: str,
) -> str:
    if transfer_promotes:
        return "already promoted by transferred selector"
    if context_classification == _HEADING_CANDIDATE:
        return "promoted by route/context heading candidate"
    if context_classification == _ROUTE_CONTEXT_HOLD:
        return "held by route/context audit"
    if not replay_accepted:
        return "preserved replay-held negative control"
    return "held by transferred selector"


def _next_validation_step(context_classification: str) -> str:
    if context_classification == _HEADING_CANDIDATE:
        return "Retest on a broader replay queue with additional held negatives."
    if context_classification == _ROUTE_CONTEXT_HOLD:
        return "Inspect lane direction, route context, and coordinate frame first."
    return "No route/context candidate action."


def _match_label(selector_promotes: bool, replay_accepted: bool) -> str:
    if selector_promotes and replay_accepted:
        return "true_positive_recovery"
    if selector_promotes and not replay_accepted:
        return "false_promote"
    if not selector_promotes and replay_accepted:
        return "false_hold"
    return "true_hold"


def _split_label(value: object) -> str:
    if value == "overlap_with_calibration":
        return "overlap"
    if value == "novel_case":
        return "novel"
    return str(value)


def _case_key(case: dict[str, object]) -> tuple[str, str]:
    return (str(case.get("scenario_id", "")), str(case.get("track_id", "")))


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"


_ERROR_LABELS = {"false_promote", "false_hold"}
