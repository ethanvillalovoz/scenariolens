from __future__ import annotations

import json
from dataclasses import dataclass, replace
from math import cos, isfinite, radians, sin
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.prediction import (
    PredictionBaselineComparison,
    _anchor_index,
    compare_prediction_baselines,
)
from scenariolens.replay_candidates import REPLAY_CANDIDATE_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State
from scenariolens.visualize import scenario_svg

REPLAY_PROTOTYPE_FORMAT = "scenariolens.replay_prototype.v1"

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
class ReplayPrototypeResult:
    """Files produced by an open-loop replay prototype run."""

    ready: bool
    case_count: int
    replay_track_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_replay_prototype(
    candidate_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = 2,
    public_report_path: str | Path | None = None,
) -> ReplayPrototypeResult:
    """Generate an honest, laptop-safe open-loop replay prototype packet."""

    source = Path(candidate_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = replay_prototype_payload(
        candidate_manifest_path=source,
        output_dir=target,
        top=top,
    )
    report = replay_prototype_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return ReplayPrototypeResult(
        ready=bool(payload["ready"]),
        case_count=int(payload["replayed_case_count"]),
        replay_track_count=int(aggregate["replay_track_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def replay_prototype_payload(
    candidate_manifest_path: Path,
    output_dir: Path,
    top: int,
) -> dict[str, object]:
    """Return deterministic replay/perturbation evidence for replay-ready cases."""

    if top < 1:
        raise ValueError("top must be at least 1.")

    candidate_payload = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    if candidate_payload.get("format") != REPLAY_CANDIDATE_FORMAT:
        raise ValueError(
            "Expected a replay-candidates manifest with format "
            f"{REPLAY_CANDIDATE_FORMAT}."
        )
    source_kind = str(candidate_payload.get("source_kind", "baseline_compare_study"))

    debug_manifest_path = Path(str(candidate_payload.get("source", "")))
    if not debug_manifest_path.exists():
        raise FileNotFoundError(
            f"Replay-candidates source debug manifest not found: {debug_manifest_path}"
        )
    debug_payload = json.loads(debug_manifest_path.read_text(encoding="utf-8"))
    debug_cases = _required_list(debug_payload, "cases")
    debug_by_key = _debug_case_lookup(debug_cases)
    candidates = _required_list(candidate_payload, "candidates")
    replay_ready = []
    skipped_candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        readiness = str(candidate.get("readiness", ""))
        if readiness in {"ready_for_regression_replay", "ready_for_improvement_replay"}:
            replay_ready.append(candidate)
        elif readiness.startswith("ready_for_"):
            skipped_candidates.append(
                {
                    "scenario_id": candidate.get("scenario_id"),
                    "source_name": candidate.get("source_name"),
                    "readiness": readiness,
                    "comparison_mode": candidate.get("comparison_mode", "unknown"),
                    "reason": (
                        "unsupported_replay_candidate_mode: this prototype "
                        "currently replays constant-velocity vs default "
                        "lane-aware candidates only."
                    ),
                }
            )
    replay_ready = replay_ready[:top]

    replay_cases = []
    for rank, candidate in enumerate(replay_ready, start=1):
        assert isinstance(candidate, dict)
        case = _matching_debug_case(candidate, debug_by_key)
        if case is None:
            skipped_candidates.append(
                {
                    "scenario_id": candidate.get("scenario_id"),
                    "source_name": candidate.get("source_name"),
                    "reason": "candidate_not_found_in_debug_manifest",
                }
            )
            continue
        replay_cases.append(
            _replay_case(
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
        "format": REPLAY_PROTOTYPE_FORMAT,
        "candidate_manifest": str(candidate_manifest_path),
        "candidate_format": candidate_payload.get("format"),
        "source_kind": source_kind,
        "debug_manifest": str(debug_manifest_path),
        "output_dir": str(output_dir),
        "ready": ready,
        "requested_top": top,
        "selected_candidate_count": len(replay_ready),
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
            "Open-loop deterministic replay over ScenarioLens baselines; not a "
            "closed-loop simulator, not Waymax/JAX execution, and not a Waymo "
            "benchmark claim."
        ),
    }


def replay_prototype_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a replay prototype payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    perturbations = _required_list(payload, "perturbations")
    skipped = _required_list(payload, "skipped_candidates")
    context_mode = str(payload.get("source_kind")) == "context_eval_set"
    lines = [
        "# ScenarioLens Context Open-Loop Replay Prototype"
        if context_mode
        else "# ScenarioLens Open-Loop Replay Prototype",
        "",
        (
            "This report executes the replay-ready portion of the context "
            "replay queue. It reloads selected context-evaluation seeds from "
            "local Waymo Motion shards, replays constant-velocity and "
            "lane-aware open-loop rollouts from the same anchor state, and "
            "applies small deterministic anchor-velocity perturbations to test "
            "whether each context-derived diagnostic remains stable."
        )
        if context_mode
        else (
            "This report takes the replay-candidate queue one step further: it "
            "reloads selected local Waymo Motion scenarios, replays the "
            "constant-velocity and lane-aware open-loop rollouts from the same "
            "anchor state, and applies small deterministic anchor-velocity "
            "perturbations to test whether each diagnostic remains stable."
        ),
        "",
        "It is intentionally scoped: this is not a closed-loop simulator, not "
        "Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files "
        "and local per-case replay packets stay out of git.",
        "",
        "## Scope",
        "",
        f"- Candidate manifest: `{payload['candidate_manifest']}`",
        f"- Source kind: `{payload.get('source_kind', 'baseline_compare_study')}`",
        f"- Debug manifest: `{payload['debug_manifest']}`",
        f"- Ready for replay analysis: {payload['ready']}",
        f"- Requested top candidates: {payload['requested_top']}",
        f"- Replay cases evaluated: {payload['replayed_case_count']}",
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
        f"| Regression cases replayed | {aggregate['regression_case_count']} |",
        f"| Improvement cases replayed | {aggregate['improvement_case_count']} |",
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
            "| Rank | Scenario | Case | Readiness | Targets | CV FDE | Lane FDE | FDE delta | Sign stability | Max delta swing |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not cases:
        lines.append("| n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | n/a | n/a |")
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
            f"{_meter_text(nominal['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(nominal['fde_improvement_m'])} | "
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
                f"- Nominal winner: {nominal['nominal_winner']}",
                f"- Nominal FDE delta: {_signed_meter_text(nominal['fde_improvement_m'])}",
                f"- Perturbation stability label: `{stability['label']}`",
                f"- Sign-preservation rate: {_percent_text(stability['sign_preservation_rate'])}",
                f"- Local replay packet: `{case['local_packet_path']}`",
                f"- Local SVG overlay: `{case['local_svg_path']}`",
                "",
                "Target replay rows:",
                "",
                "| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback |",
                "| --- | --- | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for track in tracks:
            assert isinstance(track, dict)
            lines.append(
                "| "
                f"`{track['track_id']}` | "
                f"`{track['agent_type']}` | "
                f"{_meter_text(track['constant_velocity_fde_m'])} | "
                f"{_meter_text(track['lane_aware_fde_m'])} | "
                f"{_signed_meter_text(track['fde_improvement_m'])} | "
                f"{track['lane_map_used']} | "
                f"`{track['lane_fallback_reason'] or 'none'}` |"
            )

        lines.extend(
            [
                "",
                "Perturbation trials:",
                "",
                "| Trial | FDE delta | Preserves expected sign | CV FDE | Lane FDE |",
                "| --- | ---: | --- | ---: | ---: |",
            ]
        )
        for trial in trials:
            assert isinstance(trial, dict)
            lines.append(
                "| "
                f"`{trial['label']}` | "
                f"{_signed_meter_text(trial['fde_improvement_m'])} | "
                f"{trial['preserves_expected_sign']} | "
                f"{_meter_text(trial['constant_velocity_fde_m'])} | "
                f"{_meter_text(trial['lane_aware_fde_m'])} |"
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
            "- Stable improvement candidates are useful positive controls for the lane-aware baseline.",
            "- Stable regression candidates are useful debugging targets because the warning persists under small anchor-state changes.",
            "- Sensitive candidates are still valuable: they identify cases where evaluation conclusions depend on small state-estimation differences.",
            "- Context-derived candidates keep their eval-set seed labels so "
            "signal, topology, regression, and fallback follow-up does not "
            "collapse into one aggregate score."
            if context_mode
            else "- Candidate labels should stay attached to replay packets so "
            "follow-up work can trace results back to the debug casebook.",
            "- Fallback-heavy candidates remain outside this replay prototype until map matching and coordinate-frame checks are resolved.",
            "- This is open-loop diagnostic evidence, not a production prediction model or closed-loop autonomy simulator.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _replay_case(
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
    packet_path = case_dir / "replay_packet.json"
    svg_path = case_dir / "nominal_replay.svg"

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

    nominal = compare_prediction_baselines(scenario)
    target_ids = tuple(track.track_id for track in nominal.track_results)
    trials = [
        _perturbation_trial(
            scenario=scenario,
            target_ids=target_ids,
            perturbation=perturbation,
            expected_sign=_expected_sign(candidate),
        )
        for perturbation in _PERTURBATIONS
    ]
    case_payload = {
        "ready": bool(input_ready),
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
        "nominal": _nominal_summary(nominal),
        "track_replays": _track_replays(nominal),
        "perturbation_trials": trials,
        "perturbation_stability": _perturbation_stability(
            nominal_delta=nominal.fde_improvement_m,
            expected_sign=_expected_sign(candidate),
            trials=trials,
        ),
        "local_packet_path": str(packet_path),
        "local_svg_path": str(svg_path),
    }
    _write_json(packet_path, case_payload)
    svg_path.write_text(
        scenario_svg(scenario, show_lane_aware_baseline=True),
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
    comparison = compare_prediction_baselines(perturbed)
    delta = comparison.fde_improvement_m
    preserves = _preserves_expected_sign(delta, expected_sign)
    return {
        "label": perturbation["label"],
        "speed_scale": perturbation["speed_scale"],
        "heading_delta_deg": perturbation["heading_delta_deg"],
        "constant_velocity_fde_m": comparison.constant_velocity_fde_m,
        "lane_aware_fde_m": comparison.lane_aware_fde_m,
        "fde_improvement_m": delta,
        "map_used_count": comparison.map_used_count,
        "fallback_count": comparison.fallback_count,
        "evaluated_track_count": comparison.evaluated_track_count,
        "preserves_expected_sign": preserves,
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


def _nominal_summary(comparison: PredictionBaselineComparison) -> dict[str, object]:
    delta = comparison.fde_improvement_m
    if delta is None:
        winner = "n/a"
    elif delta > 0:
        winner = "lane_aware"
    elif delta < 0:
        winner = "constant_velocity"
    else:
        winner = "tie"
    return {
        "target_source": comparison.target_source,
        "requested_target_count": comparison.requested_target_count,
        "evaluated_track_count": comparison.evaluated_track_count,
        "constant_velocity_ade_m": comparison.constant_velocity_ade_m,
        "constant_velocity_fde_m": comparison.constant_velocity_fde_m,
        "constant_velocity_miss_rate": comparison.constant_velocity_miss_rate,
        "lane_aware_ade_m": comparison.lane_aware_ade_m,
        "lane_aware_fde_m": comparison.lane_aware_fde_m,
        "lane_aware_miss_rate": comparison.lane_aware_miss_rate,
        "fde_improvement_m": delta,
        "map_used_count": comparison.map_used_count,
        "fallback_count": comparison.fallback_count,
        "nominal_winner": winner,
    }


def _track_replays(comparison: PredictionBaselineComparison) -> list[dict[str, object]]:
    return [
        {
            "track_id": row.track_id,
            "agent_type": row.agent_type,
            "constant_velocity_ade_m": row.constant_velocity_ade_m,
            "constant_velocity_fde_m": row.constant_velocity_fde_m,
            "lane_aware_ade_m": row.lane_aware_ade_m,
            "lane_aware_fde_m": row.lane_aware_fde_m,
            "fde_improvement_m": row.fde_improvement_m,
            "lane_map_used": row.lane_map_used,
            "lane_fallback_reason": row.lane_fallback_reason,
        }
        for row in comparison.track_results
    ]


def _perturbation_stability(
    nominal_delta: float | None,
    expected_sign: int,
    trials: list[dict[str, object]],
) -> dict[str, object]:
    valid_deltas = [
        float(trial["fde_improvement_m"])
        for trial in trials
        if trial.get("fde_improvement_m") is not None
    ]
    valid_count = len(valid_deltas)
    sign_preserving = sum(
        bool(trial["preserves_expected_sign"])
        for trial in trials
        if trial.get("fde_improvement_m") is not None
    )
    sign_rate = (sign_preserving / valid_count) if valid_count else None
    swings = (
        [abs(delta - nominal_delta) for delta in valid_deltas]
        if nominal_delta is not None
        else []
    )
    label = _stability_label(
        expected_sign=expected_sign,
        valid_count=valid_count,
        sign_preserving=sign_preserving,
    )
    return {
        "label": label,
        "expected_sign": "positive" if expected_sign > 0 else "negative",
        "valid_trial_count": valid_count,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "min_fde_delta_m": round(min(valid_deltas), 3) if valid_deltas else None,
        "max_fde_delta_m": round(max(valid_deltas), 3) if valid_deltas else None,
        "max_delta_swing_m": round(max(swings), 3) if swings else None,
    }


def _stability_label(
    expected_sign: int,
    valid_count: int,
    sign_preserving: int,
) -> str:
    if valid_count == 0:
        return "not_evaluable"
    if sign_preserving == valid_count and expected_sign < 0:
        return "stable_regression_warning"
    if sign_preserving == valid_count and expected_sign > 0:
        return "stable_positive_control"
    if sign_preserving == 0:
        return "sign_flipped_under_all_perturbations"
    return "sensitive_to_anchor_perturbation"


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
    return {
        "replayed_case_count": len(replayed),
        "replay_track_count": sum(
            len(_required_list(case, "track_replays")) for case in replayed
        ),
        "perturbation_trial_count": valid_trials,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "regression_case_count": sum(
            str(case.get("readiness")) == "ready_for_regression_replay"
            for case in replayed
        ),
        "improvement_case_count": sum(
            str(case.get("readiness")) == "ready_for_improvement_replay"
            for case in replayed
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


def _expected_sign(candidate: dict[str, object]) -> int:
    readiness = str(candidate.get("readiness", ""))
    if readiness == "ready_for_regression_replay":
        return -1
    return 1


def _preserves_expected_sign(value: float | None, expected_sign: int) -> bool:
    if value is None:
        return False
    return value > 0 if expected_sign > 0 else value < 0


def _why_replayed(candidate: dict[str, object]) -> str:
    readiness = str(candidate.get("readiness", ""))
    if readiness == "ready_for_regression_replay":
        return (
            "Regression candidate: replay checks whether the lane-aware warning "
            "persists under small anchor-state perturbations."
        )
    if readiness == "ready_for_improvement_replay":
        return (
            "Improvement candidate: replay checks whether the map-conditioned "
            "advantage survives small anchor-state perturbations."
        )
    return "Candidate was replayed for manual diagnostic review."


def _empty_nominal() -> dict[str, object]:
    return {
        "target_source": "n/a",
        "requested_target_count": 0,
        "evaluated_track_count": 0,
        "constant_velocity_ade_m": None,
        "constant_velocity_fde_m": None,
        "constant_velocity_miss_rate": None,
        "lane_aware_ade_m": None,
        "lane_aware_fde_m": None,
        "lane_aware_miss_rate": None,
        "fde_improvement_m": None,
        "map_used_count": 0,
        "fallback_count": 0,
        "nominal_winner": "n/a",
    }


def _empty_stability() -> dict[str, object]:
    return {
        "label": "not_evaluable",
        "expected_sign": "n/a",
        "valid_trial_count": 0,
        "sign_preserving_trial_count": 0,
        "sign_preservation_rate": None,
        "min_fde_delta_m": None,
        "max_fde_delta_m": None,
        "max_delta_swing_m": None,
    }


def _meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    return f"{number:.3f} m"


def _signed_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    if not isfinite(number):
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _percent_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_slug(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        elif char in {"-", "_", " "}:
            safe.append("-")
    return "-".join("".join(safe).split("-"))[:120] or "case"


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
