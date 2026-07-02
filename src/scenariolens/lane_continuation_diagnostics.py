from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT

LANE_CONTINUATION_DIAGNOSTICS_FORMAT = (
    "scenariolens.lane_continuation_route_diagnostics.v1"
)

_DIAGNOSTIC_BUCKETS = ("regression_replay_debug", "topology_audit")


@dataclass(frozen=True)
class LaneContinuationDiagnosticsResult:
    """Files produced by a lane-continuation route/topology diagnostic run."""

    ready: bool
    diagnostic_count: int
    regression_count: int
    topology_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_route_diagnostics(
    replay_manifest_path: str | Path,
    output_dir: str | Path,
    top: int = 10,
    public_report_path: str | Path | None = None,
) -> LaneContinuationDiagnosticsResult:
    """Generate public-safe route/topology diagnostics from replay output."""

    source = Path(replay_manifest_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_diagnostics_payload(
        replay_manifest_path=source,
        output_dir=target,
        top=top,
    )
    report = lane_continuation_diagnostics_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationDiagnosticsResult(
        ready=bool(payload["ready"]),
        diagnostic_count=int(payload["diagnostic_count"]),
        regression_count=int(aggregate["regression_diagnostic_count"]),
        topology_count=int(aggregate["topology_diagnostic_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_diagnostics_payload(
    replay_manifest_path: Path,
    output_dir: Path,
    top: int,
) -> dict[str, object]:
    """Return route/topology follow-up diagnostics from replay cases."""

    if top < 1:
        raise ValueError("top must be at least 1.")

    replay_payload = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay_payload.get("format") != LANE_CONTINUATION_REPLAY_FORMAT:
        raise ValueError(
            "Expected a lane-continuation replay manifest with format "
            f"{LANE_CONTINUATION_REPLAY_FORMAT}."
        )

    diagnostics = [
        _diagnostic_from_case(case)
        for case in _required_list(replay_payload, "cases")
        if isinstance(case, dict) and case.get("bucket") in _DIAGNOSTIC_BUCKETS
    ]
    diagnostics = sorted(
        diagnostics,
        key=lambda row: (
            _bucket_rank(str(row["bucket"])),
            -float(row["priority_score"]),
            str(row["scenario_id"]),
            str(row["track_id"]),
        ),
    )[:top]
    for rank, diagnostic in enumerate(diagnostics, start=1):
        diagnostic["rank"] = rank

    aggregate = _aggregate_diagnostics(diagnostics)
    return {
        "format": LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay_payload.get("format"),
        "candidate_manifest": replay_payload.get("candidate_manifest"),
        "study_manifest": replay_payload.get("study_manifest"),
        "output_dir": str(output_dir),
        "ready": bool(replay_payload.get("ready")) and bool(diagnostics),
        "top": top,
        "source_replay_summary": replay_payload.get("aggregate", {}),
        "diagnostic_count": len(diagnostics),
        "aggregate": aggregate,
        "diagnostics": diagnostics,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Lane-continuation route/topology diagnostics only; this is not "
            "route planning, not closed-loop simulation, not Waymax/JAX "
            "execution, and not a Waymo benchmark claim."
        ),
    }


def lane_continuation_diagnostics_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for route/topology diagnostics."""

    aggregate = _required_mapping(payload, "aggregate")
    source_summary = _required_mapping(payload, "source_replay_summary")
    diagnostics = _required_list(payload, "diagnostics")
    regression_rows = [
        row
        for row in diagnostics
        if isinstance(row, dict) and row.get("bucket") == "regression_replay_debug"
    ]
    topology_rows = [
        row
        for row in diagnostics
        if isinstance(row, dict) and row.get("bucket") == "topology_audit"
    ]

    lines = [
        "# ScenarioLens Lane-Continuation Route Diagnostics",
        "",
        "This report turns the lane-continuation replay prototype into a "
        "route-choice and topology diagnostic casebook. It keeps stable "
        "regressions separate from topology blockers so the next engineering "
        "step is clear: route-choice priors for linked-lane regressions, and "
        "map/parser coverage for unresolved continuation gaps.",
        "",
        "It is intentionally scoped: this is not a route planner, not "
        "closed-loop simulation, not Waymax/JAX execution, and not a Waymo "
        "benchmark claim. Raw Waymo files and local replay packets stay out of "
        "git.",
        "",
        "## Scope",
        "",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Candidate manifest: `{payload.get('candidate_manifest')}`",
        f"- Study manifest: `{payload.get('study_manifest')}`",
        f"- Ready for diagnostics: {payload['ready']}",
        f"- Diagnostics published: {payload['diagnostic_count']}",
        f"- Source replay cases: {source_summary.get('replayed_case_count')}",
        f"- Source topology probes: {source_summary.get('topology_probe_count')}",
        "- Raw scenario data committed: no",
        "",
        "## Diagnostic Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Diagnostics | {aggregate['diagnostic_count']} |",
        f"| Regression diagnostics | {aggregate['regression_diagnostic_count']} |",
        f"| Topology diagnostics | {aggregate['topology_diagnostic_count']} |",
        f"| Stable regression warnings | {aggregate['stable_regression_count']} |",
        f"| Horizon-limit cases | {aggregate['horizon_limit_count']} |",
        f"| Link worse than constant velocity | {aggregate['link_worse_than_cv_count']} |",
        f"| Topology blockers | {aggregate['topology_blocker_count']} |",
        f"| Missing linked features | {aggregate['missing_link_count']} |",
        f"| Terminal/no-exit lane probes | {aggregate['terminal_link_count']} |",
        "",
        "## Stable Regression Diagnostics",
        "",
        "| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |",
        "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    _append_rows(lines, regression_rows)

    lines.extend(
        [
            "",
            "## Topology Diagnostics",
            "",
            "| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |",
            "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    _append_rows(lines, topology_rows)

    for item in diagnostics:
        assert isinstance(item, dict)
        evidence = _required_mapping(item, "evidence")
        actions = _required_list(item, "next_actions")
        blockers = _required_list(item, "blockers")
        lines.extend(
            [
                "",
                f"## `{item['scenario_id']}` / track `{item['track_id']}`",
                "",
                f"- Queue: `{item['bucket']}`",
                f"- Diagnosis: **{item['diagnosis_label']}**",
                f"- Priority score: {float(item['priority_score']):.2f}",
                f"- Why it matters: {item['why_it_matters']}",
                f"- Source: `{item['source_name']}`",
                f"- Replay stability: `{evidence['stability_label']}`",
                f"- Link status/count: `{evidence['lane_link_status']}` / {evidence['lane_link_count']}",
                f"- Feature chain: {_feature_chain_text(evidence)}",
                f"- Nearest-lane FDE: {_meter_text(evidence['nearest_lane_fde_m'])}",
                f"- Lane-link FDE: {_meter_text(evidence['lane_link_fde_m'])}",
                f"- Link improvement over nearest: {_signed_meter_text(evidence['lane_link_improvement_over_nearest_m'])}",
                f"- Link improvement over constant velocity: {_signed_meter_text(evidence['lane_link_improvement_over_constant_m'])}",
                f"- Horizon / route remaining: {_meter_text(evidence['horizon_travel_m'])} / {_meter_text(evidence['route_remaining_m'])}",
                "",
                "Recommended next actions:",
            ]
        )
        lines.extend(f"- {action}" for action in actions)
        if blockers:
            lines.extend(["", "Blockers / cautions:"])
            lines.extend(f"- {blocker}" for blocker in blockers)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stable linked-lane regressions are valuable because they expose route-choice, lane-branch selection, or speed-prior assumptions after the topology mechanism is available.",
            "- Horizon-limit cases should not be treated as model failures until the linked chain covers the prediction horizon.",
            "- Topology blockers are parser/map coverage work, not prediction evidence.",
            "- This report is an audit plan for the next implementation step, not a claim that ScenarioLens is a production planner.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _diagnostic_from_case(case: dict[str, object]) -> dict[str, object]:
    nominal = _required_mapping(case, "nominal")
    stability = _required_mapping(case, "perturbation_stability")
    bucket = str(case.get("bucket", "unknown"))
    evidence = {
        "constant_velocity_fde_m": _optional_float(nominal.get("constant_velocity_fde_m")),
        "nearest_lane_fde_m": _optional_float(nominal.get("nearest_lane_fde_m")),
        "heading_lane_fde_m": _optional_float(nominal.get("heading_lane_fde_m")),
        "lane_link_fde_m": _optional_float(nominal.get("lane_link_fde_m")),
        "lane_link_improvement_over_nearest_m": _optional_float(
            nominal.get("lane_link_improvement_over_nearest_m")
        ),
        "lane_link_improvement_over_constant_m": _optional_float(
            nominal.get("lane_link_improvement_over_constant_m")
        ),
        "lane_link_status": nominal.get("lane_link_status", "unknown"),
        "lane_link_count": int(nominal.get("lane_link_count", 0) or 0),
        "feature_chain": nominal.get("feature_chain", []),
        "base_remaining_m": _optional_float(nominal.get("base_remaining_m")),
        "route_remaining_m": _optional_float(nominal.get("route_remaining_m")),
        "horizon_travel_m": _optional_float(nominal.get("horizon_travel_m")),
        "lane_end_clamp_risk_after": bool(nominal.get("lane_end_clamp_risk_after")),
        "stability_label": stability.get("label", "unknown"),
        "max_delta_swing_m": _optional_float(stability.get("max_delta_swing_m")),
    }
    label = _diagnosis_label(bucket=bucket, evidence=evidence)
    return {
        "rank": 0,
        "bucket": bucket,
        "scenario_id": str(case.get("scenario_id", "")),
        "track_id": str(case.get("track_id", "")),
        "source_name": str(case.get("source_name", "")),
        "readiness": str(case.get("readiness", "")),
        "diagnosis_label": label,
        "priority_score": _priority_score(bucket=bucket, evidence=evidence),
        "why_it_matters": _why_it_matters(label),
        "evidence": evidence,
        "next_actions": _next_actions(label),
        "blockers": _blockers(evidence),
    }


def _diagnosis_label(bucket: str, evidence: dict[str, object]) -> str:
    link_count = int(evidence.get("lane_link_count", 0) or 0)
    status = str(evidence.get("lane_link_status", "unknown"))
    if bucket == "topology_audit" or link_count <= 0:
        if status == "linked_feature_missing":
            return "missing_linked_feature"
        if status in {"no_exit_lanes", "no_entry_lanes"}:
            return "terminal_lane_or_parser_gap"
        return "topology_blocker"
    if bool(evidence.get("lane_end_clamp_risk_after")):
        return "route_horizon_limit"
    link_vs_cv = _optional_float(evidence.get("lane_link_improvement_over_constant_m"))
    if link_vs_cv is not None and link_vs_cv < -1.0:
        return "linked_route_worse_than_constant_velocity"
    stability = str(evidence.get("stability_label", ""))
    if stability == "stable_regression_warning":
        return "stable_route_choice_regression"
    return "route_choice_or_speed_prior_audit"


def _priority_score(bucket: str, evidence: dict[str, object]) -> float:
    delta = abs(_optional_float(evidence.get("lane_link_improvement_over_nearest_m")) or 0.0)
    nearest = _optional_float(evidence.get("nearest_lane_fde_m")) or 0.0
    swing = _optional_float(evidence.get("max_delta_swing_m")) or 0.0
    score = min(delta / 10.0, 8.0) + min(nearest / 50.0, 3.0) + min(swing / 10.0, 2.0)
    if bucket == "topology_audit":
        score += 1.5
    if bool(evidence.get("lane_end_clamp_risk_after")):
        score += 0.75
    return round(score, 3)


def _why_it_matters(label: str) -> str:
    if label == "stable_route_choice_regression":
        return "The linked route remains worse than nearest-lane under perturbation, which points to route-choice or branch-selection logic."
    if label == "route_horizon_limit":
        return "The target still out-travels the linked lane chain, so the next fix is longer or better-connected topology before model tuning."
    if label == "linked_route_worse_than_constant_velocity":
        return "Linked-lane continuation is worse than both nearest-lane and constant velocity, making this a high-value route-prior debugging case."
    if label == "missing_linked_feature":
        return "The selected feature references a continuation that the lightweight parser did not make usable."
    if label == "terminal_lane_or_parser_gap":
        return "The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it."
    if label == "topology_blocker":
        return "The queued row cannot support replay evidence until map topology coverage improves."
    return "The case needs route-choice, speed-prior, or topology review before changing scoring behavior."


def _next_actions(label: str) -> list[str]:
    if label == "stable_route_choice_regression":
        return [
            "Compare alternate linked-lane branches from the same selected feature.",
            "Add a route-choice prior before accepting the first linked continuation.",
            "Keep nearest-lane and linked-lane results side by side in the next replay pass.",
        ]
    if label == "route_horizon_limit":
        return [
            "Extend linked-lane search depth or route-chain coverage before tuning prediction behavior.",
            "Check whether the target's observed future leaves the parsed lane graph.",
            "Rerun the replay prototype after topology coverage changes.",
        ]
    if label == "linked_route_worse_than_constant_velocity":
        return [
            "Inspect whether the linked route turns away from the target's future motion.",
            "Test route candidates ranked by heading and future displacement consistency.",
            "Treat this as a route-choice regression, not a scoring-baseline failure.",
        ]
    if label in {"missing_linked_feature", "terminal_lane_or_parser_gap", "topology_blocker"}:
        return [
            "Audit the selected map feature's parsed entry/exit lane IDs.",
            "Check whether the feature cap dropped the referenced continuation.",
            "Regenerate continuation studies after parser/topology changes.",
        ]
    return [
        "Inspect route choice, lane topology, and speed priors before changing baseline behavior.",
        "Promote the case into the next replay batch if the hypothesis is stable.",
    ]


def _blockers(evidence: dict[str, object]) -> list[str]:
    blockers = []
    if int(evidence.get("lane_link_count", 0) or 0) <= 0:
        blockers.append("No usable parsed linked-lane chain is available yet.")
    if bool(evidence.get("lane_end_clamp_risk_after")):
        blockers.append("The linked lane chain is still shorter than the target horizon.")
    blockers.append("Raw Waymo TFRecords and local replay packets must stay ignored.")
    return blockers


def _aggregate_diagnostics(diagnostics: list[dict[str, object]]) -> dict[str, object]:
    labels = [str(row["diagnosis_label"]) for row in diagnostics]
    return {
        "diagnostic_count": len(diagnostics),
        "regression_diagnostic_count": sum(
            row["bucket"] == "regression_replay_debug" for row in diagnostics
        ),
        "topology_diagnostic_count": sum(
            row["bucket"] == "topology_audit" for row in diagnostics
        ),
        "stable_regression_count": labels.count("stable_route_choice_regression"),
        "horizon_limit_count": labels.count("route_horizon_limit"),
        "link_worse_than_cv_count": labels.count(
            "linked_route_worse_than_constant_velocity"
        ),
        "topology_blocker_count": sum(
            label
            in {
                "topology_blocker",
                "missing_linked_feature",
                "terminal_lane_or_parser_gap",
            }
            for label in labels
        ),
        "missing_link_count": labels.count("missing_linked_feature"),
        "terminal_link_count": labels.count("terminal_lane_or_parser_gap"),
    }


def _append_rows(lines: list[str], rows: list[dict[str, object]]) -> None:
    if not rows:
        lines.append("| n/a | n/a | n/a | 0.00 | n/a | n/a | n/a | n/a | n/a | n/a |")
        return
    for row in rows:
        evidence = _required_mapping(row, "evidence")
        actions = _required_list(row, "next_actions")
        lines.append(
            "| "
            f"{row['rank']} | "
            f"`{row['scenario_id']}` | "
            f"`{row['track_id']}` | "
            f"{float(row['priority_score']):.2f} | "
            f"`{row['diagnosis_label']}` | "
            f"{_meter_text(evidence['nearest_lane_fde_m'])} | "
            f"{_meter_text(evidence['lane_link_fde_m'])} | "
            f"{_signed_meter_text(evidence['lane_link_improvement_over_nearest_m'])} | "
            f"{_feature_chain_text(evidence)} | "
            f"{actions[0] if actions else 'Manual review.'} |"
        )


def _bucket_rank(bucket: str) -> int:
    return {"regression_replay_debug": 0, "topology_audit": 1}.get(bucket, 99)


def _feature_chain_text(evidence: dict[str, object]) -> str:
    chain = evidence.get("feature_chain")
    if not isinstance(chain, list) or not chain:
        return "n/a"
    return " -> ".join(str(item) for item in chain)


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
