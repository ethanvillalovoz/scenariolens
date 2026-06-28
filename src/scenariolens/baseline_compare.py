from __future__ import annotations

import json
from dataclasses import asdict

from scenariolens.prediction import (
    PredictionBaselineComparison,
    compare_prediction_baselines,
)
from scenariolens.schema import Scenario

BASELINE_COMPARISON_FORMAT = "scenariolens.baseline_comparison.v1"


def baseline_comparisons(
    scenarios: tuple[Scenario, ...],
    limit: int | None = None,
) -> tuple[PredictionBaselineComparison, ...]:
    """Return baseline comparisons ranked by lane-aware FDE improvement."""

    comparisons = tuple(compare_prediction_baselines(scenario) for scenario in scenarios)
    ranked = tuple(
        sorted(
            comparisons,
            key=lambda item: (
                item.fde_improvement_m is not None,
                item.fde_improvement_m or float("-inf"),
                item.map_used_count,
            ),
            reverse=True,
        )
    )
    if limit is not None:
        return ranked[:limit]
    return ranked


def baseline_comparison_payload(
    scenarios: tuple[Scenario, ...],
    limit: int | None = None,
) -> dict[str, object]:
    comparisons = baseline_comparisons(scenarios, limit=limit)
    return {
        "format": BASELINE_COMPARISON_FORMAT,
        "scenario_count": len(scenarios),
        "reported_count": len(comparisons),
        "aggregate": _aggregate(comparisons),
        "scenarios": [asdict(comparison) for comparison in comparisons],
    }


def json_baseline_comparison_report(
    scenarios: tuple[Scenario, ...],
    limit: int | None = None,
) -> str:
    return json.dumps(baseline_comparison_payload(scenarios, limit=limit), indent=2)


def markdown_baseline_comparison_report(
    scenarios: tuple[Scenario, ...],
    limit: int | None = None,
) -> str:
    comparisons = baseline_comparisons(scenarios, limit=limit)
    aggregate = _aggregate(comparisons)
    lines = [
        "# Lane-Aware Baseline Comparison",
        "",
        "ScenarioLens compares the default constant-velocity baseline against a "
        "lightweight lane-aware baseline that follows parsed Waymo lane polylines "
        "when map context is available.",
        "",
        f"Scenarios analyzed: {len(scenarios)}",
        f"Scenarios reported: {len(comparisons)}",
        "",
        "## Aggregate",
        "",
        f"- Constant-velocity mean FDE: {_format_optional(aggregate['constant_velocity_fde_m'], 'm')}",
        f"- Lane-aware mean FDE: {_format_optional(aggregate['lane_aware_fde_m'], 'm')}",
        f"- Mean FDE improvement: {_format_optional(aggregate['fde_improvement_m'], 'm')}",
        f"- Tracks using lane map: {aggregate['map_used_count']}",
        f"- Tracks falling back to constant velocity: {aggregate['fallback_count']}",
        "",
        "## Ranked Scenarios",
        "",
        "| Rank | Scenario | Targets | CV FDE | Lane FDE | Improvement | Map used | Fallbacks |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for rank, comparison in enumerate(comparisons, start=1):
        lines.append(
            "| "
            f"{rank} | `{comparison.scenario_id}` | "
            f"{comparison.evaluated_track_count} | "
            f"{_format_optional(comparison.constant_velocity_fde_m, 'm')} | "
            f"{_format_optional(comparison.lane_aware_fde_m, 'm')} | "
            f"{_format_optional(comparison.fde_improvement_m, 'm')} | "
            f"{comparison.map_used_count} | "
            f"{comparison.fallback_count} |"
        )

    lines.extend(["", "## Notes", ""])
    lines.extend(
        [
            "- Positive improvement means the lane-aware baseline had lower FDE.",
            "- Pedestrians, missing map context, low-speed targets, and distant lane "
            "matches intentionally fall back to constant velocity.",
            "- This is a comparison baseline for scenario triage, not a certified "
            "prediction model.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _aggregate(
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> dict[str, object]:
    track_rows = tuple(row for comparison in comparisons for row in comparison.track_results)
    return {
        "evaluated_track_count": len(track_rows),
        "constant_velocity_fde_m": _mean(
            tuple(row.constant_velocity_fde_m for row in track_rows)
        ),
        "lane_aware_fde_m": _mean(tuple(row.lane_aware_fde_m for row in track_rows)),
        "fde_improvement_m": _mean(tuple(row.fde_improvement_m for row in track_rows)),
        "map_used_count": sum(row.lane_map_used for row in track_rows),
        "fallback_count": sum(row.lane_fallback_reason is not None for row in track_rows),
    }


def _mean(values: tuple[float, ...]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _format_optional(value: object, unit: str) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f} {unit}"
