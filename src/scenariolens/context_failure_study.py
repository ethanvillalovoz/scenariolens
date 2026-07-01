from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    load_failure_study_input,
)
from scenariolens.metrics import score_scenario
from scenariolens.prediction import DEFAULT_MISS_THRESHOLD_M, compare_prediction_baselines
from scenariolens.schema import Scenario

CONTEXT_FAILURE_STUDY_FORMAT = "scenariolens.context_failure_study.v1"
CONTEXT_FAILURE_STUDY_INPUT_FORMATS = FAILURE_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class ContextFailureStudyResult:
    """Files produced by a public-safe context/failure join study."""

    ready: bool
    source_count: int
    scenario_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_context_failure_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 10,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> ContextFailureStudyResult:
    """Generate a report joining baseline failures with map/signal context."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = context_failure_study_payload(
        input_paths=tuple(Path(path) for path in input_paths),
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        input_format=input_format,
    )
    report = context_failure_study_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return ContextFailureStudyResult(
        ready=bool(payload["ready"]),
        source_count=int(payload["source_count"]),
        scenario_count=int(payload["scenario_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def context_failure_study_payload(
    input_paths: tuple[Path, ...],
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    input_format: str,
) -> dict[str, object]:
    """Return deterministic context/failure evidence for local slices."""

    if not input_paths:
        raise ValueError("At least one input path is required for context-failure-study.")
    if input_format not in CONTEXT_FAILURE_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported context-failure-study input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(CONTEXT_FAILURE_STUDY_INPUT_FORMATS)}"
        )
    if top < 1:
        raise ValueError("top must be at least 1.")

    ready = True
    sources: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    for source_index, source in enumerate(input_paths, start=1):
        input_ready, preflight, scenarios = load_failure_study_input(
            source=source,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )
        if not input_ready:
            ready = False
            sources.append(
                {
                    "input_path": str(source),
                    "source_name": _source_name(source),
                    "ready": False,
                    "preflight": preflight or {},
                    **_aggregate_rows(()),
                }
            )
            continue

        source_rows = tuple(
            _scenario_context_failure_row(
                source=source,
                source_index=source_index,
                scenario_index=scenario_index,
                scenario=scenario,
            )
            for scenario_index, scenario in enumerate(scenarios, start=1)
        )
        rows.extend(source_rows)
        sources.append(
            {
                "input_path": str(source),
                "source_name": _source_name(source),
                "ready": True,
                "preflight": preflight or {},
                **_aggregate_rows(source_rows),
            }
        )

    row_tuple = tuple(rows)
    return {
        "format": CONTEXT_FAILURE_STUDY_FORMAT,
        "input_paths": [str(path) for path in input_paths],
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios_per_input": max_scenarios,
        "top": top,
        "ready": ready,
        "source_count": len(input_paths),
        "scenario_count": sum(int(source["scenario_count"]) for source in sources),
        "aggregate": _aggregate_rows(row_tuple),
        "sources": sources,
        "context_groups": _context_groups(row_tuple),
        "hardest_context_failures": _rank_context_failures(row_tuple, top=top),
        "signal_context_failures": _rank_signal_failures(row_tuple, top=top),
        "route_context_failures": _rank_route_failures(row_tuple, top=top),
        "lane_regressions_with_context": _rank_lane_regressions(row_tuple, top=top),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "This joins ScenarioLens baseline diagnostics with parsed map/signal "
            "context. It is not a causal analysis, routing model, or Waymo "
            "benchmark claim."
        ),
    }


def context_failure_study_markdown(payload: dict[str, object]) -> str:
    """Return Markdown report from a context/failure join payload."""

    aggregate = _required_mapping(payload, "aggregate")
    sources = _required_list(payload, "sources")
    context_groups = _required_list(payload, "context_groups")
    hardest = _required_list(payload, "hardest_context_failures")
    signal_failures = _required_list(payload, "signal_context_failures")
    route_failures = _required_list(payload, "route_context_failures")
    lane_regressions = _required_list(payload, "lane_regressions_with_context")

    lines = [
        "# ScenarioLens Context-Joined Failure Study",
        "",
        "This report joins ScenarioLens baseline failure metrics with parsed "
        "Waymo Motion map, traffic-signal, stop-point, and lane-topology context. "
        "The goal is to move from 'this scenario is hard' toward 'this scenario "
        "is hard and has specific context that evaluation should preserve.'",
        "",
        "Raw Waymo files and per-scenario derived packets remain outside git.",
        "",
        "## Run Scope",
        "",
        f"- Inputs: {', '.join(f'`{path}`' for path in payload['input_paths'])}",
        f"- Input format: `{payload['input_format']}`",
        f"- Ready for analysis: {payload['ready']}",
        f"- Sources analyzed: {payload['source_count']}",
        f"- Scenarios analyzed: {payload['scenario_count']}",
        f"- Max scenarios per input: {payload['max_scenarios_per_input']}",
        "- Raw scenario data committed: no",
        "- Public artifact contains aggregate counts, scenario IDs, and metrics only",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Scenarios | {aggregate['scenario_count']} |",
        f"| Evaluated prediction targets | {aggregate['evaluated_target_count']} |",
        f"| Mean ScenarioLens score | {_number_text(aggregate['mean_score'])} |",
        f"| Mean constant-velocity FDE | {_meter_text(aggregate['constant_velocity_fde_m'])} |",
        f"| Constant-velocity miss rate | {_percent_text(aggregate['constant_velocity_miss_rate'])} |",
        f"| Mean lane-aware FDE | {_meter_text(aggregate['lane_aware_fde_m'])} |",
        f"| Mean lane-aware FDE improvement | {_signed_meter_text(aggregate['fde_improvement_m'])} |",
        f"| Signal-context scenarios | {aggregate['signal_context_scenario_count']} |",
        f"| Route-context scenarios | {aggregate['route_context_scenario_count']} |",
        f"| Lane-aware map-used targets | {aggregate['map_used_count']} |",
        f"| Lane-aware fallback targets | {aggregate['fallback_count']} |",
        "",
        "## Context Buckets",
        "",
        "| Bucket | Scenarios | Targets | Mean score | CV FDE | CV miss | Lane FDE | Lane delta | Signal states | Route links |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in context_groups:
        assert isinstance(group, dict)
        lines.append(
            "| "
            f"{group['label']} | "
            f"{group['scenario_count']} | "
            f"{group['evaluated_target_count']} | "
            f"{_number_text(group['mean_score'])} | "
            f"{_meter_text(group['constant_velocity_fde_m'])} | "
            f"{_percent_text(group['constant_velocity_miss_rate'])} | "
            f"{_meter_text(group['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(group['fde_improvement_m'])} | "
            f"{group['signal_lane_state_count']} | "
            f"{group['route_link_count']} |"
        )

    lines.extend(
        [
            "",
            "## Per-Source Summary",
            "",
            "| Source | Scenarios | Targets | Mean score | CV FDE | CV miss | Signal ctx | Route ctx |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in sources:
        assert isinstance(source, dict)
        lines.append(
            "| "
            f"`{source['source_name']}` | "
            f"{source['scenario_count']} | "
            f"{source['evaluated_target_count']} | "
            f"{_number_text(source['mean_score'])} | "
            f"{_meter_text(source['constant_velocity_fde_m'])} | "
            f"{_percent_text(source['constant_velocity_miss_rate'])} | "
            f"{source['signal_context_scenario_count']} | "
            f"{source['route_context_scenario_count']} |"
        )

    lines.extend(
        [
            "",
            "## Hardest Context-Rich Baseline Failures",
            "",
            "| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Map features | Signal states | Route links | Top signal |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_failure_rows(lines, hardest)

    lines.extend(
        [
            "",
            "## Signal-Context Failures",
            "",
            "| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Signal states | Stop states | Top signal |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_failure_rows(lines, signal_failures, mode="signal")

    lines.extend(
        [
            "",
            "## Route-Context Failures",
            "",
            "| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Route links | Entry | Exit | Neighbors |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    _append_failure_rows(lines, route_failures, mode="route")

    lines.extend(
        [
            "",
            "## Lane-Aware Regressions With Context",
            "",
            "Negative lane delta means the lane-aware baseline had higher FDE than "
            "constant velocity. These are useful debugging targets when they also "
            "have rich map, signal, or route context.",
            "",
            "| Rank | Source | Scenario | CV FDE | Lane FDE | Lane delta | Map used | Fallbacks | Signal states | Route links | Top signal |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_regression_rows(lines, lane_regressions)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a diagnostic join, not a causal claim that traffic lights or "
            "route links caused a baseline failure.",
            "- Signal-context and route-context buckets help select cases for "
            "casebooks, replay, and future route/intent features.",
            "- Lane-aware regressions remain valuable: they show where simple lane "
            "following is not enough even when rich context is available.",
            "- These joined rows feed `scenariolens context-eval-set`, which "
            "turns ranked context failures into curated scenario groups for "
            "casebook and replay-candidate selection.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _scenario_context_failure_row(
    source: Path,
    source_index: int,
    scenario_index: int,
    scenario: Scenario,
) -> dict[str, object]:
    score = score_scenario(scenario)
    comparison = compare_prediction_baselines(scenario)
    map_summary = _mapping(scenario.metadata.get("waymo_map_summary"))
    dynamic_summary = _mapping(scenario.metadata.get("waymo_dynamic_map_summary"))
    signal_state_counts = _mapping(dynamic_summary.get("state_counts"))
    top_signal_state = _top_count_label(signal_state_counts)
    signal_lane_state_count = _int(dynamic_summary.get("lane_state_count"))
    route_link_count = _int(map_summary.get("route_link_count"))
    map_feature_count = _int(map_summary.get("feature_count"))
    return {
        "source_input": str(source),
        "source_name": _source_name(source),
        "source_index": source_index,
        "scenario_index": scenario_index,
        "scenario_id": scenario.scenario_id,
        "tags": list(score.tags),
        "score": score.interaction_score,
        "baseline_failure_score": score.baseline_failure_score,
        "evaluated_target_count": comparison.evaluated_track_count,
        "constant_velocity_fde_m": comparison.constant_velocity_fde_m,
        "constant_velocity_miss_rate": comparison.constant_velocity_miss_rate,
        "lane_aware_fde_m": comparison.lane_aware_fde_m,
        "fde_improvement_m": comparison.fde_improvement_m,
        "map_used_count": comparison.map_used_count,
        "fallback_count": comparison.fallback_count,
        "map_context": map_feature_count > 0 or "map_context" in score.tags,
        "signal_context": signal_lane_state_count > 0,
        "route_context": route_link_count > 0,
        "map_feature_count": map_feature_count,
        "lane_count": _int(map_summary.get("lane_count")),
        "signal_lane_state_count": signal_lane_state_count,
        "signal_stop_state_count": _int(dynamic_summary.get("stop_state_count")),
        "signal_go_state_count": _int(dynamic_summary.get("go_state_count")),
        "signal_unknown_state_count": _int(dynamic_summary.get("unknown_state_count")),
        "route_link_count": route_link_count,
        "entry_link_count": _int(map_summary.get("entry_link_count")),
        "exit_link_count": _int(map_summary.get("exit_link_count")),
        "neighbor_link_count": _int(map_summary.get("neighbor_link_count")),
        "top_signal_state": top_signal_state,
        "dominant_signal_bucket": _dominant_signal_bucket(top_signal_state),
    }


def _aggregate_rows(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    return {
        "scenario_count": len(rows),
        "evaluated_target_count": _sum_rows(rows, "evaluated_target_count"),
        "mean_score": _mean(tuple(_float(row.get("score")) for row in rows)),
        "constant_velocity_fde_m": _mean(
            tuple(
                value
                for row in rows
                if (value := _optional_float(row.get("constant_velocity_fde_m"))) is not None
            )
        ),
        "constant_velocity_miss_rate": _weighted_miss_rate(rows),
        "lane_aware_fde_m": _mean(
            tuple(
                value
                for row in rows
                if (value := _optional_float(row.get("lane_aware_fde_m"))) is not None
            )
        ),
        "fde_improvement_m": _mean(
            tuple(
                value
                for row in rows
                if (value := _optional_float(row.get("fde_improvement_m"))) is not None
            )
        ),
        "map_used_count": _sum_rows(rows, "map_used_count"),
        "fallback_count": _sum_rows(rows, "fallback_count"),
        "map_context_scenario_count": sum(bool(row.get("map_context")) for row in rows),
        "signal_context_scenario_count": sum(
            bool(row.get("signal_context")) for row in rows
        ),
        "route_context_scenario_count": sum(
            bool(row.get("route_context")) for row in rows
        ),
        "map_feature_count": _sum_rows(rows, "map_feature_count"),
        "signal_lane_state_count": _sum_rows(rows, "signal_lane_state_count"),
        "signal_stop_state_count": _sum_rows(rows, "signal_stop_state_count"),
        "signal_go_state_count": _sum_rows(rows, "signal_go_state_count"),
        "signal_unknown_state_count": _sum_rows(rows, "signal_unknown_state_count"),
        "route_link_count": _sum_rows(rows, "route_link_count"),
        "entry_link_count": _sum_rows(rows, "entry_link_count"),
        "exit_link_count": _sum_rows(rows, "exit_link_count"),
        "neighbor_link_count": _sum_rows(rows, "neighbor_link_count"),
    }


def _context_groups(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    group_specs = (
        ("all", "All scenarios", lambda row: True),
        ("signal", "Traffic signal context", lambda row: bool(row.get("signal_context"))),
        ("no_signal", "No parsed signal states", lambda row: not bool(row.get("signal_context"))),
        ("route", "Lane-topology context", lambda row: bool(row.get("route_context"))),
        ("no_route", "No lane-topology links", lambda row: not bool(row.get("route_context"))),
        (
            "stop_dominant",
            "Stop-dominant signal",
            lambda row: row.get("dominant_signal_bucket") == "stop",
        ),
        (
            "go_dominant",
            "Go-dominant signal",
            lambda row: row.get("dominant_signal_bucket") == "go",
        ),
        (
            "unknown_dominant",
            "Unknown-dominant signal",
            lambda row: row.get("dominant_signal_bucket") == "unknown",
        ),
    )
    groups = []
    for group_id, label, predicate in group_specs:
        group_rows = tuple(row for row in rows if predicate(row))
        if not group_rows and group_id != "all":
            continue
        groups.append({"group_id": group_id, "label": label, **_aggregate_rows(group_rows)})
    return groups


def _rank_context_failures(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        (
            row
            for row in _rankable_failure_rows(rows)
            if row.get("map_context") or row.get("signal_context") or row.get("route_context")
        ),
        key=lambda row: (
            -float(row["constant_velocity_fde_m"]),
            -float(row["score"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_signal_failures(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        (row for row in _rankable_failure_rows(rows) if row.get("signal_context")),
        key=lambda row: (
            -float(row["constant_velocity_fde_m"]),
            -_int(row.get("signal_lane_state_count")),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_route_failures(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        (row for row in _rankable_failure_rows(rows) if row.get("route_context")),
        key=lambda row: (
            -float(row["constant_velocity_fde_m"]),
            -_int(row.get("route_link_count")),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_lane_regressions(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        (
            row
            for row in rows
            if _optional_float(row.get("fde_improvement_m")) is not None
            if row.get("map_context") or row.get("signal_context") or row.get("route_context")
        ),
        key=lambda row: (
            float(row["fde_improvement_m"]),
            -float(row.get("constant_velocity_fde_m") or 0.0),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rankable_failure_rows(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        row for row in rows if _optional_float(row.get("constant_velocity_fde_m")) is not None
    )


def _append_failure_rows(
    lines: list[str],
    rows: list[object],
    mode: str = "context",
) -> None:
    if not rows:
        if mode == "route":
            lines.append("| n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | 0 | 0 |")
        elif mode == "signal":
            lines.append("| n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | n/a |")
        else:
            lines.append("| n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | 0 | n/a |")
        return

    for rank, row in enumerate(rows, start=1):
        assert isinstance(row, dict)
        if mode == "signal":
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{_number_text(row['score'])} | "
                f"{_meter_text(row['constant_velocity_fde_m'])} | "
                f"{_percent_text(row['constant_velocity_miss_rate'])} | "
                f"{_signed_meter_text(row['fde_improvement_m'])} | "
                f"{row['signal_lane_state_count']} | "
                f"{row['signal_stop_state_count']} | "
                f"`{row['top_signal_state']}` |"
            )
        elif mode == "route":
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{_number_text(row['score'])} | "
                f"{_meter_text(row['constant_velocity_fde_m'])} | "
                f"{_percent_text(row['constant_velocity_miss_rate'])} | "
                f"{_signed_meter_text(row['fde_improvement_m'])} | "
                f"{row['route_link_count']} | "
                f"{row['entry_link_count']} | "
                f"{row['exit_link_count']} | "
                f"{row['neighbor_link_count']} |"
            )
        else:
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{_number_text(row['score'])} | "
                f"{_meter_text(row['constant_velocity_fde_m'])} | "
                f"{_percent_text(row['constant_velocity_miss_rate'])} | "
                f"{_signed_meter_text(row['fde_improvement_m'])} | "
                f"{row['map_feature_count']} | "
                f"{row['signal_lane_state_count']} | "
                f"{row['route_link_count']} | "
                f"`{row['top_signal_state']}` |"
            )


def _append_regression_rows(lines: list[str], rows: list[object]) -> None:
    if not rows:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0 | n/a |")
        return

    for rank, row in enumerate(rows, start=1):
        assert isinstance(row, dict)
        lines.append(
            "| "
            f"{rank} | "
            f"`{row['source_name']}` | "
            f"`{row['scenario_id']}` | "
            f"{_meter_text(row['constant_velocity_fde_m'])} | "
            f"{_meter_text(row['lane_aware_fde_m'])} | "
            f"{_signed_meter_text(row['fde_improvement_m'])} | "
            f"{row['map_used_count']} | "
            f"{row['fallback_count']} | "
            f"{row['signal_lane_state_count']} | "
            f"{row['route_link_count']} | "
            f"`{row['top_signal_state']}` |"
        )


def _dominant_signal_bucket(label: str) -> str:
    if label == "none":
        return "none"
    if "UNKNOWN" in label:
        return "unknown"
    if "STOP" in label:
        return "stop"
    if "CAUTION" in label:
        return "caution"
    if "_GO" in label:
        return "go"
    return "other"


def _weighted_miss_rate(rows: tuple[dict[str, object], ...]) -> float | None:
    numerator = 0.0
    denominator = 0
    for row in rows:
        targets = _int(row.get("evaluated_target_count"))
        miss_rate = _optional_float(row.get("constant_velocity_miss_rate"))
        if targets <= 0 or miss_rate is None:
            continue
        numerator += miss_rate * targets
        denominator += targets
    if denominator <= 0:
        return None
    return round(numerator / denominator, 3)


def _top_count_label(counts: dict[str, object]) -> str:
    if not counts:
        return "none"
    key, value = sorted(
        counts.items(),
        key=lambda item: (-_int(item[1]), str(item[0])),
    )[0]
    return f"{key} ({value})"


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _sum_rows(rows: tuple[dict[str, object], ...], key: str) -> int:
    return sum(_int(row.get(key)) for row in rows)


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


def _source_name(path: Path) -> str:
    return path.name or str(path)


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
