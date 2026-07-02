from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
    _chain_text,
    _evaluate_branch_routes,
    _find_scenario,
    _find_track,
    _meter_text,
    _optional_float,
    _optional_int,
    _required_list,
    _required_mapping,
    _resolve_path,
    _signed_meter_text,
    _write_json,
)
from scenariolens.lane_continuation_replay import (
    LANE_CONTINUATION_REPLAY_FORMAT,
    _PERTURBATIONS,
    _perturb_anchor_velocity,
)
from scenariolens.schema import Scenario

LANE_CONTINUATION_BRANCH_REPLAY_FORMAT = (
    "scenariolens.lane_continuation_branch_replay.v1"
)

_MIN_STABLE_GAIN_M = 1.0


@dataclass(frozen=True)
class LaneContinuationBranchReplayResult:
    """Files produced by a motion-context branch replay diagnostic run."""

    ready: bool
    case_count: int
    replayed_case_count: int
    stable_case_count: int
    accepted_case_count: int
    history_speed_prior_accepted_case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_branch_replay(
    branch_selection_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = 5,
    public_report_path: str | Path | None = None,
) -> LaneContinuationBranchReplayResult:
    """Generate a public-safe perturbation replay for motion-context branches."""

    source = Path(branch_selection_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_branch_replay_payload(
        branch_selection_manifest_path=source,
        output_dir=target,
        top=top,
    )
    report = lane_continuation_branch_replay_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationBranchReplayResult(
        ready=bool(payload["ready"]),
        case_count=int(payload["case_count"]),
        replayed_case_count=int(aggregate["replayed_case_count"]),
        stable_case_count=int(aggregate["stable_motion_context_case_count"]),
        accepted_case_count=int(aggregate["accepted_branch_case_count"]),
        history_speed_prior_accepted_case_count=int(
            aggregate["history_speed_prior_accepted_case_count"]
        ),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_branch_replay_payload(
    branch_selection_manifest_path: Path,
    output_dir: Path,
    top: int,
) -> dict[str, object]:
    """Return perturbation replay evidence for motion-context branch choices."""

    if top < 1:
        raise ValueError("top must be at least 1.")

    branch_selection = json.loads(
        branch_selection_manifest_path.read_text(encoding="utf-8")
    )
    if branch_selection.get("format") != LANE_CONTINUATION_BRANCH_SELECTION_FORMAT:
        raise ValueError(
            "Expected a lane-continuation branch-selection manifest with format "
            f"{LANE_CONTINUATION_BRANCH_SELECTION_FORMAT}."
        )

    replay_manifest_path = _resolve_path(
        branch_selection.get("replay_manifest"),
        branch_selection_manifest_path,
    )
    replay = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay.get("format") != LANE_CONTINUATION_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation replay manifest with format "
            f"{LANE_CONTINUATION_REPLAY_FORMAT}."
        )

    replay_cases = {
        (str(case.get("scenario_id")), str(case.get("track_id"))): case
        for case in _required_list(replay, "cases")
        if isinstance(case, dict)
    }
    selected = [
        case
        for case in _required_list(branch_selection, "cases")
        if isinstance(case, dict) and _is_motion_context_replay_candidate(case)
    ][:top]

    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ] = {}
    max_hops = int(branch_selection.get("max_lane_link_hops", 2) or 2)
    replay_max_scenarios = _optional_int(replay.get("max_scenarios_per_source"))
    cases = [
        _branch_replay_case(
            branch_case=case,
            replay_case=replay_cases.get(
                (str(case.get("scenario_id")), str(case.get("track_id")))
            ),
            source_cache=source_cache,
            max_hops=max_hops,
            replay_max_scenarios=replay_max_scenarios,
        )
        for case in selected
    ]
    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
        "branch_selection_manifest": str(branch_selection_manifest_path),
        "branch_selection_format": branch_selection.get("format"),
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(branch_selection.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "top": top,
        "max_lane_link_hops": max_hops,
        "minimum_stable_gain_m": _MIN_STABLE_GAIN_M,
        "acceptance_gate": (
            "Accept a motion-context branch for broader selector rollout only "
            "when every valid perturbation preserves the selected branch and "
            f"keeps recoverable FDE above {_MIN_STABLE_GAIN_M:.1f} m."
        ),
        "history_speed_prior_note": (
            "The history-speed-prior candidate is an experimental replay score "
            "only: it blends anchor speed with recent target speed and does not "
            "change the branch selector or default ScenarioLens metrics."
        ),
        "case_count": len(cases),
        "source_branch_case_count": len(_required_list(branch_selection, "cases")),
        "selected_motion_context_case_count": len(selected),
        "perturbations": list(_PERTURBATIONS),
        "aggregate": aggregate,
        "cases": cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Motion-context branch replay is an open-loop deterministic "
            "diagnostic over parsed lane candidates. It is not a route planner, "
            "not closed-loop simulation, not Waymax/JAX execution, and not a "
            "Waymo benchmark claim."
        ),
    }


def lane_continuation_branch_replay_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for motion-context branch replay diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    perturbations = _required_list(payload, "perturbations")
    cases = _required_list(payload, "cases")

    lines = [
        "# ScenarioLens Motion-Context Branch Replay Diagnostic",
        "",
        "This report takes the non-oracle `motion_context` branch selector from "
        "the lane-continuation branch sweep and replays the selected branch "
        "under deterministic anchor-velocity perturbations. The goal is to "
        "check whether the selector's branch choice and positive FDE gain are "
        "stable when the anchor state is nudged.",
        "",
        "It also reports an experimental `history_speed_prior` candidate for "
        "the same selected branch. That candidate blends anchor speed with "
        "recent target speed during replay scoring only; it does not change "
        "the branch selector, the default baseline, or the public performance "
        "claims.",
        "",
        "The replay still uses open-loop ground-truth future states for scoring. "
        "It is a diagnostic stability check, not a route planner, not "
        "closed-loop simulation, not Waymax/JAX execution, and not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Branch-selection manifest: `{payload['branch_selection_manifest']}`",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Ready for branch replay: {payload['ready']}",
        f"- Motion-context cases selected: {payload['selected_motion_context_case_count']}",
        f"- Perturbations per case: {len(perturbations)}",
        f"- Minimum stable gain: {_meter_text(payload['minimum_stable_gain_m'])}",
        f"- Acceptance gate: {payload['acceptance_gate']}",
        f"- Experimental candidate: {payload['history_speed_prior_note']}",
        "- Raw scenario data committed: no",
        "- Local per-case replay packets committed: no",
        "",
        "## Replay Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Cases analyzed | {aggregate['case_count']} |",
        f"| Replayed cases | {aggregate['replayed_case_count']} |",
        f"| Perturbation trials | {aggregate['perturbation_trial_count']} |",
        f"| Stable motion-context cases | {aggregate['stable_motion_context_case_count']} |",
        f"| Sensitive motion-context cases | {aggregate['sensitive_case_count']} |",
        f"| Branch-preserving trials | {aggregate['branch_preserving_trial_count']} |",
        f"| Positive-gain trials | {aggregate['positive_gain_trial_count']} |",
        f"| Stable positive trials | {aggregate['stable_positive_trial_count']} |",
        f"| Accepted branch cases | {aggregate['accepted_branch_case_count']} |",
        f"| Route-context follow-up cases | {aggregate['route_context_followup_case_count']} |",
        f"| Selector-stability follow-up cases | {aggregate['selector_stability_followup_case_count']} |",
        f"| History speed-prior accepted cases | {aggregate['history_speed_prior_accepted_case_count']} |",
        f"| Margin follow-ups resolved by speed prior | {aggregate['history_speed_prior_resolved_margin_case_count']} |",
        f"| History speed-prior stable positive trials | {aggregate['history_speed_prior_stable_positive_trial_count']} |",
        f"| Mean nominal recoverable FDE | {_signed_meter_text(aggregate['mean_nominal_gain_m'])} |",
        f"| Mean perturbed recoverable FDE | {_signed_meter_text(aggregate['mean_trial_gain_m'])} |",
        f"| Min perturbed recoverable FDE | {_signed_meter_text(aggregate['min_trial_gain_m'])} |",
        f"| Max perturbed recoverable FDE | {_signed_meter_text(aggregate['max_trial_gain_m'])} |",
        f"| Min robustness margin | {_signed_meter_text(aggregate['min_robustness_margin_m'])} |",
        f"| Mean robustness margin | {_signed_meter_text(aggregate['mean_robustness_margin_m'])} |",
        f"| History speed-prior min margin | {_signed_meter_text(aggregate['min_history_speed_prior_margin_m'])} |",
        f"| History speed-prior mean margin | {_signed_meter_text(aggregate['mean_history_speed_prior_margin_m'])} |",
        "",
        "## Perturbations",
        "",
    ]
    for perturbation in perturbations:
        assert isinstance(perturbation, dict)
        lines.append(f"- `{perturbation['label']}`: {perturbation['description']}")

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Rank | Scenario | Track | Default chain | Motion-context chain | Nominal gain | Stable trials | Margin | Speed-prior margin | Acceptance | Speed-prior acceptance | Stability |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    if not cases:
        lines.append(
            "| n/a | n/a | n/a | n/a | n/a | n/a | 0/0 | n/a | n/a | n/a | n/a | n/a |"
        )
    for case in cases:
        assert isinstance(case, dict)
        stability = _required_mapping(case, "perturbation_stability")
        acceptance = _required_mapping(case, "acceptance_decision")
        speed_prior_stability = _required_mapping(
            case,
            "history_speed_prior_stability",
        )
        speed_prior_acceptance = _required_mapping(
            case,
            "history_speed_prior_acceptance_decision",
        )
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"{_chain_text(case.get('default_chain'))} | "
            f"{_chain_text(case.get('motion_context_chain'))} | "
            f"{_signed_meter_text(case.get('nominal_motion_context_gain_m'))} | "
            f"{stability['stable_positive_trial_count']}/"
            f"{stability['valid_trial_count']} | "
            f"{_signed_meter_text(stability.get('robustness_margin_m'))} | "
            f"{_signed_meter_text(speed_prior_stability.get('robustness_margin_m'))} | "
            f"`{acceptance['label']}` | "
            f"`{speed_prior_acceptance['label']}` | "
            f"`{stability['label']}` |"
        )

    for case in cases:
        assert isinstance(case, dict)
        stability = _required_mapping(case, "perturbation_stability")
        acceptance = _required_mapping(case, "acceptance_decision")
        speed_prior_stability = _required_mapping(
            case,
            "history_speed_prior_stability",
        )
        speed_prior_acceptance = _required_mapping(
            case,
            "history_speed_prior_acceptance_decision",
        )
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Diagnosis source: `{case['diagnosis_label']}`",
                f"- Source: `{case['source_name']}`",
                f"- Ready: {case['ready']}",
                f"- Stability: **{stability['label']}**",
                f"- Acceptance: **{acceptance['label']}**",
                f"- History speed-prior acceptance: **{speed_prior_acceptance['label']}**",
                f"- Why it matters: {case['why_it_matters']}",
                f"- Acceptance reason: {acceptance['reason']}",
                f"- Recommended next action: {acceptance['next_action']}",
                f"- Speed-prior reason: {speed_prior_acceptance['reason']}",
                f"- Speed-prior next action: {speed_prior_acceptance['next_action']}",
                "- Default linked-route FDE: "
                f"{_meter_text(case.get('default_fde_m'))}",
                "- Motion-context route FDE: "
                f"{_meter_text(case.get('motion_context_fde_m'))}",
                "- History speed-prior route FDE: "
                f"{_meter_text(case.get('history_speed_prior_fde_m'))}",
                "- Nominal recoverable FDE: "
                f"{_signed_meter_text(case.get('nominal_motion_context_gain_m'))}",
                "- Nominal history speed-prior recoverable FDE: "
                f"{_signed_meter_text(case.get('nominal_history_speed_prior_gain_m'))}",
                "- Branch-preserving trials: "
                f"{stability['branch_preserving_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "- Positive-gain trials: "
                f"{stability['positive_gain_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "- Stable positive trials: "
                f"{stability['stable_positive_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "- Worst perturbation: "
                f"`{stability['worst_trial_label']}`",
                "- Robustness margin: "
                f"{_signed_meter_text(stability.get('robustness_margin_m'))}",
                "- History speed-prior stable positive trials: "
                f"{speed_prior_stability['stable_positive_trial_count']}/"
                f"{speed_prior_stability['valid_trial_count']}",
                "- History speed-prior worst perturbation: "
                f"`{speed_prior_stability['worst_trial_label']}`",
                "- History speed-prior robustness margin: "
                f"{_signed_meter_text(speed_prior_stability.get('robustness_margin_m'))}",
                "",
                "Perturbation trials:",
                "",
                "| Perturbation | Motion-context chain | Gain vs default | Speed-prior gain | Branch preserved | Positive gain | Speed-prior positive | Verdict |",
                "| --- | --- | ---: | ---: | --- | --- | --- | --- |",
            ]
        )
        for trial in _required_list(case, "perturbation_trials"):
            assert isinstance(trial, dict)
            lines.append(
                "| "
                f"`{trial['label']}` | "
                f"{_chain_text(trial.get('motion_context_chain'))} | "
                f"{_signed_meter_text(trial.get('motion_context_gain_m'))} | "
                f"{_signed_meter_text(trial.get('history_speed_prior_gain_m'))} | "
                f"{trial['branch_preserved']} | "
                f"{trial['positive_gain']} | "
                f"{trial['history_speed_prior_positive_gain']} | "
                f"`{trial['verdict']}` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stable motion-context cases preserve the selected branch and keep "
            "positive recoverable FDE across all deterministic perturbations.",
            "- Accepted branch cases pass the stricter rollout gate: branch "
            "preservation plus at least 1.0 m recoverable FDE in every valid "
            "perturbation trial.",
            "- History speed-prior accepted cases show whether a simple "
            "non-oracle speed calibration would clear the same replay gate; "
            "they are candidates for the next selector experiment, not a new "
            "default metric.",
            "- Sensitive cases are still useful: they identify where a "
            "hand-built selector needs richer route context or a learned "
            "candidate scorer.",
            "- The oracle upper bound from the branch-selection report remains "
            "a diagnostic ceiling only; this replay does not use oracle "
            "futures to choose a branch.",
            "- Public outputs stay aggregate and case-summary oriented; raw "
            "Waymo TFRecords and local packets remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_motion_context_replay_candidate(case: dict[str, object]) -> bool:
    gain = _optional_float(case.get("motion_context_recoverable_fde_m"))
    return (
        bool(case.get("ready"))
        and bool(case.get("branchable"))
        and str(case.get("verdict")) == "motion_context_selector_improves"
        and gain is not None
        and gain > _MIN_STABLE_GAIN_M
    )


def _branch_replay_case(
    branch_case: dict[str, object],
    replay_case: dict[str, object] | None,
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
    max_hops: int,
    replay_max_scenarios: int | None,
) -> dict[str, object]:
    rank = int(branch_case.get("rank", 0) or 0)
    scenario_id = str(branch_case.get("scenario_id", ""))
    track_id = str(branch_case.get("track_id", ""))
    base = {
        "rank": rank,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "diagnosis_label": str(branch_case.get("diagnosis_label", "unknown")),
        "source_name": str(branch_case.get("source_name", "")),
        "ready": False,
        "default_chain": [],
        "motion_context_chain": [],
        "default_fde_m": None,
        "motion_context_fde_m": None,
        "history_speed_prior_fde_m": None,
        "nominal_motion_context_gain_m": None,
        "nominal_history_speed_prior_gain_m": None,
        "perturbation_trials": [],
        "perturbation_stability": _empty_stability(),
        "acceptance_decision": _acceptance_decision(_empty_stability()),
        "history_speed_prior_stability": _empty_stability(),
        "history_speed_prior_acceptance_decision": _acceptance_decision(
            _empty_stability()
        ),
        "why_it_matters": "The motion-context branch case could not be replayed.",
    }
    if replay_case is None:
        base["error"] = "replay_case_not_found"
        return base

    source_input = Path(str(replay_case.get("source_input", "")))
    input_format = str(
        replay_case.get(
            "input_format",
            branch_case.get("input_format", "native"),
        )
    )
    source_key = (str(source_input), input_format, replay_max_scenarios)
    if source_key not in source_cache:
        source_cache[source_key] = load_failure_study_input(
            source=source_input,
            input_format=input_format,
            max_scenarios=replay_max_scenarios,
        )
    input_ready, preflight, scenarios = source_cache[source_key]
    scenario = _find_scenario(scenarios, scenario_id)
    if scenario is None:
        base["input_ready"] = input_ready
        base["preflight"] = preflight or {}
        base["error"] = "scenario_not_found_in_loaded_source"
        return base

    track = _find_track(scenario, track_id)
    if track is None:
        base["error"] = "track_not_found"
        return base

    nominal = _evaluate_branch_routes(
        scenario=scenario,
        track=track,
        replay_case=replay_case,
        max_hops=max_hops,
    )
    if not bool(nominal.get("ready")):
        base.update(nominal)
        base["error"] = str(nominal.get("verdict", "not_evaluable"))
        return base

    expected_chain = tuple(
        str(item) for item in nominal.get("motion_context_chain", [])
    )
    nominal_motion_context_route = _selected_motion_context_route(nominal)
    nominal_history_speed_prior_gain = (
        _optional_float(
            nominal_motion_context_route.get(
                "history_speed_prior_gain_vs_default_m"
            )
        )
        if nominal_motion_context_route is not None
        else None
    )
    trials = [
        _perturbation_trial(
            scenario=scenario,
            track_id=track_id,
            replay_case=replay_case,
            max_hops=max_hops,
            expected_chain=expected_chain,
            perturbation=perturbation,
        )
        for perturbation in _PERTURBATIONS
    ]
    stability = _perturbation_stability(
        nominal_gain=nominal.get("motion_context_recoverable_fde_m"),
        expected_chain=expected_chain,
        trials=trials,
    )
    acceptance = _acceptance_decision(stability)
    speed_prior_stability = _history_speed_prior_stability(
        nominal_gain=nominal_history_speed_prior_gain,
        expected_chain=expected_chain,
        trials=trials,
    )
    speed_prior_acceptance = _acceptance_decision(speed_prior_stability)
    base.update(
        {
            "ready": True,
            "source_input": str(source_input),
            "source_name": str(replay_case.get("source_name", source_input.name)),
            "input_format": input_format,
            "input_ready": input_ready,
            "preflight": preflight or {},
            "default_chain": nominal.get("default_chain", []),
            "motion_context_chain": nominal.get("motion_context_chain", []),
            "oracle_chain": nominal.get("oracle_chain", []),
            "default_fde_m": nominal.get("default_fde_m"),
            "motion_context_fde_m": nominal.get("motion_context_fde_m"),
            "history_speed_prior_fde_m": (
                nominal_motion_context_route.get("history_speed_prior_fde_m")
                if nominal_motion_context_route is not None
                else None
            ),
            "history_speed_prior_mps": (
                nominal_motion_context_route.get("history_speed_prior_mps")
                if nominal_motion_context_route is not None
                else None
            ),
            "oracle_fde_m": nominal.get("oracle_fde_m"),
            "nominal_motion_context_gain_m": nominal.get(
                "motion_context_recoverable_fde_m"
            ),
            "nominal_history_speed_prior_gain_m": nominal_history_speed_prior_gain,
            "nominal_oracle_gain_m": nominal.get("oracle_recoverable_fde_m"),
            "perturbation_trials": trials,
            "perturbation_stability": stability,
            "acceptance_decision": acceptance,
            "history_speed_prior_stability": speed_prior_stability,
            "history_speed_prior_acceptance_decision": speed_prior_acceptance,
            "why_it_matters": _why_it_matters(stability, acceptance),
        }
    )
    return base


def _perturbation_trial(
    scenario: Scenario,
    track_id: str,
    replay_case: dict[str, object],
    max_hops: int,
    expected_chain: tuple[str, ...],
    perturbation: dict[str, object],
) -> dict[str, object]:
    perturbed = _perturb_anchor_velocity(
        scenario=scenario,
        track_id=track_id,
        speed_scale=float(perturbation["speed_scale"]),
        heading_delta_deg=float(perturbation["heading_delta_deg"]),
    )
    track = _find_track(perturbed, track_id)
    if track is None:
        return {
            "label": perturbation["label"],
            "speed_scale": perturbation["speed_scale"],
            "heading_delta_deg": perturbation["heading_delta_deg"],
            "ready": False,
            "motion_context_chain": [],
            "motion_context_gain_m": None,
            "branch_preserved": False,
            "positive_gain": False,
            "verdict": "track_not_found",
        }
    evaluation = _evaluate_branch_routes(
        scenario=perturbed,
        track=track,
        replay_case=replay_case,
        max_hops=max_hops,
    )
    chain = tuple(str(item) for item in evaluation.get("motion_context_chain", []))
    gain = _optional_float(evaluation.get("motion_context_recoverable_fde_m"))
    motion_context_route = _selected_motion_context_route(evaluation)
    history_speed_prior_gain = (
        _optional_float(
            motion_context_route.get("history_speed_prior_gain_vs_default_m")
        )
        if motion_context_route is not None
        else None
    )
    branch_preserved = bool(evaluation.get("ready")) and chain == expected_chain
    positive_gain = gain is not None and gain > _MIN_STABLE_GAIN_M
    history_speed_prior_positive_gain = (
        history_speed_prior_gain is not None
        and history_speed_prior_gain > _MIN_STABLE_GAIN_M
    )
    if not bool(evaluation.get("ready")):
        verdict = str(evaluation.get("verdict", "not_evaluable"))
    elif branch_preserved and positive_gain:
        verdict = "stable_positive_motion_context_branch"
    elif branch_preserved:
        verdict = "branch_preserved_gain_sensitive"
    elif positive_gain:
        verdict = "positive_gain_selector_shifted"
    else:
        verdict = "sensitive_to_anchor_perturbation"
    return {
        "label": perturbation["label"],
        "speed_scale": perturbation["speed_scale"],
        "heading_delta_deg": perturbation["heading_delta_deg"],
        "ready": bool(evaluation.get("ready")),
        "default_chain": evaluation.get("default_chain", []),
        "motion_context_chain": evaluation.get("motion_context_chain", []),
        "default_fde_m": evaluation.get("default_fde_m"),
        "motion_context_fde_m": evaluation.get("motion_context_fde_m"),
        "motion_context_gain_m": gain,
        "motion_context_score": _selected_motion_context_score(evaluation),
        "history_speed_prior_fde_m": (
            motion_context_route.get("history_speed_prior_fde_m")
            if motion_context_route is not None
            else None
        ),
        "history_speed_prior_mps": (
            motion_context_route.get("history_speed_prior_mps")
            if motion_context_route is not None
            else None
        ),
        "history_speed_prior_gain_m": history_speed_prior_gain,
        "history_speed_prior_positive_gain": history_speed_prior_positive_gain,
        "branch_preserved": branch_preserved,
        "positive_gain": positive_gain,
        "verdict": verdict,
    }


def _selected_motion_context_score(evaluation: dict[str, object]) -> float | None:
    route = _selected_motion_context_route(evaluation)
    if route is None:
        return None
    return _optional_float(route.get("motion_context_score"))


def _selected_motion_context_route(
    evaluation: dict[str, object],
) -> dict[str, object] | None:
    for route in _required_list(evaluation, "route_candidates"):
        if isinstance(route, dict) and bool(route.get("is_motion_context_selected")):
            return route
    return None


def _perturbation_stability(
    nominal_gain: object,
    expected_chain: tuple[str, ...],
    trials: list[dict[str, object]],
) -> dict[str, object]:
    return _gain_stability(
        nominal_gain=nominal_gain,
        expected_chain=expected_chain,
        trials=trials,
        gain_field="motion_context_gain_m",
        positive_field="positive_gain",
        stable_label="stable_motion_context_branch",
        selector_shifted_label="positive_gain_but_selector_shifted",
        branch_gain_sensitive_label="branch_stable_gain_sensitive",
        sensitive_label="sensitive_to_anchor_perturbation",
    )


def _history_speed_prior_stability(
    nominal_gain: object,
    expected_chain: tuple[str, ...],
    trials: list[dict[str, object]],
) -> dict[str, object]:
    return _gain_stability(
        nominal_gain=nominal_gain,
        expected_chain=expected_chain,
        trials=trials,
        gain_field="history_speed_prior_gain_m",
        positive_field="history_speed_prior_positive_gain",
        stable_label="stable_history_speed_prior_branch",
        selector_shifted_label="history_speed_prior_positive_gain_but_selector_shifted",
        branch_gain_sensitive_label="history_speed_prior_branch_stable_gain_sensitive",
        sensitive_label="history_speed_prior_sensitive_to_anchor_perturbation",
    )


def _gain_stability(
    nominal_gain: object,
    expected_chain: tuple[str, ...],
    trials: list[dict[str, object]],
    gain_field: str,
    positive_field: str,
    stable_label: str,
    selector_shifted_label: str,
    branch_gain_sensitive_label: str,
    sensitive_label: str,
) -> dict[str, object]:
    valid = [trial for trial in trials if bool(trial.get("ready"))]
    gains = [
        gain
        for trial in valid
        if (gain := _optional_float(trial.get(gain_field))) is not None
    ]
    branch_preserving = sum(bool(trial.get("branch_preserved")) for trial in valid)
    positive_gain = sum(bool(trial.get(positive_field)) for trial in valid)
    stable_positive = sum(
        bool(trial.get("branch_preserved")) and bool(trial.get(positive_field))
        for trial in valid
    )
    nominal = _optional_float(nominal_gain)
    max_swing = (
        max(abs(gain - nominal) for gain in gains)
        if gains and nominal is not None
        else None
    )
    min_gain = min(gains) if gains else None
    worst_trial_label = _worst_trial_label(valid, gain_field=gain_field)
    robustness_margin = (
        round(min_gain - _MIN_STABLE_GAIN_M, 3) if min_gain is not None else None
    )
    if not valid:
        label = "not_evaluable"
    elif stable_positive == len(valid):
        label = stable_label
    elif positive_gain == len(valid):
        label = selector_shifted_label
    elif branch_preserving == len(valid):
        label = branch_gain_sensitive_label
    else:
        label = sensitive_label
    return {
        "label": label,
        "expected_chain": list(expected_chain),
        "valid_trial_count": len(valid),
        "branch_preserving_trial_count": branch_preserving,
        "positive_gain_trial_count": positive_gain,
        "stable_positive_trial_count": stable_positive,
        "branch_preservation_rate": round(branch_preserving / len(valid), 3)
        if valid
        else None,
        "positive_gain_rate": round(positive_gain / len(valid), 3) if valid else None,
        "stable_positive_rate": round(stable_positive / len(valid), 3)
        if valid
        else None,
        "min_gain_m": round(min_gain, 3) if min_gain is not None else None,
        "max_gain_m": round(max(gains), 3) if gains else None,
        "mean_gain_m": _mean(tuple(gains)),
        "max_gain_swing_m": round(max_swing, 3) if max_swing is not None else None,
        "worst_trial_label": worst_trial_label,
        "robustness_margin_m": robustness_margin,
    }


def _acceptance_decision(stability: dict[str, object]) -> dict[str, object]:
    label = str(stability.get("label", "not_evaluable"))
    valid_count = int(stability.get("valid_trial_count", 0) or 0)
    branch_rate = _optional_float(stability.get("branch_preservation_rate")) or 0.0
    positive_rate = _optional_float(stability.get("positive_gain_rate")) or 0.0
    margin = _optional_float(stability.get("robustness_margin_m"))
    is_speed_prior = label.startswith("history_speed_prior_") or (
        label == "stable_history_speed_prior_branch"
    )
    if valid_count == 0:
        return {
            "label": "not_evaluable",
            "accepted": False,
            "reason": "No valid perturbation trials were available for the gate.",
            "next_action": "Confirm the local replay inputs and rerun branch replay.",
        }
    if (
        label in {"stable_motion_context_branch", "stable_history_speed_prior_branch"}
        and margin is not None
        and margin >= 0.0
    ):
        subject = (
            "history speed-prior branch"
            if label == "stable_history_speed_prior_branch"
            else "motion-context branch"
        )
        return {
            "label": "accepted_for_selector_rollout",
            "accepted": True,
            "reason": (
                f"All perturbations preserved the {subject} and kept "
                "recoverable FDE above the acceptance threshold."
            ),
            "next_action": (
                "Evaluate this selector behavior on a broader branchable "
                "continuation queue."
            ),
        }
    if branch_rate >= 1.0 and positive_rate < 1.0:
        reason = (
            "The selected branch is stable, but the history speed-prior "
            "candidate still falls below the recoverable-FDE threshold."
            if is_speed_prior
            else (
                "The selected branch is stable, but at least one perturbation "
                "falls below the recoverable-FDE threshold."
            )
        )
        next_action = (
            "Add richer route context before treating this branch as robust."
            if is_speed_prior
            else (
                "Add richer route context or speed-prior calibration before "
                "treating this branch as robust."
            )
        )
        return {
            "label": "needs_route_context_margin",
            "accepted": False,
            "reason": reason,
            "next_action": next_action,
        }
    if branch_rate < 1.0 and positive_rate >= 1.0:
        return {
            "label": "needs_selector_stability",
            "accepted": False,
            "reason": (
                "Recoverable FDE remains positive, but the selected branch "
                "changes under perturbation."
            ),
            "next_action": (
                "Increase selector margin or add learned route-candidate "
                "scoring before rollout."
            ),
        }
    return {
        "label": "needs_route_and_selector_followup",
        "accepted": False,
        "reason": (
            "The branch choice and recoverable FDE are both sensitive under "
            "perturbation."
        ),
        "next_action": (
            "Keep this case in the diagnostic queue for route-context and "
            "selector-stability work."
        ),
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    stabilities = [
        _required_mapping(case, "perturbation_stability") for case in ready
    ]
    speed_prior_stabilities = [
        _required_mapping(case, "history_speed_prior_stability") for case in ready
    ]
    trials = [
        trial
        for case in ready
        for trial in _required_list(case, "perturbation_trials")
        if isinstance(trial, dict) and bool(trial.get("ready"))
    ]
    trial_gains = [
        gain
        for trial in trials
        if (gain := _optional_float(trial.get("motion_context_gain_m"))) is not None
    ]
    speed_prior_trial_gains = [
        gain
        for trial in trials
        if (gain := _optional_float(trial.get("history_speed_prior_gain_m")))
        is not None
    ]
    nominal_gains = [
        gain
        for case in ready
        if (gain := _optional_float(case.get("nominal_motion_context_gain_m")))
        is not None
    ]
    acceptances = [
        _required_mapping(case, "acceptance_decision") for case in ready
    ]
    speed_prior_acceptances = [
        _required_mapping(case, "history_speed_prior_acceptance_decision")
        for case in ready
    ]
    margins = [
        margin
        for stability in stabilities
        if (margin := _optional_float(stability.get("robustness_margin_m")))
        is not None
    ]
    speed_prior_margins = [
        margin
        for stability in speed_prior_stabilities
        if (margin := _optional_float(stability.get("robustness_margin_m")))
        is not None
    ]
    return {
        "case_count": len(cases),
        "replayed_case_count": len(ready),
        "perturbation_trial_count": len(trials),
        "stable_motion_context_case_count": sum(
            str(stability.get("label")) == "stable_motion_context_branch"
            for stability in stabilities
        ),
        "sensitive_case_count": sum(
            str(stability.get("label")) != "stable_motion_context_branch"
            for stability in stabilities
        ),
        "branch_preserving_trial_count": sum(
            bool(trial.get("branch_preserved")) for trial in trials
        ),
        "positive_gain_trial_count": sum(
            bool(trial.get("positive_gain")) for trial in trials
        ),
        "stable_positive_trial_count": sum(
            bool(trial.get("branch_preserved")) and bool(trial.get("positive_gain"))
            for trial in trials
        ),
        "history_speed_prior_positive_gain_trial_count": sum(
            bool(trial.get("history_speed_prior_positive_gain")) for trial in trials
        ),
        "history_speed_prior_stable_positive_trial_count": sum(
            bool(trial.get("branch_preserved"))
            and bool(trial.get("history_speed_prior_positive_gain"))
            for trial in trials
        ),
        "accepted_branch_case_count": sum(
            str(decision.get("label")) == "accepted_for_selector_rollout"
            for decision in acceptances
        ),
        "history_speed_prior_accepted_case_count": sum(
            str(decision.get("label")) == "accepted_for_selector_rollout"
            for decision in speed_prior_acceptances
        ),
        "history_speed_prior_resolved_margin_case_count": sum(
            str(base_decision.get("label")) == "needs_route_context_margin"
            and str(speed_decision.get("label")) == "accepted_for_selector_rollout"
            for base_decision, speed_decision in zip(
                acceptances,
                speed_prior_acceptances,
            )
        ),
        "history_speed_prior_route_context_followup_case_count": sum(
            str(decision.get("label")) == "needs_route_context_margin"
            for decision in speed_prior_acceptances
        ),
        "route_context_followup_case_count": sum(
            str(decision.get("label")) == "needs_route_context_margin"
            for decision in acceptances
        ),
        "selector_stability_followup_case_count": sum(
            str(decision.get("label")) in {
                "needs_selector_stability",
                "needs_route_and_selector_followup",
            }
            for decision in acceptances
        ),
        "mean_nominal_gain_m": _mean(tuple(nominal_gains)),
        "mean_trial_gain_m": _mean(tuple(trial_gains)),
        "min_trial_gain_m": round(min(trial_gains), 3) if trial_gains else None,
        "max_trial_gain_m": round(max(trial_gains), 3) if trial_gains else None,
        "mean_history_speed_prior_gain_m": _mean(tuple(speed_prior_trial_gains)),
        "min_history_speed_prior_gain_m": (
            round(min(speed_prior_trial_gains), 3)
            if speed_prior_trial_gains
            else None
        ),
        "max_history_speed_prior_gain_m": (
            round(max(speed_prior_trial_gains), 3)
            if speed_prior_trial_gains
            else None
        ),
        "min_robustness_margin_m": round(min(margins), 3) if margins else None,
        "mean_robustness_margin_m": _mean(tuple(margins)),
        "min_history_speed_prior_margin_m": (
            round(min(speed_prior_margins), 3) if speed_prior_margins else None
        ),
        "mean_history_speed_prior_margin_m": _mean(tuple(speed_prior_margins)),
    }


def _empty_stability() -> dict[str, object]:
    return {
        "label": "not_evaluable",
        "expected_chain": [],
        "valid_trial_count": 0,
        "branch_preserving_trial_count": 0,
        "positive_gain_trial_count": 0,
        "stable_positive_trial_count": 0,
        "branch_preservation_rate": None,
        "positive_gain_rate": None,
        "stable_positive_rate": None,
        "min_gain_m": None,
        "max_gain_m": None,
        "mean_gain_m": None,
        "max_gain_swing_m": None,
        "worst_trial_label": None,
        "robustness_margin_m": None,
    }


def _worst_trial_label(
    trials: list[dict[str, object]],
    gain_field: str = "motion_context_gain_m",
) -> str | None:
    worst_label = None
    worst_gain = None
    for trial in trials:
        gain = _optional_float(trial.get(gain_field))
        if gain is None:
            continue
        if worst_gain is None or gain < worst_gain:
            worst_gain = gain
            worst_label = str(trial.get("label"))
    return worst_label


def _why_it_matters(
    stability: dict[str, object],
    acceptance: dict[str, object],
) -> str:
    if str(acceptance.get("label")) == "accepted_for_selector_rollout":
        return (
            "The motion-context branch passes the acceptance gate, making it "
            "ready for broader selector evaluation."
        )
    if str(acceptance.get("label")) == "needs_route_context_margin":
        return (
            "The branch choice is stable, but the gain margin is too thin "
            "under at least one perturbation."
        )
    label = str(stability.get("label"))
    if label == "positive_gain_but_selector_shifted":
        return (
            "The motion-context prior kept positive recoverable FDE, but the "
            "selected parsed branch changed under at least one perturbation."
        )
    if label == "branch_stable_gain_sensitive":
        return (
            "The motion-context prior stayed on the same parsed branch, but "
            "its recoverable FDE became sensitive to anchor perturbations."
        )
    if label == "sensitive_to_anchor_perturbation":
        return (
            "The branch choice or recoverable FDE changed under perturbation, "
            "making this a good target for richer route context or learned "
            "scoring."
        )
    return "The case could not produce enough replay trials for stability analysis."


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)
