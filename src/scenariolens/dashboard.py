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
DEFAULT_LANE_SELECTION_MANIFEST = Path(
    "data/processed/waymo_lane_selection_study/manifest.json"
)
DASHBOARD_FORMAT = "scenariolens.dashboard.v1"
CASE_DIAGNOSTICS_FORMAT = "scenariolens.dashboard.case_diagnostics.v1"
CASE_DIAGNOSTICS_REPORT_PATH = (
    "../reports/waymo_heading_aware_lane_selection_study.md"
)
CASE_DIAGNOSTICS_DEBUG_REPORT_PATH = (
    "../reports/waymo_heading_aware_debug_casebook.md"
)

_CASE_GROUPS = (
    (
        "improvements",
        "Largest improvements",
        "Heading-aware lane selection reduced final displacement error versus nearest-lane selection.",
        "top_heading_improvements",
    ),
    (
        "regressions",
        "Largest regressions",
        "Heading-aware lane selection increased final displacement error versus nearest-lane selection.",
        "top_heading_regressions",
    ),
    (
        "fallbacks",
        "Fallback-heavy cases",
        "The lane selector fell back often enough to expose map coverage, distance threshold, or target-type limits.",
        "top_heading_fallbacks",
    ),
)


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
    lane_selection_manifest_path: str | Path | None = DEFAULT_LANE_SELECTION_MANIFEST,
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
        case_diagnostics=load_lane_selection_case_diagnostics(
            lane_selection_manifest_path,
        ),
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
    case_diagnostics: dict[str, object] | None = None,
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

    payload: dict[str, object] = {
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
    if case_diagnostics is not None:
        payload["case_diagnostics"] = case_diagnostics
    return payload


def load_lane_selection_case_diagnostics(
    manifest_path: str | Path | None = DEFAULT_LANE_SELECTION_MANIFEST,
    report_path: str = CASE_DIAGNOSTICS_REPORT_PATH,
    debug_report_path: str = CASE_DIAGNOSTICS_DEBUG_REPORT_PATH,
    limit_per_group: int = 6,
) -> dict[str, object] | None:
    """Load public-safe real-data lane-selection diagnostics for the Explorer."""

    if manifest_path is None:
        return None
    path = Path(manifest_path)
    if not path.exists():
        return None

    manifest = json.loads(path.read_text(encoding="utf-8"))
    aggregate = _public_metrics(manifest.get("aggregate", {}))
    groups = []
    for group_id, label, description, manifest_key in _CASE_GROUPS:
        cases = [
            _public_case(row)
            for row in manifest.get(manifest_key, [])[:limit_per_group]
        ]
        groups.append(
            {
                "group_id": group_id,
                "label": label,
                "description": description,
                "cases": cases,
            }
        )

    return {
        "format": CASE_DIAGNOSTICS_FORMAT,
        "study": "Heading-aware lane selection",
        "report_path": report_path,
        "debug_report_path": debug_report_path,
        "scope_note": manifest.get(
            "scope_note",
            "Heading-aware lane selection is a diagnostic ablation, not a production prediction model.",
        ),
        "source_count": manifest.get("source_count", len(manifest.get("sources", []))),
        "scenario_count": manifest.get("scenario_count", 0),
        "summary": aggregate,
        "fallback_reasons": [
            {"reason": reason, "count": count}
            for reason, count in sorted(
                manifest.get("heading_fallback_reasons", {}).items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "sources": [
            _public_source_summary(source)
            for source in manifest.get("sources", [])
        ],
        "groups": groups,
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


def _public_case(row: dict[str, object]) -> dict[str, object]:
    return {
        "scenario_id": row.get("scenario_id"),
        "source_name": row.get("source_name"),
        "source_index": row.get("source_index"),
        "scenario_index": row.get("scenario_index"),
        "evaluated_target_count": row.get("evaluated_target_count"),
        **_public_metrics(row),
        "nearest_map_used_count": row.get("nearest_map_used_count"),
        "nearest_fallback_count": row.get("nearest_fallback_count"),
        "heading_map_used_count": row.get("heading_map_used_count"),
        "heading_fallback_count": row.get("heading_fallback_count"),
        "top_heading_fallback_reason": row.get(
            "top_heading_fallback_reason",
            "none",
        ),
    }


def _public_source_summary(row: dict[str, object]) -> dict[str, object]:
    return {
        "source_name": row.get("source_name"),
        "ready": row.get("ready"),
        "scenario_count": row.get("scenario_count"),
        "evaluated_target_count": row.get("evaluated_target_count"),
        **_public_metrics(row),
        "heading_map_used_count": row.get("heading_map_used_count"),
        "heading_fallback_count": row.get("heading_fallback_count"),
    }


def _public_metrics(row: dict[str, object]) -> dict[str, object]:
    metric_names = (
        "evaluated_target_count",
        "constant_velocity_fde_m",
        "nearest_lane_fde_m",
        "heading_lane_fde_m",
        "heading_vs_nearest_fde_improvement_m",
        "heading_vs_constant_velocity_fde_improvement_m",
        "constant_velocity_miss_rate",
        "nearest_lane_miss_rate",
        "heading_lane_miss_rate",
        "nearest_map_used_count",
        "heading_map_used_count",
        "nearest_fallback_count",
        "heading_fallback_count",
    )
    return {
        name: _round_json_number(row.get(name))
        for name in metric_names
        if name in row
    }


def _round_json_number(value: object) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 3)
    return value


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
