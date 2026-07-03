from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_selection import (
    _chain_text,
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

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector.v1"
)

DEFAULT_MAX_ALTERNATE_DISTANCE_M = 5.0
DEFAULT_MIN_HEADING_ALIGNMENT = 0.95
DEFAULT_MIN_ROUTE_EXTENSION_M = 50.0

_PROMOTE_DECISION = "promote_terminal_neighborhood_alternate"
_HOLD_DECISION = "hold_for_terminal_neighborhood_context"
_NOT_EVALUABLE_DECISION = "not_evaluable"


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorResult:
    """Files produced by a terminal-neighborhood selector experiment run."""

    ready: bool
    case_count: int
    promoted_case_count: int
    held_case_count: int
    replay_gate_match_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector(
    terminal_neighborhood_replay_manifest_path: str | Path,
    output_dir: str | Path,
    max_alternate_distance_m: float = DEFAULT_MAX_ALTERNATE_DISTANCE_M,
    min_heading_alignment: float = DEFAULT_MIN_HEADING_ALIGNMENT,
    min_route_extension_m: float = DEFAULT_MIN_ROUTE_EXTENSION_M,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorResult:
    """Generate a public-safe bounded selector experiment from replay evidence."""

    source = Path(terminal_neighborhood_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_selector_payload(
        terminal_neighborhood_replay_manifest_path=source,
        output_dir=target,
        max_alternate_distance_m=max_alternate_distance_m,
        min_heading_alignment=min_heading_alignment,
        min_route_extension_m=min_route_extension_m,
    )
    report = lane_continuation_terminal_neighborhood_selector_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodSelectorResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        promoted_case_count=int(aggregate["selector_promote_count"]),
        held_case_count=int(aggregate["selector_hold_count"]),
        replay_gate_match_count=int(aggregate["selector_replay_gate_match_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_payload(
    terminal_neighborhood_replay_manifest_path: Path,
    output_dir: Path,
    max_alternate_distance_m: float = DEFAULT_MAX_ALTERNATE_DISTANCE_M,
    min_heading_alignment: float = DEFAULT_MIN_HEADING_ALIGNMENT,
    min_route_extension_m: float = DEFAULT_MIN_ROUTE_EXTENSION_M,
) -> dict[str, object]:
    """Return bounded selector decisions for terminal-neighborhood candidates."""

    if max_alternate_distance_m <= 0.0:
        raise ValueError("max-alternate-distance-m must be positive.")
    if not 0.0 <= min_heading_alignment <= 1.0:
        raise ValueError("min-heading-alignment must be between 0 and 1.")
    if min_route_extension_m <= 0.0:
        raise ValueError("min-route-extension-m must be positive.")

    replay = json.loads(
        terminal_neighborhood_replay_manifest_path.read_text(encoding="utf-8")
    )
    if replay.get("format") != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT:
        raise ValueError(
            "Expected a terminal-neighborhood replay manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT}."
        )

    policy = {
        "description": (
            "Promote a nearby alternate lane only when it is close to the "
            "selected terminal lane, both selected and alternate lane headings "
            "align with the anchor motion, the alternate route adds enough "
            "remaining lane distance, and the alternate chain extends beyond "
            "the selected terminal chain. Replay-gate outcomes are used only "
            "as validation labels after the selector decision is made."
        ),
        "max_alternate_distance_m": round(max_alternate_distance_m, 3),
        "min_heading_alignment": round(min_heading_alignment, 3),
        "min_route_extension_m": round(min_route_extension_m, 3),
        "require_chain_extension": True,
    }
    cases = [
        _selector_case(
            replay_case=case,
            max_alternate_distance_m=max_alternate_distance_m,
            min_heading_alignment=min_heading_alignment,
            min_route_extension_m=min_route_extension_m,
        )
        for case in _required_list(replay, "cases")
        if isinstance(case, dict)
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_FORMAT,
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
        "ready": bool(replay.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "selector_policy": policy,
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
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The terminal-neighborhood selector is a bounded diagnostic policy "
            "over replay-gated nearby-lane candidates. It does not change the "
            "default ScenarioLens scorer, does not publish raw map geometry, "
            "and is not a Waymo benchmark claim."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for the selector experiment."""

    policy = _required_mapping(payload, "selector_policy")
    aggregate = _required_mapping(payload, "aggregate")
    source_scope = _required_mapping(payload, "source_scope")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Experiment",
        "",
        "This experiment turns the accepted terminal-neighborhood replay case "
        "into a bounded, non-oracle selector policy. The selector uses local "
        "geometry and route-extension checks to decide whether a nearby lane "
        "should replace a selected terminal lane; replay-gate labels are used "
        "only afterward to measure agreement.",
        "",
        "The result is intentionally narrow. It is not a route planner, not a "
        "default scorer change, and not a Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Terminal-neighborhood replay manifest: `{payload['terminal_neighborhood_replay_manifest']}`",
        f"- Terminal-neighborhood audit manifest: `{payload['terminal_neighborhood_audit_manifest']}`",
        f"- Topology manifest: `{payload['topology_manifest']}`",
        f"- Ready for selector experiment: {payload['ready']}",
        f"- Replay cases: {source_scope['replay_case_count']}",
        f"- Replayed cases: {source_scope['replayed_case_count']}",
        f"- Replay-gate accepted cases: {source_scope['accepted_case_count']}",
        f"- Replay-gate held cases: {source_scope['held_case_count']}",
        f"- Perturbation trials behind replay labels: {source_scope['perturbation_trial_count']}",
        f"- Max alternate distance: {_meter_text(policy['max_alternate_distance_m'])}",
        f"- Minimum heading alignment: {policy['min_heading_alignment']}",
        f"- Minimum route extension: {_meter_text(policy['min_route_extension_m'])}",
        f"- Chain extension required: {policy['require_chain_extension']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Selector Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Ready cases | {aggregate['ready_case_count']} |",
        f"| Selector promotions | {aggregate['selector_promote_count']} |",
        f"| Selector holds | {aggregate['selector_hold_count']} |",
        f"| Not evaluable | {aggregate['not_evaluable_count']} |",
        f"| Replay-gate accepted | {aggregate['replay_gate_accepted_count']} |",
        f"| Replay-gate held | {aggregate['replay_gate_held_count']} |",
        f"| Selector/replay-gate matches | {aggregate['selector_replay_gate_match_count']} |",
        f"| Selector false promotions | {aggregate['selector_false_promote_count']} |",
        f"| Selector false holds | {aggregate['selector_false_hold_count']} |",
        f"| Mean promoted replay gain | {_signed_meter_text(aggregate['mean_promoted_replay_gain_m'])} |",
        f"| Mean held replay gain | {_signed_meter_text(aggregate['mean_held_replay_gain_m'])} |",
        f"| Mean promoted route extension | {_meter_text(aggregate['mean_promoted_route_extension_m'])} |",
        "",
        "## Selector Decisions",
        "",
        "| Rank | Scenario | Track | Selector | Replay gate | Alternate distance | Heading min | Route extension | Chain extended | Replay gain | First next action |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
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
            f"`{case['selector_label']}` | "
            f"`{case['replay_gate_label']}` | "
            f"{_meter_text(case.get('alternate_lane_distance_m'))} | "
            f"{_score_text(case.get('minimum_heading_alignment'))} | "
            f"{_meter_text(case.get('route_extension_m'))} | "
            f"{case['chain_extended']} | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{case['first_next_action']} |"
        )

    promoted = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("selector_label") == _PROMOTE_DECISION
    ]
    held = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("selector_label") != _PROMOTE_DECISION
    ]
    lines.extend(["", "## Promote Queue", ""])
    if not promoted:
        lines.append("- No candidates currently clear the bounded selector policy.")
    for case in promoted:
        assert isinstance(case, dict)
        lines.append(
            "- "
            f"`{case['scenario_id']}` track `{case['track_id']}`: choose "
            f"alternate lane `{case['selector_selected_feature_id']}` with "
            f"{_signed_meter_text(case.get('replay_gain_m'))} replay gain and "
            f"{_meter_text(case.get('route_extension_m'))} route extension."
        )

    lines.extend(["", "## Hold Queue", ""])
    if not held:
        lines.append("- No candidates are held by the bounded selector policy.")
    for case in held:
        assert isinstance(case, dict)
        flags = _required_list(case, "selector_hold_flags")
        flag_text = ", ".join(str(flag) for flag in flags) if flags else "none"
        lines.append(
            "- "
            f"`{case['scenario_id']}` track `{case['track_id']}`: "
            f"`{case['selector_label']}` because {flag_text}. "
            f"Replay label: `{case['replay_gate_label']}`."
        )

    for case in cases:
        assert isinstance(case, dict)
        checks = _required_mapping(case, "selector_checks")
        flags = _required_list(case, "selector_hold_flags")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Selector label: **{case['selector_label']}**",
                f"- Selector reason: {case['selector_reason']}",
                f"- Replay-gate label: **{case['replay_gate_label']}**",
                f"- Selector matched replay gate: {case['selector_matches_replay_gate']}",
                f"- Selected chain: {_chain_text(case.get('selected_chain'))}",
                f"- Alternate chain: {_chain_text(case.get('alternate_chain'))}",
                f"- Selector-selected chain: {_chain_text(case.get('selector_selected_chain'))}",
                f"- Hold flags: {', '.join(str(flag) for flag in flags) if flags else 'none'}",
                "",
                "Selector checks:",
                "",
                "| Check | Passed | Value | Gate |",
                "| --- | --- | ---: | ---: |",
                f"| Alternate distance | {checks['alternate_distance_ok']} | {_meter_text(case.get('alternate_lane_distance_m'))} | <= {_meter_text(policy['max_alternate_distance_m'])} |",
                f"| Selected heading alignment | {checks['selected_heading_ok']} | {_score_text(case.get('selected_heading_alignment'))} | >= {policy['min_heading_alignment']} |",
                f"| Alternate heading alignment | {checks['alternate_heading_ok']} | {_score_text(case.get('alternate_heading_alignment'))} | >= {policy['min_heading_alignment']} |",
                f"| Route extension | {checks['route_extension_ok']} | {_meter_text(case.get('route_extension_m'))} | >= {_meter_text(policy['min_route_extension_m'])} |",
                f"| Chain extension | {checks['chain_extension_ok']} | {case['chain_extended']} | true |",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Selector promotions are bounded experiment candidates, not default behavior.",
            "- Replay-gate labels validate the selector after the policy decision; they are not used as selector inputs.",
            "- Held cases remain useful because they show which local geometry cues prevent over-promotion.",
            "- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _selector_case(
    replay_case: dict[str, object],
    max_alternate_distance_m: float,
    min_heading_alignment: float,
    min_route_extension_m: float,
) -> dict[str, object]:
    ready = bool(replay_case.get("ready"))
    selected_route_remaining = _optional_float(
        replay_case.get("selected_route_remaining_m")
    )
    alternate_route_remaining = _optional_float(
        replay_case.get("alternate_route_remaining_m")
    )
    route_extension = (
        round(alternate_route_remaining - selected_route_remaining, 3)
        if selected_route_remaining is not None
        and alternate_route_remaining is not None
        else None
    )
    selected_link_count = int(replay_case.get("selected_link_count", 0) or 0)
    alternate_link_count = int(replay_case.get("alternate_link_count", 0) or 0)
    selected_heading = _optional_float(replay_case.get("selected_heading_alignment"))
    alternate_heading = _optional_float(replay_case.get("alternate_heading_alignment"))
    alternate_distance = _optional_float(replay_case.get("alternate_lane_distance_m"))
    replay_decision = _required_mapping(replay_case, "gate_decision")
    replay_accepted = bool(replay_decision.get("accepted"))
    chain_extended = alternate_link_count > selected_link_count
    checks = {
        "alternate_distance_ok": (
            alternate_distance is not None
            and alternate_distance <= max_alternate_distance_m
        ),
        "selected_heading_ok": (
            selected_heading is not None and selected_heading >= min_heading_alignment
        ),
        "alternate_heading_ok": (
            alternate_heading is not None
            and alternate_heading >= min_heading_alignment
        ),
        "route_extension_ok": (
            route_extension is not None and route_extension >= min_route_extension_m
        ),
        "chain_extension_ok": chain_extended,
    }
    hold_flags = _hold_flags(checks)
    selector_promotes = ready and all(bool(value) for value in checks.values())
    if not ready:
        selector_label = _NOT_EVALUABLE_DECISION
        selector_reason = "The replay case is not ready for selector evaluation."
        first_next_action = "Rerun the terminal-neighborhood replay gate after fixing source readiness."
    elif selector_promotes:
        selector_label = _PROMOTE_DECISION
        selector_reason = (
            "The nearby alternate lane is close, heading-aligned, route-extending, "
            "and chain-extending under the bounded selector policy."
        )
        first_next_action = "Evaluate this selector rule on a broader terminal-neighborhood queue."
    else:
        selector_label = _HOLD_DECISION
        selector_reason = (
            "The nearby alternate lane does not clear every bounded selector "
            "check, so it stays held for context before broader rollout."
        )
        first_next_action = "Add richer route, heading, or map-neighborhood context before promotion."

    return {
        "rank": int(replay_case.get("rank", 0) or 0),
        "scenario_id": str(replay_case.get("scenario_id", "")),
        "track_id": str(replay_case.get("track_id", "")),
        "source_name": str(replay_case.get("source_name", "")),
        "ready": ready,
        "selected_feature_id": str(replay_case.get("selected_feature_id", "")),
        "alternate_feature_id": str(replay_case.get("alternate_feature_id", "")),
        "selected_chain": replay_case.get("selected_chain", []),
        "alternate_chain": replay_case.get("alternate_chain", []),
        "selected_link_count": selected_link_count,
        "alternate_link_count": alternate_link_count,
        "selected_lane_distance_m": replay_case.get("selected_lane_distance_m"),
        "alternate_lane_distance_m": alternate_distance,
        "selected_heading_alignment": selected_heading,
        "alternate_heading_alignment": alternate_heading,
        "minimum_heading_alignment": _min_optional(selected_heading, alternate_heading),
        "selected_route_remaining_m": selected_route_remaining,
        "alternate_route_remaining_m": alternate_route_remaining,
        "route_extension_m": route_extension,
        "chain_extended": chain_extended,
        "replay_gain_m": _optional_float(replay_case.get("nominal_gain_m")),
        "replay_gate_label": str(replay_decision.get("label", "")),
        "replay_gate_accepted": replay_accepted,
        "selector_label": selector_label,
        "selector_promotes": selector_promotes,
        "selector_reason": selector_reason,
        "selector_hold_flags": hold_flags,
        "selector_checks": checks,
        "selector_selected_feature_id": (
            str(replay_case.get("alternate_feature_id", ""))
            if selector_promotes
            else str(replay_case.get("selected_feature_id", ""))
        ),
        "selector_selected_chain": (
            replay_case.get("alternate_chain", [])
            if selector_promotes
            else replay_case.get("selected_chain", [])
        ),
        "selector_matches_replay_gate": selector_promotes == replay_accepted,
        "selector_gate_match_label": _match_label(selector_promotes, replay_accepted),
        "first_next_action": first_next_action,
    }


def _hold_flags(checks: dict[str, bool]) -> list[str]:
    names = {
        "alternate_distance_ok": "alternate_too_far",
        "selected_heading_ok": "selected_heading_below_gate",
        "alternate_heading_ok": "alternate_heading_below_gate",
        "route_extension_ok": "route_extension_below_gate",
        "chain_extension_ok": "no_chain_extension",
    }
    return [label for key, label in names.items() if not checks.get(key)]


def _match_label(selector_promotes: bool, replay_accepted: bool) -> str:
    if selector_promotes and replay_accepted:
        return "true_positive_recovery"
    if selector_promotes and not replay_accepted:
        return "false_promote"
    if not selector_promotes and replay_accepted:
        return "false_hold"
    return "true_hold"


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    promoted = [case for case in ready if bool(case.get("selector_promotes"))]
    held = [case for case in ready if not bool(case.get("selector_promotes"))]
    matches = [
        case for case in ready if bool(case.get("selector_matches_replay_gate"))
    ]
    false_promotes = [
        case
        for case in ready
        if case.get("selector_gate_match_label") == "false_promote"
    ]
    false_holds = [
        case for case in ready if case.get("selector_gate_match_label") == "false_hold"
    ]
    promoted_gains = _numeric_values(promoted, "replay_gain_m")
    held_gains = _numeric_values(held, "replay_gain_m")
    promoted_extensions = _numeric_values(promoted, "route_extension_m")
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready),
        "selector_promote_count": len(promoted),
        "selector_hold_count": len(held),
        "not_evaluable_count": len(cases) - len(ready),
        "replay_gate_accepted_count": sum(
            bool(case.get("replay_gate_accepted")) for case in ready
        ),
        "replay_gate_held_count": sum(
            not bool(case.get("replay_gate_accepted")) for case in ready
        ),
        "selector_replay_gate_match_count": len(matches),
        "selector_false_promote_count": len(false_promotes),
        "selector_false_hold_count": len(false_holds),
        "mean_promoted_replay_gain_m": _mean(promoted_gains),
        "mean_held_replay_gain_m": _mean(held_gains),
        "mean_promoted_route_extension_m": _mean(promoted_extensions),
    }


def _numeric_values(cases: list[dict[str, object]], key: str) -> list[float]:
    return [
        value
        for case in cases
        if (value := _optional_float(case.get(key))) is not None
    ]


def _min_optional(first: float | None, second: float | None) -> float | None:
    if first is None or second is None:
        return None
    return round(min(first, second), 3)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"
