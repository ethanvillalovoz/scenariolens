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
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ERROR_AUDIT_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_error_audit.v1"
)


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorErrorAuditResult:
    """Files produced by a terminal-neighborhood selector error audit."""

    ready: bool
    case_count: int
    false_hold_count: int
    false_promote_count: int
    counterfactual_policy_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_error_audit(
    selector_transfer_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorErrorAuditResult:
    """Generate a public-safe audit of selector transfer errors."""

    source = Path(selector_transfer_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_selector_error_audit_payload(
        selector_transfer_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_terminal_neighborhood_selector_error_audit_markdown(
        payload
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodSelectorErrorAuditResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        false_hold_count=int(aggregate["false_hold_count"]),
        false_promote_count=int(aggregate["false_promote_count"]),
        counterfactual_policy_count=len(
            _required_list(payload, "counterfactual_policies")
        ),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_error_audit_payload(
    selector_transfer_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return selector transfer error diagnostics and counterfactual gates."""

    transfer = json.loads(selector_transfer_manifest_path.read_text(encoding="utf-8"))
    if (
        transfer.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector transfer manifest with "
            f"format {LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT}."
        )

    transfer_result = _required_mapping(transfer, "transfer_policy_result")
    transfer_policy = _required_mapping(transfer_result, "policy")
    cases = [
        case
        for case in _required_list(transfer_result, "cases")
        if isinstance(case, dict)
    ]
    counterfactuals = _counterfactual_sweep(
        cases=cases,
        transfer_policy=transfer_policy,
    )
    false_hold_cases = [
        _diagnosed_false_hold(case)
        for case in cases
        if case.get("selector_gate_match_label") == "false_hold"
    ]
    false_promote_cases = [
        _diagnosed_false_promote(case)
        for case in cases
        if case.get("selector_gate_match_label") == "false_promote"
    ]
    aggregate = _aggregate_errors(
        cases=cases,
        false_hold_cases=false_hold_cases,
        false_promote_cases=false_promote_cases,
    )
    recommendation = _recommendation(
        false_hold_cases=false_hold_cases,
        false_promote_cases=false_promote_cases,
        counterfactuals=counterfactuals,
    )
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ERROR_AUDIT_FORMAT,
        "selector_transfer_manifest": str(selector_transfer_manifest_path),
        "selector_transfer_format": transfer.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(transfer.get("ready")) and bool(cases),
        "source_scope": {
            "training_scope": transfer.get("training_scope", {}),
            "validation_scope": transfer.get("validation_scope", {}),
        },
        "transfer_policy": transfer_policy,
        "aggregate": aggregate,
        "false_hold_cases": false_hold_cases,
        "false_promote_cases": false_promote_cases,
        "counterfactual_policies": counterfactuals,
        "recommendation": recommendation,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Selector error audit uses only derived transfer-validation "
            "metrics and replay labels. It does not publish raw Waymo records, "
            "trajectory points, or map polylines, and it does not change the "
            "default selector."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_error_audit_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for selector transfer error diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    transfer_policy = _required_mapping(payload, "transfer_policy")
    source_scope = _required_mapping(payload, "source_scope")
    validation_scope = _required_mapping(source_scope, "validation_scope")
    false_holds = _required_list(payload, "false_hold_cases")
    false_promotes = _required_list(payload, "false_promote_cases")
    counterfactuals = _required_list(payload, "counterfactual_policies")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Error Audit",
        "",
        "This audit follows the selector transfer validation by explaining the "
        "remaining false holds and testing small counterfactual selector gates. "
        "It is meant to turn transfer errors into the next evidence queue, not "
        "to tune a default policy from a small sample.",
        "",
        "The audit is intentionally narrow. It is not a route planner, not a "
        "learned model, not closed-loop simulation, and not a Waymo benchmark "
        "claim.",
        "",
        "## Scope",
        "",
        f"- Selector transfer manifest: `{payload['selector_transfer_manifest']}`",
        f"- Ready for error audit: {payload['ready']}",
        f"- Validation cases: {validation_scope.get('validation_case_count')}",
        f"- Novel validation cases: {validation_scope.get('novel_case_count')}",
        f"- Transfer false promotions: {aggregate['false_promote_count']}",
        f"- Transfer false holds: {aggregate['false_hold_count']}",
        f"- Transfer policy heading gate: {_score_text(transfer_policy['min_heading_alignment'])}",
        f"- Transfer policy route-extension gate: {_meter_text(transfer_policy['min_route_extension_m'])}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Error Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| False promotions | {aggregate['false_promote_count']} |",
        f"| False holds | {aggregate['false_hold_count']} |",
        f"| Novel false holds | {aggregate['novel_false_hold_count']} |",
        f"| Overlap false holds | {aggregate['overlap_false_hold_count']} |",
        f"| False holds with heading blockers | {aggregate['heading_blocked_false_hold_count']} |",
        f"| False holds with route-extension blockers | {aggregate['route_blocked_false_hold_count']} |",
        f"| Mean false-hold replay gain | {_signed_meter_text(aggregate['mean_false_hold_gain_m'])} |",
        "",
        "## Counterfactual Gate Sweep",
        "",
        "| Policy | Heading gate | Route gate | Promotions | Matches | False promotions | False holds | Note |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for policy in counterfactuals:
        assert isinstance(policy, dict)
        lines.append(
            "| "
            f"{policy['policy_label']} | "
            f"{_score_text(policy['min_heading_alignment'])} | "
            f"{_meter_text(policy['min_route_extension_m'])} | "
            f"{policy['selector_promote_count']} | "
            f"{policy['selector_replay_gate_match_count']} | "
            f"{policy['false_promote_count']} | "
            f"{policy['false_hold_count']} | "
            f"{policy['diagnostic_note']} |"
        )

    lines.extend(
        [
            "",
            "## False-Hold Diagnosis",
            "",
            "| Rank | Split | Scenario | Track | Replay gain | Heading min | Route extension | Blocking gates | Diagnosis | Next action |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    if not false_holds:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in false_holds:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"{_split_label(case['validation_split'])} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{_signed_meter_text(case['replay_gain_m'])} | "
            f"{_score_text(case['minimum_heading_alignment'])} | "
            f"{_meter_text(case['route_extension_m'])} | "
            f"{case['blocking_gates']} | "
            f"{case['diagnosis']} | "
            f"{case['next_action']} |"
        )

    lines.extend(
        [
            "",
            "## False-Promotion Diagnosis",
            "",
            "| Rank | Split | Scenario | Track | Replay gain | Blocking issue | Next action |",
            "| ---: | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    if not false_promotes:
        lines.append("| n/a | n/a | n/a | n/a | n/a | none | none |")
    for case in false_promotes:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['rank']} | "
            f"{_split_label(case['validation_split'])} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{_signed_meter_text(case['replay_gain_m'])} | "
            f"{case['diagnosis']} | "
            f"{case['next_action']} |"
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
            "- Counterfactual policies are evaluated against the same derived replay labels; they are not trained on raw trajectory data.",
            "- A counterfactual that reduces false holds is still only a diagnostic candidate until more replay-held negatives are added.",
            "- Severe heading disagreement should trigger route/context inspection before relaxing heading gates globally.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _counterfactual_sweep(
    cases: list[dict[str, object]],
    transfer_policy: dict[str, object],
) -> list[dict[str, object]]:
    max_distance = _required_float(transfer_policy, "max_alternate_distance_m")
    route_gate = _required_float(transfer_policy, "min_route_extension_m")
    heading_gate = _required_float(transfer_policy, "min_heading_alignment")
    policies = [
        ("transferred_policy", heading_gate, route_gate),
        ("relax_heading_to_0.90", 0.90, route_gate),
        ("relax_heading_to_0.70", 0.70, route_gate),
        ("relax_route_to_25m", heading_gate, 25.0),
        ("relax_heading_0.70_route_25m", 0.70, 25.0),
    ]
    return [
        _evaluate_counterfactual_policy(
            cases=cases,
            policy_label=label,
            max_alternate_distance_m=max_distance,
            min_heading_alignment=heading,
            min_route_extension_m=route,
        )
        for label, heading, route in policies
    ]


def _evaluate_counterfactual_policy(
    cases: list[dict[str, object]],
    policy_label: str,
    max_alternate_distance_m: float,
    min_heading_alignment: float,
    min_route_extension_m: float,
) -> dict[str, object]:
    decisions = [
        _counterfactual_decision(
            case=case,
            max_alternate_distance_m=max_alternate_distance_m,
            min_heading_alignment=min_heading_alignment,
            min_route_extension_m=min_route_extension_m,
        )
        for case in cases
    ]
    false_promotes = [
        decision for decision in decisions if decision["match_label"] == "false_promote"
    ]
    false_holds = [
        decision for decision in decisions if decision["match_label"] == "false_hold"
    ]
    matches = [
        decision for decision in decisions if bool(decision["matches_replay_gate"])
    ]
    promotions = [
        decision for decision in decisions if bool(decision["selector_promotes"])
    ]
    return {
        "policy_label": policy_label,
        "max_alternate_distance_m": round(max_alternate_distance_m, 3),
        "min_heading_alignment": round(min_heading_alignment, 3),
        "min_route_extension_m": round(min_route_extension_m, 3),
        "selector_promote_count": len(promotions),
        "selector_replay_gate_match_count": len(matches),
        "false_promote_count": len(false_promotes),
        "false_hold_count": len(false_holds),
        "diagnostic_note": _counterfactual_note(
            false_promote_count=len(false_promotes),
            false_hold_count=len(false_holds),
        ),
    }


def _counterfactual_decision(
    case: dict[str, object],
    max_alternate_distance_m: float,
    min_heading_alignment: float,
    min_route_extension_m: float,
) -> dict[str, object]:
    ready = bool(case.get("ready", True))
    alternate_distance = _optional_float(case.get("alternate_lane_distance_m"))
    selected_heading = _optional_float(case.get("selected_heading_alignment"))
    alternate_heading = _optional_float(case.get("alternate_heading_alignment"))
    route_extension = _optional_float(case.get("route_extension_m"))
    chain_extended = bool(case.get("chain_extended"))
    replay_accepted = bool(case.get("replay_gate_accepted"))
    selector_promotes = (
        ready
        and alternate_distance is not None
        and alternate_distance <= max_alternate_distance_m
        and selected_heading is not None
        and selected_heading >= min_heading_alignment
        and alternate_heading is not None
        and alternate_heading >= min_heading_alignment
        and route_extension is not None
        and route_extension >= min_route_extension_m
        and chain_extended
    )
    return {
        "selector_promotes": selector_promotes,
        "matches_replay_gate": selector_promotes == replay_accepted,
        "match_label": _match_label(selector_promotes, replay_accepted),
    }


def _diagnosed_false_hold(case: dict[str, object]) -> dict[str, object]:
    hold_flags = [
        str(flag)
        for flag in case.get("selector_hold_flags", [])
        if isinstance(flag, str)
    ]
    return {
        "rank": int(case.get("rank", 0) or 0),
        "validation_split": str(case.get("validation_split", "")),
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "replay_gain_m": _optional_float(case.get("replay_gain_m")),
        "minimum_heading_alignment": _optional_float(
            case.get("minimum_heading_alignment")
        ),
        "route_extension_m": _optional_float(case.get("route_extension_m")),
        "alternate_lane_distance_m": _optional_float(
            case.get("alternate_lane_distance_m")
        ),
        "blocking_flags": hold_flags,
        "blocking_gates": ", ".join(hold_flags) if hold_flags else "none",
        "diagnosis": _false_hold_diagnosis(case, hold_flags),
        "next_action": _false_hold_next_action(case, hold_flags),
    }


def _diagnosed_false_promote(case: dict[str, object]) -> dict[str, object]:
    return {
        "rank": int(case.get("rank", 0) or 0),
        "validation_split": str(case.get("validation_split", "")),
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "replay_gain_m": _optional_float(case.get("replay_gain_m")),
        "diagnosis": "selector promoted a replay-held alternate",
        "next_action": "Add stricter route/context guards before considering any policy relaxation.",
    }


def _aggregate_errors(
    cases: list[dict[str, object]],
    false_hold_cases: list[dict[str, object]],
    false_promote_cases: list[dict[str, object]],
) -> dict[str, object]:
    false_hold_gains = [
        value
        for case in false_hold_cases
        if (value := _optional_float(case.get("replay_gain_m"))) is not None
    ]
    return {
        "case_count": len(cases),
        "false_promote_count": len(false_promote_cases),
        "false_hold_count": len(false_hold_cases),
        "novel_false_hold_count": sum(
            case.get("validation_split") == "novel_case"
            for case in false_hold_cases
        ),
        "overlap_false_hold_count": sum(
            case.get("validation_split") == "overlap_with_calibration"
            for case in false_hold_cases
        ),
        "heading_blocked_false_hold_count": sum(
            _has_heading_blocker(case) for case in false_hold_cases
        ),
        "route_blocked_false_hold_count": sum(
            "route_extension_below_gate" in case.get("blocking_flags", [])
            for case in false_hold_cases
        ),
        "mean_false_hold_gain_m": _mean(false_hold_gains),
    }


def _recommendation(
    false_hold_cases: list[dict[str, object]],
    false_promote_cases: list[dict[str, object]],
    counterfactuals: list[dict[str, object]],
) -> str:
    if false_promote_cases:
        return (
            "Do not relax selector gates. False promotions are already present, "
            "so the next step is stricter route/context guards and more "
            "replay-held negative coverage."
        )
    zero_false_promote = [
        policy
        for policy in counterfactuals
        if int(policy.get("false_promote_count", 0) or 0) == 0
    ]
    best = sorted(
        zero_false_promote,
        key=lambda policy: (
            int(policy.get("false_hold_count", 0) or 0),
            -int(policy.get("selector_replay_gate_match_count", 0) or 0),
        ),
    )[0]
    if int(best.get("false_hold_count", 0) or 0) < len(false_hold_cases):
        return (
            f"Keep the default selector unchanged, but use `{best['policy_label']}` "
            "as the next diagnostic candidate. It reduces false holds without "
            "adding false promotions on this small transfer queue, while the "
            "remaining severe heading case needs route/context inspection."
        )
    return (
        "Keep the current transfer policy as a conservative diagnostic. The "
        "tested counterfactuals do not reduce false holds without adding risk, "
        "so the next work is broader evidence rather than gate relaxation."
    )


def _false_hold_diagnosis(case: dict[str, object], hold_flags: list[str]) -> str:
    heading = _optional_float(case.get("minimum_heading_alignment"))
    if _has_heading_flag(hold_flags) and heading is not None and heading < 0.5:
        return "severe heading disagreement"
    if _has_heading_flag(hold_flags):
        return "borderline heading gate miss"
    if "route_extension_below_gate" in hold_flags:
        return "route-extension gate miss"
    return "non-heading selector hold"


def _false_hold_next_action(case: dict[str, object], hold_flags: list[str]) -> str:
    heading = _optional_float(case.get("minimum_heading_alignment"))
    if _has_heading_flag(hold_flags) and heading is not None and heading < 0.5:
        return "Audit lane direction, route context, and coordinate alignment before relaxing heading gates."
    if _has_heading_flag(hold_flags):
        return "Try a heading-relaxed candidate on a larger validation queue with replay-held negatives."
    if "route_extension_below_gate" in hold_flags:
        return "Broaden route-extension calibration only if false-promotion coverage grows."
    return "Add more replay evidence before changing selector gates."


def _counterfactual_note(
    false_promote_count: int,
    false_hold_count: int,
) -> str:
    if false_promote_count:
        return "reject: introduces false promotions"
    if false_hold_count:
        return "diagnostic only: false holds remain"
    return "diagnostic candidate: no transfer errors on this queue"


def _match_label(selector_promotes: bool, replay_accepted: bool) -> str:
    if selector_promotes and replay_accepted:
        return "true_positive_recovery"
    if selector_promotes and not replay_accepted:
        return "false_promote"
    if not selector_promotes and replay_accepted:
        return "false_hold"
    return "true_hold"


def _required_float(mapping: dict[str, object], key: str) -> float:
    value = _optional_float(mapping.get(key))
    if value is None:
        raise ValueError(f"Missing numeric selector policy field: {key}.")
    return value


def _has_heading_blocker(case: dict[str, object]) -> bool:
    return _has_heading_flag(
        [
            str(flag)
            for flag in case.get("blocking_flags", [])
            if isinstance(flag, str)
        ]
    )


def _has_heading_flag(flags: list[str]) -> bool:
    return any("heading" in flag for flag in flags)


def _split_label(value: object) -> str:
    if value == "overlap_with_calibration":
        return "overlap"
    if value == "novel_case":
        return "novel"
    return str(value)


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)
