from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    load_failure_study_input,
)
from scenariolens.schema import Scenario

CONTEXT_STUDY_FORMAT = "scenariolens.context_study.v1"
CONTEXT_STUDY_INPUT_FORMATS = FAILURE_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class ContextStudyResult:
    """Files produced by a public-safe Waymo context coverage study."""

    ready: bool
    source_count: int
    scenario_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_context_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 10,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> ContextStudyResult:
    """Generate a public-safe map, signal, and route-context summary."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = context_study_payload(
        input_paths=tuple(Path(path) for path in input_paths),
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        input_format=input_format,
    )
    report = context_study_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return ContextStudyResult(
        ready=bool(payload["ready"]),
        source_count=int(payload["source_count"]),
        scenario_count=int(payload["scenario_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def context_study_payload(
    input_paths: tuple[Path, ...],
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    input_format: str,
) -> dict[str, object]:
    """Return deterministic public-safe context metadata for input slices."""

    if not input_paths:
        raise ValueError("At least one input path is required for context-study.")
    if input_format not in CONTEXT_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported context-study input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(CONTEXT_STUDY_INPUT_FORMATS)}"
        )
    if top < 1:
        raise ValueError("top must be at least 1.")

    ready = True
    sources: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []

    for source_index, source in enumerate(input_paths, start=1):
        input_ready, preflight, scenarios = load_failure_study_input(
            source=source,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )
        if not input_ready:
            ready = False
            source_summary = _aggregate_rows(())
            sources.append(
                {
                    "input_path": str(source),
                    "source_name": _source_name(source),
                    "ready": False,
                    "preflight": preflight or {},
                    **source_summary,
                }
            )
            continue

        rows = tuple(
            _scenario_context_row(
                source=source,
                source_index=source_index,
                scenario_index=scenario_index,
                scenario=scenario,
            )
            for scenario_index, scenario in enumerate(scenarios, start=1)
        )
        scenario_rows.extend(rows)
        sources.append(
            {
                "input_path": str(source),
                "source_name": _source_name(source),
                "ready": True,
                "preflight": preflight or {},
                **_aggregate_rows(rows),
            }
        )

    rows_tuple = tuple(scenario_rows)
    return {
        "format": CONTEXT_STUDY_FORMAT,
        "input_paths": [str(path) for path in input_paths],
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios_per_input": max_scenarios,
        "top": top,
        "ready": ready,
        "source_count": len(input_paths),
        "scenario_count": sum(int(source["scenario_count"]) for source in sources),
        "aggregate": _aggregate_rows(rows_tuple),
        "sources": sources,
        "signal_state_counts": _merge_counter_rows(rows_tuple, "signal_state_counts"),
        "map_feature_kind_counts": _merge_counter_rows(rows_tuple, "map_feature_kind_counts"),
        "lane_type_counts": _merge_counter_rows(rows_tuple, "lane_type_counts"),
        "top_map_dense_scenarios": _rank_map_dense(rows_tuple, top=top),
        "top_signal_dense_scenarios": _rank_signal_dense(rows_tuple, top=top),
        "top_route_context_scenarios": _rank_route_context(rows_tuple, top=top),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "This is aggregate context coverage over local slices. It is not a "
            "full Waymo benchmark, routing model, or traffic-light quality audit."
        ),
    }


def context_study_markdown(payload: dict[str, object]) -> str:
    """Return Markdown report from a context-study payload."""

    aggregate = _required_mapping(payload, "aggregate")
    sources = _required_list(payload, "sources")
    signal_state_counts = _required_mapping(payload, "signal_state_counts")
    map_feature_kind_counts = _required_mapping(payload, "map_feature_kind_counts")
    lane_type_counts = _required_mapping(payload, "lane_type_counts")
    map_dense = _required_list(payload, "top_map_dense_scenarios")
    signal_dense = _required_list(payload, "top_signal_dense_scenarios")
    route_dense = _required_list(payload, "top_route_context_scenarios")

    lines = [
        "# ScenarioLens Waymo Map and Signal Context Study",
        "",
        "This report summarizes public-safe map, traffic-signal, and lane-topology "
        "context parsed from local Waymo Motion slices. It exists to answer a "
        "recruiter-facing question that pure ADE/FDE reports cannot answer: "
        "what contextual evidence is available when a scenario looks hard?",
        "",
        "Raw Waymo TFRecords and per-scenario derived packets remain outside git.",
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
        "- Public artifact contains scenario IDs plus aggregate counts only",
        "",
        "## Executive Summary",
        "",
        "| Context family | Scenarios | Coverage | Count |",
        "| --- | ---: | ---: | ---: |",
        f"| Static map features | {aggregate['map_context_scenario_count']} | "
        f"{_percent_count(aggregate['map_context_scenario_count'], aggregate['scenario_count'])} | "
        f"{aggregate['map_feature_count']} features |",
        f"| Traffic signal lane states | {aggregate['signal_context_scenario_count']} | "
        f"{_percent_count(aggregate['signal_context_scenario_count'], aggregate['scenario_count'])} | "
        f"{aggregate['signal_lane_state_count']} lane states |",
        f"| Lane topology / route hints | {aggregate['route_context_scenario_count']} | "
        f"{_percent_count(aggregate['route_context_scenario_count'], aggregate['scenario_count'])} | "
        f"{aggregate['route_link_count']} links |",
        f"| Signal stop points | n/a | n/a | {aggregate['signal_stop_point_count']} stop points |",
        "",
        "## Static Map Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total map features | {aggregate['map_feature_count']} |",
        f"| Lane features | {aggregate['lane_count']} |",
        f"| Lane speed limits parsed | {aggregate['lane_speed_limit_count']} |",
        f"| Mean parsed lane speed limit | {_mph_text(aggregate['mean_lane_speed_limit_mph'])} |",
        f"| Entry-lane links | {aggregate['entry_link_count']} |",
        f"| Exit-lane links | {aggregate['exit_link_count']} |",
        f"| Neighbor-lane links | {aggregate['neighbor_link_count']} |",
        "",
        "Map feature kinds:",
        "",
    ]
    _append_counts(lines, map_feature_kind_counts)

    lines.extend(["", "Lane types:", ""])
    _append_counts(lines, lane_type_counts)

    lines.extend(
        [
            "",
            "## Traffic Signal Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Dynamic-map timesteps | {aggregate['dynamic_map_timestep_count']} |",
            f"| Timesteps with observed lane states | {aggregate['signal_observed_timestep_count']} |",
            f"| Signal-controlled lane references | {aggregate['signal_controlled_lane_count']} |",
            f"| Stop-state observations | {aggregate['signal_stop_state_count']} |",
            f"| Caution-state observations | {aggregate['signal_caution_state_count']} |",
            f"| Go-state observations | {aggregate['signal_go_state_count']} |",
            f"| Unknown-state observations | {aggregate['signal_unknown_state_count']} |",
            "",
            "Signal state distribution:",
            "",
        ]
    )
    _append_counts(lines, signal_state_counts)

    lines.extend(
        [
            "",
            "## Per-Source Summary",
            "",
            "| Source | Scenarios | Map ctx | Signal ctx | Route ctx | Features | Lane states | Route links |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in sources:
        assert isinstance(source, dict)
        lines.append(
            "| "
            f"`{source['source_name']}` | "
            f"{source['scenario_count']} | "
            f"{source['map_context_scenario_count']} | "
            f"{source['signal_context_scenario_count']} | "
            f"{source['route_context_scenario_count']} | "
            f"{source['map_feature_count']} | "
            f"{source['signal_lane_state_count']} | "
            f"{source['route_link_count']} |"
        )

    lines.extend(
        [
            "",
            "## Map-Dense Scenarios",
            "",
            "| Rank | Source | Scenario | Features | Lanes | Crosswalks | Route links | Signal states |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    _append_ranked_rows(lines, map_dense)

    lines.extend(
        [
            "",
            "## Signal-Dense Scenarios",
            "",
            "| Rank | Source | Scenario | Signal states | Controlled lanes | Stop points | Top state | Map features |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    _append_ranked_rows(lines, signal_dense, mode="signal")

    lines.extend(
        [
            "",
            "## Route-Context Scenarios",
            "",
            "| Rank | Source | Scenario | Route links | Entry | Exit | Neighbors | Lane speed limits |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    _append_ranked_rows(lines, route_dense, mode="route")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Map and signal context are coverage signals for evaluation design, not "
            "proof that a baseline understands right-of-way.",
            "- Route-context counts are lane-graph hints from entry, exit, and neighbor "
            "relationships; ScenarioLens does not infer a route plan yet.",
            "- Traffic-signal counts are parsed from public Waymo Motion dynamic-map "
            "lane states. This report does not validate signal label quality.",
            "- The useful next step is to join these context summaries back to "
            "baseline failures so hard scenarios can be grouped by map, signal, "
            "and route evidence.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _scenario_context_row(
    source: Path,
    source_index: int,
    scenario_index: int,
    scenario: Scenario,
) -> dict[str, object]:
    map_summary = _mapping(scenario.metadata.get("waymo_map_summary"))
    dynamic_summary = _mapping(scenario.metadata.get("waymo_dynamic_map_summary"))
    feature_kind_counts = _mapping(map_summary.get("kind_counts"))
    lane_type_counts = _mapping(map_summary.get("lane_type_counts"))
    signal_state_counts = _mapping(dynamic_summary.get("state_counts"))
    route_link_count = _int(map_summary.get("route_link_count"))
    feature_count = _int(map_summary.get("feature_count"))
    signal_lane_state_count = _int(dynamic_summary.get("lane_state_count"))
    top_signal_state = _top_count_label(signal_state_counts)
    return {
        "source_input": str(source),
        "source_name": _source_name(source),
        "source_index": source_index,
        "scenario_index": scenario_index,
        "scenario_id": scenario.scenario_id,
        "tags": list(scenario.tags),
        "map_context": feature_count > 0 or "map_context" in scenario.tags,
        "signal_context": signal_lane_state_count > 0,
        "dynamic_map_context": _int(dynamic_summary.get("timestep_count")) > 0
        or "traffic_signal_context" in scenario.tags,
        "route_context": route_link_count > 0,
        "map_feature_count": feature_count,
        "lane_count": _int(map_summary.get("lane_count")),
        "crosswalk_count": _int(feature_kind_counts.get("crosswalk")),
        "road_line_count": _int(feature_kind_counts.get("road_line")),
        "road_edge_count": _int(feature_kind_counts.get("road_edge")),
        "lane_speed_limit_count": _int(map_summary.get("lane_speed_limit_count")),
        "lane_speed_limit_sum_mph": _speed_limit_sum(scenario),
        "entry_link_count": _int(map_summary.get("entry_link_count")),
        "exit_link_count": _int(map_summary.get("exit_link_count")),
        "neighbor_link_count": _int(map_summary.get("neighbor_link_count")),
        "route_link_count": route_link_count,
        "dynamic_map_timestep_count": _int(dynamic_summary.get("timestep_count")),
        "signal_observed_timestep_count": _int(
            dynamic_summary.get("observed_timestep_count")
        ),
        "signal_lane_state_count": signal_lane_state_count,
        "signal_controlled_lane_count": _int(dynamic_summary.get("controlled_lane_count")),
        "signal_stop_point_count": _int(dynamic_summary.get("stop_point_count")),
        "signal_stop_state_count": _int(dynamic_summary.get("stop_state_count")),
        "signal_caution_state_count": _int(dynamic_summary.get("caution_state_count")),
        "signal_go_state_count": _int(dynamic_summary.get("go_state_count")),
        "signal_unknown_state_count": _int(dynamic_summary.get("unknown_state_count")),
        "map_feature_kind_counts": dict(sorted(feature_kind_counts.items())),
        "lane_type_counts": dict(sorted(lane_type_counts.items())),
        "signal_state_counts": dict(sorted(signal_state_counts.items())),
        "top_signal_state": top_signal_state,
    }


def _aggregate_rows(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    speed_count = sum(_int(row.get("lane_speed_limit_count")) for row in rows)
    speed_sum = sum(float(row.get("lane_speed_limit_sum_mph", 0.0) or 0.0) for row in rows)
    return {
        "scenario_count": len(rows),
        "map_context_scenario_count": sum(bool(row.get("map_context")) for row in rows),
        "signal_context_scenario_count": sum(
            bool(row.get("signal_context")) for row in rows
        ),
        "dynamic_map_context_scenario_count": sum(
            bool(row.get("dynamic_map_context")) for row in rows
        ),
        "route_context_scenario_count": sum(
            bool(row.get("route_context")) for row in rows
        ),
        "map_feature_count": _sum_rows(rows, "map_feature_count"),
        "lane_count": _sum_rows(rows, "lane_count"),
        "crosswalk_count": _sum_rows(rows, "crosswalk_count"),
        "road_line_count": _sum_rows(rows, "road_line_count"),
        "road_edge_count": _sum_rows(rows, "road_edge_count"),
        "lane_speed_limit_count": speed_count,
        "mean_lane_speed_limit_mph": round(speed_sum / speed_count, 3)
        if speed_count
        else None,
        "entry_link_count": _sum_rows(rows, "entry_link_count"),
        "exit_link_count": _sum_rows(rows, "exit_link_count"),
        "neighbor_link_count": _sum_rows(rows, "neighbor_link_count"),
        "route_link_count": _sum_rows(rows, "route_link_count"),
        "dynamic_map_timestep_count": _sum_rows(rows, "dynamic_map_timestep_count"),
        "signal_observed_timestep_count": _sum_rows(
            rows,
            "signal_observed_timestep_count",
        ),
        "signal_lane_state_count": _sum_rows(rows, "signal_lane_state_count"),
        "signal_controlled_lane_count": _sum_rows(rows, "signal_controlled_lane_count"),
        "signal_stop_point_count": _sum_rows(rows, "signal_stop_point_count"),
        "signal_stop_state_count": _sum_rows(rows, "signal_stop_state_count"),
        "signal_caution_state_count": _sum_rows(rows, "signal_caution_state_count"),
        "signal_go_state_count": _sum_rows(rows, "signal_go_state_count"),
        "signal_unknown_state_count": _sum_rows(rows, "signal_unknown_state_count"),
        "map_feature_kind_counts": _merge_counter_rows(rows, "map_feature_kind_counts"),
        "lane_type_counts": _merge_counter_rows(rows, "lane_type_counts"),
        "signal_state_counts": _merge_counter_rows(rows, "signal_state_counts"),
    }


def _rank_map_dense(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            -_int(row.get("map_feature_count")),
            -_int(row.get("signal_lane_state_count")),
            str(row.get("scenario_id")),
        ),
    )[:top]


def _rank_signal_dense(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            -_int(row.get("signal_lane_state_count")),
            -_int(row.get("signal_controlled_lane_count")),
            str(row.get("scenario_id")),
        ),
    )[:top]


def _rank_route_context(
    rows: tuple[dict[str, object], ...],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            -_int(row.get("route_link_count")),
            -_int(row.get("lane_speed_limit_count")),
            str(row.get("scenario_id")),
        ),
    )[:top]


def _append_ranked_rows(
    lines: list[str],
    rows: list[object],
    mode: str = "map",
) -> None:
    if not rows:
        lines.append("| n/a | n/a | n/a | 0 | 0 | 0 | 0 | 0 |")
        return

    for rank, row in enumerate(rows, start=1):
        assert isinstance(row, dict)
        if mode == "signal":
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{row['signal_lane_state_count']} | "
                f"{row['signal_controlled_lane_count']} | "
                f"{row['signal_stop_point_count']} | "
                f"`{row['top_signal_state']}` | "
                f"{row['map_feature_count']} |"
            )
        elif mode == "route":
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{row['route_link_count']} | "
                f"{row['entry_link_count']} | "
                f"{row['exit_link_count']} | "
                f"{row['neighbor_link_count']} | "
                f"{row['lane_speed_limit_count']} |"
            )
        else:
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['source_name']}` | "
                f"`{row['scenario_id']}` | "
                f"{row['map_feature_count']} | "
                f"{row['lane_count']} | "
                f"{row['crosswalk_count']} | "
                f"{row['route_link_count']} | "
                f"{row['signal_lane_state_count']} |"
            )


def _append_counts(lines: list[str], counts: dict[str, object]) -> None:
    if not counts:
        lines.append("- none")
        return
    for key, value in counts.items():
        lines.append(f"- `{key}`: {value}")


def _speed_limit_sum(scenario: Scenario) -> float:
    total = 0.0
    for feature in _as_list(scenario.metadata.get("waymo_map_features")):
        if not isinstance(feature, dict):
            continue
        value = feature.get("speed_limit_mph")
        if value is None:
            continue
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
    return round(total, 3)


def _top_count_label(counts: dict[str, object]) -> str:
    if not counts:
        return "none"
    key, value = sorted(
        counts.items(),
        key=lambda item: (-_int(item[1]), str(item[0])),
    )[0]
    return f"{key} ({value})"


def _merge_counter_rows(
    rows: tuple[dict[str, object], ...],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        values = _mapping(row.get(key))
        for name, count in values.items():
            counts[str(name)] = counts.get(str(name), 0) + _int(count)
    return dict(sorted(counts.items()))


def _sum_rows(rows: tuple[dict[str, object], ...], key: str) -> int:
    return sum(_int(row.get(key)) for row in rows)


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _source_name(path: Path) -> str:
    return path.name or str(path)


def _percent_count(value: object, total: object) -> str:
    denominator = _int(total)
    if denominator <= 0:
        return "n/a"
    return f"{(_int(value) / denominator) * 100:.1f}%"


def _mph_text(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1f} mph"


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
