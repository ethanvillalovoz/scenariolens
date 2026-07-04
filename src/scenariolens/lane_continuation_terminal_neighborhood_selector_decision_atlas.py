from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_selection import (
    _meter_text,
    _required_list,
    _required_mapping,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_terminal_neighborhood_casebook import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_candidate_validation import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas.v1"
)


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorDecisionAtlasResult:
    """Files produced by a terminal-neighborhood selector decision atlas run."""

    ready: bool
    case_count: int
    visual_asset_count: int
    candidate_match_count: int
    recovered_false_hold_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None
    demo_json_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_decision_atlas(
    casebook_manifest_path: str | Path,
    candidate_validation_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
    demo_json_path: str | Path | None = None,
    demo_assets_dir: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorDecisionAtlasResult:
    """Generate a public-safe selector decision atlas and optional demo payload."""

    casebook_source = Path(casebook_manifest_path)
    candidate_source = Path(candidate_validation_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None
    copied_demo_path = Path(demo_json_path) if demo_json_path else None

    payload = lane_continuation_terminal_neighborhood_selector_decision_atlas_payload(
        casebook_manifest_path=casebook_source,
        candidate_validation_manifest_path=candidate_source,
        output_dir=target,
        asset_base_path="assets",
        report_path=(
            _relative_report_path(copied_report_path)
            if copied_report_path is not None
            else None
        ),
    )
    report = lane_continuation_terminal_neighborhood_selector_decision_atlas_markdown(
        payload
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    _copy_case_assets(payload, source_root=casebook_source.parent, assets_dir=target / "assets")

    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        _copy_case_assets(
            payload,
            source_root=casebook_source.parent,
            assets_dir=copied_report_path.parent / "assets",
        )
        copied_report_path.write_text(report, encoding="utf-8")

    if copied_demo_path is not None:
        assets_dir = Path(demo_assets_dir) if demo_assets_dir else copied_demo_path.parent / "assets"
        demo_asset_base = os.path.relpath(assets_dir, start=copied_demo_path.parent)
        demo_payload = (
            lane_continuation_terminal_neighborhood_selector_decision_atlas_payload(
                casebook_manifest_path=casebook_source,
                candidate_validation_manifest_path=candidate_source,
                output_dir=target,
                asset_base_path=demo_asset_base,
                report_path=payload.get("report_path"),
            )
        )
        copied_demo_path.parent.mkdir(parents=True, exist_ok=True)
        _copy_case_assets(
            demo_payload,
            source_root=casebook_source.parent,
            assets_dir=assets_dir,
        )
        _write_json(copied_demo_path, demo_payload)

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationTerminalNeighborhoodSelectorDecisionAtlasResult(
        ready=bool(payload["ready"]),
        case_count=int(aggregate["case_count"]),
        visual_asset_count=int(aggregate["visual_asset_count"]),
        candidate_match_count=int(aggregate["candidate_match_count"]),
        recovered_false_hold_count=int(aggregate["recovered_false_hold_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
        demo_json_path=copied_demo_path,
    )


def lane_continuation_terminal_neighborhood_selector_decision_atlas_payload(
    casebook_manifest_path: Path,
    candidate_validation_manifest_path: Path,
    output_dir: Path,
    asset_base_path: str = "assets",
    report_path: str | None = None,
) -> dict[str, object]:
    """Return public-safe selector decision cards joined to candidate validation."""

    casebook = json.loads(casebook_manifest_path.read_text(encoding="utf-8"))
    if (
        casebook.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector casebook manifest with "
            f"format {LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT}."
        )
    candidate = json.loads(
        candidate_validation_manifest_path.read_text(encoding="utf-8")
    )
    if (
        candidate.get("format")
        != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT
    ):
        raise ValueError(
            "Expected a terminal-neighborhood selector candidate-validation "
            "manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT}."
        )

    casebook_cases = [
        case
        for case in _required_list(casebook, "cases")
        if isinstance(case, dict)
    ]
    candidate_cases = {
        _case_key(case): case
        for case in _required_list(candidate, "cases")
        if isinstance(case, dict)
    }
    cases = [
        _atlas_case(
            casebook_case=case,
            candidate_case=_candidate_case(candidate_cases, case),
            asset_base_path=asset_base_path,
        )
        for case in casebook_cases
    ]
    aggregate = _aggregate_cases(
        cases=cases,
        candidate_aggregate=_required_mapping(candidate, "aggregate"),
        casebook_aggregate=_required_mapping(casebook, "aggregate"),
    )
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT,
        "casebook_manifest": str(casebook_manifest_path),
        "casebook_format": casebook.get("format"),
        "candidate_validation_manifest": str(candidate_validation_manifest_path),
        "candidate_validation_format": candidate.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(casebook.get("ready")) and bool(candidate.get("ready")) and bool(cases),
        "study": "Terminal-neighborhood selector decision atlas",
        "report_path": report_path
        or "../reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md",
        "casebook_report_path": (
            "../reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md"
        ),
        "candidate_validation_report_path": (
            "../reports/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md"
        ),
        "asset_base_path": asset_base_path,
        "source_scope": {
            "casebook": casebook.get("source_scope", {}),
            "candidate_validation": candidate.get("source_scope", {}),
        },
        "candidate_policy": candidate.get("candidate_policy", {}),
        "aggregate": aggregate,
        "cases": cases,
        "recommendation": candidate.get("recommendation"),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "assets_dir": "assets",
        },
        "scope_note": (
            "The selector decision atlas joins derived visual casebook cards "
            "with candidate-validation labels. It publishes no raw Waymo "
            "records, trajectories, or map geometry, and it does not change "
            "ScenarioLens default selector behavior."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_decision_atlas_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for selector decision cards."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    category_counts = _required_mapping(aggregate, "category_counts")

    lines = [
        "# ScenarioLens Terminal Selector Decision Atlas",
        "",
        "This atlas connects the 7-card terminal-neighborhood selector casebook "
        "to the candidate-validation outcome for each case. It is meant to be "
        "read visually: every card is a derived metric diagram that explains "
        "whether the candidate policy promotes, holds, recovers, or preserves "
        "a negative control.",
        "",
        "The atlas is intentionally narrow. It is not a default selector "
        "change, not a route planner, not closed-loop simulation, and not a "
        "Waymo benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Casebook manifest: `{payload['casebook_manifest']}`",
        f"- Candidate-validation manifest: `{payload['candidate_validation_manifest']}`",
        f"- Ready for atlas: {payload['ready']}",
        f"- Visual cards: {aggregate['visual_asset_count']}",
        f"- Candidate matches: {aggregate['candidate_match_count']} / {aggregate['case_count']}",
        f"- Candidate false promotions: {aggregate['candidate_false_promote_count']}",
        f"- Candidate false holds: {aggregate['candidate_false_hold_count']}",
        f"- Recovered transfer false holds: {aggregate['recovered_false_hold_count']}",
        f"- Replay-held negatives preserved: {aggregate['negative_control_count']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Category Summary",
        "",
        "| Category | Count | Meaning |",
        "| --- | ---: | --- |",
    ]
    for category, label, meaning in _CATEGORY_ORDER:
        lines.append(
            f"| {label} | {int(category_counts.get(category, 0) or 0)} | {meaning} |"
        )

    lines.extend(
        [
            "",
            "## Decision Index",
            "",
            "| Case | Scenario | Track | Category | Replay | Transfer | Candidate | Gain | Route extension | Visual |",
            "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for case in cases:
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{case['case_label']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{case['decision_label']} | "
            f"{case['replay_label']} | "
            f"`{case['transfer_decision']}` | "
            f"`{case['candidate_decision']}` | "
            f"{_signed_meter_text(case.get('replay_gain_m'))} | "
            f"{_meter_text(case.get('route_extension_m'))} | "
            f"[card]({case['report_asset_path']}) |"
        )

    for case in cases:
        assert isinstance(case, dict)
        hold_flags = _required_list(case, "selector_hold_flags")
        lines.extend(
            [
                "",
                f"## {case['case_label']}: {case['decision_label']}",
                "",
                f"![{case['case_label']} selector diagnostic]({case['report_asset_path']})",
                "",
                f"- Scenario / track: `{case['scenario_id']}` / `{case['track_id']}`",
                f"- Source: `{case['source_name']}`",
                f"- Candidate match: `{case['candidate_match_label']}`",
                f"- Route/context class: `{case['route_context_classification']}`",
                f"- Replay label: `{case['replay_label']}` with {_signed_meter_text(case.get('replay_gain_m'))} nominal gain.",
                f"- Transfer decision: `{case['transfer_decision']}`; candidate decision: `{case['candidate_decision']}`.",
                f"- Heading selected/alternate: {_score_text(case.get('selected_heading_alignment'))} / {_score_text(case.get('alternate_heading_alignment'))}.",
                f"- Route extension: {_meter_text(case.get('route_extension_m'))}.",
                f"- Hold flags: {', '.join(str(flag) for flag in hold_flags) if hold_flags else 'none'}.",
                f"- Rationale: {case['candidate_rationale']}",
                f"- Next validation step: {case['next_validation_step']}",
            ]
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The recovered case is useful because it improves replay-label agreement without broadening the default selector.",
            "- The negative controls are useful because they show the candidate did not promote replay-held regressions.",
            "- The remaining hold is useful because it keeps a severe route/context disagreement out of the promotion set.",
            "- The next stronger validation step is a broader replay queue before changing default scoring behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


_CATEGORY_ORDER = (
    (
        "candidate_recovery",
        "Recovered false hold",
        "The candidate promotes a replay-accepted case that the transfer policy held.",
    ),
    (
        "accepted_recovery",
        "Accepted recovery",
        "The candidate keeps an already promoted replay-accepted recovery.",
    ),
    (
        "negative_control",
        "Negative control",
        "The candidate preserves a replay-held regression as held.",
    ),
    (
        "retained_hold",
        "Retained hold",
        "The candidate holds a replay-accepted case because context is still too risky.",
    ),
    (
        "false_promotion",
        "False promotion",
        "The candidate would promote a replay-held regression.",
    ),
)


def _atlas_case(
    casebook_case: dict[str, object],
    candidate_case: dict[str, object],
    asset_base_path: str,
) -> dict[str, object]:
    asset_name = str(casebook_case.get("asset_name") or Path(str(casebook_case["asset_path"])).name)
    category = _category(candidate_case)
    return {
        "case_label": casebook_case.get("case_label"),
        "rank": candidate_case.get("rank", casebook_case.get("rank")),
        "validation_split": candidate_case.get("validation_split"),
        "scenario_id": casebook_case.get("scenario_id"),
        "track_id": casebook_case.get("track_id"),
        "source_name": casebook_case.get("source_name"),
        "asset_name": asset_name,
        "asset_path": _join_asset_path(asset_base_path, asset_name),
        "report_asset_path": f"assets/{asset_name}",
        "casebook_asset_path": casebook_case.get("asset_path"),
        "category": category,
        "decision_label": _category_label(category),
        "replay_label": candidate_case.get("replay_label"),
        "replay_gate_accepted": candidate_case.get("replay_gate_accepted"),
        "transfer_decision": candidate_case.get("transfer_decision"),
        "candidate_decision": candidate_case.get("candidate_decision"),
        "transfer_match_label": candidate_case.get("transfer_match_label"),
        "candidate_match_label": candidate_case.get("candidate_match_label"),
        "changed_by_candidate": candidate_case.get("changed_by_candidate"),
        "route_context_classification": candidate_case.get(
            "route_context_classification"
        ),
        "context_labels": list(candidate_case.get("context_labels", []) or []),
        "candidate_rationale": candidate_case.get("candidate_rationale"),
        "next_validation_step": candidate_case.get("next_validation_step"),
        "replay_gain_m": candidate_case.get(
            "replay_gain_m", casebook_case.get("replay_gain_m")
        ),
        "route_extension_m": candidate_case.get(
            "route_extension_m", casebook_case.get("route_extension_m")
        ),
        "alternate_lane_distance_m": casebook_case.get("alternate_lane_distance_m"),
        "selected_heading_alignment": candidate_case.get(
            "selected_heading_alignment",
            casebook_case.get("selected_heading_alignment"),
        ),
        "alternate_heading_alignment": candidate_case.get(
            "alternate_heading_alignment",
            casebook_case.get("alternate_heading_alignment"),
        ),
        "minimum_heading_alignment": casebook_case.get("minimum_heading_alignment"),
        "selector_hold_flags": list(casebook_case.get("selector_hold_flags", []) or []),
        "selector_checks": casebook_case.get("selector_checks", {}),
        "case_read": casebook_case.get("case_read"),
    }


def _aggregate_cases(
    cases: list[dict[str, object]],
    candidate_aggregate: dict[str, object],
    casebook_aggregate: dict[str, object],
) -> dict[str, object]:
    category_counts = {
        category: sum(case.get("category") == category for case in cases)
        for category, _, _ in _CATEGORY_ORDER
    }
    return {
        "case_count": len(cases),
        "visual_asset_count": int(casebook_aggregate.get("visual_asset_count", len(cases)) or 0),
        "replay_accepted_count": int(candidate_aggregate.get("replay_accepted_count", 0) or 0),
        "replay_held_count": int(candidate_aggregate.get("replay_held_count", 0) or 0),
        "transfer_match_count": int(candidate_aggregate.get("transfer_match_count", 0) or 0),
        "candidate_match_count": int(candidate_aggregate.get("candidate_match_count", 0) or 0),
        "match_delta": int(candidate_aggregate.get("match_delta", 0) or 0),
        "candidate_false_promote_count": int(candidate_aggregate.get("candidate_false_promote_count", 0) or 0),
        "candidate_false_hold_count": int(candidate_aggregate.get("candidate_false_hold_count", 0) or 0),
        "recovered_false_hold_count": int(candidate_aggregate.get("recovered_false_hold_count", 0) or 0),
        "negative_control_count": int(candidate_aggregate.get("preserved_negative_control_count", 0) or 0),
        "retained_route_context_hold_count": int(candidate_aggregate.get("retained_route_context_hold_count", 0) or 0),
        "candidate_promote_count": int(candidate_aggregate.get("candidate_promote_count", 0) or 0),
        "candidate_hold_count": int(candidate_aggregate.get("candidate_hold_count", 0) or 0),
        "category_counts": category_counts,
    }


def _candidate_case(
    candidate_cases: dict[tuple[str, str], dict[str, object]],
    casebook_case: dict[str, object],
) -> dict[str, object]:
    key = _case_key(casebook_case)
    candidate_case = candidate_cases.get(key)
    if candidate_case is None:
        raise ValueError(
            "Candidate-validation manifest is missing case "
            f"{key[0]} / track {key[1]} from the selector casebook."
        )
    return candidate_case


def _category(candidate_case: dict[str, object]) -> str:
    replay_accepted = bool(candidate_case.get("replay_gate_accepted"))
    candidate_promotes = bool(candidate_case.get("candidate_promotes"))
    changed = bool(candidate_case.get("changed_by_candidate"))
    if not replay_accepted and candidate_promotes:
        return "false_promotion"
    if replay_accepted and changed and candidate_promotes:
        return "candidate_recovery"
    if replay_accepted and candidate_promotes:
        return "accepted_recovery"
    if not replay_accepted and not candidate_promotes:
        return "negative_control"
    return "retained_hold"


def _category_label(category: str) -> str:
    for value, label, _ in _CATEGORY_ORDER:
        if value == category:
            return label
    return category.replace("_", " ")


def _copy_case_assets(
    payload: dict[str, object],
    source_root: Path,
    assets_dir: Path,
) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    for case in _required_list(payload, "cases"):
        assert isinstance(case, dict)
        source_asset = source_root / str(case["casebook_asset_path"])
        target_asset = assets_dir / str(case["asset_name"])
        if not source_asset.exists():
            raise FileNotFoundError(f"Missing selector casebook asset: {source_asset}")
        shutil.copyfile(source_asset, target_asset)


def _relative_report_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return os.path.relpath(path, start=Path("docs/demo"))
    except ValueError:
        return str(path)


def _case_key(case: dict[str, object]) -> tuple[str, str]:
    return str(case.get("scenario_id")), str(case.get("track_id"))


def _join_asset_path(asset_base_path: str, asset_name: str) -> str:
    base = asset_base_path.strip("/")
    return f"{base}/{asset_name}" if base else asset_name


def _score_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"
