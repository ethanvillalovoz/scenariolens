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
from scenariolens.lane_continuation_terminal_neighborhood_selector_calibration import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
)

LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT = (
    "scenariolens.lane_continuation_terminal_neighborhood_selector_transfer.v1"
)

SELECTOR_TRANSFER_POLICY_SOURCES = ("recommended", "current")


@dataclass(frozen=True)
class LaneContinuationTerminalNeighborhoodSelectorTransferResult:
    """Files produced by a terminal-neighborhood selector transfer run."""

    ready: bool
    validation_case_count: int
    overlap_case_count: int
    novel_case_count: int
    transfer_match_count: int
    transfer_false_promote_count: int
    transfer_false_hold_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_terminal_neighborhood_selector_transfer(
    selector_calibration_manifest_path: str | Path,
    terminal_neighborhood_replay_manifest_path: str | Path,
    output_dir: str | Path,
    policy_source: str = "recommended",
    public_report_path: str | Path | None = None,
) -> LaneContinuationTerminalNeighborhoodSelectorTransferResult:
    """Validate a calibrated selector policy on a broader replay queue."""

    source = Path(selector_calibration_manifest_path)
    replay_source = Path(terminal_neighborhood_replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_terminal_neighborhood_selector_transfer_payload(
        selector_calibration_manifest_path=source,
        terminal_neighborhood_replay_manifest_path=replay_source,
        output_dir=target,
        policy_source=policy_source,
    )
    report = lane_continuation_terminal_neighborhood_selector_transfer_markdown(
        payload
    )
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    transfer = _required_mapping(payload, "transfer_policy_result")
    transfer_aggregate = _required_mapping(transfer, "aggregate")
    validation = _required_mapping(payload, "validation_scope")
    return LaneContinuationTerminalNeighborhoodSelectorTransferResult(
        ready=bool(payload["ready"]),
        validation_case_count=int(validation["validation_case_count"]),
        overlap_case_count=int(validation["overlap_case_count"]),
        novel_case_count=int(validation["novel_case_count"]),
        transfer_match_count=int(
            transfer_aggregate["selector_replay_gate_match_count"]
        ),
        transfer_false_promote_count=int(
            transfer_aggregate["selector_false_promote_count"]
        ),
        transfer_false_hold_count=int(transfer_aggregate["selector_false_hold_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_terminal_neighborhood_selector_transfer_payload(
    selector_calibration_manifest_path: Path,
    terminal_neighborhood_replay_manifest_path: Path,
    output_dir: Path,
    policy_source: str = "recommended",
) -> dict[str, object]:
    """Return transfer validation data for a calibrated selector policy."""

    if policy_source not in SELECTOR_TRANSFER_POLICY_SOURCES:
        raise ValueError(
            "policy-source must be one of: "
            f"{', '.join(SELECTOR_TRANSFER_POLICY_SOURCES)}."
        )
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
    replay = json.loads(
        terminal_neighborhood_replay_manifest_path.read_text(encoding="utf-8")
    )
    if replay.get("format") != LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT:
        raise ValueError(
            "Expected a terminal-neighborhood replay manifest with format "
            f"{LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT}."
        )

    training_cases = _training_cases(calibration)
    training_keys = _case_keys(training_cases)
    validation_replay_cases = [
        case for case in _required_list(replay, "cases") if isinstance(case, dict)
    ]
    transfer_policy = _policy_from_calibration(
        calibration=calibration,
        policy_source=policy_source,
    )
    current_policy = _current_policy(calibration)
    current_result = _evaluate_policy(
        replay_cases=validation_replay_cases,
        policy=current_policy,
        policy_label="current_default",
        training_keys=training_keys,
    )
    transfer_result = _evaluate_policy(
        replay_cases=validation_replay_cases,
        policy=transfer_policy,
        policy_label=f"{policy_source}_transfer",
        training_keys=training_keys,
    )
    validation_cases = _required_list(transfer_result, "cases")
    overlap_cases = [
        case
        for case in validation_cases
        if isinstance(case, dict)
        and case.get("validation_split") == "overlap_with_calibration"
    ]
    novel_cases = [
        case
        for case in validation_cases
        if isinstance(case, dict) and case.get("validation_split") == "novel_case"
    ]
    transfer_aggregate = _required_mapping(transfer_result, "aggregate")
    recommendation = _recommendation(
        transfer_aggregate=transfer_aggregate,
        novel_case_count=len(novel_cases),
    )
    return {
        "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
        "selector_calibration_manifest": str(selector_calibration_manifest_path),
        "selector_calibration_format": calibration.get("format"),
        "terminal_neighborhood_replay_manifest": str(
            terminal_neighborhood_replay_manifest_path
        ),
        "terminal_neighborhood_replay_format": replay.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(calibration.get("ready"))
        and bool(replay.get("ready"))
        and bool(validation_replay_cases),
        "policy_source": policy_source,
        "training_scope": _training_scope(calibration, training_cases),
        "validation_scope": {
            "validation_case_count": len(validation_replay_cases),
            "overlap_case_count": len(overlap_cases),
            "novel_case_count": len(novel_cases),
            "replay_gate_accepted_count": _required_mapping(
                replay, "aggregate"
            ).get("accepted_case_count"),
            "replay_gate_held_count": _required_mapping(replay, "aggregate").get(
                "held_case_count"
            ),
            "perturbation_trial_count": _required_mapping(replay, "aggregate").get(
                "perturbation_trial_count"
            ),
        },
        "current_policy_result": current_result,
        "transfer_policy_result": transfer_result,
        "overlap_aggregate": _aggregate_cases(
            [case for case in overlap_cases if isinstance(case, dict)]
        ),
        "novel_aggregate": _aggregate_cases(
            [case for case in novel_cases if isinstance(case, dict)]
        ),
        "recommendation": recommendation,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Terminal-neighborhood selector transfer validation applies a "
            "calibrated threshold policy to a separate replay manifest. "
            "Replay labels are used only as validation labels after the "
            "selector decision. It does not change the default scorer, publish "
            "raw map geometry, or claim Waymo benchmark performance."
        ),
    }


def lane_continuation_terminal_neighborhood_selector_transfer_markdown(
    payload: dict[str, object],
) -> str:
    """Return public-safe Markdown for selector transfer validation."""

    training = _required_mapping(payload, "training_scope")
    validation = _required_mapping(payload, "validation_scope")
    current = _required_mapping(payload, "current_policy_result")
    transfer = _required_mapping(payload, "transfer_policy_result")
    current_policy = _required_mapping(current, "policy")
    transfer_policy = _required_mapping(transfer, "policy")
    current_aggregate = _required_mapping(current, "aggregate")
    transfer_aggregate = _required_mapping(transfer, "aggregate")
    overlap_aggregate = _required_mapping(payload, "overlap_aggregate")
    novel_aggregate = _required_mapping(payload, "novel_aggregate")
    cases = _required_list(transfer, "cases")

    lines = [
        "# ScenarioLens Terminal-Neighborhood Selector Transfer Validation",
        "",
        "This report applies a terminal-neighborhood selector policy calibrated "
        "on one replay queue to a broader replay manifest. The goal is to test "
        "whether the policy transfers without false promotions, not to change "
        "ScenarioLens default behavior.",
        "",
        "The validation is intentionally narrow. It is not a route planner, "
        "not a learned policy, not closed-loop simulation, and not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Calibration manifest: `{payload['selector_calibration_manifest']}`",
        f"- Validation replay manifest: `{payload['terminal_neighborhood_replay_manifest']}`",
        f"- Policy source: {payload['policy_source']}",
        f"- Ready for transfer validation: {payload['ready']}",
        f"- Calibration training cases: {training['training_case_count']}",
        f"- Validation cases: {validation['validation_case_count']}",
        f"- Overlap with calibration queue: {validation['overlap_case_count']}",
        f"- Novel validation cases: {validation['novel_case_count']}",
        f"- Validation replay-gate accepted cases: {validation['replay_gate_accepted_count']}",
        f"- Validation replay-gate held cases: {validation['replay_gate_held_count']}",
        f"- Perturbation trials behind validation labels: {validation['perturbation_trial_count']}",
        "- Raw scenario data committed: no",
        "- Raw map geometry published: no",
        "",
        "## Policy Transfer Summary",
        "",
        "| Metric | Current default on validation | Transferred policy on validation |",
        "| --- | ---: | ---: |",
        f"| Max alternate distance | {_meter_text(current_policy['max_alternate_distance_m'])} | {_meter_text(transfer_policy['max_alternate_distance_m'])} |",
        f"| Minimum heading alignment | {_score_text(current_policy['min_heading_alignment'])} | {_score_text(transfer_policy['min_heading_alignment'])} |",
        f"| Minimum route extension | {_meter_text(current_policy['min_route_extension_m'])} | {_meter_text(transfer_policy['min_route_extension_m'])} |",
        f"| Selector promotions | {current_aggregate['selector_promote_count']} | {transfer_aggregate['selector_promote_count']} |",
        f"| Selector holds | {current_aggregate['selector_hold_count']} | {transfer_aggregate['selector_hold_count']} |",
        f"| Replay-gate matches | {current_aggregate['selector_replay_gate_match_count']} | {transfer_aggregate['selector_replay_gate_match_count']} |",
        f"| False promotions | {current_aggregate['selector_false_promote_count']} | {transfer_aggregate['selector_false_promote_count']} |",
        f"| False holds | {current_aggregate['selector_false_hold_count']} | {transfer_aggregate['selector_false_hold_count']} |",
        f"| Mean promoted replay gain | {_signed_meter_text(current_aggregate['mean_promoted_replay_gain_m'])} | {_signed_meter_text(transfer_aggregate['mean_promoted_replay_gain_m'])} |",
        "",
        "## Split Summary",
        "",
        "| Split | Cases | Matches | False promotions | False holds |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| Calibration overlap | {overlap_aggregate['case_count']} | {overlap_aggregate['selector_replay_gate_match_count']} | {overlap_aggregate['selector_false_promote_count']} | {overlap_aggregate['selector_false_hold_count']} |",
        f"| Novel validation cases | {novel_aggregate['case_count']} | {novel_aggregate['selector_replay_gate_match_count']} | {novel_aggregate['selector_false_promote_count']} | {novel_aggregate['selector_false_hold_count']} |",
        "",
        "## Validation Decisions",
        "",
        "| Rank | Split | Scenario | Track | Replay gate | Current default | Transferred policy | Transfer match | Replay gain | Distance | Heading min | Route extension | Hold flags |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if not cases:
        lines.append(
            "| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |"
        )
    current_decisions = _decision_index(_required_list(current, "cases"))
    for case in cases:
        assert isinstance(case, dict)
        key = (str(case.get("scenario_id")), str(case.get("track_id")))
        current_case = current_decisions.get(key, {})
        lines.append(
            "| "
            f"{case['rank']} | "
            f"{_split_label(case['validation_split'])} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{case['replay_gate_label']} | "
            f"{_decision_text(current_case)} | "
            f"{_decision_text(case)} | "
            f"{case['selector_gate_match_label']} | "
            f"{_signed_meter_text(case['replay_gain_m'])} | "
            f"{_meter_text(case['alternate_lane_distance_m'])} | "
            f"{_score_text(case['minimum_heading_alignment'])} | "
            f"{_meter_text(case['route_extension_m'])} | "
            f"{_hold_flags_text(case)} |"
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
            *[
                f"- {line}"
                for line in _interpretation_lines(
                    transfer_aggregate=transfer_aggregate,
                    novel_aggregate=novel_aggregate,
                )
            ],
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _policy_from_calibration(
    calibration: dict[str, object],
    policy_source: str,
) -> dict[str, object]:
    if policy_source == "recommended":
        source = _required_mapping(calibration, "recommended_policy")
    else:
        source = _required_mapping(calibration, "current_policy")
    return {
        "max_alternate_distance_m": _required_float(
            source, "max_alternate_distance_m"
        ),
        "min_heading_alignment": _required_float(source, "min_heading_alignment"),
        "min_route_extension_m": _required_float(source, "min_route_extension_m"),
        "require_chain_extension": True,
    }


def _current_policy(calibration: dict[str, object]) -> dict[str, object]:
    source = calibration.get("current_policy")
    if isinstance(source, dict):
        return _policy_from_calibration(calibration, "current")
    return {
        "max_alternate_distance_m": DEFAULT_MAX_ALTERNATE_DISTANCE_M,
        "min_heading_alignment": DEFAULT_MIN_HEADING_ALIGNMENT,
        "min_route_extension_m": DEFAULT_MIN_ROUTE_EXTENSION_M,
        "require_chain_extension": True,
    }


def _evaluate_policy(
    replay_cases: list[dict[str, object]],
    policy: dict[str, object],
    policy_label: str,
    training_keys: set[tuple[str, str]],
) -> dict[str, object]:
    max_distance = _required_float(policy, "max_alternate_distance_m")
    min_heading = _required_float(policy, "min_heading_alignment")
    min_route = _required_float(policy, "min_route_extension_m")
    cases = []
    for replay_case in replay_cases:
        case = _selector_case(
            replay_case=replay_case,
            max_alternate_distance_m=max_distance,
            min_heading_alignment=min_heading,
            min_route_extension_m=min_route,
        )
        key = (str(case.get("scenario_id")), str(case.get("track_id")))
        case["validation_split"] = (
            "overlap_with_calibration" if key in training_keys else "novel_case"
        )
        cases.append(case)
    return {
        "policy_label": policy_label,
        "policy": {
            "max_alternate_distance_m": round(max_distance, 3),
            "min_heading_alignment": round(min_heading, 3),
            "min_route_extension_m": round(min_route, 3),
            "require_chain_extension": True,
        },
        "aggregate": _aggregate_cases(cases),
        "cases": cases,
    }


def _training_cases(calibration: dict[str, object]) -> list[dict[str, object]]:
    cases = [
        case
        for case in _required_list(calibration, "cases")
        if isinstance(case, dict)
    ]
    if cases:
        return cases
    recommended = _required_mapping(calibration, "recommended_policy")
    return [
        case
        for case in _required_list(recommended, "cases")
        if isinstance(case, dict)
    ]


def _training_scope(
    calibration: dict[str, object],
    training_cases: list[dict[str, object]],
) -> dict[str, object]:
    aggregate = _required_mapping(calibration, "aggregate")
    current = _required_mapping(calibration, "current_policy_result")
    recommended = _required_mapping(calibration, "recommended_policy")
    return {
        "training_case_count": len(training_cases),
        "training_ready_case_count": aggregate.get("ready_case_count"),
        "training_policy_count": aggregate.get("policy_count"),
        "training_replay_gate_accepted_count": aggregate.get(
            "replay_gate_accepted_count"
        ),
        "training_replay_gate_held_count": aggregate.get("replay_gate_held_count"),
        "training_current_false_promote_count": current.get("false_promote_count"),
        "training_current_false_hold_count": current.get("false_hold_count"),
        "training_recommended_false_promote_count": recommended.get(
            "false_promote_count"
        ),
        "training_recommended_false_hold_count": recommended.get("false_hold_count"),
    }


def _case_keys(cases: list[dict[str, object]]) -> set[tuple[str, str]]:
    return {
        (str(case.get("scenario_id")), str(case.get("track_id"))) for case in cases
    }


def _decision_index(cases: list[object]) -> dict[tuple[str, str], dict[str, object]]:
    index: dict[tuple[str, str], dict[str, object]] = {}
    for case in cases:
        if isinstance(case, dict):
            index[(str(case.get("scenario_id")), str(case.get("track_id")))] = case
    return index


def _recommendation(
    transfer_aggregate: dict[str, object],
    novel_case_count: int,
) -> str:
    false_promotes = int(transfer_aggregate.get("selector_false_promote_count", 0) or 0)
    false_holds = int(transfer_aggregate.get("selector_false_hold_count", 0) or 0)
    matches = int(transfer_aggregate.get("selector_replay_gate_match_count", 0) or 0)
    cases = int(transfer_aggregate.get("case_count", 0) or 0)
    if false_promotes > 0:
        return (
            "Do not adopt the transferred selector policy. It creates false "
            "promotions on this validation queue, so the next step is to "
            "inspect those cases and add stronger route/context gates."
        )
    if false_holds > 0:
        return (
            "Keep the default selector unchanged. The transferred policy keeps "
            "false promotions at zero on this queue but still leaves false "
            f"holds, including validation coverage over {novel_case_count} "
            "novel case(s). Treat it as a diagnostic candidate for the next "
            "expanded queue, not a default-policy change."
        )
    return (
        "The transferred policy matches all validation replay labels on this "
        f"{cases}-case queue ({matches}/{cases}) with zero false promotions. "
        "Keep it provisional until a larger holdout queue adds more negative "
        "controls and shard diversity."
    )


def _interpretation_lines(
    transfer_aggregate: dict[str, object],
    novel_aggregate: dict[str, object],
) -> list[str]:
    false_promotes = int(transfer_aggregate.get("selector_false_promote_count", 0) or 0)
    false_holds = int(transfer_aggregate.get("selector_false_hold_count", 0) or 0)
    novel_false_promotes = int(
        novel_aggregate.get("selector_false_promote_count", 0) or 0
    )
    lines = [
        "The transferred selector is evaluated against replay-gate labels only after it makes geometry-only decisions.",
        "Overlap and novel-case counts are reported so this is not mistaken for a fully independent benchmark.",
    ]
    if false_promotes == 0:
        lines.append(
            "Zero false promotions preserves the conservative safety posture on this validation queue."
        )
    else:
        lines.append(
            f"{false_promotes} false promotion(s) mean the policy needs stronger guards before any broader rollout."
        )
    if false_holds > 0:
        lines.append(
            f"{false_holds} false hold(s) remain, so the result supports continued calibration work rather than default adoption."
        )
    if novel_false_promotes == 0:
        lines.append(
            "Novel validation cases did not introduce false promotions, which is useful transfer evidence but still small-sample."
        )
    return lines


def _required_float(mapping: dict[str, object], key: str) -> float:
    value = _optional_float(mapping.get(key))
    if value is None:
        raise ValueError(f"Missing numeric selector policy field: {key}.")
    return value


def _score_text(value: object) -> str:
    number = _optional_float(value)
    return "n/a" if number is None else f"{number:.3f}"


def _decision_text(case: dict[str, object]) -> str:
    if not case:
        return "n/a"
    return "promote" if bool(case.get("selector_promotes")) else "hold"


def _hold_flags_text(case: dict[str, object]) -> str:
    flags = [
        str(flag)
        for flag in case.get("selector_hold_flags", [])
        if isinstance(flag, str)
    ]
    return ", ".join(flags) if flags else "none"


def _split_label(value: object) -> str:
    if value == "overlap_with_calibration":
        return "overlap"
    if value == "novel_case":
        return "novel"
    return str(value)
