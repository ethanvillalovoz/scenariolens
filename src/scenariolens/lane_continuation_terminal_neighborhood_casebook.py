from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from scenariolens.lane_continuation_branch_selection import (
    _chain_text,
    _meter_text,
    _optional_float,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector import (
    _HOLD_DECISION,
    _PROMOTE_DECISION,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_calibration import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_casebook.v1"
)


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodCasebookResult:
    """Files produced by a terminal-neighborhood selector casebook run."""

    ready: bool
    case_count: int
    asset_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_casebook(
    selector_calibration_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodCasebookResult:
    """Generate a public-safe visual casebook from selector calibration output."""

    source = Path(selector_calibration_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_casebook_payload(
        selector_calibration_manifest_path=source,
        output_dir=target,
    )
    report = lane_continuation_terminal_neighborhood_casebook_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")

    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        _write_case_card_assets(
            cases=_required_list(payload, "cases"),
            assets_dir=copied_report_path.parent / "assets",
        )
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodCasebookResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        asset_count=int(aggregate["visual_asset_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_casebook_payload(
    selector_calibration_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return public-safe casebook data and write local derived SVG cards."""

    calibration = json.loads(
        selector_calibration_manifest_path.read_text(encoding="utf-8")
    )
    if (
        calibration.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector calibration manifest "
            "with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT}."
        )

    raw_cases = [
        case
        for case in _required_list(calibration, "cases")
        if isinstance(case, dict)
    ]
    cases = [_casebook_case(case, index + 1) for index, case in enumerate(raw_cases)]
    assets_dir = output_dir / "assets"
    _write_case_card_assets(cases=cases, assets_dir=assets_dir)

    current = _required_mapping(calibration, "current_policy_result")
    recommended = _required_mapping(calibration, "recommended_policy")
    aggregate = _casebook_aggregate(
        cases=cases,
        calibration_aggregate=_required_mapping(calibration, "aggregate"),
        current_policy_result=current,
        recommended_policy=recommended,
    )
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
        "selector_calibration_manifest": str(selector_calibration_manifest_path),
        "selector_calibration_format": calibration.get("format"),
        "terminal_neighborhood_replay_manifest": calibration.get(
            "terminal_neighborhood_replay_manifest"
        ),
        "terminal_neighborhood_audit_manifest": calibration.get(
            "terminal_neighborhood_audit_manifest"
        ),
        "topology_manifest": calibration.get("topology_manifest"),
        "output_dir": str(output_dir),
        "assets_dir": "assets",
        "ready": bool(calibration.get("ready")) and bool(cases),
        "source_scope": calibration.get("source_scope", {}),
        "current_policy": calibration.get("current_policy", {}),
        "recommended_policy": _policy_summary(recommended),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "assets_dir": "assets",
        },
        "scope_note": (
            "The terminal-neighborhood selector casebook is a visual diagnostic "
            "built only from derived replay and calibration metrics. It does "
            "not publish raw Waymo records, raw trajectories, or raw map "
            "geometry, and it is not a Waymo benchmark claim."
        ),
    }


def lane_continuation_terminal_neighborhood_casebook_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for terminal-neighborhood selector cases."""

    aggregate = _required_mapping(payload, "aggregate")
    source_scope = _required_mapping(payload, "source_scope")
    current = _required_mapping(payload, "current_policy")
    recommended = _required_mapping(payload, "recommended_policy")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Casebook",
        "",
        "This casebook turns the expanded terminal-neighborhood replay and "
        "selector-calibration queue into six visual decision cards. Each card "
        "explains why a nearby lane alternate is promoted or held using only "
        "derived metrics: replay gain, route extension, heading alignment, "
        "alternate-lane distance, and selector gate outcomes.",
        "",
        "It is intentionally narrow: this is not a route planner, not a "
        "default scorer change, and not a Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Selector calibration manifest: `{payload['selector_calibration_manifest']}`",
        f"- Terminal-neighborhood replay manifest: `{payload['terminal_neighborhood_replay_manifest']}`",
        f"- Terminal-neighborhood audit manifest: `{payload['terminal_neighborhood_audit_manifest']}`",
        f"- Topology manifest: `{payload['topology_manifest']}`",
        f"- Ready for casebook: {payload['ready']}",
        f"- Replay cases: {source_scope.get('replay_case_count')}",
        f"- Replay-gate accepted cases: {source_scope.get('accepted_case_count')}",
        f"- Replay-gate held cases: {source_scope.get('held_case_count')}",
        f"- Policy candidates swept: {aggregate['policy_count']}",
        f"- Visual cards: {aggregate['visual_asset_count']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "- Visual cards are derived metric diagrams, not trajectory or map overlays.",
        "",
        "## Decision Summary",
        "",
        "| Metric | Current | Recommended |",
        "| --- | ---: | ---: |",
        f"| Max alternate distance | {_meter_text(current.get('max_alternate_distance_m'))} | {_meter_text(recommended.get('max_alternate_distance_m'))} |",
        f"| Minimum heading alignment | {_score_text(current.get('min_heading_alignment'))} | {_score_text(recommended.get('min_heading_alignment'))} |",
        f"| Minimum route extension | {_meter_text(current.get('min_route_extension_m'))} | {_meter_text(recommended.get('min_route_extension_m'))} |",
        f"| Promoted candidates | {aggregate['current_promote_count']} | {aggregate['recommended_promote_count']} |",
        f"| Held candidates | {aggregate['current_hold_count']} | {aggregate['recommended_hold_count']} |",
        f"| Replay-gate matches | {aggregate['current_match_count']} | {aggregate['recommended_match_count']} |",
        f"| False promotions | {aggregate['current_false_promote_count']} | {aggregate['recommended_false_promote_count']} |",
        f"| False holds | {aggregate['current_false_hold_count']} | {aggregate['recommended_false_hold_count']} |",
        "",
        "## Case Index",
        "",
        "| Case | Scenario | Track | Replay gate | Current | Recommended | Gain | Route extension | Visual |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['case_label']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['replay_gate_label']}` | "
            f"`{case['current_decision']}` | "
            f"`{case['recommended_decision']}` | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{_meter_text(case.get('route_extension_m'))} | "
            f"[card]({case['asset_path']}) |"
        )

    for case in cases:
        assert isinstance(case, dict)
        checks = _required_mapping(case, "selector_checks")
        flags = _required_list(case, "selector_hold_flags")
        lines.extend(
            [
                "",
                f"## {case['case_label']}: `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"![{case['case_label']} selector diagnostic]({case['asset_path']})",
                "",
                f"- Source: `{case['source_name']}`",
                f"- Decision read: {case['case_read']}",
                f"- Replay label: **{case['replay_gate_label']}** with {_signed_meter_text(case.get('replay_gain_m'))} nominal gain.",
                f"- Current selector: **{case['current_decision']}**; recommended calibration: **{case['recommended_decision']}**.",
                f"- Selected chain: {_chain_text(case.get('selected_chain'))}; alternate chain: {_chain_text(case.get('alternate_chain'))}.",
                f"- Alternate distance / heading min / route extension: {_meter_text(case.get('alternate_lane_distance_m'))} / {_score_text(case.get('minimum_heading_alignment'))} / {_meter_text(case.get('route_extension_m'))}.",
                f"- Hold flags: {', '.join(str(flag) for flag in flags) if flags else 'none'}.",
                f"- Next action: {case['next_action']}",
                "",
                "Selector checks:",
                "",
                "| Check | Passed |",
                "| --- | --- |",
                f"| Alternate distance gate | {checks.get('alternate_distance_ok')} |",
                f"| Selected heading gate | {checks.get('selected_heading_ok')} |",
                f"| Alternate heading gate | {checks.get('alternate_heading_ok')} |",
                f"| Route-extension gate | {checks.get('route_extension_ok')} |",
                f"| Chain-extension gate | {checks.get('chain_extension_ok')} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The three promoted cases are replay-accepted recoveries under the recommended calibration, not default production behavior.",
            "- The three held cases are useful negative controls: low heading alignment, short route extension, or too much alternate-lane distance prevents over-promotion.",
            "- The visual cards make the selector failure modes inspectable without committing raw Waymo trajectories or map geometry.",
            "- The next stronger validation step is to broaden terminal-neighborhood replay coverage across more shards before changing default scoring behavior.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _casebook_case(case: dict[str, object], index: int) -> dict[str, object]:
    current_decision = str(case.get("current_decision", "not_evaluable"))
    recommended_decision = str(case.get("recommended_decision", "not_evaluable"))
    replay_accepted = bool(case.get("replay_gate_accepted"))
    changed = bool(case.get("changed_by_recommendation"))
    return {
        "case_label": f"Case {index:02d}",
        "asset_name": f"terminal_selector_casebook_{index:02d}.svg",
        "asset_path": f"assets/terminal_selector_casebook_{index:02d}.svg",
        "rank": int(case.get("rank", 0) or 0),
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "source_name": str(case.get("source_name", "")),
        "ready": bool(case.get("ready")),
        "selected_feature_id": str(case.get("selected_feature_id", "")),
        "alternate_feature_id": str(case.get("alternate_feature_id", "")),
        "selected_chain": case.get("selected_chain", []),
        "alternate_chain": case.get("alternate_chain", []),
        "selected_link_count": int(case.get("selected_link_count", 0) or 0),
        "alternate_link_count": int(case.get("alternate_link_count", 0) or 0),
        "selected_lane_distance_m": case.get("selected_lane_distance_m"),
        "alternate_lane_distance_m": case.get("alternate_lane_distance_m"),
        "selected_heading_alignment": case.get("selected_heading_alignment"),
        "alternate_heading_alignment": case.get("alternate_heading_alignment"),
        "minimum_heading_alignment": case.get("minimum_heading_alignment"),
        "selected_route_remaining_m": case.get("selected_route_remaining_m"),
        "alternate_route_remaining_m": case.get("alternate_route_remaining_m"),
        "route_extension_m": case.get("route_extension_m"),
        "chain_extended": bool(case.get("chain_extended")),
        "replay_gain_m": case.get("replay_gain_m"),
        "replay_gate_label": str(case.get("replay_gate_label", "")),
        "replay_gate_accepted": replay_accepted,
        "selector_hold_flags": case.get("selector_hold_flags", []),
        "selector_checks": case.get("selector_checks", {}),
        "current_decision": current_decision,
        "recommended_decision": recommended_decision,
        "current_match_label": case.get("current_match_label"),
        "recommended_match_label": case.get("recommended_match_label"),
        "changed_by_recommendation": changed,
        "case_read": _case_read(
            replay_accepted=replay_accepted,
            current_decision=current_decision,
            recommended_decision=recommended_decision,
            changed=changed,
            replay_gain_m=_optional_float(case.get("replay_gain_m")),
        ),
        "next_action": _next_action(
            replay_accepted=replay_accepted,
            current_decision=current_decision,
            recommended_decision=recommended_decision,
            changed=changed,
        ),
    }


def _case_read(
    replay_accepted: bool,
    current_decision: str,
    recommended_decision: str,
    changed: bool,
    replay_gain_m: float | None,
) -> str:
    if replay_accepted and current_decision == _PROMOTE_DECISION:
        return "Clean recovery: current gates already promote the replay-accepted alternate."
    if replay_accepted and changed and recommended_decision == _PROMOTE_DECISION:
        return (
            "Calibration recovery: the current route-extension gate held a "
            "replay-accepted alternate that the recommended gate would promote."
        )
    if not replay_accepted and recommended_decision == _HOLD_DECISION:
        if replay_gain_m is not None and replay_gain_m < 0.0:
            return "Negative control: replay regressed, and the selector correctly keeps the case held."
        return "Guarded hold: replay did not justify promotion, and calibration keeps the case held."
    if recommended_decision == _PROMOTE_DECISION:
        return "Promotion candidate under the recommended calibration; inspect negative coverage before rollout."
    return "Held for additional route or map-neighborhood context."


def _next_action(
    replay_accepted: bool,
    current_decision: str,
    recommended_decision: str,
    changed: bool,
) -> str:
    if replay_accepted and current_decision == _PROMOTE_DECISION:
        return "Keep as the positive control for future terminal-neighborhood queues."
    if replay_accepted and changed and recommended_decision == _PROMOTE_DECISION:
        return "Retest on broader shards before adopting the relaxed route-extension gate."
    if not replay_accepted and recommended_decision == _HOLD_DECISION:
        return "Keep as negative coverage for selector calibration."
    return "Hold until more terminal-neighborhood replay evidence is available."


def _casebook_aggregate(
    cases: list[dict[str, object]],
    calibration_aggregate: dict[str, object],
    current_policy_result: dict[str, object],
    recommended_policy: dict[str, object],
) -> dict[str, object]:
    current_promotes = [
        case for case in cases if case.get("current_decision") == _PROMOTE_DECISION
    ]
    recommended_promotes = [
        case
        for case in cases
        if case.get("recommended_decision") == _PROMOTE_DECISION
    ]
    ready_cases = [case for case in cases if bool(case.get("ready"))]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready_cases),
        "policy_count": int(calibration_aggregate.get("policy_count", 0) or 0),
        "visual_asset_count": len(cases),
        "replay_gate_accepted_count": sum(
            bool(case.get("replay_gate_accepted")) for case in ready_cases
        ),
        "replay_gate_held_count": sum(
            not bool(case.get("replay_gate_accepted")) for case in ready_cases
        ),
        "current_promote_count": len(current_promotes),
        "current_hold_count": len(ready_cases) - len(current_promotes),
        "recommended_promote_count": len(recommended_promotes),
        "recommended_hold_count": len(ready_cases) - len(recommended_promotes),
        "current_match_count": int(
            current_policy_result.get("selector_replay_gate_match_count", 0) or 0
        ),
        "recommended_match_count": int(
            recommended_policy.get("selector_replay_gate_match_count", 0) or 0
        ),
        "current_false_promote_count": int(
            current_policy_result.get("false_promote_count", 0) or 0
        ),
        "current_false_hold_count": int(
            current_policy_result.get("false_hold_count", 0) or 0
        ),
        "recommended_false_promote_count": int(
            recommended_policy.get("false_promote_count", 0) or 0
        ),
        "recommended_false_hold_count": int(
            recommended_policy.get("false_hold_count", 0) or 0
        ),
        "changed_case_count": sum(
            bool(case.get("changed_by_recommendation")) for case in cases
        ),
    }


def _policy_summary(policy: dict[str, object]) -> dict[str, object]:
    return {
        "max_alternate_distance_m": policy.get("max_alternate_distance_m"),
        "min_heading_alignment": policy.get("min_heading_alignment"),
        "min_route_extension_m": policy.get("min_route_extension_m"),
        "selector_promote_count": policy.get("selector_promote_count"),
        "selector_hold_count": policy.get("selector_hold_count"),
        "selector_replay_gate_match_count": policy.get(
            "selector_replay_gate_match_count"
        ),
        "false_promote_count": policy.get("false_promote_count"),
        "false_hold_count": policy.get("false_hold_count"),
        "recommendation": policy.get("recommendation"),
    }


def _write_case_card_assets(cases: list[object], assets_dir: Path) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        if not isinstance(case, dict):
            continue
        asset_name = str(case.get("asset_name", "terminal_selector_casebook.svg"))
        (assets_dir / asset_name).write_text(_case_card_svg(case), encoding="utf-8")


def _case_card_svg(case: dict[str, object]) -> str:
    width = 920
    height = 520
    gain = _optional_float(case.get("replay_gain_m")) or 0.0
    route_extension = _optional_float(case.get("route_extension_m")) or 0.0
    heading = _optional_float(case.get("minimum_heading_alignment")) or 0.0
    distance = _optional_float(case.get("alternate_lane_distance_m")) or 0.0
    current_promotes = case.get("current_decision") == _PROMOTE_DECISION
    recommended_promotes = case.get("recommended_decision") == _PROMOTE_DECISION
    replay_accepted = bool(case.get("replay_gate_accepted"))
    flags = _required_list(case, "selector_hold_flags")
    flag_text = ", ".join(str(flag) for flag in flags) if flags else "none"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f"<title>{_xml(case['case_label'])} terminal-neighborhood selector diagnostic</title>",
        "<style>",
        ".bg{fill:#f8fafc}.panel{fill:#ffffff;stroke:#cbd5e1;stroke-width:1.5}.muted{fill:#64748b}.text{fill:#0f172a;font:600 20px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.small{fill:#334155;font:500 14px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.tiny{fill:#475569;font:500 12px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.label{fill:#0f172a;font:700 13px system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.chip{fill:#e2e8f0}.promote{fill:#dcfce7}.hold{fill:#fee2e2}.accept{fill:#dbeafe}.barbg{fill:#e2e8f0}.green{fill:#16a34a}.red{fill:#dc2626}.blue{fill:#2563eb}.amber{fill:#d97706}.slate{fill:#64748b}.gate{stroke:#0f172a;stroke-width:2;stroke-dasharray:5 5}",
        "</style>",
        '<rect class="bg" x="0" y="0" width="920" height="520"/>',
        '<rect class="panel" x="24" y="24" width="872" height="472" rx="16"/>',
        f'<text class="text" x="48" y="62">{_xml(case["case_label"])}: scenario {_xml(case["scenario_id"])} / track {_xml(case["track_id"])}</text>',
        f'<text class="small muted" x="48" y="89">Source: {_xml(case["source_name"])}</text>',
        _pill(48, 112, "Replay", "accept" if replay_accepted else "hold", replay_accepted),
        _pill(244, 112, "Current", "promote" if current_promotes else "hold", current_promotes),
        _pill(440, 112, "Recommended", "promote" if recommended_promotes else "hold", recommended_promotes),
        f'<text class="small" x="48" y="184">Selected chain: {_xml(_chain_text(case.get("selected_chain")))}</text>',
        f'<text class="small" x="48" y="208">Alternate chain: {_xml(_chain_text(case.get("alternate_chain")))}</text>',
        f'<text class="small" x="48" y="232">Hold flags: {_xml(flag_text)}</text>',
        _metric_bar(
            x=48,
            y=276,
            width=370,
            label="Route extension",
            value=route_extension,
            max_value=max(250.0, route_extension),
            gate_value=40.0,
            value_text=_meter_text(route_extension),
            gate_text="40.000 m recommended gate",
            color="blue",
        ),
        _metric_bar(
            x=48,
            y=350,
            width=370,
            label="Heading alignment min",
            value=heading,
            max_value=1.0,
            gate_value=0.95,
            value_text=_score_text(heading),
            gate_text="0.950 gate",
            color="green" if heading >= 0.95 else "amber",
        ),
        _metric_bar(
            x=500,
            y=276,
            width=340,
            label="Alternate distance",
            value=distance,
            max_value=max(6.0, distance),
            gate_value=5.0,
            value_text=_meter_text(distance),
            gate_text="5.000 m gate",
            color="green" if distance <= 5.0 else "red",
        ),
        _gain_bar(
            x=500,
            y=350,
            width=340,
            value=gain,
            max_abs=130.0,
            value_text=_signed_meter_text(gain),
        ),
    ]
    lines.extend(_wrapped_svg_text(str(case["case_read"]), x=48, y=454, width=112))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _pill(
    x: int,
    y: int,
    label: str,
    value: str,
    positive: bool,
) -> str:
    klass = "promote" if value == "promote" else "accept" if positive else "hold"
    return (
        f'<g><rect class="{klass}" x="{x}" y="{y}" width="170" height="38" '
        'rx="19"/>'
        f'<text class="tiny" x="{x + 16}" y="{y + 16}">{_xml(label)}</text>'
        f'<text class="label" x="{x + 16}" y="{y + 31}">{_xml(value)}</text></g>'
    )


def _metric_bar(
    x: int,
    y: int,
    width: int,
    label: str,
    value: float,
    max_value: float,
    gate_value: float,
    value_text: str,
    gate_text: str,
    color: str,
) -> str:
    bar_width = _scaled_width(value, max_value, width)
    gate_x = x + _scaled_width(gate_value, max_value, width)
    return "\n".join(
        [
            f'<text class="label" x="{x}" y="{y}">{_xml(label)}</text>',
            f'<rect class="barbg" x="{x}" y="{y + 16}" width="{width}" height="16" rx="8"/>',
            f'<rect class="{color}" x="{x}" y="{y + 16}" width="{bar_width}" height="16" rx="8"/>',
            f'<line class="gate" x1="{gate_x}" y1="{y + 10}" x2="{gate_x}" y2="{y + 38}"/>',
            f'<text class="tiny" x="{x}" y="{y + 54}">{_xml(value_text)}</text>',
            f'<text class="tiny muted" x="{x + width - 150}" y="{y + 54}">{_xml(gate_text)}</text>',
        ]
    )


def _gain_bar(
    x: int,
    y: int,
    width: int,
    value: float,
    max_abs: float,
    value_text: str,
) -> str:
    center = x + width // 2
    half = width // 2
    scaled = min(half, int(round(abs(value) / max_abs * half)))
    if value >= 0.0:
        rect_x = center
        rect_width = scaled
        klass = "green"
    else:
        rect_x = center - scaled
        rect_width = scaled
        klass = "red"
    return "\n".join(
        [
            f'<text class="label" x="{x}" y="{y}">Replay gain</text>',
            f'<rect class="barbg" x="{x}" y="{y + 16}" width="{width}" height="16" rx="8"/>',
            f'<line class="gate" x1="{center}" y1="{y + 10}" x2="{center}" y2="{y + 38}"/>',
            f'<rect class="{klass}" x="{rect_x}" y="{y + 16}" width="{rect_width}" height="16" rx="8"/>',
            f'<text class="tiny" x="{x}" y="{y + 54}">{_xml(value_text)}</text>',
            f'<text class="tiny muted" x="{center + 8}" y="{y + 54}">zero gain</text>',
        ]
    )


def _scaled_width(value: float, max_value: float, width: int) -> int:
    if max_value <= 0.0:
        return 0
    return max(0, min(width, int(round(value / max_value * width))))


def _wrapped_svg_text(text: str, x: int, y: int, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return [
        f'<text class="tiny" x="{x}" y="{y + index * 18}">{_xml(line)}</text>'
        for index, line in enumerate(lines[:2])
    ]


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"


def _xml(value: object) -> str:
    return escape(str(value), {'"': "&quot;"})
