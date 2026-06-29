from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.baseline_debug import BASELINE_DEBUG_FORMAT

REPLAY_CANDIDATE_FORMAT = "scenariolens.replay_candidates.v1"


@dataclass(frozen=True)
class ReplayCandidateResult:
    """Files produced by a replay-candidate planning run."""

    ready: bool
    candidate_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_replay_candidate_plan(
    debug_manifest_path: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
) -> ReplayCandidateResult:
    """Generate a public-safe plan for the next replay/simulation step."""

    source = Path(debug_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = replay_candidate_payload(source, output_dir=target)
    report = replay_candidate_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return ReplayCandidateResult(
        ready=bool(payload["ready"]),
        candidate_count=len(_required_list(payload, "candidates")),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def replay_candidate_payload(
    debug_manifest_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Return deterministic replay-candidate metadata from a debug casebook."""

    debug_payload = json.loads(debug_manifest_path.read_text(encoding="utf-8"))
    if debug_payload.get("format") != BASELINE_DEBUG_FORMAT:
        raise ValueError(
            "Expected a baseline-debug manifest with format "
            f"{BASELINE_DEBUG_FORMAT}."
        )

    debug_output_dir = Path(str(debug_payload.get("output_dir", ".")))
    cases = _required_list(debug_payload, "cases")
    candidates = [
        _candidate_from_case(case, debug_output_dir=debug_output_dir)
        for case in cases
        if isinstance(case, dict)
    ]
    candidates = sorted(
        candidates,
        key=lambda row: (
            -float(row["priority_score"]),
            str(row["scenario_id"]),
        ),
    )
    aggregate = _aggregate_candidates(candidates)
    ready = bool(debug_payload.get("ready")) and bool(candidates)

    return {
        "format": REPLAY_CANDIDATE_FORMAT,
        "source": str(debug_manifest_path),
        "source_format": debug_payload.get("format"),
        "output_dir": str(output_dir),
        "ready": ready,
        "case_count": len(cases),
        "candidate_count": len(candidates),
        "aggregate": aggregate,
        "candidates": candidates,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
    }


def replay_candidate_markdown(payload: dict[str, object]) -> str:
    """Return a public-safe Markdown replay-candidate plan."""

    aggregate = _required_mapping(payload, "aggregate")
    candidates = _required_list(payload, "candidates")
    lines = [
        "# ScenarioLens Replay Candidate Plan",
        "",
        "This report turns the baseline-debug casebook into a small, honest "
        "candidate queue for the next Waymax/JAX replay experiment. It does "
        "not claim that ScenarioLens already performs simulation replay. It "
        "identifies which cases should be replayed first, why they matter, and "
        "what must be checked before treating replay results as evidence.",
        "",
        "## Scope",
        "",
        f"- Source debug manifest: `{payload['source']}`",
        f"- Ready for planning: {payload['ready']}",
        f"- Debug cases read: {payload['case_count']}",
        f"- Replay candidates produced: {payload['candidate_count']}",
        "- Raw Waymo files committed: no",
        "- Local SVG overlays and per-track debug manifests committed: no",
        "",
        "## Queue Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Replay-ready candidates | {aggregate['replay_ready_count']} |",
        f"| Regression-focused candidates | {aggregate['regression_candidate_count']} |",
        f"| Improvement-focused candidates | {aggregate['improvement_candidate_count']} |",
        f"| Fallback-audit candidates | {aggregate['fallback_audit_count']} |",
        f"| Local overlay artifacts present | {aggregate['local_overlay_present_count']} |",
        "",
        "## Ranked Candidates",
        "",
        "| Rank | Scenario | Case | Readiness | Priority | FDE delta | Map used | Fallbacks | Main next action |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]

    if not candidates:
        lines.append("| n/a | n/a | n/a | n/a | 0.00 | n/a | 0 | 0 | n/a |")
    for rank, candidate in enumerate(candidates, start=1):
        assert isinstance(candidate, dict)
        actions = _required_list(candidate, "next_actions")
        action = str(actions[0]) if actions else "Manual triage."
        lines.append(
            "| "
            f"{rank} | "
            f"`{candidate['scenario_id']}` | "
            f"{candidate['case_label']} | "
            f"`{candidate['readiness']}` | "
            f"{float(candidate['priority_score']):.2f} | "
            f"{_signed_meter_text(candidate['fde_improvement_m'])} | "
            f"{candidate['map_used_count']} | "
            f"{candidate['fallback_count']} | "
            f"{action} |"
        )

    for candidate in candidates:
        assert isinstance(candidate, dict)
        blockers = _required_list(candidate, "blockers")
        actions = _required_list(candidate, "next_actions")
        evidence = _required_mapping(candidate, "evidence")
        lines.extend(
            [
                "",
                f"## `{candidate['scenario_id']}`",
                "",
                f"- Case type: {candidate['case_label']}",
                f"- Readiness: `{candidate['readiness']}`",
                f"- Priority score: {float(candidate['priority_score']):.2f}",
                f"- Why it matters: {candidate['why_it_matters']}",
                f"- Constant-velocity FDE: {_meter_text(evidence['constant_velocity_fde_m'])}",
                f"- Lane-aware FDE: {_meter_text(evidence['lane_aware_fde_m'])}",
                f"- FDE delta: {_signed_meter_text(candidate['fde_improvement_m'])}",
                f"- Worst track delta: {_signed_meter_text(evidence['worst_track_delta_m'])}",
                f"- Max lane distance: {_meter_text(evidence['max_lane_distance_m'])}",
                f"- Local overlay available: {candidate['local_overlay_present']}",
                "",
                "Recommended next actions:",
            ]
        )
        lines.extend(f"- {action}" for action in actions)
        lines.extend(["", "Blockers / cautions:"])
        if blockers:
            lines.extend(f"- {blocker}" for blocker in blockers)
        else:
            lines.append("- No blocking issue identified from the debug manifest.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Improvement candidates test whether map-conditioned rollouts preserve the observed lane-aware advantage under replay.",
            "- Regression candidates are higher-value debugging targets because they expose lane choice, direction, route, or intent assumptions.",
            "- Fallback-audit candidates should not be replayed as model evidence until map matching, coordinate frames, and target eligibility are checked.",
            "- This is a planning artifact for the next experiment, not a completed Waymax/JAX integration.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _candidate_from_case(
    case: dict[str, object],
    debug_output_dir: Path,
) -> dict[str, object]:
    summary = _required_mapping(case, "summary")
    tracks = _required_list(case, "track_diagnostics")
    fde_improvement = _optional_float(summary.get("fde_improvement_m")) or 0.0
    evaluated_targets = _optional_int(summary.get("evaluated_target_count")) or 0
    map_used = _optional_int(summary.get("map_used_count")) or 0
    fallback_count = _optional_int(summary.get("fallback_count")) or 0
    constant_fde = _optional_float(summary.get("constant_velocity_fde_m"))
    lane_fde = _optional_float(summary.get("lane_aware_fde_m"))
    worst_track_delta = _worst_track_delta(tracks)
    max_lane_distance = _max_lane_distance(tracks)
    local_svg = debug_output_dir / str(case.get("svg_path", ""))
    readiness = _readiness(
        fde_improvement=fde_improvement,
        evaluated_targets=evaluated_targets,
        map_used=map_used,
        fallback_count=fallback_count,
    )
    priority = _priority_score(
        fde_improvement=fde_improvement,
        constant_fde=constant_fde,
        lane_fde=lane_fde,
        evaluated_targets=evaluated_targets,
        map_used=map_used,
        fallback_count=fallback_count,
        worst_track_delta=worst_track_delta,
    )
    actions = _next_actions(readiness)
    blockers = _blockers(
        readiness=readiness,
        evaluated_targets=evaluated_targets,
        map_used=map_used,
        fallback_count=fallback_count,
        max_lane_distance=max_lane_distance,
    )

    return {
        "case_label": str(case.get("case_label", "Case")),
        "scenario_id": str(case.get("scenario_id", "")),
        "source_name": str(case.get("source_name", "")),
        "readiness": readiness,
        "priority_score": priority,
        "why_it_matters": _why_it_matters(readiness),
        "fde_improvement_m": round(fde_improvement, 3),
        "evaluated_target_count": evaluated_targets,
        "map_used_count": map_used,
        "fallback_count": fallback_count,
        "top_fallback_reason": summary.get("top_fallback_reason", "none"),
        "local_svg_path": str(local_svg),
        "local_overlay_present": local_svg.exists(),
        "evidence": {
            "constant_velocity_fde_m": constant_fde,
            "lane_aware_fde_m": lane_fde,
            "worst_track_delta_m": worst_track_delta,
            "max_lane_distance_m": max_lane_distance,
            "track_count": len(tracks),
        },
        "next_actions": actions,
        "blockers": blockers,
    }


def _readiness(
    fde_improvement: float,
    evaluated_targets: int,
    map_used: int,
    fallback_count: int,
) -> str:
    if evaluated_targets <= 0:
        return "not_ready_no_targets"
    if fallback_count >= evaluated_targets and fallback_count > 0:
        return "needs_map_match_audit"
    if fde_improvement < 0 and map_used > 0:
        return "ready_for_regression_replay"
    if fde_improvement > 0 and map_used > 0:
        return "ready_for_improvement_replay"
    if fallback_count > 0:
        return "mixed_replay_with_fallback_audit"
    return "needs_manual_triage"


def _priority_score(
    fde_improvement: float,
    constant_fde: float | None,
    lane_fde: float | None,
    evaluated_targets: int,
    map_used: int,
    fallback_count: int,
    worst_track_delta: float | None,
) -> float:
    largest_fde = max(
        value for value in (constant_fde, lane_fde, 0.0) if value is not None
    )
    score = min(abs(fde_improvement) / 8.0, 8.0)
    score += min(abs(worst_track_delta or 0.0) / 12.0, 4.0)
    score += min(largest_fde / 40.0, 3.0)
    score += min(evaluated_targets, 8) * 0.15
    score += min(map_used, 4) * 0.35
    if fallback_count >= evaluated_targets and fallback_count > 0:
        score += 1.0
    elif fallback_count > 0:
        score += 0.45
    return round(score, 3)


def _next_actions(readiness: str) -> list[str]:
    if readiness == "ready_for_regression_replay":
        return [
            "Replay the scenario with constant-velocity and lane-aware rollouts from the same anchor state.",
            "Visualize nearest-lane choice, lane direction, and candidate alternative lanes before changing the baseline.",
            "Use replay output to decide whether a route/intent prior or richer map matching is needed.",
        ]
    if readiness == "ready_for_improvement_replay":
        return [
            "Replay the scenario to confirm the map-conditioned advantage under the same initial state.",
            "Compare final displacement and miss status against the debug casebook metrics.",
            "Use the result as a positive control before tuning lane-aware behavior on harder regressions.",
        ]
    if readiness == "needs_map_match_audit":
        return [
            "Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay.",
            "Confirm targets are eligible vehicle/cyclist tracks and are near usable lane polylines.",
            "Rerun baseline-debug after map matching is corrected, then reconsider replay.",
        ]
    if readiness == "mixed_replay_with_fallback_audit":
        return [
            "Replay only map-used targets first and keep fallback targets marked as unsupported.",
            "Audit fallback reasons separately so replay evidence is not mixed with map-coverage failures.",
        ]
    return [
        "Inspect the debug manifest manually before promoting this case to replay.",
    ]


def _blockers(
    readiness: str,
    evaluated_targets: int,
    map_used: int,
    fallback_count: int,
    max_lane_distance: float | None,
) -> list[str]:
    blockers: list[str] = []
    if evaluated_targets <= 0:
        blockers.append("No evaluated prediction targets are available.")
    if readiness == "needs_map_match_audit":
        blockers.append("Lane-aware fallback was used for every evaluated target.")
    if map_used == 0:
        blockers.append("No target used lane-map context in the lane-aware baseline.")
    if fallback_count > 0 and readiness != "needs_map_match_audit":
        blockers.append("Some targets still require fallback-reason audit.")
    if max_lane_distance is not None and max_lane_distance > 25.0:
        blockers.append("At least one target is far from its nearest lane polyline.")
    return blockers


def _why_it_matters(readiness: str) -> str:
    if readiness == "ready_for_regression_replay":
        return "A map-used lane-aware forecast regressed sharply, making this a high-value replay/debug target."
    if readiness == "ready_for_improvement_replay":
        return "A map-used lane-aware forecast improved final displacement error, making this a positive replay control."
    if readiness == "needs_map_match_audit":
        return "The case exposes map-match coverage or coordinate-frame limits before replay should be trusted."
    if readiness == "mixed_replay_with_fallback_audit":
        return "The case combines map-used evidence with fallback behavior and needs target-level separation."
    return "The case needs manual review before it can support a replay experiment."


def _aggregate_candidates(candidates: list[dict[str, object]]) -> dict[str, object]:
    return {
        "replay_ready_count": sum(
            str(row["readiness"]).startswith("ready_for_") for row in candidates
        ),
        "regression_candidate_count": sum(
            row["readiness"] == "ready_for_regression_replay"
            for row in candidates
        ),
        "improvement_candidate_count": sum(
            row["readiness"] == "ready_for_improvement_replay"
            for row in candidates
        ),
        "fallback_audit_count": sum(
            row["readiness"] == "needs_map_match_audit" for row in candidates
        ),
        "local_overlay_present_count": sum(
            bool(row["local_overlay_present"]) for row in candidates
        ),
    }


def _worst_track_delta(tracks: list[object]) -> float | None:
    deltas = []
    for track in tracks:
        if isinstance(track, dict) and track.get("fde_improvement_m") is not None:
            deltas.append(float(track["fde_improvement_m"]))
    if not deltas:
        return None
    return round(max(deltas, key=lambda value: abs(value)), 3)


def _max_lane_distance(tracks: list[object]) -> float | None:
    distances = []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        lane = track.get("lane_match")
        if not isinstance(lane, dict):
            continue
        distance = lane.get("nearest_lane_distance_m")
        if distance is not None:
            distances.append(float(distance))
    if not distances:
        return None
    return round(max(distances), 3)


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
