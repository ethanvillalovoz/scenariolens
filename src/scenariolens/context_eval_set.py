from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.context_failure_study import CONTEXT_FAILURE_STUDY_FORMAT

CONTEXT_EVAL_SET_FORMAT = "scenariolens.context_eval_set.v1"


@dataclass(frozen=True)
class ContextEvalSetResult:
    """Files produced by a public-safe context evaluation-set run."""

    ready: bool
    group_count: int
    unique_scenario_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    scenario_ids_path: Path
    public_report_path: Path | None


def generate_context_eval_set(
    context_failure_manifest_path: str | Path,
    output_dir: str | Path,
    top_per_group: int = 5,
    public_report_path: str | Path | None = None,
) -> ContextEvalSetResult:
    """Generate a curated eval-set artifact from a context-failure manifest."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    scenario_ids_path = target / "scenario_ids.txt"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = context_eval_set_payload(
        context_failure_manifest_path=Path(context_failure_manifest_path),
        output_dir=target,
        top_per_group=top_per_group,
    )
    report = context_eval_set_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    scenario_ids_path.write_text(
        "\n".join(str(case["scenario_id"]) for case in payload["deduplicated_cases"])
        + "\n",
        encoding="utf-8",
    )
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return ContextEvalSetResult(
        ready=bool(payload["ready"]),
        group_count=int(aggregate["group_count"]),
        unique_scenario_count=int(aggregate["unique_scenario_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        scenario_ids_path=scenario_ids_path,
        public_report_path=copied_report_path,
    )


def context_eval_set_payload(
    context_failure_manifest_path: Path,
    output_dir: Path,
    top_per_group: int,
) -> dict[str, object]:
    """Return a reusable public-safe eval set from context/failure rankings."""

    if top_per_group < 1:
        raise ValueError("top-per-group must be at least 1.")

    source_payload = json.loads(context_failure_manifest_path.read_text(encoding="utf-8"))
    if source_payload.get("format") != CONTEXT_FAILURE_STUDY_FORMAT:
        raise ValueError(
            "Expected a context-failure-study manifest with format "
            f"{CONTEXT_FAILURE_STUDY_FORMAT}."
        )

    group_specs = (
        {
            "group_id": "context_rich_failures",
            "label": "Context-rich failures",
            "source_key": "hardest_context_failures",
            "purpose": (
                "Stress the baseline on high-FDE scenes that preserve map, "
                "signal, or route context."
            ),
            "next_experiment": "Use as broad smoke cases for baseline-debug and replay triage.",
        },
        {
            "group_id": "signal_context_failures",
            "label": "Signal-context failures",
            "source_key": "signal_context_failures",
            "purpose": (
                "Preserve dynamic traffic-signal evidence while checking "
                "whether simple motion baselines miss long-tail behavior."
            ),
            "next_experiment": "Add signal-state features or replay these cases with signal annotations visible.",
        },
        {
            "group_id": "route_topology_failures",
            "label": "Route/topology failures",
            "source_key": "route_context_failures",
            "purpose": (
                "Focus on lane-entry, exit, neighbor, and route-link context "
                "that a naive baseline does not reason about."
            ),
            "next_experiment": "Compare nearest-lane, heading-aware, and route-aware lane selection.",
        },
        {
            "group_id": "lane_aware_regressions",
            "label": "Lane-aware regressions",
            "source_key": "lane_regressions_with_context",
            "purpose": (
                "Expose cases where naive lane following is worse than "
                "constant velocity even though map context is present."
            ),
            "next_experiment": "Run map-match and intent-prior audits before tuning lane-following behavior.",
        },
    )

    groups = [
        _group_payload(
            spec=spec,
            rows=_rows(source_payload, str(spec["source_key"])),
            top_per_group=top_per_group,
        )
        for spec in group_specs
    ]
    fallback_group = _fallback_group(
        rows=_all_ranked_rows(source_payload),
        top_per_group=top_per_group,
    )
    if fallback_group["case_count"]:
        groups.append(fallback_group)

    deduplicated_cases = _deduplicate_cases(groups)
    aggregate = _aggregate(groups, deduplicated_cases)

    return {
        "format": CONTEXT_EVAL_SET_FORMAT,
        "source_manifest": str(context_failure_manifest_path),
        "source_format": source_payload.get("format"),
        "input_format": source_payload.get("input_format", "native"),
        "max_scenarios_per_input": source_payload.get("max_scenarios_per_input"),
        "source_scope": _source_scope(source_payload),
        "output_dir": str(output_dir),
        "top_per_group": top_per_group,
        "ready": bool(source_payload.get("ready")) and bool(deduplicated_cases),
        "aggregate": aggregate,
        "groups": groups,
        "deduplicated_cases": deduplicated_cases,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "scenario_ids": "scenario_ids.txt",
        },
        "scope_note": (
            "This is a curated evaluation-set artifact derived from public-safe "
            "context/failure rankings. It is not an official Waymo benchmark, "
            "does not contain raw scenario data, and should be rerun when the "
            "underlying shard sample changes."
        ),
    }


def context_eval_set_markdown(payload: dict[str, object]) -> str:
    """Return Markdown for a public-safe context evaluation set."""

    aggregate = _required_mapping(payload, "aggregate")
    source_scope = _required_mapping(payload, "source_scope")
    groups = _required_list(payload, "groups")
    deduplicated_cases = _required_list(payload, "deduplicated_cases")

    lines = [
        "# ScenarioLens Context Evaluation Set",
        "",
        "This report turns the context-joined failure study into a reusable, "
        "public-safe evaluation set. The goal is to make the next experiment "
        "obvious: which scenario IDs should be kept together, what context must "
        "be preserved, and what would count as a useful follow-up check.",
        "",
        "It is not an official Waymo benchmark and does not include raw Waymo "
        "scenario data.",
        "",
        "## Scope",
        "",
        f"- Source manifest: `{payload['source_manifest']}`",
        f"- Source format: `{payload['source_format']}`",
        f"- Source scenarios analyzed: {source_scope['scenario_count']}",
        f"- Source prediction targets: {source_scope['evaluated_target_count']}",
        f"- Ready for eval-set use: {payload['ready']}",
        f"- Eval groups: {aggregate['group_count']}",
        f"- Unique scenario IDs: {aggregate['unique_scenario_count']}",
        "- Raw scenario data committed: no",
        "- Public artifact contains scenario IDs, group labels, metrics, and checks only",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Group memberships | {aggregate['case_membership_count']} |",
        f"| Unique scenarios | {aggregate['unique_scenario_count']} |",
        f"| Signal-focused cases | {aggregate['signal_case_count']} |",
        f"| Route/topology cases | {aggregate['route_case_count']} |",
        f"| Lane-regression cases | {aggregate['lane_regression_case_count']} |",
        f"| Fallback-stress cases | {aggregate['fallback_stress_case_count']} |",
        f"| Mean priority score | {_number_text(aggregate['mean_priority_score'])} |",
        "",
        "## Eval Groups",
        "",
        "| Group | Cases | Unique scenarios | Purpose | Next experiment |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for group in groups:
        assert isinstance(group, dict)
        lines.append(
            "| "
            f"{group['label']} | "
            f"{group['case_count']} | "
            f"{group['unique_scenario_count']} | "
            f"{group['purpose']} | "
            f"{group['next_experiment']} |"
        )

    lines.extend(
        [
            "",
            "## Deduplicated Seed Set",
            "",
            "| Rank | Source | Scenario | Priority | Groups | CV FDE | Lane delta | Signal states | Route links | Fallbacks |",
            "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not deduplicated_cases:
        lines.append("| n/a | n/a | n/a | 0.000 | n/a | n/a | n/a | 0 | 0 | 0 |")
    for rank, case in enumerate(deduplicated_cases, start=1):
        assert isinstance(case, dict)
        lines.append(
            "| "
            f"{rank} | "
            f"`{case['source_name']}` | "
            f"`{case['scenario_id']}` | "
            f"{_number_text(case['priority_score'])} | "
            f"{', '.join(str(group) for group in case['selection_groups'])} | "
            f"{_meter_text(case['constant_velocity_fde_m'])} | "
            f"{_signed_meter_text(case['fde_improvement_m'])} | "
            f"{case['signal_lane_state_count']} | "
            f"{case['route_link_count']} | "
            f"{case['fallback_count']} |"
        )

    for group in groups:
        assert isinstance(group, dict)
        cases = _required_list(group, "cases")
        checks = _required_list(group, "acceptance_checks")
        lines.extend(
            [
                "",
                f"## {group['label']}",
                "",
                f"Purpose: {group['purpose']}",
                "",
                "Acceptance checks:",
            ]
        )
        lines.extend(f"- {check}" for check in checks)
        lines.extend(
            [
                "",
                "| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |",
                "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        if not cases:
            lines.append("| n/a | n/a | n/a | 0.000 | n/a | n/a | n/a | n/a | 0 | 0 |")
        for rank, case in enumerate(cases, start=1):
            assert isinstance(case, dict)
            lines.append(
                "| "
                f"{rank} | "
                f"`{case['source_name']}` | "
                f"`{case['scenario_id']}` | "
                f"{_number_text(case['priority_score'])} | "
                f"{case['selection_reason']} | "
                f"{_meter_text(case['constant_velocity_fde_m'])} | "
                f"{_percent_text(case['constant_velocity_miss_rate'])} | "
                f"{_signed_meter_text(case['fde_improvement_m'])} | "
                f"{case['signal_lane_state_count']} | "
                f"{case['route_link_count']} |"
            )

    lines.extend(
        [
            "",
            "## How To Use This",
            "",
            "- Treat this as a deterministic candidate set for the next ScenarioLens "
            "experiment, not as a benchmark leaderboard.",
            "- Keep scenario IDs grouped by their selection reason so improvements "
            "do not hide regressions in signal, route, or fallback-heavy cases.",
            "- For local debugging, feed selected source files and scenario IDs into "
            "`scenariolens baseline-debug`, then rerun replay-candidate and "
            "open-loop replay reports.",
            "- Regenerate this eval set whenever the context-failure study inputs or "
            "selection thresholds change.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _group_payload(
    spec: dict[str, object],
    rows: tuple[dict[str, object], ...],
    top_per_group: int,
) -> dict[str, object]:
    group_id = str(spec["group_id"])
    cases = [
        _case_from_row(row, group_id=group_id, group_label=str(spec["label"]))
        for row in rows[:top_per_group]
    ]
    return {
        "group_id": group_id,
        "label": str(spec["label"]),
        "purpose": str(spec["purpose"]),
        "next_experiment": str(spec["next_experiment"]),
        "case_count": len(cases),
        "unique_scenario_count": len({case["scenario_key"] for case in cases}),
        "acceptance_checks": _acceptance_checks(group_id),
        "cases": cases,
    }


def _fallback_group(
    rows: tuple[dict[str, object], ...],
    top_per_group: int,
) -> dict[str, object]:
    fallback_rows = sorted(
        (row for row in rows if _int(row.get("fallback_count")) > 0),
        key=lambda row: (
            -_int(row.get("fallback_count")),
            -_float(row.get("constant_velocity_fde_m")),
            str(row.get("scenario_id", "")),
        ),
    )
    spec = {
        "group_id": "fallback_stress_cases",
        "label": "Fallback-stress cases",
        "purpose": (
            "Audit scenarios where map-conditioned baselines could not use map "
            "context for one or more evaluated targets."
        ),
        "next_experiment": "Separate supported targets from fallback targets before replay.",
    }
    return _group_payload(spec=spec, rows=tuple(fallback_rows), top_per_group=top_per_group)


def _case_from_row(
    row: dict[str, object],
    group_id: str,
    group_label: str,
) -> dict[str, object]:
    priority = _priority_score(row=row, group_id=group_id)
    return {
        "case_id": f"{group_id}:{row.get('source_name', '')}:{row.get('scenario_id', '')}",
        "scenario_key": f"{row.get('source_name', '')}:{row.get('scenario_id', '')}",
        "scenario_id": str(row.get("scenario_id", "")),
        "source_name": str(row.get("source_name", "")),
        "source_input": str(row.get("source_input", "")),
        "source_index": _int(row.get("source_index")),
        "scenario_index": _int(row.get("scenario_index")),
        "selection_group": group_id,
        "selection_group_label": group_label,
        "selection_reason": _selection_reason(group_id),
        "priority_score": priority,
        "score": _optional_float(row.get("score")),
        "evaluated_target_count": _int(row.get("evaluated_target_count")),
        "constant_velocity_fde_m": _optional_float(row.get("constant_velocity_fde_m")),
        "constant_velocity_miss_rate": _optional_float(
            row.get("constant_velocity_miss_rate")
        ),
        "lane_aware_fde_m": _optional_float(row.get("lane_aware_fde_m")),
        "fde_improvement_m": _optional_float(row.get("fde_improvement_m")),
        "map_used_count": _int(row.get("map_used_count")),
        "fallback_count": _int(row.get("fallback_count")),
        "map_feature_count": _int(row.get("map_feature_count")),
        "lane_count": _int(row.get("lane_count")),
        "signal_lane_state_count": _int(row.get("signal_lane_state_count")),
        "signal_stop_state_count": _int(row.get("signal_stop_state_count")),
        "route_link_count": _int(row.get("route_link_count")),
        "entry_link_count": _int(row.get("entry_link_count")),
        "exit_link_count": _int(row.get("exit_link_count")),
        "neighbor_link_count": _int(row.get("neighbor_link_count")),
        "top_signal_state": str(row.get("top_signal_state", "none")),
        "recommended_next_step": _recommended_next_step(group_id),
    }


def _priority_score(row: dict[str, object], group_id: str) -> float:
    cv_fde = _float(row.get("constant_velocity_fde_m"))
    score = _float(row.get("score"))
    delta = _float(row.get("fde_improvement_m"))
    priority = min(cv_fde / 20.0, 5.0)
    priority += min(score / 20.0, 3.0)
    priority += min(_int(row.get("signal_lane_state_count")) / 20.0, 1.5)
    priority += min(_int(row.get("route_link_count")) / 60.0, 1.5)
    priority += min(_int(row.get("fallback_count")), 4) * 0.25
    if group_id == "lane_aware_regressions":
        priority += min(abs(delta) / 10.0, 2.0)
    if group_id == "fallback_stress_cases":
        priority += min(_int(row.get("fallback_count")) / 2.0, 2.0)
    return round(priority, 3)


def _deduplicate_cases(groups: list[dict[str, object]]) -> list[dict[str, object]]:
    by_key: dict[str, dict[str, object]] = {}
    for group in groups:
        cases = _required_list(group, "cases")
        for case in cases:
            if not isinstance(case, dict):
                continue
            key = str(case["scenario_key"])
            current = by_key.get(key)
            if current is None:
                current = {
                    **case,
                    "selection_groups": [case["selection_group_label"]],
                    "selection_group_ids": [case["selection_group"]],
                }
                by_key[key] = current
                continue
            current["priority_score"] = max(
                _float(current.get("priority_score")),
                _float(case.get("priority_score")),
            )
            _append_unique(current, "selection_groups", str(case["selection_group_label"]))
            _append_unique(current, "selection_group_ids", str(case["selection_group"]))

    return sorted(
        by_key.values(),
        key=lambda case: (
            -_float(case.get("priority_score")),
            str(case.get("source_name", "")),
            str(case.get("scenario_id", "")),
        ),
    )


def _aggregate(
    groups: list[dict[str, object]],
    deduplicated_cases: list[dict[str, object]],
) -> dict[str, object]:
    priorities = tuple(_float(case.get("priority_score")) for case in deduplicated_cases)
    return {
        "group_count": len(groups),
        "case_membership_count": sum(_int(group.get("case_count")) for group in groups),
        "unique_scenario_count": len(deduplicated_cases),
        "signal_case_count": _group_case_count(groups, "signal_context_failures"),
        "route_case_count": _group_case_count(groups, "route_topology_failures"),
        "lane_regression_case_count": _group_case_count(groups, "lane_aware_regressions"),
        "fallback_stress_case_count": _group_case_count(groups, "fallback_stress_cases"),
        "mean_priority_score": _mean(priorities),
    }


def _source_scope(payload: dict[str, object]) -> dict[str, object]:
    aggregate = _required_mapping(payload, "aggregate")
    return {
        "source_count": _int(payload.get("source_count")),
        "scenario_count": _int(payload.get("scenario_count")),
        "evaluated_target_count": _int(aggregate.get("evaluated_target_count")),
        "constant_velocity_fde_m": aggregate.get("constant_velocity_fde_m"),
        "constant_velocity_miss_rate": aggregate.get("constant_velocity_miss_rate"),
    }


def _all_ranked_rows(payload: dict[str, object]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for key in (
        "hardest_context_failures",
        "signal_context_failures",
        "route_context_failures",
        "lane_regressions_with_context",
    ):
        for row in _rows(payload, key):
            identity = (
                str(row.get("source_name", "")),
                str(row.get("scenario_id", "")),
            )
            if identity in seen:
                continue
            seen.add(identity)
            rows.append(row)
    return tuple(rows)


def _rows(payload: dict[str, object], key: str) -> tuple[dict[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(row for row in value if isinstance(row, dict))


def _selection_reason(group_id: str) -> str:
    if group_id == "signal_context_failures":
        return "High baseline error with parsed traffic-signal state context."
    if group_id == "route_topology_failures":
        return "High baseline error with lane topology or route-link context."
    if group_id == "lane_aware_regressions":
        return "Lane-aware baseline regressed despite context being available."
    if group_id == "fallback_stress_cases":
        return "One or more evaluated targets required lane-aware fallback."
    return "High baseline error with map, signal, or route context."


def _recommended_next_step(group_id: str) -> str:
    if group_id == "signal_context_failures":
        return "Replay or debug with signal-state annotations visible."
    if group_id == "route_topology_failures":
        return "Audit lane topology, route links, and heading-aware selection."
    if group_id == "lane_aware_regressions":
        return "Run map-match and intent-prior debugging before model tuning."
    if group_id == "fallback_stress_cases":
        return "Separate unsupported fallback targets from replay-ready targets."
    return "Use as a context-rich smoke case for baseline-debug."


def _acceptance_checks(group_id: str) -> list[str]:
    common = [
        "Scenario ID and source shard remain stable across reruns.",
        "Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.",
        "No raw Waymo trajectory or map packet is committed.",
    ]
    if group_id == "signal_context_failures":
        return [
            "Traffic-signal lane-state counts are present in the context manifest.",
            "Stop/go/unknown signal buckets remain visible in the public report.",
            *common,
        ]
    if group_id == "route_topology_failures":
        return [
            "Route, entry, exit, or neighbor link counts are present.",
            "Lane-topology context is preserved before comparing map-aware baselines.",
            *common,
        ]
    if group_id == "lane_aware_regressions":
        return [
            "The lane-aware FDE delta remains negative or is explicitly explained.",
            "Map-used and fallback counts are reported with the regression.",
            *common,
        ]
    if group_id == "fallback_stress_cases":
        return [
            "Fallback count is nonzero and kept separate from map-used targets.",
            "Replay follow-up does not treat fallback targets as map-conditioned evidence.",
            *common,
        ]
    return [
        "At least one map, signal, or route context count is nonzero.",
        "The case remains in the high-FDE context-failure ranking.",
        *common,
    ]


def _group_case_count(groups: list[dict[str, object]], group_id: str) -> int:
    for group in groups:
        if group.get("group_id") == group_id:
            return _int(group.get("case_count"))
    return 0


def _append_unique(payload: dict[str, object], key: str, value: str) -> None:
    values = payload.get(key)
    if not isinstance(values, list):
        values = []
        payload[key] = values
    if value not in values:
        values.append(value)


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float:
    optional = _optional_float(value)
    return optional if optional is not None else 0.0


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _number_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


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
