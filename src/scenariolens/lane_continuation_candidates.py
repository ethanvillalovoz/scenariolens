from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from scenariolens.lane_continuation import LANE_CONTINUATION_STUDY_FORMAT

LANE_CONTINUATION_CANDIDATES_FORMAT = (
    "scenariolens.lane_continuation_candidates.v1"
)


@dataclass(frozen=True)
class LaneContinuationCandidateResult:
    """Files produced by a lane-continuation replay/audit queue."""

    ready: bool
    candidate_count: int
    replay_candidate_count: int
    audit_candidate_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_candidate_plan(
    study_manifest_path: str | Path,
    output_dir: str | Path,
    top_per_bucket: int = 5,
    public_report_path: str | Path | None = None,
) -> LaneContinuationCandidateResult:
    """Generate a public-safe candidate queue from a continuation study."""

    source = Path(study_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_candidate_payload(
        study_manifest_path=source,
        output_dir=target,
        top_per_bucket=top_per_bucket,
    )
    report = lane_continuation_candidate_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationCandidateResult(
        ready=bool(payload["ready"]),
        candidate_count=int(payload["candidate_count"]),
        replay_candidate_count=int(aggregate["replay_candidate_count"]),
        audit_candidate_count=int(aggregate["topology_audit_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_candidate_payload(
    study_manifest_path: Path,
    output_dir: Path,
    top_per_bucket: int,
) -> dict[str, object]:
    """Return deterministic replay/audit candidate metadata from a study."""

    if top_per_bucket < 1:
        raise ValueError("top-per-bucket must be at least 1.")

    study = json.loads(study_manifest_path.read_text(encoding="utf-8"))
    if study.get("format") != LANE_CONTINUATION_STUDY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation study manifest with format "
            f"{LANE_CONTINUATION_STUDY_FORMAT}."
        )

    candidates = [
        *(
            _candidate_from_track(
                track=track,
                bucket="improvement_replay_control",
            )
            for track in _required_list(study, "top_improvements")[:top_per_bucket]
            if isinstance(track, dict)
        ),
        *(
            _candidate_from_track(
                track=track,
                bucket="regression_replay_debug",
            )
            for track in _required_list(study, "top_regressions")[:top_per_bucket]
            if isinstance(track, dict)
        ),
        *(
            _candidate_from_track(
                track=track,
                bucket="topology_audit",
            )
            for track in _required_list(study, "top_topology_gaps")[:top_per_bucket]
            if isinstance(track, dict)
        ),
    ]
    candidates = sorted(
        candidates,
        key=lambda candidate: (
            _bucket_rank(str(candidate["bucket"])),
            -float(candidate["priority_score"]),
            str(candidate["scenario_id"]),
            str(candidate["track_id"]),
        ),
    )
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank

    return {
        "format": LANE_CONTINUATION_CANDIDATES_FORMAT,
        "study_manifest": str(study_manifest_path),
        "study_format": study.get("format"),
        "output_dir": str(output_dir),
        "ready": bool(study.get("ready")) and bool(candidates),
        "top_per_bucket": top_per_bucket,
        "study_summary": {
            "source_count": study.get("source_count"),
            "scenario_count": study.get("scenario_count"),
            "candidate_case_count": study.get("candidate_case_count"),
            "candidate_track_count": study.get("candidate_track_count"),
            "aggregate": study.get("aggregate", {}),
        },
        "candidate_count": len(candidates),
        "aggregate": _aggregate_candidates(candidates),
        "candidates": candidates,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Lane-continuation candidate plan only; this is not route planning, "
            "not closed-loop simulation, not a completed Waymax/JAX integration, "
            "and not a Waymo benchmark claim."
        ),
    }


def lane_continuation_candidate_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a lane-continuation candidate queue."""

    aggregate = _required_mapping(payload, "aggregate")
    study_summary = _required_mapping(payload, "study_summary")
    study_aggregate = _required_mapping(study_summary, "aggregate")
    candidates = _required_list(payload, "candidates")
    lines = [
        "# ScenarioLens Lane-Continuation Candidate Plan",
        "",
        "This report turns the lane-continuation validation study into an "
        "actionable queue for the next replay or topology-audit pass. It keeps "
        "positive controls, regressions, and unresolved topology gaps separate "
        "so follow-up work does not collapse them into one average score.",
        "",
        "It is intentionally scoped: this is not route planning, not closed-loop "
        "simulation, not a completed Waymax/JAX integration, and not a Waymo "
        "benchmark claim. Raw Waymo files stay local.",
        "",
        "## Scope",
        "",
        f"- Source study manifest: `{payload['study_manifest']}`",
        f"- Ready for planning: {payload['ready']}",
        f"- Top rows per bucket: {payload['top_per_bucket']}",
        f"- Study scenarios scanned: {study_summary.get('scenario_count')}",
        f"- Study candidate tracks: {study_summary.get('candidate_track_count')}",
        "- Raw scenario data committed: no",
        "",
        "## Source Study Snapshot",
        "",
        "| Metric | Count / Value |",
        "| --- | ---: |",
        f"| Tracks using linked lanes | {study_aggregate.get('linked_lane_track_count', 0)} |",
        f"| Tracks improved over nearest lane | {study_aggregate.get('improved_over_nearest_count', 0)} |",
        f"| Tracks regressed vs nearest lane | {study_aggregate.get('regressed_vs_nearest_count', 0)} |",
        f"| Topology gaps | {study_aggregate.get('topology_gap_count', 0)} |",
        f"| Mean lane-link improvement | {_signed_meter_text(study_aggregate.get('mean_lane_link_improvement_m'))} |",
        "",
        "## Queue Summary",
        "",
        "| Queue | Count |",
        "| --- | ---: |",
        f"| Replay candidates | {aggregate['replay_candidate_count']} |",
        f"| Improvement controls | {aggregate['improvement_control_count']} |",
        f"| Regression debug targets | {aggregate['regression_debug_count']} |",
        f"| Topology audit targets | {aggregate['topology_audit_count']} |",
        f"| Candidates still clamped after links | {aggregate['still_clamped_count']} |",
        "",
        "## Replay Controls: Largest Improvements",
        "",
        "| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    _append_bucket_rows(lines, candidates, "improvement_replay_control")

    lines.extend(
        [
            "",
            "## Replay Debug Targets: Largest Regressions",
            "",
            "| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    _append_bucket_rows(lines, candidates, "regression_replay_debug")

    lines.extend(
        [
            "",
            "## Topology Audit Queue",
            "",
            "| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    _append_bucket_rows(lines, candidates, "topology_audit")

    for candidate in candidates:
        assert isinstance(candidate, dict)
        blockers = _required_list(candidate, "blockers")
        actions = _required_list(candidate, "next_actions")
        evidence = _required_mapping(candidate, "evidence")
        lines.extend(
            [
                "",
                f"## `{candidate['scenario_id']}` / track `{candidate['track_id']}`",
                "",
                f"- Queue: `{candidate['bucket']}`",
                f"- Readiness: `{candidate['readiness']}`",
                f"- Priority score: {float(candidate['priority_score']):.2f}",
                f"- Why it matters: {candidate['why_it_matters']}",
                f"- Source: `{candidate['source_name']}`",
                f"- Feature chain: {_feature_chain_text(candidate)}",
                f"- Link status: `{evidence.get('link_status')}`",
                f"- Nearest-lane FDE: {_meter_text(evidence.get('nearest_lane_fde_m'))}",
                f"- Lane-link FDE: {_meter_text(evidence.get('lane_link_fde_m'))}",
                f"- Link improvement: {_signed_meter_text(evidence.get('lane_link_improvement_over_nearest_m'))}",
                f"- Before/after remaining lane distance: {_meter_text(evidence.get('base_remaining_m'))} / {_meter_text(evidence.get('route_remaining_m'))}",
                "",
                "Recommended next actions:",
            ]
        )
        lines.extend(f"- {action}" for action in actions)
        lines.extend(["", "Blockers / cautions:"])
        lines.extend(f"- {blocker}" for blocker in blockers)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Improvement controls are useful for proving the lane-link mechanism under replay before debugging harder cases.",
            "- Regression targets are high-value because they expose route choice, map topology, and future-intent assumptions.",
            "- Topology audit targets should be fixed or explained before they are treated as model-performance evidence.",
            "- This is a planning artifact for the next experiment, not a completed simulation or planner integration.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _candidate_from_track(track: dict[str, object], bucket: str) -> dict[str, object]:
    link = _required_mapping(track, "lane_link")
    improvement = _optional_float(track.get("lane_link_improvement_over_nearest_m")) or 0.0
    nearest_fde = _optional_float(track.get("nearest_lane_fde_m"))
    lane_link_fde = _optional_float(track.get("lane_link_fde_m"))
    link_count = int(link.get("link_count", 0) or 0)
    still_clamped = bool(link.get("lane_end_clamp_risk_after"))
    readiness = _readiness(bucket=bucket, link_count=link_count, still_clamped=still_clamped)
    evidence = {
        "constant_velocity_fde_m": _optional_float(track.get("constant_velocity_fde_m")),
        "heading_lane_fde_m": _optional_float(track.get("heading_lane_fde_m")),
        "nearest_lane_fde_m": nearest_fde,
        "lane_link_fde_m": lane_link_fde,
        "lane_link_improvement_over_nearest_m": round(improvement, 3),
        "link_status": link.get("status"),
        "selected_feature_id": link.get("selected_feature_id"),
        "feature_chain": link.get("feature_chain", []),
        "link_count": link_count,
        "base_remaining_m": _optional_float(link.get("base_remaining_m")),
        "route_remaining_m": _optional_float(link.get("route_remaining_m")),
        "horizon_travel_m": _optional_float(link.get("horizon_travel_m")),
        "lane_end_clamp_risk_after": still_clamped,
    }
    candidate = {
        "rank": 0,
        "bucket": bucket,
        "readiness": readiness,
        "scenario_id": str(track.get("scenario_id", "")),
        "track_id": str(track.get("track_id", "")),
        "source_name": str(track.get("source_name", "")),
        "source_input": str(track.get("source_input", "")),
        "priority_score": _priority_score(
            bucket=bucket,
            improvement=improvement,
            nearest_fde=nearest_fde,
            lane_link_fde=lane_link_fde,
            link_count=link_count,
            still_clamped=still_clamped,
        ),
        "why_it_matters": _why_it_matters(bucket, readiness),
        "evidence": evidence,
        "next_actions": _next_actions(bucket, readiness),
        "blockers": _blockers(bucket, link_count, still_clamped),
    }
    return candidate


def _readiness(bucket: str, link_count: int, still_clamped: bool) -> str:
    if bucket == "topology_audit" or link_count <= 0:
        return "needs_topology_audit"
    if bucket == "regression_replay_debug":
        return (
            "ready_for_continuation_regression_replay"
            if not still_clamped
            else "ready_for_regression_replay_with_horizon_caution"
        )
    return (
        "ready_for_continuation_improvement_replay"
        if not still_clamped
        else "ready_for_improvement_replay_with_horizon_caution"
    )


def _priority_score(
    bucket: str,
    improvement: float,
    nearest_fde: float | None,
    lane_link_fde: float | None,
    link_count: int,
    still_clamped: bool,
) -> float:
    largest_fde = max(value for value in (nearest_fde, lane_link_fde, 0.0) if value is not None)
    score = min(abs(improvement) / 15.0, 8.0)
    score += min(largest_fde / 50.0, 3.0)
    score += min(link_count, 2) * 0.6
    if bucket == "topology_audit":
        score += 1.5
    if still_clamped:
        score += 0.75
    return round(score, 3)


def _why_it_matters(bucket: str, readiness: str) -> str:
    if bucket == "improvement_replay_control":
        return "Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control."
    if bucket == "regression_replay_debug":
        return "Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target."
    if readiness == "needs_topology_audit":
        return "The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay."
    return "The candidate needs manual review before it supports a replay experiment."


def _next_actions(bucket: str, readiness: str) -> list[str]:
    if bucket == "improvement_replay_control":
        return [
            "Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.",
            "Verify the feature chain aligns with the target's observed future before claiming route intent.",
            "Use this case to calibrate expected linked-lane behavior before tuning regressions.",
        ]
    if bucket == "regression_replay_debug":
        return [
            "Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.",
            "Check whether the target actually follows a different route, turns, slows, or changes lanes.",
            "Use the result to decide whether route-choice priors or richer lane-candidate search are needed.",
        ]
    return [
        "Inspect parsed entry/exit links for the selected feature and its missing continuation.",
        "Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.",
        "Rerun the continuation study after parser/topology coverage changes before replaying this case.",
    ]


def _blockers(bucket: str, link_count: int, still_clamped: bool) -> list[str]:
    blockers = ["Raw Waymo TFRecords must remain local and ignored for replay."]
    if bucket == "topology_audit" or link_count <= 0:
        blockers.append("No usable parsed linked-lane chain is available yet.")
    if still_clamped:
        blockers.append("The target still out-travels the linked lane chain within the prediction horizon.")
    return blockers


def _aggregate_candidates(candidates: list[dict[str, object]]) -> dict[str, object]:
    return {
        "candidate_count": len(candidates),
        "replay_candidate_count": sum(
            str(candidate["readiness"]).startswith("ready_for_")
            for candidate in candidates
        ),
        "improvement_control_count": sum(
            candidate["bucket"] == "improvement_replay_control"
            for candidate in candidates
        ),
        "regression_debug_count": sum(
            candidate["bucket"] == "regression_replay_debug"
            for candidate in candidates
        ),
        "topology_audit_count": sum(
            candidate["bucket"] == "topology_audit"
            for candidate in candidates
        ),
        "still_clamped_count": sum(
            bool(_required_mapping(candidate, "evidence").get("lane_end_clamp_risk_after"))
            for candidate in candidates
        ),
    }


def _append_bucket_rows(
    lines: list[str],
    candidates: list[object],
    bucket: str,
) -> None:
    rows = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and candidate.get("bucket") == bucket
    ]
    if not rows:
        lines.append("| n/a | n/a | n/a | n/a | 0.00 | n/a | n/a | n/a | n/a | n/a |")
        return
    for candidate in rows:
        actions = _required_list(candidate, "next_actions")
        evidence = _required_mapping(candidate, "evidence")
        lines.append(
            "| "
            f"{candidate['rank']} | "
            f"`{candidate['source_name']}` | "
            f"`{candidate['scenario_id']}` | "
            f"`{candidate['track_id']}` | "
            f"{float(candidate['priority_score']):.2f} | "
            f"{_meter_text(evidence.get('nearest_lane_fde_m'))} | "
            f"{_meter_text(evidence.get('lane_link_fde_m'))} | "
            f"{_signed_meter_text(evidence.get('lane_link_improvement_over_nearest_m'))} | "
            f"{_feature_chain_text(candidate)} | "
            f"{actions[0] if actions else 'Manual triage.'} |"
        )


def _bucket_rank(bucket: str) -> int:
    return {
        "improvement_replay_control": 0,
        "regression_replay_debug": 1,
        "topology_audit": 2,
    }.get(bucket, 99)


def _feature_chain_text(candidate: dict[str, object]) -> str:
    evidence = _required_mapping(candidate, "evidence")
    chain = evidence.get("feature_chain")
    if not isinstance(chain, list) or not chain:
        return "n/a"
    return " -> ".join(str(item) for item in chain)


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


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
