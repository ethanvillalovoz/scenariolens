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
        f"| Mean nominal recoverable FDE | {_signed_meter_text(aggregate['mean_nominal_gain_m'])} |",
        f"| Mean perturbed recoverable FDE | {_signed_meter_text(aggregate['mean_trial_gain_m'])} |",
        f"| Min perturbed recoverable FDE | {_signed_meter_text(aggregate['min_trial_gain_m'])} |",
        f"| Max perturbed recoverable FDE | {_signed_meter_text(aggregate['max_trial_gain_m'])} |",
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
            "| Rank | Scenario | Track | Default chain | Motion-context chain | Nominal gain | Stable trials | Trial gain range | Stability |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | 0/0 | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        stability = _required_mapping(case, "perturbation_stability")
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
            f"{_signed_meter_text(stability.get('min_gain_m'))} to "
            f"{_signed_meter_text(stability.get('max_gain_m'))} | "
            f"`{stability['label']}` |"
        )

    for case in cases:
        assert isinstance(case, dict)
        stability = _required_mapping(case, "perturbation_stability")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Diagnosis source: `{case['diagnosis_label']}`",
                f"- Source: `{case['source_name']}`",
                f"- Ready: {case['ready']}",
                f"- Stability: **{stability['label']}**",
                f"- Why it matters: {case['why_it_matters']}",
                "- Default linked-route FDE: "
                f"{_meter_text(case.get('default_fde_m'))}",
                "- Motion-context route FDE: "
                f"{_meter_text(case.get('motion_context_fde_m'))}",
                "- Nominal recoverable FDE: "
                f"{_signed_meter_text(case.get('nominal_motion_context_gain_m'))}",
                "- Branch-preserving trials: "
                f"{stability['branch_preserving_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "- Positive-gain trials: "
                f"{stability['positive_gain_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "- Stable positive trials: "
                f"{stability['stable_positive_trial_count']}/"
                f"{stability['valid_trial_count']}",
                "",
                "Perturbation trials:",
                "",
                "| Perturbation | Motion-context chain | Gain vs default | Branch preserved | Positive gain | Verdict |",
                "| --- | --- | ---: | --- | --- | --- |",
            ]
        )
        for trial in _required_list(case, "perturbation_trials"):
            assert isinstance(trial, dict)
            lines.append(
                "| "
                f"`{trial['label']}` | "
                f"{_chain_text(trial.get('motion_context_chain'))} | "
                f"{_signed_meter_text(trial.get('motion_context_gain_m'))} | "
                f"{trial['branch_preserved']} | "
                f"{trial['positive_gain']} | "
                f"`{trial['verdict']}` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stable motion-context cases preserve the selected branch and keep "
            "positive recoverable FDE across all deterministic perturbations.",
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
        "nominal_motion_context_gain_m": None,
        "perturbation_trials": [],
        "perturbation_stability": _empty_stability(),
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
            "oracle_fde_m": nominal.get("oracle_fde_m"),
            "nominal_motion_context_gain_m": nominal.get(
                "motion_context_recoverable_fde_m"
            ),
            "nominal_oracle_gain_m": nominal.get("oracle_recoverable_fde_m"),
            "perturbation_trials": trials,
            "perturbation_stability": stability,
            "why_it_matters": _why_it_matters(stability),
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
    branch_preserved = bool(evaluation.get("ready")) and chain == expected_chain
    positive_gain = gain is not None and gain > _MIN_STABLE_GAIN_M
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
        "branch_preserved": branch_preserved,
        "positive_gain": positive_gain,
        "verdict": verdict,
    }


def _selected_motion_context_score(evaluation: dict[str, object]) -> float | None:
    for route in _required_list(evaluation, "route_candidates"):
        if isinstance(route, dict) and bool(route.get("is_motion_context_selected")):
            return _optional_float(route.get("motion_context_score"))
    return None


def _perturbation_stability(
    nominal_gain: object,
    expected_chain: tuple[str, ...],
    trials: list[dict[str, object]],
) -> dict[str, object]:
    valid = [trial for trial in trials if bool(trial.get("ready"))]
    gains = [
        gain
        for trial in valid
        if (gain := _optional_float(trial.get("motion_context_gain_m"))) is not None
    ]
    branch_preserving = sum(bool(trial.get("branch_preserved")) for trial in valid)
    positive_gain = sum(bool(trial.get("positive_gain")) for trial in valid)
    stable_positive = sum(
        bool(trial.get("branch_preserved")) and bool(trial.get("positive_gain"))
        for trial in valid
    )
    nominal = _optional_float(nominal_gain)
    max_swing = (
        max(abs(gain - nominal) for gain in gains)
        if gains and nominal is not None
        else None
    )
    if not valid:
        label = "not_evaluable"
    elif stable_positive == len(valid):
        label = "stable_motion_context_branch"
    elif positive_gain == len(valid):
        label = "positive_gain_but_selector_shifted"
    elif branch_preserving == len(valid):
        label = "branch_stable_gain_sensitive"
    else:
        label = "sensitive_to_anchor_perturbation"
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
        "min_gain_m": round(min(gains), 3) if gains else None,
        "max_gain_m": round(max(gains), 3) if gains else None,
        "mean_gain_m": _mean(tuple(gains)),
        "max_gain_swing_m": round(max_swing, 3) if max_swing is not None else None,
    }


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready = [case for case in cases if bool(case.get("ready"))]
    stabilities = [
        _required_mapping(case, "perturbation_stability") for case in ready
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
    nominal_gains = [
        gain
        for case in ready
        if (gain := _optional_float(case.get("nominal_motion_context_gain_m")))
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
        "mean_nominal_gain_m": _mean(tuple(nominal_gains)),
        "mean_trial_gain_m": _mean(tuple(trial_gains)),
        "min_trial_gain_m": round(min(trial_gains), 3) if trial_gains else None,
        "max_trial_gain_m": round(max(trial_gains), 3) if trial_gains else None,
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
    }


def _why_it_matters(stability: dict[str, object]) -> str:
    label = str(stability.get("label"))
    if label == "stable_motion_context_branch":
        return (
            "The non-oracle branch choice stayed on the same parsed route and "
            "kept positive recoverable FDE under all deterministic perturbations."
        )
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
