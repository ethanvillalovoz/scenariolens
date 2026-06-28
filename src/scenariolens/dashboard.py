from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    load_normalized_motion_csv,
    load_waymo_motion,
)
from scenariolens.portfolio import (
    DEFAULT_WAYMO_NATIVE_PATH,
    DEFAULT_WAYMO_NORMALIZED_PATH,
)
from scenariolens.prediction import compare_prediction_baselines
from scenariolens.report import ranked_scores, score_reasons
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario, ScenarioScore
from scenariolens.visualize import scenario_svg

DEFAULT_DASHBOARD_OUTPUT = Path("docs/demo/scenarios.json")
DEFAULT_DASHBOARD_ASSETS_DIR = Path("docs/demo/assets")
DASHBOARD_FORMAT = "scenariolens.dashboard.v1"


@dataclass(frozen=True)
class DashboardScenarioSet:
    """Named group of scenarios included in the static dashboard payload."""

    dataset_id: str
    label: str
    scenarios: tuple[Scenario, ...]


def default_dashboard_scenario_sets(
    waymo_normalized_path: str | Path = DEFAULT_WAYMO_NORMALIZED_PATH,
    waymo_native_path: str | Path = DEFAULT_WAYMO_NATIVE_PATH,
) -> tuple[DashboardScenarioSet, ...]:
    return (
        DashboardScenarioSet(
            dataset_id="synthetic",
            label="Synthetic scenarios",
            scenarios=synthetic_scenarios(),
        ),
        DashboardScenarioSet(
            dataset_id="waymo_native_json",
            label="Native Waymo Motion JSON mini-slice",
            scenarios=load_waymo_motion(waymo_native_path),
        ),
        DashboardScenarioSet(
            dataset_id="waymo_normalized_csv",
            label="Normalized Waymo-shaped CSV fixture",
            scenarios=load_normalized_motion_csv(waymo_normalized_path),
        ),
    )


def generate_dashboard_data(
    output_path: str | Path = DEFAULT_DASHBOARD_OUTPUT,
    assets_dir: str | Path = DEFAULT_DASHBOARD_ASSETS_DIR,
    waymo_normalized_path: str | Path = DEFAULT_WAYMO_NORMALIZED_PATH,
    waymo_native_path: str | Path = DEFAULT_WAYMO_NATIVE_PATH,
    limit: int | None = None,
) -> None:
    """Generate static dashboard JSON and SVG assets."""

    target = Path(output_path)
    assets = Path(assets_dir)
    scenario_sets = default_dashboard_scenario_sets(
        waymo_normalized_path=waymo_normalized_path,
        waymo_native_path=waymo_native_path,
    )

    assets.mkdir(parents=True, exist_ok=True)
    payload = dashboard_payload(
        scenario_sets=scenario_sets,
        asset_prefix=Path(os.path.relpath(assets, start=target.parent)),
        limit=limit,
    )

    scenario_lookup = _scenario_lookup(scenario_sets)
    for item in payload["scenarios"]:
        scenario_id = str(item["scenario_id"])
        (assets / f"{scenario_id}.svg").write_text(
            scenario_svg(scenario_lookup[scenario_id]),
            encoding="utf-8",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def dashboard_payload(
    scenario_sets: tuple[DashboardScenarioSet, ...],
    asset_prefix: str | Path,
    limit: int | None = None,
) -> dict[str, object]:
    scenario_lookup = _scenario_lookup(scenario_sets)
    dataset_lookup = {
        scenario.scenario_id: scenario_set
        for scenario_set in scenario_sets
        for scenario in scenario_set.scenarios
    }
    scores = ranked_scores(tuple(scenario_lookup.values()))
    if limit is not None:
        scores = scores[:limit]

    asset_root = Path(asset_prefix)
    scenarios = [
        _dashboard_item(
            rank=rank,
            score=score,
            scenario=scenario_lookup[score.scenario_id],
            scenario_set=dataset_lookup[score.scenario_id],
            asset_root=asset_root,
        )
        for rank, score in enumerate(scores, start=1)
    ]

    return {
        "format": DASHBOARD_FORMAT,
        "scenario_count": len(scenario_lookup),
        "reported_count": len(scenarios),
        "datasets": [
            {
                "dataset_id": scenario_set.dataset_id,
                "label": scenario_set.label,
                "scenario_count": len(scenario_set.scenarios),
            }
            for scenario_set in scenario_sets
        ],
        "filters": {
            "datasets": [scenario_set.dataset_id for scenario_set in scenario_sets],
            "tags": sorted({tag for item in scenarios for tag in item["tags"]}),
            "component_names": sorted(
                {name for item in scenarios for name in item["score"]["components"]}
            ),
        },
        "scenarios": scenarios,
    }


def _dashboard_item(
    rank: int,
    score: ScenarioScore,
    scenario: Scenario,
    scenario_set: DashboardScenarioSet,
    asset_root: Path,
) -> dict[str, object]:
    baseline_comparison = compare_prediction_baselines(scenario)
    return {
        "rank": rank,
        "scenario_id": score.scenario_id,
        "dataset_id": scenario_set.dataset_id,
        "dataset_label": scenario_set.label,
        "source": scenario.source,
        "svg_path": (asset_root / f"{score.scenario_id}.svg").as_posix(),
        "tags": list(score.tags),
        "reasons": list(score_reasons(score)),
        "score": {
            "interaction": round(score.interaction_score, 3),
            "taxonomy": round(score.taxonomy_score, 3),
            "components": {
                name: round(value, 3)
                for name, value in score.component_scores.items()
            },
        },
        "metrics": {
            "agent_count": score.agent_count,
            "scoring_agent_count": score.scoring_agent_count,
            "excluded_track_count": score.excluded_track_count,
            "low_quality_track_count": score.low_quality_track_count,
            "vulnerable_road_user_count": score.vulnerable_road_user_count,
            "scoring_vulnerable_road_user_count": score.scoring_vulnerable_road_user_count,
            "sdc_track_present": score.sdc_track_present,
            "prediction_target_count": score.prediction_target_count,
            "object_of_interest_count": score.object_of_interest_count,
            "min_pairwise_distance_m": _round_optional(score.min_pairwise_distance_m),
            "min_vru_distance_m": _round_optional(score.min_vru_distance_m),
            "min_path_distance_m": _round_optional(score.min_path_distance_m),
            "min_time_to_collision_s": _round_optional(score.min_time_to_collision_s),
            "max_speed_mps": _round_optional(score.max_speed_mps),
            "ego_max_speed_mps": _round_optional(score.ego_max_speed_mps),
            "max_deceleration_mps2": _round_optional(score.max_deceleration_mps2),
            "prediction_target_source": score.prediction_target_source,
            "prediction_target_evaluated_count": score.prediction_target_evaluated_count,
            "baseline_ade_m": _round_optional(score.baseline_ade_m),
            "baseline_fde_m": _round_optional(score.baseline_fde_m),
            "baseline_max_fde_m": _round_optional(score.baseline_max_fde_m),
            "baseline_miss_rate": _round_optional(score.baseline_miss_rate),
            "baseline_failure_score": _round_optional(score.baseline_failure_score),
            "lane_aware_ade_m": _round_optional(
                baseline_comparison.lane_aware_ade_m
            ),
            "lane_aware_fde_m": _round_optional(
                baseline_comparison.lane_aware_fde_m
            ),
            "lane_aware_miss_rate": _round_optional(
                baseline_comparison.lane_aware_miss_rate
            ),
            "baseline_fde_improvement_m": _round_optional(
                baseline_comparison.fde_improvement_m
            ),
            "lane_aware_map_used_count": baseline_comparison.map_used_count,
            "lane_aware_fallback_count": baseline_comparison.fallback_count,
            "lane_aware_fallback_reasons": _fallback_reasons(
                baseline_comparison
            ),
        },
        "tracks": {
            "count": len(scenario.tracks),
            "ego_track_id": scenario.ego_track_id,
            "agent_types": sorted({track.agent_type for track in scenario.tracks}),
        },
    }


def _scenario_lookup(
    scenario_sets: tuple[DashboardScenarioSet, ...],
) -> dict[str, Scenario]:
    scenarios: dict[str, Scenario] = {}
    for scenario_set in scenario_sets:
        for scenario in scenario_set.scenarios:
            if scenario.scenario_id in scenarios:
                raise ValueError(f"Duplicate scenario id: {scenario.scenario_id}")
            scenarios[scenario.scenario_id] = scenario
    return scenarios


def _round_optional(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 3)


def _fallback_reasons(baseline_comparison: object) -> list[str]:
    track_results = getattr(baseline_comparison, "track_results", ())
    counts: dict[str, int] = {}
    for row in track_results:
        reason = getattr(row, "lane_fallback_reason", None)
        if reason is None:
            continue
        counts[reason] = counts.get(reason, 0) + 1
    return [
        f"{reason} ({count})"
        for reason, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
