from __future__ import annotations

import json
from dataclasses import dataclass, replace
from math import cos, radians, sin
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.prediction import (
    PredictionBaselineSummary,
    _anchor_index,
    constant_velocity_baseline,
    heading_aware_lane_baseline,
    lane_aware_baseline,
)
from scenariolens.replay_candidates import REPLAY_CANDIDATE_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State
from scenariolens.visualize import scenario_svg

HEADING_REPLAY_PROTOTYPE_FORMAT = "scenariolens.heading_replay_prototype.v1"

_HEADING_COMPARISON_MODE = "heading_lane_selection"
_HEADING_READY = {
    "ready_for_heading_improvement_replay",
    "ready_for_heading_regression_replay",
}
_PERTURBATIONS: tuple[dict[str, object], ...] = (
    {
        "label": "speed_minus_10pct",
        "speed_scale": 0.90,
        "heading_delta_deg": 0.0,
        "description": "Anchor velocity magnitude reduced by 10%.",
    },
    {
        "label": "speed_plus_10pct",
        "speed_scale": 1.10,
        "heading_delta_deg": 0.0,
        "description": "Anchor velocity magnitude increased by 10%.",
    },
    {
        "label": "heading_left_5deg",
        "speed_scale": 1.0,
        "heading_delta_deg": 5.0,
        "description": "Anchor velocity heading rotated left by 5 degrees.",
    },
    {
        "label": "heading_right_5deg",
        "speed_scale": 1.0,
        "heading_delta_deg": -5.0,
        "description": "Anchor velocity heading rotated right by 5 degrees.",
    },
)


@dataclass(frozen=True)
class HeadingReplayPrototypeResult:
    """Files produced by a heading-aware open-loop replay prototype run."""

    ready: bool
    case_count: int
    replay_track_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_heading_replay_prototype(
    candidate_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = 5,
    public_report_path: str | Path | None = None,
) -> HeadingReplayPrototypeResult:
    """Generate a laptop-safe nearest-lane vs heading-aware replay packet."""

    source = Path(candidate_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = heading_replay_prototype_payload(
        candidate_manifest_path=source,
        output_dir=target,
        top=top,
    )
    report = heading_replay_prototype_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return HeadingReplayPrototypeResult(
        ready=bool(payload["ready"]),
        case_count=int(payload["replayed_case_count"]),
        replay_track_count=int(aggregate["replay_track_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def heading_replay_prototype_payload(
    candidate_manifest_path: Path,
    output_dir: Path,
    top: int = 5,
) -> dict[str, object]:
    """Return deterministic heading-aware replay evidence for selected cases."""

    if top < 1:
        raise ValueError("top must be at least 1.")

    candidate_payload = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    if candidate_payload.get("format") != REPLAY_CANDIDATE_FORMAT:
        raise ValueError(
            "Expected a replay-candidates manifest with format "
            f"{REPLAY_CANDIDATE_FORMAT}."
        )

    debug_manifest_path = Path(str(candidate_payload.get("source", "")))
    if not debug_manifest_path.exists():
        raise FileNotFoundError(
            f"Replay-candidates source debug manifest not found: {debug_manifest_path}"
        )
    debug_payload = json.loads(debug_manifest_path.read_text(encoding="utf-8"))
    debug_cases = _required_list(debug_payload, "cases")
    debug_by_key = _debug_case_lookup(debug_cases)
    candidates = _required_list(candidate_payload, "candidates")
    selected_candidates, skipped_candidates = _select_heading_candidates(
        candidates,
        top=top,
    )

    replay_cases = []
    for rank, candidate in enumerate(selected_candidates, start=1):
        case = _matching_debug_case(candidate, debug_by_key)
        if case is None:
            skipped_candidates.append(
                {
                    "scenario_id": candidate.get("scenario_id"),
                    "source_name": candidate.get("source_name"),
                    "readiness": candidate.get("readiness", "unknown"),
                    "comparison_mode": candidate.get("comparison_mode", "unknown"),
                    "reason": "candidate_not_found_in_debug_manifest",
                }
            )
            continue
        replay_cases.append(
            _heading_replay_case(
                candidate=candidate,
                debug_case=case,
                output_dir=output_dir,
                rank=rank,
                max_scenarios=_optional_int(debug_payload.get("max_scenarios")),
            )
        )

    aggregate = _aggregate_replays(replay_cases)
    ready = bool(candidate_payload.get("ready")) and any(
        bool(case.get("ready")) for case in replay_cases
    )

    return {
        "format": HEADING_REPLAY_PROTOTYPE_FORMAT,
        "candidate_manifest": str(candidate_manifest_path),
        "candidate_format": candidate_payload.get("format"),
        "debug_manifest": str(debug_manifest_path),
        "output_dir": str(output_dir),
        "ready": ready,
        "requested_top": top,
        "selected_candidate_count": len(selected_candidates),
        "replayed_case_count": len(replay_cases),
        "skipped_candidate_count": len(skipped_candidates),
        "perturbations": list(_PERTURBATIONS),
        "aggregate": aggregate,
        "cases": replay_cases,
        "skipped_candidates": skipped_candidates,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
        "scope_note": (
            "Open-loop deterministic replay comparing nearest-lane and "
            "heading-aware selector baselines; not a closed-loop simulator, "
            "not Waymax/JAX execution, and not a Waymo benchmark claim."
        ),
    }


def heading_replay_prototype_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a heading-aware replay payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    perturbations = _required_list(payload, "perturbations")
    skipped = _required_list(payload, "skipped_candidates")
    lines = [
        "# ScenarioLens Heading-Aware Replay Prototype",
        "",
        "This report executes the next laptop-safe step after the heading-aware "
        "replay candidate plan: it reloads selected local scenarios, replays "
        "nearest-lane and heading-aware open-loop rollouts from the same anchor "
        "state, and applies small deterministic anchor-velocity perturbations "
        "to check whether the selector win or regression is stable.",
        "",
        "It is intentionally scoped: this is not a closed-loop simulator, not "
        "Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files "
        "and local per-case replay packets stay out of git.",
        "",
        "## Scope",
        "",
        f"- Candidate manifest: `{payload['candidate_manifest']}`",
        f"- Debug manifest: `{payload['debug_manifest']}`",
        f"- Ready for replay analysis: {payload['ready']}",
        f"- Requested top candidates: {payload['requested_top']}",
        f"- Heading replay cases evaluated: {payload['replayed_case_count']}",
        f"- Perturbations per case: {len(perturbations)}",
        "- Raw Waymo files committed: no",
        "- Local replay packets and SVG overlays committed: no",
        "",
        "## Replay Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Replayed cases | {aggregate['replayed_case_count']} |",
        f"| Replayed targets | {aggregate['replay_track_count']} |",
        f"| Perturbation trials | {aggregate['perturbation_trial_count']} |",
        f"| Sign-preserving trials | {aggregate['sign_preserving_trial_count']} |",
        f"| Sign-preservation rate | {_percent_text(aggregate['sign_preservation_rate'])} |",
        f"| Heading improvement cases replayed | {aggregate['improvement_case_count']} |",
        f"| Heading regression cases replayed | {aggregate['regression_case_count']} |",
        f"| Heading map-used targets | {aggregate['heading_map_used_count']} |",
        f"| Heading fallback targets | {aggregate['heading_fallback_count']} |",
        "",
        "## Perturbation Set",
        "",
    ]
    for perturbation in perturbations:
        assert isinstance(perturbation, dict)
        lines.append(f"- `{perturbation['label']}`: {perturbation['description']}")

    lines.extend(
        [
            "",
            "## Replayed Candidates",
            "",
            "| Rank | Scenario | Case | Readiness | Targets | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Sign stability | Max delta swing |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in cases:
        assert isinstance(case, dict)
        nominal = _required_mapping(case, "nominal")
        stability = _required_mapping(case, "perturbation_stability")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"{case['case_label']} | "
            f"`{case['readiness']}` | "
            f"{nominal['evaluated_track_count']} | "
            f"{_meter_text(nominal['constant_velocity_fde_m'])} | "
            f"{_meter_text(nominal['nearest_lane_fde_m'])} | "
            f"{_meter_text(nominal['heading_lane_fde_m'])} | "
            f"{_signed_meter_text(nominal['heading_vs_nearest_fde_improvement_m'])} | "
            f"{stability['sign_preserving_trial_count']}/{stability['valid_trial_count']} | "
            f"{_meter_text(stability['max_delta_swing_m'])} |"
        )

    for case in cases:
        assert isinstance(case, dict)
        nominal = _required_mapping(case, "nominal")
        stability = _required_mapping(case, "perturbation_stability")
        trials = _required_list(case, "perturbation_trials")
        tracks = _required_list(case, "track_replays")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}`",
                "",
                f"- Case: {case['case_label']}",
                f"- Source: `{case['source_name']}`",
                f"- Readiness: `{case['readiness']}`",
                f"- Why replayed: {case['why_replayed']}",
                f"- Nominal selector winner: {nominal['nominal_selector_winner']}",
                f"- Heading vs nearest FDE delta: {_signed_meter_text(nominal['heading_vs_nearest_fde_improvement_m'])}",
                f"- Heading vs constant-velocity FDE delta: {_signed_meter_text(nominal['heading_vs_constant_velocity_fde_improvement_m'])}",
                f"- Perturbation stability label: `{stability['label']}`",
                f"- Sign-preservation rate: {_percent_text(stability['sign_preservation_rate'])}",
                f"- Local replay packet: `{case['local_packet_path']}`",
                f"- Local SVG overlay: `{case['local_svg_path']}`",
                "",
                "Target replay rows:",
                "",
                "| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest map | Heading map | Heading fallback |",
                "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"`{track['agent_type']}` | "
                f"{_meter_text(track['constant_velocity_fde_m'])} | "
                f"{_meter_text(track['nearest_lane_fde_m'])} | "
                f"{_meter_text(track['heading_lane_fde_m'])} | "
                f"{_signed_meter_text(track['heading_vs_nearest_fde_improvement_m'])} | "
                f"{track['nearest_map_used']} | "
                f"{track['heading_map_used']} | "
                f"`{track['heading_fallback_reason'] or 'none'}` |"
            )

        lines.extend(
            [
                "",
                "Perturbation trials:",
                "",
                "| Trial | Heading vs nearest | Preserves expected sign | CV FDE | Nearest FDE | Heading FDE |",
                "| --- | ---: | --- | ---: | ---: | ---: |",
            ]
        )
        for trial in trials:
            assert isinstance(trial, dict)
            lines.append(
                "| "
                f"`{trial['label']}` | "
                f"{_signed_meter_text(trial['heading_vs_nearest_fde_improvement_m'])} | "
                f"{trial['preserves_expected_sign']} | "
                f"{_meter_text(trial['constant_velocity_fde_m'])} | "
                f"{_meter_text(trial['nearest_lane_fde_m'])} | "
                f"{_meter_text(trial['heading_lane_fde_m'])} |"
            )

    if skipped:
        lines.extend(["", "## Skipped Candidates", ""])
        for item in skipped:
            assert isinstance(item, dict)
            lines.append(
                f"- `{item.get('scenario_id', 'unknown')}`: {item.get('reason', 'unknown')}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stable heading-improvement cases are useful positive controls for the selector because the nearest-lane advantage survives small anchor-state perturbations.",
            "- Stable heading-regression cases are useful debugging targets because the warning persists under small state-estimation differences.",
            "- Sensitive cases are still useful: they show where selector conclusions depend on small changes in anchor velocity.",
            "- Fallback-heavy cases remain outside this prototype until map matching, coordinate frames, and target eligibility are audited.",
            "- This is open-loop diagnostic evidence, not a production prediction model or closed-loop autonomy simulator.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _select_heading_candidates(
    candidates: list[object],
    top: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ready = []
    skipped = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        mode = str(candidate.get("comparison_mode", ""))
        readiness = str(candidate.get("readiness", ""))
        if mode != _HEADING_COMPARISON_MODE:
            skipped.append(
                {
                    "scenario_id": candidate.get("scenario_id"),
                    "source_name": candidate.get("source_name"),
                    "readiness": readiness,
                    "comparison_mode": mode or "unknown",
                    "reason": "unsupported_candidate_mode",
                }
            )
            continue
        if readiness in _HEADING_READY:
            ready.append(candidate)
            continue
        skipped.append(
            {
                "scenario_id": candidate.get("scenario_id"),
                "source_name": candidate.get("source_name"),
                "readiness": readiness,
                "comparison_mode": mode,
                "reason": "not_heading_replay_ready",
            }
        )
    selected = ready[:top]
    for candidate in ready[top:]:
        skipped.append(
            {
                "scenario_id": candidate.get("scenario_id"),
                "source_name": candidate.get("source_name"),
                "readiness": candidate.get("readiness", "unknown"),
                "comparison_mode": candidate.get("comparison_mode", "unknown"),
                "reason": "not_selected_due_to_top_limit",
            }
        )
    return selected, skipped


def _heading_replay_case(
    candidate: dict[str, object],
    debug_case: dict[str, object],
    output_dir: Path,
    rank: int,
    max_scenarios: int | None,
) -> dict[str, object]:
    source_input = Path(str(debug_case["source_input"]))
    input_format = str(debug_case.get("input_format", "native"))
    input_ready, preflight, scenarios = load_failure_study_input(
        source=source_input,
        input_format=input_format,
        max_scenarios=max_scenarios,
    )
    scenario = _find_scenario(scenarios, str(debug_case["scenario_id"]))
    case_slug = _safe_slug(
        f"{rank}-{debug_case.get('case_label', 'case')}-{debug_case['scenario_id']}"
    )
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    packet_path = case_dir / "heading_replay_packet.json"
    svg_path = case_dir / "heading_replay.svg"

    if scenario is None:
        case_payload = {
            "ready": False,
            "rank": rank,
            "case_label": debug_case.get("case_label", "Case"),
            "scenario_id": debug_case.get("scenario_id", ""),
            "source_name": debug_case.get("source_name", source_input.name),
            "readiness": candidate.get("readiness", "unknown"),
            "why_replayed": "Scenario could not be reloaded from the local source.",
            "error": "scenario_not_found",
            "input_ready": input_ready,
            "preflight": preflight or {},
            "nominal": _empty_nominal(),
            "track_replays": [],
            "perturbation_trials": [],
            "perturbation_stability": _empty_stability(),
            "local_packet_path": str(packet_path),
            "local_svg_path": str(svg_path),
        }
        _write_json(packet_path, case_payload)
        return case_payload

    constant = constant_velocity_baseline(scenario)
    nearest = lane_aware_baseline(scenario)
    heading = heading_aware_lane_baseline(scenario)
    track_replays = _track_replays(
        constant=constant,
        nearest=nearest,
        heading=heading,
    )
    target_ids = tuple(str(row["track_id"]) for row in track_replays)
    nominal = _nominal_summary(
        constant=constant,
        nearest=nearest,
        heading=heading,
        track_replays=track_replays,
    )
    expected_sign = _expected_sign(candidate)
    trials = [
        _perturbation_trial(
            scenario=scenario,
            target_ids=target_ids,
            perturbation=perturbation,
            expected_sign=expected_sign,
        )
        for perturbation in _PERTURBATIONS
    ]
    case_payload = {
        "ready": bool(input_ready) and bool(track_replays),
        "rank": rank,
        "case_label": debug_case.get("case_label", "Case"),
        "scenario_id": scenario.scenario_id,
        "source_input": str(source_input),
        "source_name": debug_case.get("source_name", source_input.name),
        "input_format": input_format,
        "readiness": candidate.get("readiness", "unknown"),
        "why_replayed": _why_replayed(candidate),
        "input_ready": input_ready,
        "preflight": preflight or {},
        "nominal": nominal,
        "track_replays": track_replays,
        "perturbation_trials": trials,
        "perturbation_stability": _perturbation_stability(
            nominal_delta=nominal["heading_vs_nearest_fde_improvement_m"],
            expected_sign=expected_sign,
            trials=trials,
        ),
        "local_packet_path": str(packet_path),
        "local_svg_path": str(svg_path),
    }
    _write_json(packet_path, case_payload)
    svg_path.write_text(
        scenario_svg(
            scenario,
            show_lane_aware_baseline=True,
            show_heading_aware_baseline=True,
        ),
        encoding="utf-8",
    )
    return case_payload


def _perturbation_trial(
    scenario: Scenario,
    target_ids: tuple[str, ...],
    perturbation: dict[str, object],
    expected_sign: int,
) -> dict[str, object]:
    perturbed = _perturb_anchor_velocities(
        scenario=scenario,
        target_ids=target_ids,
        speed_scale=float(perturbation["speed_scale"]),
        heading_delta_deg=float(perturbation["heading_delta_deg"]),
    )
    constant = constant_velocity_baseline(perturbed)
    nearest = lane_aware_baseline(perturbed)
    heading = heading_aware_lane_baseline(perturbed)
    delta = _optional_delta(nearest.fde_m, heading.fde_m)
    return {
        "label": perturbation["label"],
        "speed_scale": perturbation["speed_scale"],
        "heading_delta_deg": perturbation["heading_delta_deg"],
        "constant_velocity_fde_m": constant.fde_m,
        "nearest_lane_fde_m": nearest.fde_m,
        "heading_lane_fde_m": heading.fde_m,
        "heading_vs_nearest_fde_improvement_m": delta,
        "heading_vs_constant_velocity_fde_improvement_m": _optional_delta(
            constant.fde_m,
            heading.fde_m,
        ),
        "nearest_map_used_count": nearest.map_used_count,
        "heading_map_used_count": heading.map_used_count,
        "nearest_fallback_count": nearest.fallback_count,
        "heading_fallback_count": heading.fallback_count,
        "evaluated_track_count": _intersection_track_count(
            constant=constant,
            nearest=nearest,
            heading=heading,
        ),
        "preserves_expected_sign": _preserves_expected_sign(delta, expected_sign),
    }


def _perturb_anchor_velocities(
    scenario: Scenario,
    target_ids: tuple[str, ...],
    speed_scale: float,
    heading_delta_deg: float,
) -> Scenario:
    target_set = set(target_ids)
    tracks = []
    for track in scenario.tracks:
        if track.agent_id not in target_set:
            tracks.append(track)
            continue
        states = tuple(sorted(track.states, key=lambda state: state.t))
        if len(states) < 2:
            tracks.append(track)
            continue
        anchor_index = _anchor_index(states, scenario)
        updated_states = list(states)
        updated_states[anchor_index] = _perturbed_state(
            states[anchor_index],
            speed_scale=speed_scale,
            heading_delta_deg=heading_delta_deg,
        )
        tracks.append(
            AgentTrack(
                agent_id=track.agent_id,
                agent_type=track.agent_type,
                states=tuple(updated_states),
            )
        )
    return replace(scenario, tracks=tuple(tracks))


def _perturbed_state(
    state: State,
    speed_scale: float,
    heading_delta_deg: float,
) -> State:
    angle = radians(heading_delta_deg)
    scaled_vx = state.vx * speed_scale
    scaled_vy = state.vy * speed_scale
    return replace(
        state,
        vx=(scaled_vx * cos(angle)) - (scaled_vy * sin(angle)),
        vy=(scaled_vx * sin(angle)) + (scaled_vy * cos(angle)),
    )


def _nominal_summary(
    constant: PredictionBaselineSummary,
    nearest: PredictionBaselineSummary,
    heading: PredictionBaselineSummary,
    track_replays: list[dict[str, object]],
) -> dict[str, object]:
    heading_delta = _optional_delta(nearest.fde_m, heading.fde_m)
    return {
        "target_source": constant.target_source,
        "requested_target_count": constant.requested_target_count,
        "evaluated_track_count": len(track_replays),
        "constant_velocity_fde_m": constant.fde_m,
        "nearest_lane_fde_m": nearest.fde_m,
        "heading_lane_fde_m": heading.fde_m,
        "heading_vs_nearest_fde_improvement_m": heading_delta,
        "heading_vs_constant_velocity_fde_improvement_m": _optional_delta(
            constant.fde_m,
            heading.fde_m,
        ),
        "constant_velocity_miss_rate": constant.miss_rate,
        "nearest_lane_miss_rate": nearest.miss_rate,
        "heading_lane_miss_rate": heading.miss_rate,
        "nearest_map_used_count": nearest.map_used_count,
        "heading_map_used_count": heading.map_used_count,
        "nearest_fallback_count": nearest.fallback_count,
        "heading_fallback_count": heading.fallback_count,
        "nominal_selector_winner": _selector_winner(heading_delta),
    }


def _track_replays(
    constant: PredictionBaselineSummary,
    nearest: PredictionBaselineSummary,
    heading: PredictionBaselineSummary,
) -> list[dict[str, object]]:
    nearest_by_track = {result.track_id: result for result in nearest.track_results}
    heading_by_track = {result.track_id: result for result in heading.track_results}
    rows = []
    for constant_result in constant.track_results:
        nearest_result = nearest_by_track.get(constant_result.track_id)
        heading_result = heading_by_track.get(constant_result.track_id)
        if nearest_result is None or heading_result is None:
            continue
        rows.append(
            {
                "track_id": constant_result.track_id,
                "agent_type": constant_result.agent_type,
                "constant_velocity_fde_m": constant_result.fde_m,
                "nearest_lane_fde_m": nearest_result.fde_m,
                "heading_lane_fde_m": heading_result.fde_m,
                "heading_vs_nearest_fde_improvement_m": round(
                    nearest_result.fde_m - heading_result.fde_m,
                    3,
                ),
                "heading_vs_constant_velocity_fde_improvement_m": round(
                    constant_result.fde_m - heading_result.fde_m,
                    3,
                ),
                "nearest_map_used": nearest_result.map_used,
                "heading_map_used": heading_result.map_used,
                "nearest_fallback_reason": nearest_result.fallback_reason,
                "heading_fallback_reason": heading_result.fallback_reason,
            }
        )
    return rows


def _perturbation_stability(
    nominal_delta: object,
    expected_sign: int,
    trials: list[dict[str, object]],
) -> dict[str, object]:
    nominal = _optional_float(nominal_delta)
    trial_deltas = [
        _optional_float(trial.get("heading_vs_nearest_fde_improvement_m"))
        for trial in trials
    ]
    valid_deltas = [delta for delta in trial_deltas if delta is not None]
    valid_count = len(valid_deltas)
    sign_preserving = sum(
        _preserves_expected_sign(delta, expected_sign) for delta in valid_deltas
    )
    sign_rate = sign_preserving / valid_count if valid_count else None
    max_swing = (
        max(abs(delta - nominal) for delta in valid_deltas)
        if valid_deltas and nominal is not None
        else None
    )
    if valid_count == 0:
        label = "not_evaluable"
    elif sign_preserving == valid_count:
        label = "stable"
    elif sign_preserving > 0:
        label = "mixed"
    else:
        label = "sign_reversed"

    return {
        "label": label,
        "valid_trial_count": valid_count,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "max_delta_swing_m": round(max_swing, 3) if max_swing is not None else None,
    }


def _aggregate_replays(cases: list[dict[str, object]]) -> dict[str, object]:
    replayed = [case for case in cases if bool(case.get("ready"))]
    stability_rows = [
        _required_mapping(case, "perturbation_stability") for case in replayed
    ]
    valid_trials = sum(int(row["valid_trial_count"]) for row in stability_rows)
    sign_preserving = sum(
        int(row["sign_preserving_trial_count"]) for row in stability_rows
    )
    sign_rate = (sign_preserving / valid_trials) if valid_trials else None
    nominal_rows = [_required_mapping(case, "nominal") for case in replayed]
    return {
        "replayed_case_count": len(replayed),
        "replay_track_count": sum(
            len(_required_list(case, "track_replays")) for case in replayed
        ),
        "perturbation_trial_count": valid_trials,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "improvement_case_count": sum(
            str(case.get("readiness")) == "ready_for_heading_improvement_replay"
            for case in replayed
        ),
        "regression_case_count": sum(
            str(case.get("readiness")) == "ready_for_heading_regression_replay"
            for case in replayed
        ),
        "heading_map_used_count": sum(
            int(row["heading_map_used_count"]) for row in nominal_rows
        ),
        "heading_fallback_count": sum(
            int(row["heading_fallback_count"]) for row in nominal_rows
        ),
    }


def _debug_case_lookup(cases: list[object]) -> dict[tuple[str, str], dict[str, object]]:
    lookup = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        key = (str(case.get("scenario_id", "")), str(case.get("source_name", "")))
        lookup[key] = case
    return lookup


def _matching_debug_case(
    candidate: dict[str, object],
    lookup: dict[tuple[str, str], dict[str, object]],
) -> dict[str, object] | None:
    key = (
        str(candidate.get("scenario_id", "")),
        str(candidate.get("source_name", "")),
    )
    if key in lookup:
        return lookup[key]
    scenario_id = key[0]
    for (candidate_id, _source_name), case in lookup.items():
        if candidate_id == scenario_id:
            return case
    return None


def _find_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str,
) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _intersection_track_count(
    constant: PredictionBaselineSummary,
    nearest: PredictionBaselineSummary,
    heading: PredictionBaselineSummary,
) -> int:
    constant_ids = {result.track_id for result in constant.track_results}
    nearest_ids = {result.track_id for result in nearest.track_results}
    heading_ids = {result.track_id for result in heading.track_results}
    return len(constant_ids & nearest_ids & heading_ids)


def _expected_sign(candidate: dict[str, object]) -> int:
    readiness = str(candidate.get("readiness", ""))
    if readiness == "ready_for_heading_regression_replay":
        return -1
    return 1


def _preserves_expected_sign(value: float | None, expected_sign: int) -> bool:
    if value is None:
        return False
    return value > 0 if expected_sign > 0 else value < 0


def _why_replayed(candidate: dict[str, object]) -> str:
    readiness = str(candidate.get("readiness", ""))
    if readiness == "ready_for_heading_regression_replay":
        return (
            "Heading regression candidate: replay checks whether the "
            "nearest-lane vs heading-aware warning persists under small "
            "anchor-state perturbations."
        )
    if readiness == "ready_for_heading_improvement_replay":
        return (
            "Heading improvement candidate: replay checks whether the "
            "heading-aware selector advantage survives small anchor-state "
            "perturbations."
        )
    return "Candidate was replayed for manual heading-aware selector review."


def _selector_winner(delta: float | None) -> str:
    if delta is None:
        return "n/a"
    if delta > 0:
        return "heading_aware"
    if delta < 0:
        return "nearest_lane"
    return "tie"


def _empty_nominal() -> dict[str, object]:
    return {
        "target_source": "n/a",
        "requested_target_count": 0,
        "evaluated_track_count": 0,
        "constant_velocity_fde_m": None,
        "nearest_lane_fde_m": None,
        "heading_lane_fde_m": None,
        "heading_vs_nearest_fde_improvement_m": None,
        "heading_vs_constant_velocity_fde_improvement_m": None,
        "constant_velocity_miss_rate": None,
        "nearest_lane_miss_rate": None,
        "heading_lane_miss_rate": None,
        "nearest_map_used_count": 0,
        "heading_map_used_count": 0,
        "nearest_fallback_count": 0,
        "heading_fallback_count": 0,
        "nominal_selector_winner": "n/a",
    }


def _empty_stability() -> dict[str, object]:
    return {
        "label": "not_evaluable",
        "valid_trial_count": 0,
        "sign_preserving_trial_count": 0,
        "sign_preservation_rate": None,
        "max_delta_swing_m": None,
    }


def _optional_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 3)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f} m"


def _signed_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _percent_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _safe_slug(value: object) -> str:
    slug = "".join(
        character.lower() if character.isalnum() else "-"
        for character in str(value)
    )
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "case"


def _required_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping field: {key}")
    return value


def _required_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}")
    return value


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
