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
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_route_context_audit.v1"
)


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorRouteContextAuditResult:
    """Files produced by a selector false-hold route/context audit."""

    ready: bool
    false_hold_count: int
    joined_false_hold_count: int
    heading_relaxation_candidate_count: int
    route_context_hold_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_route_context_audit(
    selector_transfer_manifest_path: str | Path,
    terminal_neighborhood_replay_manifest_path: str | Path,
    output_dir: str | Path,
    diagnostic_heading_gate: float = 0.70,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorRouteContextAuditResult:
    """Generate a public-safe route/context audit for selector false holds."""

    if not 0.0 <= diagnostic_heading_gate <= 1.0:
        raise ValueError("diagnostic-heading-gate must be between 0.0 and 1.0.")

    source = Path(selector_transfer_manifest_path)
    replay_source = Path(terminal_neighborhood_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = (
        lane_continuation_terminal_neighborhood_selector_route_context_audit_payload(
            selector_transfer_manifest_path=source,
            terminal_neighborhood_replay_manifest_path=replay_source,
            output_dir=target,
            diagnostic_heading_gate=diagnostic_heading_gate,
        )
    )
    report = (
        lane_continuation_terminal_neighborhood_selector_route_context_audit_markdown(
            payload
        )
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodSelectorRouteContextAuditResult(
        ready=bool(payload["ready"]),
        false_hold_count=int(aggregate["false_hold_count"]),
        joined_false_hold_count=int(aggregate["joined_false_hold_count"]),
        heading_relaxation_candidate_count=int(
            aggregate["heading_relaxation_candidate_count"]
        ),
        route_context_hold_count=int(aggregate["route_context_hold_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_route_context_audit_payload(
    selector_transfer_manifest_path: Path,
    terminal_neighborhood_replay_manifest_path: Path,
    output_dir: Path,
    diagnostic_heading_gate: float = 0.70,
) -> dict[str, object]:
    """Return route/context diagnostics for selector transfer false holds."""

    transfer = json.loads(selector_transfer_manifest_path.read_text(encoding="utf-8"))
    if (
        transfer.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector transfer manifest with "
            f"format {LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT}."
        )

    replay = json.loads(
        terminal_neighborhood_replay_manifest_path.read_text(encoding="utf-8")
    )
    if replay.get("format") != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT:
        raise ValueError(
            "Expected a terminal-neighborhood replay manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT}."
        )

    transfer_result = _required_mapping(transfer, "transfer_policy_result")
    transfer_policy = _required_mapping(transfer_result, "policy")
    transfer_cases = [
        case
        for case in _required_list(transfer_result, "cases")
        if isinstance(case, dict)
    ]
    false_holds = [
        case
        for case in transfer_cases
        if case.get("selector_gate_match_label") == "false_hold"
    ]
    replay_cases = {
        _case_key(case): case
        for case in _required_list(replay, "cases")
        if isinstance(case, dict)
    }
    audited_cases = [
        _audited_case(
            transfer_case=case,
            replay_case=replay_cases.get(_case_key(case)),
            diagnostic_heading_gate=diagnostic_heading_gate,
            transfer_heading_gate=_required_float(
                transfer_policy, "min_heading_alignment"
            ),
        )
        for case in false_holds
    ]
    aggregate = _aggregate_cases(
        transfer_cases=transfer_cases,
        audited_cases=audited_cases,
    )
    return {
        "format": (
            LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT
        ),
        "selector_transfer_manifest": str(selector_transfer_manifest_path),
        "selector_transfer_format": transfer.get("format"),
        "terminal_neighborhood_replay_manifest": str(
            terminal_neighborhood_replay_manifest_path
        ),
        "terminal_neighborhood_replay_format": replay.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(transfer.get("ready"))
        and bool(replay.get("ready"))
        and bool(transfer_cases),
        "diagnostic_heading_gate": round(diagnostic_heading_gate, 3),
        "transfer_policy": transfer_policy,
        "source_scope": {
            "training_scope": transfer.get("training_scope", {}),
            "validation_scope": transfer.get("validation_scope", {}),
            "replay_aggregate": replay.get("aggregate", {}),
        },
        "aggregate": aggregate,
        "cases": audited_cases,
        "recommendation": _recommendation(audited_cases),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Selector route/context audit joins selector transfer false holds "
            "to public-safe replay diagnostics. It uses derived route lengths, "
            "heading-alignment scores, FDE deltas, and perturbation summaries; "
            "it does not publish raw Waymo records, trajectory points, or map "
            "polylines."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_route_context_audit_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for selector false-hold context diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    transfer_policy = _required_mapping(payload, "transfer_policy")
    source_scope = _required_mapping(payload, "source_scope")
    validation_scope = _required_mapping(source_scope, "validation_scope")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Route/Context Audit",
        "",
        "This report follows the selector error audit by joining the remaining "
        "false holds to derived replay and route-context diagnostics. The goal "
        "is to separate a reasonable heading-relaxation candidate from a case "
        "that should stay held for deeper map/context inspection.",
        "",
        "The audit is intentionally narrow. It is not a route planner, not a "
        "learned model, not closed-loop simulation, and not a Waymo benchmark "
        "claim.",
        "",
        "## Scope",
        "",
        f"- Selector transfer manifest: `{payload['selector_transfer_manifest']}`",
        f"- Terminal-neighborhood replay manifest: `{payload['terminal_neighborhood_replay_manifest']}`",
        f"- Ready for route/context audit: {payload['ready']}",
        f"- Validation cases: {validation_scope.get('validation_case_count')}",
        f"- Transfer false holds audited: {aggregate['false_hold_count']}",
        f"- Joined replay false holds: {aggregate['joined_false_hold_count']}",
        f"- Transfer heading gate: {_score_text(transfer_policy.get('min_heading_alignment'))}",
        f"- Diagnostic heading gate: {_score_text(payload['diagnostic_heading_gate'])}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Context Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Transfer cases | {aggregate['transfer_case_count']} |",
        f"| False holds | {aggregate['false_hold_count']} |",
        f"| Joined false holds | {aggregate['joined_false_hold_count']} |",
        f"| Stable recovery false holds | {aggregate['stable_recovery_count']} |",
        f"| No-exit to linked-chain cases | {aggregate['no_exit_to_linked_chain_count']} |",
        f"| Heading-relaxation candidates | {aggregate['heading_relaxation_candidate_count']} |",
        f"| Route/context holds | {aggregate['route_context_hold_count']} |",
        f"| Mean selected terminal deficit | {_meter_text(aggregate['mean_selected_terminal_deficit_m'])} |",
        f"| Mean route extension | {_meter_text(aggregate['mean_route_extension_m'])} |",
        f"| Mean replay gain | {_signed_meter_text(aggregate['mean_replay_gain_m'])} |",
        "",
        "## False-Hold Route/Context Table",
        "",
        "| Rank | Scenario | Track | Classification | Gain | Min perturbation gain | Heading selected/alternate | Route selected -> alternate | Context read | Next action |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{case['classification']} | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{_signed_meter_text(case.get('min_perturbation_gain_m'))} | "
            f"{_score_text(case.get('selected_heading_alignment'))} / {_score_text(case.get('alternate_heading_alignment'))} | "
            f"{case['selected_route_status']} -> {case['alternate_route_status']} | "
            f"{case['context_read']} | "
            f"{case['next_action']} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        labels = ", ".join(str(label) for label in _required_list(case, "context_labels"))
        lines.extend(
            [
                "",
                f"## Case {case['rank']}: `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Classification: **{case['classification']}**.",
                f"- Selected feature `{case['selected_feature_id']}` has {_meter_text(case.get('selected_route_remaining_m'))} remaining; alternate feature `{case['alternate_feature_id']}` has {_meter_text(case.get('alternate_route_remaining_m'))} remaining.",
                f"- Horizon travel: {_meter_text(case.get('horizon_travel_m'))}; selected terminal deficit: {_meter_text(case.get('selected_terminal_deficit_m'))}; alternate linked extension: {_meter_text(case.get('alternate_link_extension_m'))}.",
                f"- FDE selected/alternate: {_meter_text(case.get('selected_fde_m'))} / {_meter_text(case.get('alternate_fde_m'))}; replay gain: {_signed_meter_text(case.get('replay_gain_m'))}.",
                f"- Perturbation stability: {case['perturbation_label']} with minimum gain {_signed_meter_text(case.get('min_perturbation_gain_m'))}.",
                f"- Context labels: {labels if labels else 'none'}.",
                f"- Next action: {case['next_action']}",
            ]
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
            "- The audit reuses derived replay packets; it does not inspect or publish raw map polylines.",
            "- A heading-relaxation candidate remains diagnostic until replay-held negative coverage grows.",
            "- A severe selected-lane heading disagreement is treated as a context problem, not evidence to relax gates globally.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _audited_case(
    transfer_case: dict[str, object],
    replay_case: dict[str, object] | None,
    diagnostic_heading_gate: float,
    transfer_heading_gate: float,
) -> dict[str, object]:
    selected_heading = _optional_float(transfer_case.get("selected_heading_alignment"))
    alternate_heading = _optional_float(
        transfer_case.get("alternate_heading_alignment")
    )
    route_extension = _optional_float(transfer_case.get("route_extension_m"))
    replay_gain = _optional_float(transfer_case.get("replay_gain_m"))
    selected_route_remaining = _optional_float(
        _field(replay_case, transfer_case, "selected_route_remaining_m")
    )
    alternate_route_remaining = _optional_float(
        _field(replay_case, transfer_case, "alternate_route_remaining_m")
    )
    selected_base_remaining = _optional_float(
        _field(replay_case, transfer_case, "selected_base_remaining_m")
    )
    alternate_base_remaining = _optional_float(
        _field(replay_case, transfer_case, "alternate_base_remaining_m")
    )
    horizon_travel = _optional_float(_field(replay_case, transfer_case, "horizon_travel_m"))
    selected_terminal_deficit = _nonnegative_difference(
        horizon_travel, selected_route_remaining
    )
    alternate_link_extension = _nonnegative_difference(
        alternate_route_remaining, alternate_base_remaining
    )
    stability = {}
    if replay_case is not None and isinstance(
        replay_case.get("perturbation_stability"), dict
    ):
        stability = _required_mapping(replay_case, "perturbation_stability")
    min_perturbation_gain = _optional_float(stability.get("min_gain_m"))
    stable_recovery = (
        str(stability.get("label", "")) == "stable_recovery"
        and min_perturbation_gain is not None
        and min_perturbation_gain > 0.0
    )
    context_labels = _context_labels(
        selected_heading=selected_heading,
        alternate_heading=alternate_heading,
        transfer_heading_gate=transfer_heading_gate,
        diagnostic_heading_gate=diagnostic_heading_gate,
        selected_route_status=str(
            _field(replay_case, transfer_case, "selected_route_status", "")
        ),
        alternate_route_status=str(
            _field(replay_case, transfer_case, "alternate_route_status", "")
        ),
        selected_terminal_deficit=selected_terminal_deficit,
        alternate_link_extension=alternate_link_extension,
        stable_recovery=stable_recovery,
    )
    classification = _classification(
        selected_heading=selected_heading,
        alternate_heading=alternate_heading,
        diagnostic_heading_gate=diagnostic_heading_gate,
        stable_recovery=stable_recovery,
    )
    return {
        "rank": int(transfer_case.get("rank", 0) or 0),
        "validation_split": str(transfer_case.get("validation_split", "")),
        "scenario_id": str(transfer_case.get("scenario_id", "")),
        "track_id": str(transfer_case.get("track_id", "")),
        "source_name": str(transfer_case.get("source_name", "")),
        "joined_replay_case": replay_case is not None,
        "selected_feature_id": str(transfer_case.get("selected_feature_id", "")),
        "alternate_feature_id": str(transfer_case.get("alternate_feature_id", "")),
        "selected_route_status": str(
            _field(replay_case, transfer_case, "selected_route_status", "unknown")
        ),
        "alternate_route_status": str(
            _field(replay_case, transfer_case, "alternate_route_status", "unknown")
        ),
        "selected_route_remaining_m": selected_route_remaining,
        "alternate_route_remaining_m": alternate_route_remaining,
        "selected_base_remaining_m": selected_base_remaining,
        "alternate_base_remaining_m": alternate_base_remaining,
        "horizon_travel_m": horizon_travel,
        "selected_terminal_deficit_m": selected_terminal_deficit,
        "alternate_link_extension_m": alternate_link_extension,
        "route_extension_m": route_extension,
        "selected_heading_alignment": selected_heading,
        "alternate_heading_alignment": alternate_heading,
        "minimum_heading_alignment": _optional_float(
            transfer_case.get("minimum_heading_alignment")
        ),
        "selected_fde_m": _optional_float(_field(replay_case, transfer_case, "selected_fde_m")),
        "alternate_fde_m": _optional_float(_field(replay_case, transfer_case, "alternate_fde_m")),
        "selected_ade_m": _optional_float(_field(replay_case, transfer_case, "selected_ade_m")),
        "alternate_ade_m": _optional_float(_field(replay_case, transfer_case, "alternate_ade_m")),
        "replay_gain_m": replay_gain,
        "min_perturbation_gain_m": min_perturbation_gain,
        "perturbation_label": str(stability.get("label", "missing_replay_join")),
        "context_labels": context_labels,
        "classification": classification,
        "context_read": _context_read(classification),
        "next_action": _next_action(classification),
    }


def _aggregate_cases(
    transfer_cases: list[dict[str, object]],
    audited_cases: list[dict[str, object]],
) -> dict[str, object]:
    joined = [case for case in audited_cases if bool(case.get("joined_replay_case"))]
    route_context_holds = [
        case
        for case in audited_cases
        if case.get("classification") == "route_context_hold"
    ]
    heading_candidates = [
        case
        for case in audited_cases
        if case.get("classification") == "heading_relaxation_candidate"
    ]
    return {
        "transfer_case_count": len(transfer_cases),
        "false_hold_count": len(audited_cases),
        "joined_false_hold_count": len(joined),
        "stable_recovery_count": sum(
            case.get("perturbation_label") == "stable_recovery" for case in joined
        ),
        "no_exit_to_linked_chain_count": sum(
            case.get("selected_route_status") == "no_exit_lanes"
            and case.get("alternate_route_status") == "linked_lane_chain"
            for case in joined
        ),
        "heading_relaxation_candidate_count": len(heading_candidates),
        "route_context_hold_count": len(route_context_holds),
        "mean_selected_terminal_deficit_m": _mean_metric(
            joined, "selected_terminal_deficit_m"
        ),
        "mean_route_extension_m": _mean_metric(joined, "route_extension_m"),
        "mean_replay_gain_m": _mean_metric(joined, "replay_gain_m"),
    }


def _recommendation(cases: list[dict[str, object]]) -> str:
    heading_candidates = [
        case
        for case in cases
        if case.get("classification") == "heading_relaxation_candidate"
    ]
    route_context_holds = [
        case for case in cases if case.get("classification") == "route_context_hold"
    ]
    if heading_candidates and route_context_holds:
        return (
            "Keep the default selector unchanged. Move the borderline "
            "heading-relaxation case into the next diagnostic validation queue, "
            "but keep the severe heading-disagreement case held for route, lane "
            "direction, and coordinate-frame inspection."
        )
    if heading_candidates:
        return (
            "Keep the default selector unchanged, but test the heading-relaxed "
            "candidate on a broader replay queue with more held negatives."
        )
    return (
        "Do not relax selector gates from this audit alone. The remaining false "
        "holds need route/context inspection or broader replay evidence first."
    )


def _context_labels(
    selected_heading: float | None,
    alternate_heading: float | None,
    transfer_heading_gate: float,
    diagnostic_heading_gate: float,
    selected_route_status: str,
    alternate_route_status: str,
    selected_terminal_deficit: float | None,
    alternate_link_extension: float | None,
    stable_recovery: bool,
) -> list[str]:
    labels: list[str] = []
    if selected_route_status == "no_exit_lanes":
        labels.append("selected_terminal_no_exit")
    if alternate_route_status == "linked_lane_chain":
        labels.append("alternate_linked_chain")
    if selected_terminal_deficit is not None and selected_terminal_deficit > 0.0:
        labels.append("selected_route_shorter_than_horizon")
    if alternate_link_extension is not None and alternate_link_extension > 0.0:
        labels.append("alternate_chain_extends_route")
    if stable_recovery:
        labels.append("stable_replay_recovery")
    if (
        selected_heading is not None
        and alternate_heading is not None
        and selected_heading >= diagnostic_heading_gate
        and alternate_heading >= diagnostic_heading_gate
        and (
            selected_heading < transfer_heading_gate
            or alternate_heading < transfer_heading_gate
        )
    ):
        labels.append("within_diagnostic_heading_gate")
    if selected_heading is not None and selected_heading < 0.5:
        labels.append("selected_heading_disagreement")
    return labels


def _classification(
    selected_heading: float | None,
    alternate_heading: float | None,
    diagnostic_heading_gate: float,
    stable_recovery: bool,
) -> str:
    if (
        selected_heading is not None
        and alternate_heading is not None
        and selected_heading >= diagnostic_heading_gate
        and alternate_heading >= diagnostic_heading_gate
        and stable_recovery
    ):
        return "heading_relaxation_candidate"
    if selected_heading is not None and selected_heading < 0.5:
        return "route_context_hold"
    return "needs_more_evidence"


def _context_read(classification: str) -> str:
    if classification == "heading_relaxation_candidate":
        return "Stable linked-chain recovery; only the strict heading gate blocks promotion."
    if classification == "route_context_hold":
        return "Stable replay recovery but selected-lane heading disagrees severely, so route context wins over gate relaxation."
    return "Derived metrics are insufficient for a bounded selector change."


def _next_action(classification: str) -> str:
    if classification == "heading_relaxation_candidate":
        return "Retest a heading-relaxed selector with more replay-held negatives before changing defaults."
    if classification == "route_context_hold":
        return "Audit lane direction, route context, and coordinate alignment before any heading relaxation."
    return "Collect more replay evidence before changing selector gates."


def _case_key(case: dict[str, object]) -> tuple[str, str]:
    return (str(case.get("scenario_id", "")), str(case.get("track_id", "")))


def _field(
    primary: dict[str, object] | None,
    fallback: dict[str, object],
    key: str,
    default: object | None = None,
) -> object | None:
    if primary is not None and key in primary:
        return primary[key]
    if key in fallback:
        return fallback[key]
    return default


def _required_float(mapping: dict[str, object], key: str) -> float:
    value = _optional_float(mapping.get(key))
    if value is None:
        raise ValueError(f"Missing numeric selector policy field: {key}.")
    return value


def _nonnegative_difference(
    left: float | None,
    right: float | None,
) -> float | None:
    if left is None or right is None:
        return None
    return round(max(0.0, left - right), 3)


def _mean_metric(cases: list[dict[str, object]], key: str) -> float | None:
    values = [
        value
        for case in cases
        if (value := _optional_float(case.get(key))) is not None
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"
