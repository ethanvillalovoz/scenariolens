from __future__ import annotations

import json
from dataclasses import dataclass, replace
from math import cos, isfinite, radians, sin
from pathlib import Path

from scenariolens.failure_study import load_failure_study_input
from scenariolens.lane_continuation import _lane_link_baseline_with_details
from scenariolens.lane_continuation_candidates import (
    LANE_CONTINUATION_CANDIDATES_FORMAT,
)
from scenariolens.prediction import (
    DEFAULT_MISS_THRESHOLD_M,
    LANE_MATCH_THRESHOLD_M,
    PredictionBaselineSummary,
    PredictionTrackResult,
    _anchor_index,
    constant_velocity_baseline,
    heading_aware_lane_baseline,
    lane_aware_baseline,
)
from scenariolens.schema import AgentTrack, Scenario, State

LANE_CONTINUATION_REPLAY_FORMAT = (
    "scenariolens.lane_continuation_replay_prototype.v1"
)
LANE_CONTINUATION_REPLAY_INPUT_FORMATS = ("native", "scenariolens-json")

_REPLAY_BUCKETS = ("improvement_replay_control", "regression_replay_debug")
_TOPOLOGY_BUCKET = "topology_audit"
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
class LaneContinuationReplayResult:
    """Files produced by a lane-continuation replay prototype run."""

    ready: bool
    case_count: int
    replay_case_count: int
    topology_case_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_replay_prototype(
    candidate_manifest_path: str | Path,
    output_dir: str | Path,
    top_per_bucket: int = 5,
    input_format: str = "native",
    max_scenarios_per_source: int | None = 25,
    public_report_path: str | Path | None = None,
) -> LaneContinuationReplayResult:
    """Generate a laptop-safe lane-continuation replay/audit packet."""

    source = Path(candidate_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_replay_payload(
        candidate_manifest_path=source,
        output_dir=target,
        top_per_bucket=top_per_bucket,
        input_format=input_format,
        max_scenarios_per_source=max_scenarios_per_source,
    )
    report = lane_continuation_replay_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationReplayResult(
        ready=bool(payload["ready"]),
        case_count=int(payload["case_count"]),
        replay_case_count=int(aggregate["replayed_case_count"]),
        topology_case_count=int(aggregate["topology_probe_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_replay_payload(
    candidate_manifest_path: Path,
    output_dir: Path,
    top_per_bucket: int,
    input_format: str,
    max_scenarios_per_source: int | None,
) -> dict[str, object]:
    """Return deterministic replay evidence for lane-continuation candidates."""

    if top_per_bucket < 1:
        raise ValueError("top-per-bucket must be at least 1.")
    if input_format not in LANE_CONTINUATION_REPLAY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported lane-continuation replay input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(LANE_CONTINUATION_REPLAY_INPUT_FORMATS)}"
        )
    if max_scenarios_per_source is not None and max_scenarios_per_source < 1:
        raise ValueError("max-scenarios-per-source must be at least 1 when set.")

    candidate_payload = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    if candidate_payload.get("format") != LANE_CONTINUATION_CANDIDATES_FORMAT:
        raise ValueError(
            "Expected a lane-continuation candidate manifest with format "
            f"{LANE_CONTINUATION_CANDIDATES_FORMAT}."
        )

    selected = _select_candidates(
        _required_list(candidate_payload, "candidates"),
        top_per_bucket=top_per_bucket,
    )
    source_cache: dict[tuple[str, str, int | None], tuple[bool, dict[str, object] | None, tuple[Scenario, ...]]] = {}
    cases: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    for rank, candidate in enumerate(selected, start=1):
        case = _candidate_case(
            candidate=candidate,
            output_dir=output_dir,
            rank=rank,
            input_format=input_format,
            max_scenarios_per_source=max_scenarios_per_source,
            source_cache=source_cache,
        )
        if bool(case.get("selected")):
            cases.append(case)
        else:
            skipped.append(case)

    aggregate = _aggregate_cases(cases)
    return {
        "format": LANE_CONTINUATION_REPLAY_FORMAT,
        "candidate_manifest": str(candidate_manifest_path),
        "candidate_format": candidate_payload.get("format"),
        "study_manifest": candidate_payload.get("study_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(candidate_payload.get("ready")) and any(
            bool(case.get("ready")) for case in cases
        ),
        "input_format": input_format,
        "max_scenarios_per_source": max_scenarios_per_source,
        "requested_top_per_bucket": top_per_bucket,
        "selected_candidate_count": len(selected),
        "case_count": len(cases),
        "skipped_candidate_count": len(skipped),
        "perturbations": list(_PERTURBATIONS),
        "aggregate": aggregate,
        "cases": cases,
        "skipped_candidates": skipped,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "case_dir": "cases/",
        },
        "scope_note": (
            "Open-loop lane-continuation replay prototype only; this is not "
            "route planning, not closed-loop simulation, not Waymax/JAX "
            "execution, and not a Waymo benchmark claim."
        ),
    }


def lane_continuation_replay_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a lane-continuation replay payload."""

    aggregate = _required_mapping(payload, "aggregate")
    cases = _required_list(payload, "cases")
    perturbations = _required_list(payload, "perturbations")
    skipped = _required_list(payload, "skipped_candidates")
    replay_cases = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("bucket") in _REPLAY_BUCKETS
    ]
    topology_cases = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("bucket") == _TOPOLOGY_BUCKET
    ]

    lines = [
        "# ScenarioLens Lane-Continuation Replay Prototype",
        "",
        "This report executes the next laptop-safe step after the "
        "lane-continuation candidate plan. It reloads selected local scenarios, "
        "replays nearest-lane and linked-lane continuation rollouts for the "
        "queued target tracks, and applies small deterministic anchor-velocity "
        "perturbations to check whether each improvement or regression remains "
        "stable.",
        "",
        "Topology-audit candidates are re-probed as blockers instead of being "
        "treated as valid route predictions. The report is intentionally "
        "scoped: this is not route planning, not closed-loop simulation, not "
        "Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files "
        "and local replay packets stay out of git.",
        "",
        "## Scope",
        "",
        f"- Candidate manifest: `{payload['candidate_manifest']}`",
        f"- Study manifest: `{payload.get('study_manifest')}`",
        f"- Ready for replay analysis: {payload['ready']}",
        f"- Input format: `{payload['input_format']}`",
        f"- Max scenarios per source: {payload['max_scenarios_per_source']}",
        f"- Top candidates per bucket: {payload['requested_top_per_bucket']}",
        f"- Selected candidates: {payload['selected_candidate_count']}",
        "- Raw scenario data committed: no",
        "- Local replay packets committed: no",
        "",
        "## Replay Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Evaluated cases | {aggregate['case_count']} |",
        f"| Replay cases | {aggregate['replayed_case_count']} |",
        f"| Topology probes | {aggregate['topology_probe_count']} |",
        f"| Replay targets | {aggregate['replay_track_count']} |",
        f"| Perturbation trials | {aggregate['perturbation_trial_count']} |",
        f"| Sign-preserving trials | {aggregate['sign_preserving_trial_count']} |",
        f"| Sign-preservation rate | {_percent_text(aggregate['sign_preservation_rate'])} |",
        f"| Nominal lane-link improvements | {aggregate['nominal_improvement_count']} |",
        f"| Nominal lane-link regressions | {aggregate['nominal_regression_count']} |",
        f"| Topology blockers confirmed | {aggregate['topology_blocker_count']} |",
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
            "| Rank | Queue | Scenario | Track | Readiness | Nearest FDE | Lane-link FDE | Delta | Link status | Sign stability | Max swing |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    if not replay_cases:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for case in replay_cases:
        assert isinstance(case, dict)
        nominal = _required_mapping(case, "nominal")
        stability = _required_mapping(case, "perturbation_stability")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['bucket']}` | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{case['readiness']}` | "
            f"{_meter_text(nominal['nearest_lane_fde_m'])} | "
            f"{_meter_text(nominal['lane_link_fde_m'])} | "
            f"{_signed_meter_text(nominal['lane_link_improvement_over_nearest_m'])} | "
            f"`{nominal['lane_link_status']}` | "
            f"{stability['sign_preserving_trial_count']}/{stability['valid_trial_count']} | "
            f"{_meter_text(stability['max_delta_swing_m'])} |"
        )

    lines.extend(
        [
            "",
            "## Topology Probes",
            "",
            "| Rank | Scenario | Track | Link status | Link count | Nearest FDE | Lane-link FDE | First blocker |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    if not topology_cases:
        lines.append("| n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a |")
    for case in topology_cases:
        assert isinstance(case, dict)
        nominal = _required_mapping(case, "nominal")
        blockers = _required_list(case, "blockers")
        lines.append(
            "| "
            f"{case['rank']} | "
            f"`{case['scenario_id']}` | "
            f"`{case['track_id']}` | "
            f"`{nominal['lane_link_status']}` | "
            f"{nominal['lane_link_count']} | "
            f"{_meter_text(nominal['nearest_lane_fde_m'])} | "
            f"{_meter_text(nominal['lane_link_fde_m'])} | "
            f"{blockers[0] if blockers else 'Manual topology review.'} |"
        )

    for case in cases:
        if not isinstance(case, dict):
            continue
        nominal = _required_mapping(case, "nominal")
        conclusion = _required_mapping(case, "conclusion")
        trials = _required_list(case, "perturbation_trials")
        blockers = _required_list(case, "blockers")
        lines.extend(
            [
                "",
                f"## `{case['scenario_id']}` / track `{case['track_id']}`",
                "",
                f"- Queue: `{case['bucket']}`",
                f"- Readiness: `{case['readiness']}`",
                f"- Source: `{case['source_name']}`",
                f"- Result: **{conclusion['label']}**",
                f"- Why: {conclusion['reason']}",
                f"- Recommended next action: {conclusion['next_action']}",
                f"- Feature chain: {_feature_chain_text(nominal)}",
                f"- Link status/count: `{nominal['lane_link_status']}` / {nominal['lane_link_count']}",
                f"- Local replay packet: `{case['local_packet_path']}`",
                "",
                "Target replay row:",
                "",
                "| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
                "| "
                f"{_meter_text(nominal['constant_velocity_fde_m'])} | "
                f"{_meter_text(nominal['nearest_lane_fde_m'])} | "
                f"{_meter_text(nominal['heading_lane_fde_m'])} | "
                f"{_meter_text(nominal['lane_link_fde_m'])} | "
                f"{_signed_meter_text(nominal['lane_link_improvement_over_nearest_m'])} | "
                f"{_signed_meter_text(nominal['lane_link_improvement_over_constant_m'])} | "
                f"{nominal['lane_end_clamp_risk_after']} |",
            ]
        )
        if trials:
            lines.extend(
                [
                    "",
                    "Perturbation trials:",
                    "",
                    "| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |",
                    "| --- | ---: | --- | ---: | ---: | --- |",
                ]
            )
            for trial in trials:
                assert isinstance(trial, dict)
                lines.append(
                    "| "
                    f"`{trial['label']}` | "
                    f"{_signed_meter_text(trial['lane_link_improvement_over_nearest_m'])} | "
                    f"{trial['preserves_expected_sign']} | "
                    f"{_meter_text(trial['nearest_lane_fde_m'])} | "
                    f"{_meter_text(trial['lane_link_fde_m'])} | "
                    f"`{trial['lane_link_status']}` |"
                )
        if blockers:
            lines.extend(["", "Blockers / cautions:"])
            lines.extend(f"- {blocker}" for blocker in blockers)

    if skipped:
        lines.extend(["", "## Skipped Candidates", ""])
        for item in skipped:
            assert isinstance(item, dict)
            lines.append(
                f"- `{item.get('scenario_id', 'unknown')}` track "
                f"`{item.get('track_id', 'unknown')}`: {item.get('reason', 'unknown')}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stable improvement controls are useful because they prove the lane-link mechanism on cases where nearest-lane clamping was misleading.",
            "- Stable regressions are useful debugging targets because linked-lane following can still choose the wrong route or out-run available topology.",
            "- Topology probes are blockers, not model-performance claims; they identify missing links, map-feature caps, or parser coverage work.",
            "- This keeps ScenarioLens honest: public outputs are diagnostic summaries, while raw Waymo files and local replay packets remain ignored.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _select_candidates(
    candidates: list[object],
    top_per_bucket: int,
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for bucket in (*_REPLAY_BUCKETS, _TOPOLOGY_BUCKET):
        rows = [
            candidate
            for candidate in candidates
            if isinstance(candidate, dict) and candidate.get("bucket") == bucket
        ]
        selected.extend(rows[:top_per_bucket])
    return selected


def _candidate_case(
    candidate: dict[str, object],
    output_dir: Path,
    rank: int,
    input_format: str,
    max_scenarios_per_source: int | None,
    source_cache: dict[
        tuple[str, str, int | None],
        tuple[bool, dict[str, object] | None, tuple[Scenario, ...]],
    ],
) -> dict[str, object]:
    bucket = str(candidate.get("bucket", "unknown"))
    source_input = Path(str(candidate.get("source_input", "")))
    track_id = str(candidate.get("track_id", ""))
    scenario_id = str(candidate.get("scenario_id", ""))
    case_slug = _safe_slug(f"{rank}-{bucket}-{scenario_id}-{track_id}")
    case_dir = output_dir / "cases" / case_slug
    case_dir.mkdir(parents=True, exist_ok=True)
    packet_path = case_dir / "lane_continuation_replay_packet.json"

    source_key = (str(source_input), input_format, max_scenarios_per_source)
    if source_key not in source_cache:
        source_cache[source_key] = load_failure_study_input(
            source=source_input,
            input_format=input_format,
            max_scenarios=max_scenarios_per_source,
        )
    input_ready, preflight, scenarios = source_cache[source_key]
    scenario = _find_scenario(scenarios, scenario_id)
    if scenario is None:
        payload = _unavailable_case(
            candidate=candidate,
            rank=rank,
            input_ready=input_ready,
            preflight=preflight or {},
            packet_path=packet_path,
            reason="scenario_not_found_in_loaded_source",
        )
        _write_json(packet_path, payload)
        return payload

    nominal = _nominal_track_summary(scenario=scenario, track_id=track_id)
    expected_sign = _expected_sign(bucket)
    replay_enabled = bucket in _REPLAY_BUCKETS
    trials = (
        [
            _perturbation_trial(
                scenario=scenario,
                track_id=track_id,
                perturbation=perturbation,
                expected_sign=expected_sign,
            )
            for perturbation in _PERTURBATIONS
        ]
        if replay_enabled and bool(nominal["evaluated"])
        else []
    )
    stability = _perturbation_stability(
        nominal_delta=nominal["lane_link_improvement_over_nearest_m"],
        expected_sign=expected_sign,
        trials=trials,
    )
    conclusion = _case_conclusion(
        bucket=bucket,
        nominal=nominal,
        stability=stability,
    )
    payload = {
        "selected": True,
        "ready": bool(input_ready) and bool(nominal["evaluated"]),
        "rank": rank,
        "bucket": bucket,
        "readiness": candidate.get("readiness", "unknown"),
        "scenario_id": scenario.scenario_id,
        "track_id": track_id,
        "source_input": str(source_input),
        "source_name": candidate.get("source_name", source_input.name),
        "input_format": input_format,
        "input_ready": input_ready,
        "preflight": preflight or {},
        "candidate_evidence": candidate.get("evidence", {}),
        "why_replayed": candidate.get("why_it_matters", ""),
        "nominal": nominal,
        "perturbation_trials": trials,
        "perturbation_stability": stability,
        "conclusion": conclusion,
        "blockers": _blockers(bucket=bucket, nominal=nominal),
        "local_packet_path": str(packet_path),
    }
    _write_json(packet_path, payload)
    return payload


def _nominal_track_summary(scenario: Scenario, track_id: str) -> dict[str, object]:
    constant = constant_velocity_baseline(scenario)
    nearest = lane_aware_baseline(scenario)
    heading = heading_aware_lane_baseline(scenario)
    lane_link, lane_link_details = _lane_link_baseline_with_details(
        scenario=scenario,
        miss_threshold_m=DEFAULT_MISS_THRESHOLD_M,
        lane_match_threshold_m=LANE_MATCH_THRESHOLD_M,
        max_hops=2,
    )
    constant_result = _track_result(constant, track_id)
    nearest_result = _track_result(nearest, track_id)
    heading_result = _track_result(heading, track_id)
    lane_link_result = _track_result(lane_link, track_id)
    link_detail = lane_link_details.get(track_id, _empty_lane_link_detail())
    if (
        constant_result is None
        or nearest_result is None
        or heading_result is None
        or lane_link_result is None
    ):
        empty = _empty_nominal()
        empty["lane_link_status"] = link_detail.get("status", "missing_track_result")
        empty["feature_chain"] = link_detail.get("feature_chain", [])
        return empty
    delta_nearest = _optional_delta(nearest_result.fde_m, lane_link_result.fde_m)
    delta_constant = _optional_delta(constant_result.fde_m, lane_link_result.fde_m)
    return {
        "evaluated": True,
        "target_source": constant.target_source,
        "requested_target_count": constant.requested_target_count,
        "track_id": track_id,
        "agent_type": constant_result.agent_type,
        "constant_velocity_ade_m": constant_result.ade_m,
        "constant_velocity_fde_m": constant_result.fde_m,
        "nearest_lane_ade_m": nearest_result.ade_m,
        "nearest_lane_fde_m": nearest_result.fde_m,
        "heading_lane_ade_m": heading_result.ade_m,
        "heading_lane_fde_m": heading_result.fde_m,
        "lane_link_ade_m": lane_link_result.ade_m,
        "lane_link_fde_m": lane_link_result.fde_m,
        "lane_link_improvement_over_nearest_m": delta_nearest,
        "lane_link_improvement_over_constant_m": delta_constant,
        "lane_link_map_used": lane_link_result.map_used,
        "lane_link_fallback_reason": lane_link_result.fallback_reason,
        "lane_link_status": link_detail.get("status", "unknown"),
        "lane_link_count": int(link_detail.get("link_count", 0) or 0),
        "feature_chain": link_detail.get("feature_chain", []),
        "selected_feature_id": link_detail.get("selected_feature_id"),
        "base_remaining_m": _optional_float(link_detail.get("base_remaining_m")),
        "route_remaining_m": _optional_float(link_detail.get("route_remaining_m")),
        "horizon_travel_m": _optional_float(link_detail.get("horizon_travel_m")),
        "lane_end_clamp_risk_before": bool(
            link_detail.get("lane_end_clamp_risk_before")
        ),
        "lane_end_clamp_risk_after": bool(
            link_detail.get("lane_end_clamp_risk_after")
        ),
    }


def _perturbation_trial(
    scenario: Scenario,
    track_id: str,
    perturbation: dict[str, object],
    expected_sign: int,
) -> dict[str, object]:
    perturbed = _perturb_anchor_velocity(
        scenario=scenario,
        track_id=track_id,
        speed_scale=float(perturbation["speed_scale"]),
        heading_delta_deg=float(perturbation["heading_delta_deg"]),
    )
    nominal = _nominal_track_summary(scenario=perturbed, track_id=track_id)
    delta = _optional_float(nominal.get("lane_link_improvement_over_nearest_m"))
    return {
        "label": perturbation["label"],
        "speed_scale": perturbation["speed_scale"],
        "heading_delta_deg": perturbation["heading_delta_deg"],
        "constant_velocity_fde_m": nominal["constant_velocity_fde_m"],
        "nearest_lane_fde_m": nominal["nearest_lane_fde_m"],
        "heading_lane_fde_m": nominal["heading_lane_fde_m"],
        "lane_link_fde_m": nominal["lane_link_fde_m"],
        "lane_link_improvement_over_nearest_m": delta,
        "lane_link_status": nominal["lane_link_status"],
        "lane_link_count": nominal["lane_link_count"],
        "lane_end_clamp_risk_after": nominal["lane_end_clamp_risk_after"],
        "preserves_expected_sign": _preserves_expected_sign(delta, expected_sign),
    }


def _perturb_anchor_velocity(
    scenario: Scenario,
    track_id: str,
    speed_scale: float,
    heading_delta_deg: float,
) -> Scenario:
    tracks = []
    for track in scenario.tracks:
        if track.agent_id != track_id:
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


def _perturbation_stability(
    nominal_delta: object,
    expected_sign: int,
    trials: list[dict[str, object]],
) -> dict[str, object]:
    nominal = _optional_float(nominal_delta)
    trial_deltas = [
        _optional_float(trial.get("lane_link_improvement_over_nearest_m"))
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
    elif sign_preserving == valid_count and expected_sign > 0:
        label = "stable_positive_control"
    elif sign_preserving == valid_count and expected_sign < 0:
        label = "stable_regression_warning"
    elif sign_preserving > 0:
        label = "sensitive_to_anchor_perturbation"
    else:
        label = "sign_flipped_under_perturbation"
    return {
        "label": label,
        "expected_sign": "positive" if expected_sign > 0 else "negative",
        "valid_trial_count": valid_count,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "min_fde_delta_m": round(min(valid_deltas), 3) if valid_deltas else None,
        "max_fde_delta_m": round(max(valid_deltas), 3) if valid_deltas else None,
        "max_delta_swing_m": round(max_swing, 3) if max_swing is not None else None,
    }


def _case_conclusion(
    bucket: str,
    nominal: dict[str, object],
    stability: dict[str, object],
) -> dict[str, object]:
    if not bool(nominal.get("evaluated")):
        return _conclusion(
            "not_evaluable",
            "The queued target was not available in all replay baselines.",
            "Confirm local source data and target-selection metadata before rerunning.",
        )
    link_count = int(nominal.get("lane_link_count", 0) or 0)
    delta = _optional_float(nominal.get("lane_link_improvement_over_nearest_m"))
    if bucket == _TOPOLOGY_BUCKET or link_count <= 0:
        return _conclusion(
            "topology_blocker",
            "The selected feature still lacks a usable linked-lane chain.",
            "Audit parsed lane links, map-feature caps, and link direction before replaying this case.",
        )
    stable = str(stability.get("label", "")).startswith("stable_")
    if bucket == "improvement_replay_control" and delta is not None and delta > 0:
        return _conclusion(
            "stable_improvement_control" if stable else "sensitive_improvement_control",
            "Lane-link continuation improves the nearest-lane rollout for this replayed target.",
            "Use this as a positive control before tuning harder continuation regressions.",
        )
    if bucket == "regression_replay_debug" and delta is not None and delta < 0:
        return _conclusion(
            "stable_regression_debug" if stable else "sensitive_regression_debug",
            "Lane-link continuation remains worse than nearest-lane for this replayed target.",
            "Inspect route choice, lane geometry, and future intent before changing the selector.",
        )
    return _conclusion(
        "candidate_result_changed",
        "The replayed nominal sign differs from the candidate-plan expectation.",
        "Regenerate the candidate plan or inspect whether parser/input settings changed.",
    )


def _blockers(bucket: str, nominal: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    if bucket == _TOPOLOGY_BUCKET or int(nominal.get("lane_link_count", 0) or 0) <= 0:
        blockers.append("No usable parsed linked-lane chain is available yet.")
    if bool(nominal.get("lane_end_clamp_risk_after")):
        blockers.append(
            "The target still out-travels the linked lane chain within the prediction horizon."
        )
    blockers.append("Raw Waymo TFRecords and local replay packets must stay ignored.")
    return blockers


def _aggregate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    ready_cases = [case for case in cases if bool(case.get("ready"))]
    replay_cases = [
        case for case in ready_cases if str(case.get("bucket")) in _REPLAY_BUCKETS
    ]
    topology_cases = [
        case for case in ready_cases if str(case.get("bucket")) == _TOPOLOGY_BUCKET
    ]
    stability_rows = [
        _required_mapping(case, "perturbation_stability") for case in replay_cases
    ]
    valid_trials = sum(int(row["valid_trial_count"]) for row in stability_rows)
    sign_preserving = sum(
        int(row["sign_preserving_trial_count"]) for row in stability_rows
    )
    sign_rate = sign_preserving / valid_trials if valid_trials else None
    nominal_rows = [_required_mapping(case, "nominal") for case in ready_cases]
    return {
        "case_count": len(cases),
        "ready_case_count": len(ready_cases),
        "replayed_case_count": len(replay_cases),
        "topology_probe_count": len(topology_cases),
        "replay_track_count": len(replay_cases),
        "perturbation_trial_count": valid_trials,
        "sign_preserving_trial_count": sign_preserving,
        "sign_preservation_rate": round(sign_rate, 3) if sign_rate is not None else None,
        "improvement_replay_count": sum(
            str(case.get("bucket")) == "improvement_replay_control"
            for case in replay_cases
        ),
        "regression_replay_count": sum(
            str(case.get("bucket")) == "regression_replay_debug"
            for case in replay_cases
        ),
        "nominal_improvement_count": sum(
            (_optional_float(row.get("lane_link_improvement_over_nearest_m")) or 0.0)
            > 0.0
            for row in nominal_rows
        ),
        "nominal_regression_count": sum(
            (_optional_float(row.get("lane_link_improvement_over_nearest_m")) or 0.0)
            < 0.0
            for row in nominal_rows
        ),
        "topology_blocker_count": sum(
            int(row.get("lane_link_count", 0) or 0) <= 0 for row in nominal_rows
        ),
    }


def _unavailable_case(
    candidate: dict[str, object],
    rank: int,
    input_ready: bool,
    preflight: dict[str, object],
    packet_path: Path,
    reason: str,
) -> dict[str, object]:
    return {
        "selected": True,
        "ready": False,
        "rank": rank,
        "bucket": candidate.get("bucket", "unknown"),
        "readiness": candidate.get("readiness", "unknown"),
        "scenario_id": candidate.get("scenario_id", ""),
        "track_id": candidate.get("track_id", ""),
        "source_input": candidate.get("source_input", ""),
        "source_name": candidate.get("source_name", ""),
        "input_ready": input_ready,
        "preflight": preflight,
        "reason": reason,
        "candidate_evidence": candidate.get("evidence", {}),
        "nominal": _empty_nominal(),
        "perturbation_trials": [],
        "perturbation_stability": _empty_stability(),
        "conclusion": _conclusion(
            "not_evaluable",
            "The local scenario could not be reloaded for this candidate.",
            "Confirm the raw/local source path and max-scenario window, then rerun.",
        ),
        "blockers": ["Local source data is required for replay."],
        "local_packet_path": str(packet_path),
    }


def _track_result(
    summary: PredictionBaselineSummary,
    track_id: str,
) -> PredictionTrackResult | None:
    for result in summary.track_results:
        if result.track_id == track_id:
            return result
    return None


def _find_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str,
) -> Scenario | None:
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _expected_sign(bucket: str) -> int:
    if bucket == "regression_replay_debug":
        return -1
    return 1


def _preserves_expected_sign(value: float | None, expected_sign: int) -> bool:
    if value is None:
        return False
    return value > 0 if expected_sign > 0 else value < 0


def _conclusion(label: str, reason: str, next_action: str) -> dict[str, object]:
    return {
        "label": label,
        "reason": reason,
        "next_action": next_action,
    }


def _empty_lane_link_detail() -> dict[str, object]:
    return {
        "status": "missing_lane_link_detail",
        "selected_feature_id": None,
        "feature_chain": [],
        "link_count": 0,
        "base_remaining_m": None,
        "route_remaining_m": None,
        "horizon_travel_m": None,
        "lane_end_clamp_risk_before": False,
        "lane_end_clamp_risk_after": False,
    }


def _empty_nominal() -> dict[str, object]:
    return {
        "evaluated": False,
        "target_source": "n/a",
        "requested_target_count": 0,
        "track_id": "",
        "agent_type": "unknown",
        "constant_velocity_ade_m": None,
        "constant_velocity_fde_m": None,
        "nearest_lane_ade_m": None,
        "nearest_lane_fde_m": None,
        "heading_lane_ade_m": None,
        "heading_lane_fde_m": None,
        "lane_link_ade_m": None,
        "lane_link_fde_m": None,
        "lane_link_improvement_over_nearest_m": None,
        "lane_link_improvement_over_constant_m": None,
        "lane_link_map_used": False,
        "lane_link_fallback_reason": None,
        "lane_link_status": "not_evaluable",
        "lane_link_count": 0,
        "feature_chain": [],
        "selected_feature_id": None,
        "base_remaining_m": None,
        "route_remaining_m": None,
        "horizon_travel_m": None,
        "lane_end_clamp_risk_before": False,
        "lane_end_clamp_risk_after": False,
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


def _feature_chain_text(nominal: dict[str, object]) -> str:
    chain = nominal.get("feature_chain")
    if not isinstance(chain, list) or not chain:
        return "n/a"
    return " -> ".join(str(item) for item in chain)


def _optional_delta(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 3)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _meter_text(value: object) -> str:
    number = _optional_float(value)
    if number is None or not isfinite(number):
        return "n/a"
    return f"{number:.3f} m"


def _signed_meter_text(value: object) -> str:
    number = _optional_float(value)
    if number is None or not isfinite(number):
        return "n/a"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _percent_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.1f}%"


def _safe_slug(value: str) -> str:
    slug = "".join(
        character.lower() if character.isalnum() else "-"
        for character in str(value)
    )
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:120] or "case"


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
