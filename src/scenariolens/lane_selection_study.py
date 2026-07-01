from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    load_failure_study_input,
)
from scenariolens.prediction import (
    DEFAULT_MISS_THRESHOLD_M,
    PredictionBaselineSummary,
    constant_velocity_baseline,
    heading_aware_lane_baseline,
    lane_aware_baseline,
)

LANE_SELECTION_STUDY_FORMAT = "scenariolens.lane_selection_study.v1"
LANE_SELECTION_STUDY_INPUT_FORMATS = FAILURE_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class LaneSelectionStudyResult:
    """Files produced by a heading-aware lane-selection study."""

    ready: bool
    source_count: int
    scenario_count: int
    evaluated_target_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_selection_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 10,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> LaneSelectionStudyResult:
    """Generate a public-safe heading-aware lane-selection ablation."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_selection_study_payload(
        input_paths=tuple(Path(path) for path in input_paths),
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        input_format=input_format,
    )
    report = lane_selection_study_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneSelectionStudyResult(
        ready=bool(payload["ready"]),
        source_count=int(payload["source_count"]),
        scenario_count=int(payload["scenario_count"]),
        evaluated_target_count=int(aggregate["evaluated_target_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_selection_study_payload(
    input_paths: tuple[Path, ...],
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    input_format: str,
) -> dict[str, object]:
    """Return deterministic public-safe heading-aware lane-selection metadata."""

    if not input_paths:
        raise ValueError("At least one input path is required for lane-selection study.")
    if input_format not in LANE_SELECTION_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported lane-selection-study input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(LANE_SELECTION_STUDY_INPUT_FORMATS)}"
        )
    if top < 1:
        raise ValueError("top must be at least 1.")

    ready = True
    sources: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []
    track_rows: list[dict[str, object]] = []

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
                    "scenario_count": 0,
                    "preflight": preflight or {},
                    **_aggregate_track_rows(()),
                    "heading_fallback_reasons": {},
                }
            )
            continue

        source_scenario_rows: list[dict[str, object]] = []
        source_track_rows: list[dict[str, object]] = []
        for scenario_index, scenario in enumerate(scenarios, start=1):
            constant = constant_velocity_baseline(scenario)
            nearest = lane_aware_baseline(scenario)
            heading = heading_aware_lane_baseline(scenario)
            scenario_row, rows = _comparison_rows(
                source=source,
                source_index=source_index,
                scenario_index=scenario_index,
                scenario_id=scenario.scenario_id,
                constant=constant,
                nearest=nearest,
                heading=heading,
            )
            source_scenario_rows.append(scenario_row)
            source_track_rows.extend(rows)

        scenario_rows.extend(source_scenario_rows)
        track_rows.extend(source_track_rows)
        sources.append(
            {
                "input_path": str(source),
                "source_name": _source_name(source),
                "ready": True,
                "scenario_count": len(scenarios),
                "preflight": preflight or {},
                **_aggregate_track_rows(tuple(source_track_rows)),
                "heading_fallback_reasons": _fallback_reason_counts(
                    tuple(source_track_rows),
                    key="heading_fallback_reason",
                ),
            }
        )

    return {
        "format": LANE_SELECTION_STUDY_FORMAT,
        "input_paths": [str(path) for path in input_paths],
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios_per_input": max_scenarios,
        "top": top,
        "ready": ready,
        "source_count": len(input_paths),
        "scenario_count": sum(int(source["scenario_count"]) for source in sources),
        "aggregate": _aggregate_track_rows(tuple(track_rows)),
        "sources": sources,
        "heading_fallback_reasons": _fallback_reason_counts(
            tuple(track_rows),
            key="heading_fallback_reason",
        ),
        "top_heading_improvements": _rank_heading_improvements(scenario_rows, top=top),
        "top_heading_regressions": _rank_heading_regressions(scenario_rows, top=top),
        "top_heading_fallbacks": _rank_heading_fallbacks(scenario_rows, top=top),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "Heading-aware lane selection is an ablation beside the default "
            "nearest-lane baseline; it does not change ScenarioLens scoring and "
            "does not claim production map matching."
        ),
    }


def lane_selection_study_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for a lane-selection study payload."""

    aggregate = _required_mapping(payload, "aggregate")
    sources = _required_list(payload, "sources")
    fallback_reasons = _required_mapping(payload, "heading_fallback_reasons")
    top_improvements = _required_list(payload, "top_heading_improvements")
    top_regressions = _required_list(payload, "top_heading_regressions")
    top_fallbacks = _required_list(payload, "top_heading_fallbacks")

    lines = [
        "# ScenarioLens Heading-Aware Lane Selection Study",
        "",
        "This report compares the existing nearest-lane baseline with a "
        "heading-aware lane-selection variant. The variant keeps the same "
        "constant-velocity fallback discipline, but when multiple lane polylines "
        "are close to a target it prefers a lane whose tangent aligns with the "
        "target's anchor velocity.",
        "",
        "It is intentionally scoped: this is an ablation beside the default "
        "baseline, not a production map matcher, not a Waymo benchmark claim, "
        "and not a change to ScenarioLens' default scoring baseline.",
        "",
        "## Run Scope",
        "",
        f"- Inputs: {', '.join(f'`{path}`' for path in payload['input_paths'])}",
        f"- Input format: `{payload['input_format']}`",
        f"- Ready for analysis: {payload['ready']}",
        f"- Sources compared: {payload['source_count']}",
        f"- Scenarios analyzed: {payload['scenario_count']}",
        f"- Evaluated prediction targets: {aggregate['evaluated_target_count']}",
        f"- Max scenarios per input: {payload['max_scenarios_per_input']}",
        "- Raw scenario data committed: no",
        "",
        "## Executive Findings",
        "",
        "| Metric | Constant velocity | Nearest lane | Heading-aware lane |",
        "| --- | ---: | ---: | ---: |",
        f"| Mean FDE | {_meter_text(aggregate['constant_velocity_fde_m'])} | "
        f"{_meter_text(aggregate['nearest_lane_fde_m'])} | "
        f"{_meter_text(aggregate['heading_lane_fde_m'])} |",
        f"| Miss rate | {_percent_text(aggregate['constant_velocity_miss_rate'])} | "
        f"{_percent_text(aggregate['nearest_lane_miss_rate'])} | "
        f"{_percent_text(aggregate['heading_lane_miss_rate'])} |",
        f"| Map used | n/a | {aggregate['nearest_map_used_count']} | "
        f"{aggregate['heading_map_used_count']} |",
        f"| Fallbacks | n/a | {aggregate['nearest_fallback_count']} | "
        f"{aggregate['heading_fallback_count']} |",
        "",
        "| Delta | Value |",
        "| --- | ---: |",
        f"| Heading FDE improvement vs nearest lane | {_signed_meter_text(aggregate['heading_vs_nearest_fde_improvement_m'])} |",
        f"| Heading FDE improvement vs constant velocity | {_signed_meter_text(aggregate['heading_vs_constant_velocity_fde_improvement_m'])} |",
        "",
    ]

    if not payload["ready"]:
        lines.extend(
            [
                "## Next Action",
                "",
                "Fix the failing input path or use an ingestable ScenarioLens JSON "
                "file, then rerun `lane-selection-study`.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Per-Source Summary",
            "",
            "| Source | Scenarios | Targets | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Heading map used | Heading fallbacks |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in sources:
        assert isinstance(source, dict)
        lines.append(
            "| "
            f"`{source['source_name']}` | "
            f"{source['scenario_count']} | "
            f"{source['evaluated_target_count']} | "
            f"{_meter_text(source['constant_velocity_fde_m'])} | "
            f"{_meter_text(source['nearest_lane_fde_m'])} | "
            f"{_meter_text(source['heading_lane_fde_m'])} | "
            f"{_signed_meter_text(source['heading_vs_nearest_fde_improvement_m'])} | "
            f"{source['heading_map_used_count']} | "
            f"{source['heading_fallback_count']} |"
        )

    lines.extend(["", "## Heading-Aware Fallback Reasons", ""])
    if fallback_reasons:
        for reason, count in fallback_reasons.items():
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Largest Heading-Aware Improvements",
            "",
            "| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_ranked_rows(lines, top_improvements)

    lines.extend(
        [
            "",
            "## Largest Heading-Aware Regressions",
            "",
            "Negative deltas mean the heading-aware selector had higher FDE than "
            "the nearest-lane selector. Those rows are useful diagnostics for "
            "map coverage, lane direction, and intent assumptions.",
            "",
            "| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_ranked_rows(lines, top_regressions)

    lines.extend(
        [
            "",
            "## Heading-Fallback Heavy Scenarios",
            "",
            "| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    _append_ranked_rows(lines, top_fallbacks)

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            _diagnostic_note(aggregate),
            "- Heading-aware selection can reduce bad nearest-lane matches, but it can also choose to fall back more often when nearby lanes are poorly aligned.",
            "- The default ScenarioLens scorer remains constant velocity; this study is evidence for the next map-matching iteration, not a certified prediction model.",
            "- Public rows are aggregate and scenario-id level only; raw Waymo files and per-scenario derived packets stay out of git.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _comparison_rows(
    source: Path,
    source_index: int,
    scenario_index: int,
    scenario_id: str,
    constant: PredictionBaselineSummary,
    nearest: PredictionBaselineSummary,
    heading: PredictionBaselineSummary,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    nearest_by_track = {result.track_id: result for result in nearest.track_results}
    heading_by_track = {result.track_id: result for result in heading.track_results}
    track_rows = []
    for constant_result in constant.track_results:
        nearest_result = nearest_by_track.get(constant_result.track_id)
        heading_result = heading_by_track.get(constant_result.track_id)
        if nearest_result is None or heading_result is None:
            continue
        track_rows.append(
            {
                "source_input": str(source),
                "source_name": _source_name(source),
                "source_index": source_index,
                "scenario_index": scenario_index,
                "scenario_id": scenario_id,
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
                "constant_velocity_miss": constant_result.fde_m > DEFAULT_MISS_THRESHOLD_M,
                "nearest_lane_miss": nearest_result.fde_m > DEFAULT_MISS_THRESHOLD_M,
                "heading_lane_miss": heading_result.fde_m > DEFAULT_MISS_THRESHOLD_M,
                "nearest_map_used": nearest_result.map_used,
                "heading_map_used": heading_result.map_used,
                "nearest_fallback_reason": nearest_result.fallback_reason,
                "heading_fallback_reason": heading_result.fallback_reason,
            }
        )

    scenario_row = {
        "source_input": str(source),
        "source_name": _source_name(source),
        "source_index": source_index,
        "scenario_index": scenario_index,
        "scenario_id": scenario_id,
        "evaluated_target_count": len(track_rows),
        "constant_velocity_fde_m": constant.fde_m,
        "nearest_lane_fde_m": nearest.fde_m,
        "heading_lane_fde_m": heading.fde_m,
        "heading_vs_nearest_fde_improvement_m": _optional_delta(
            nearest.fde_m,
            heading.fde_m,
        ),
        "heading_vs_constant_velocity_fde_improvement_m": _optional_delta(
            constant.fde_m,
            heading.fde_m,
        ),
        "nearest_map_used_count": nearest.map_used_count,
        "nearest_fallback_count": nearest.fallback_count,
        "heading_map_used_count": heading.map_used_count,
        "heading_fallback_count": heading.fallback_count,
        "top_heading_fallback_reason": _top_fallback_reason(tuple(track_rows)),
    }
    return scenario_row, track_rows


def _aggregate_track_rows(rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    return {
        "evaluated_target_count": len(rows),
        "constant_velocity_fde_m": _mean_float(rows, "constant_velocity_fde_m"),
        "nearest_lane_fde_m": _mean_float(rows, "nearest_lane_fde_m"),
        "heading_lane_fde_m": _mean_float(rows, "heading_lane_fde_m"),
        "heading_vs_nearest_fde_improvement_m": _mean_float(
            rows,
            "heading_vs_nearest_fde_improvement_m",
        ),
        "heading_vs_constant_velocity_fde_improvement_m": _mean_float(
            rows,
            "heading_vs_constant_velocity_fde_improvement_m",
        ),
        "constant_velocity_miss_rate": _mean_bool(rows, "constant_velocity_miss"),
        "nearest_lane_miss_rate": _mean_bool(rows, "nearest_lane_miss"),
        "heading_lane_miss_rate": _mean_bool(rows, "heading_lane_miss"),
        "nearest_map_used_count": sum(bool(row["nearest_map_used"]) for row in rows),
        "heading_map_used_count": sum(bool(row["heading_map_used"]) for row in rows),
        "nearest_fallback_count": sum(
            row["nearest_fallback_reason"] is not None for row in rows
        ),
        "heading_fallback_count": sum(
            row["heading_fallback_reason"] is not None for row in rows
        ),
    }


def _rank_heading_improvements(
    rows: list[dict[str, object]],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        _rankable_rows(rows),
        key=lambda row: (
            -float(row["heading_vs_nearest_fde_improvement_m"]),
            -int(row["heading_map_used_count"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_heading_regressions(
    rows: list[dict[str, object]],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        _rankable_rows(rows),
        key=lambda row: (
            float(row["heading_vs_nearest_fde_improvement_m"]),
            -int(row["heading_map_used_count"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rank_heading_fallbacks(
    rows: list[dict[str, object]],
    top: int,
) -> list[dict[str, object]]:
    return sorted(
        (
            row
            for row in _rankable_rows(rows)
            if int(row["heading_fallback_count"]) > 0
        ),
        key=lambda row: (
            -int(row["heading_fallback_count"]),
            -int(row["evaluated_target_count"]),
            float(row["heading_vs_nearest_fde_improvement_m"]),
            str(row["scenario_id"]),
        ),
    )[:top]


def _rankable_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if row["heading_vs_nearest_fde_improvement_m"] is not None
    ]


def _append_ranked_rows(lines: list[str], rows: list[object]) -> None:
    if not rows:
        lines.append("| n/a | n/a | n/a | 0 | n/a | n/a | n/a | 0 | 0 | n/a |")
        return

    for rank, row in enumerate(rows, start=1):
        assert isinstance(row, dict)
        lines.append(
            "| "
            f"{rank} | "
            f"`{row['source_name']}` | "
            f"`{row['scenario_id']}` | "
            f"{row['evaluated_target_count']} | "
            f"{_meter_text(row['nearest_lane_fde_m'])} | "
            f"{_meter_text(row['heading_lane_fde_m'])} | "
            f"{_signed_meter_text(row['heading_vs_nearest_fde_improvement_m'])} | "
            f"{row['heading_map_used_count']} | "
            f"{row['heading_fallback_count']} | "
            f"`{row['top_heading_fallback_reason']}` |"
        )


def _fallback_reason_counts(
    rows: tuple[dict[str, object], ...],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = row.get(key)
        if reason is None:
            continue
        counts[str(reason)] = counts.get(str(reason), 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _top_fallback_reason(rows: tuple[dict[str, object], ...]) -> str:
    reasons = _fallback_reason_counts(rows, key="heading_fallback_reason")
    if not reasons:
        return "none"
    reason, count = next(iter(reasons.items()))
    return f"{reason} ({count})"


def _diagnostic_note(aggregate: dict[str, object]) -> str:
    improvement = aggregate.get("heading_vs_nearest_fde_improvement_m")
    versus_constant = aggregate.get("heading_vs_constant_velocity_fde_improvement_m")
    if improvement is None:
        return "- No evaluable prediction targets were available in this run."
    if float(improvement) < 0:
        return (
            "- Heading-aware mean FDE is higher than nearest-lane mean FDE in "
            "this run, which is useful diagnostic evidence rather than a failed "
            "project outcome."
        )
    if float(improvement) > 0:
        if versus_constant is not None and float(versus_constant) < 0:
            return (
                "- Heading-aware lane selection reduced mean FDE relative to "
                "the nearest-lane selector, but it still trails constant "
                "velocity overall in this run."
            )
        return (
            "- Heading-aware lane selection reduced mean FDE relative to the "
            "nearest-lane selector in this run."
        )
    return "- Heading-aware and nearest-lane mean FDE are tied in this run."


def _mean_float(rows: tuple[dict[str, object], ...], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _mean_bool(rows: tuple[dict[str, object], ...], key: str) -> float | None:
    if not rows:
        return None
    return round(sum(bool(row[key]) for row in rows) / len(rows), 3)


def _optional_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 3)


def _source_name(path: Path) -> str:
    return path.name or str(path)


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
