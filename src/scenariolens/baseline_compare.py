from __future__ import annotations

import json
from dataclasses import asdict

from scenariolens.prediction import (
    LANE_MATCH_THRESHOLD_M,
    PredictionBaselineComparison,
    PredictionBaselineSummary,
    compare_prediction_baselines,
    constant_velocity_baseline,
    lane_aware_baseline,
)
from scenariolens.schema import Scenario

BASELINE_COMPARISON_FORMAT = "scenariolens.baseline_comparison.v1"
BASELINE_ABLATION_FORMAT = "scenariolens.baseline_ablation.v1"
STRICT_LANE_MATCH_THRESHOLD_M = 0.5


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
        "fallback_reasons": fallback_reason_counts(comparisons),
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
        "## Fallback Reasons",
        "",
    ]

    reasons = fallback_reason_counts(comparisons)
    if reasons:
        for reason, count in reasons.items():
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Ranked Scenarios",
            "",
            "| Rank | Scenario | Targets | CV FDE | Lane FDE | Improvement | Map used | Fallbacks | Top fallback reason |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )

    for rank, comparison in enumerate(comparisons, start=1):
        lines.append(
            "| "
            f"{rank} | `{comparison.scenario_id}` | "
            f"{comparison.evaluated_track_count} | "
            f"{_format_optional(comparison.constant_velocity_fde_m, 'm')} | "
            f"{_format_optional(comparison.lane_aware_fde_m, 'm')} | "
            f"{_format_optional(comparison.fde_improvement_m, 'm')} | "
            f"{comparison.map_used_count} | "
            f"{comparison.fallback_count} | "
            f"{_top_fallback_reason(comparison)} |"
        )

    lines.extend(["", "## Track-Level Fallbacks", ""])
    fallback_rows = _track_fallback_rows(comparisons)
    if fallback_rows:
        lines.extend(
            [
                "| Scenario | Track | Agent type | Reason |",
                "| --- | --- | --- | --- |",
            ]
        )
        for scenario_id, track_id, agent_type, reason in fallback_rows:
            lines.append(
                f"| `{scenario_id}` | `{track_id}` | `{agent_type}` | `{reason}` |"
            )
    else:
        lines.append("No lane-aware fallback paths were used in the reported rows.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Positive improvement means the lane-aware baseline had lower FDE.",
            "- Pedestrians, missing map context, low-speed targets, and distant lane "
            "matches intentionally fall back to constant velocity.",
            "- This is a comparison baseline for scenario triage, not a certified "
            "prediction model.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def fallback_reason_counts(
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for comparison in comparisons:
        for row in comparison.track_results:
            if row.lane_fallback_reason is None:
                continue
            counts[row.lane_fallback_reason] = (
                counts.get(row.lane_fallback_reason, 0) + 1
            )
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def baseline_ablation_payload(
    scenarios: tuple[Scenario, ...],
    strict_lane_match_threshold_m: float = STRICT_LANE_MATCH_THRESHOLD_M,
) -> dict[str, object]:
    constant_summaries = tuple(constant_velocity_baseline(scenario) for scenario in scenarios)
    lane_default_summaries = tuple(lane_aware_baseline(scenario) for scenario in scenarios)
    lane_strict_summaries = tuple(
        lane_aware_baseline(
            scenario,
            lane_match_threshold_m=strict_lane_match_threshold_m,
        )
        for scenario in scenarios
    )
    constant = _summary_aggregate(
        "constant_velocity",
        lane_match_threshold_m=None,
        summaries=constant_summaries,
        constant_velocity_fde_m=None,
    )
    default = _summary_aggregate(
        "lane_aware_default",
        lane_match_threshold_m=LANE_MATCH_THRESHOLD_M,
        summaries=lane_default_summaries,
        constant_velocity_fde_m=constant["fde_m"],
    )
    strict = _summary_aggregate(
        "lane_aware_strict",
        lane_match_threshold_m=strict_lane_match_threshold_m,
        summaries=lane_strict_summaries,
        constant_velocity_fde_m=constant["fde_m"],
    )
    scenario_rows = baseline_comparisons(scenarios)
    return {
        "format": BASELINE_ABLATION_FORMAT,
        "scenario_count": len(scenarios),
        "variants": [constant, default, strict],
        "fallback_reasons": fallback_reason_counts(scenario_rows),
        "top_scenarios": [asdict(comparison) for comparison in scenario_rows[:8]],
    }


def json_baseline_ablation_report(
    scenarios: tuple[Scenario, ...],
    strict_lane_match_threshold_m: float = STRICT_LANE_MATCH_THRESHOLD_M,
) -> str:
    return json.dumps(
        baseline_ablation_payload(
            scenarios,
            strict_lane_match_threshold_m=strict_lane_match_threshold_m,
        ),
        indent=2,
    )


def markdown_baseline_ablation_report(
    scenarios: tuple[Scenario, ...],
    strict_lane_match_threshold_m: float = STRICT_LANE_MATCH_THRESHOLD_M,
) -> str:
    payload = baseline_ablation_payload(
        scenarios,
        strict_lane_match_threshold_m=strict_lane_match_threshold_m,
    )
    variants = payload["variants"]
    assert isinstance(variants, list)
    fallback_reasons = payload["fallback_reasons"]
    assert isinstance(fallback_reasons, dict)
    top_scenarios = payload["top_scenarios"]
    assert isinstance(top_scenarios, list)
    lines = [
        "# Baseline Ablation Study",
        "",
        "This no-auth study compares the default constant-velocity predictor with "
        "two lane-aware variants over the checked-in ScenarioLens fixture corpus. "
        "It is meant to show baseline behavior and fallback discipline without "
        "requiring gated Waymo downloads.",
        "",
        f"Scenarios analyzed: {payload['scenario_count']}",
        "",
        "## Variant Summary",
        "",
        "| Variant | Lane threshold | Tracks | ADE | FDE | Miss rate | FDE improvement vs CV | Map used | Fallbacks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in variants:
        assert isinstance(row, dict)
        lines.append(
            "| "
            f"{row['variant']} | "
            f"{_format_threshold(row['lane_match_threshold_m'])} | "
            f"{row['evaluated_track_count']} | "
            f"{_format_optional(row['ade_m'], 'm')} | "
            f"{_format_optional(row['fde_m'], 'm')} | "
            f"{_format_percent(row['miss_rate'])} | "
            f"{_format_optional(row['fde_improvement_vs_constant_velocity_m'], 'm')} | "
            f"{row['map_used_count']} | "
            f"{row['fallback_count']} |"
        )

    lines.extend(["", "## Fallback Reasons", ""])
    if fallback_reasons:
        for reason, count in fallback_reasons.items():
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Highest Default Lane-Aware Improvements",
            "",
            "| Rank | Scenario | CV FDE | Lane FDE | Improvement | Map used | Fallbacks |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for rank, comparison in enumerate(top_scenarios, start=1):
        assert isinstance(comparison, dict)
        lines.append(
            "| "
            f"{rank} | `{comparison['scenario_id']}` | "
            f"{_format_optional(comparison['constant_velocity_fde_m'], 'm')} | "
            f"{_format_optional(comparison['lane_aware_fde_m'], 'm')} | "
            f"{_format_optional(comparison['fde_improvement_m'], 'm')} | "
            f"{comparison['map_used_count']} | "
            f"{comparison['fallback_count']} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Constant velocity remains the default scoring baseline for backward compatibility.",
            "- Lane-aware variants only use map context for supported vehicle/cyclist tracks.",
            "- Strict matching is useful as a sensitivity check; it should not be treated as a tuned production threshold.",
            "- This fixture-level study complements, but does not replace, future cross-shard Waymo Motion analysis.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _summary_aggregate(
    variant: str,
    lane_match_threshold_m: float | None,
    summaries: tuple[PredictionBaselineSummary, ...],
    constant_velocity_fde_m: object,
) -> dict[str, object]:
    track_results = tuple(
        result for summary in summaries for result in summary.track_results
    )
    ade = _mean(tuple(result.ade_m for result in track_results))
    fde = _mean(tuple(result.fde_m for result in track_results))
    miss_rate = _mean(tuple(1.0 if result.miss else 0.0 for result in track_results))
    return {
        "variant": variant,
        "lane_match_threshold_m": lane_match_threshold_m,
        "evaluated_track_count": len(track_results),
        "ade_m": ade,
        "fde_m": fde,
        "miss_rate": miss_rate,
        "fde_improvement_vs_constant_velocity_m": _improvement(
            constant_velocity_fde_m,
            fde,
        ),
        "map_used_count": sum(summary.map_used_count for summary in summaries),
        "fallback_count": sum(summary.fallback_count for summary in summaries),
    }


def _improvement(baseline: object, candidate: object) -> float | None:
    if baseline is None or candidate is None:
        return None
    return round(float(baseline) - float(candidate), 3)


def _top_fallback_reason(comparison: PredictionBaselineComparison) -> str:
    reasons = fallback_reason_counts((comparison,))
    if not reasons:
        return "none"
    reason, count = next(iter(reasons.items()))
    return f"`{reason}` ({count})"


def _track_fallback_rows(
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for comparison in comparisons:
        for row in comparison.track_results:
            if row.lane_fallback_reason is None:
                continue
            rows.append(
                (
                    comparison.scenario_id,
                    row.track_id,
                    row.agent_type,
                    row.lane_fallback_reason,
                )
            )
    return rows


def _format_threshold(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.2f} m"


def _format_percent(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


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
