from __future__ import annotations

from pathlib import Path

from scenariolens.baseline_compare import baseline_comparisons
from scenariolens.ingest.waymo_motion import (
    load_normalized_motion_csv,
    load_waymo_motion,
)
from scenariolens.prediction import PredictionBaselineComparison
from scenariolens.report import ranked_scores, score_reasons
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario, ScenarioScore
from scenariolens.visualize import scenario_svg

DEFAULT_WAYMO_NORMALIZED_PATH = Path("docs/examples/waymo_motion_normalized.csv")
DEFAULT_WAYMO_NATIVE_PATH = Path("docs/examples/waymo_motion_native_sample.json")


def generate_portfolio_report(
    output_path: str | Path,
    assets_dir: str | Path,
    waymo_normalized_path: str | Path = DEFAULT_WAYMO_NORMALIZED_PATH,
    waymo_native_path: str | Path = DEFAULT_WAYMO_NATIVE_PATH,
    top_n: int = 3,
) -> None:
    """Generate a checked-in portfolio report and its SVG assets."""

    target = Path(output_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)

    synthetic = synthetic_scenarios()
    waymo_native = load_waymo_motion(waymo_native_path)
    waymo_like = load_normalized_motion_csv(waymo_normalized_path)

    synthetic_scores = ranked_scores(synthetic)[:top_n]
    waymo_native_scores = ranked_scores(waymo_native)[:top_n]
    waymo_scores = ranked_scores(waymo_like)[:top_n]

    scenario_lookup = {
        scenario.scenario_id: scenario
        for scenario in (*synthetic, *waymo_native, *waymo_like)
    }
    for score in (*synthetic_scores, *waymo_native_scores, *waymo_scores):
        scenario = scenario_lookup[score.scenario_id]
        (assets / f"{score.scenario_id}.svg").write_text(
            scenario_svg(scenario),
            encoding="utf-8",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        portfolio_markdown(
            synthetic_count=len(synthetic),
            waymo_native_count=len(waymo_native),
            waymo_like_count=len(waymo_like),
            synthetic_scores=synthetic_scores,
            waymo_native_scores=waymo_native_scores,
            waymo_scores=waymo_scores,
            lane_comparisons=baseline_comparisons(synthetic, limit=3),
            asset_prefix=assets.relative_to(target.parent),
        ),
        encoding="utf-8",
    )


def portfolio_markdown(
    synthetic_count: int,
    waymo_native_count: int,
    waymo_like_count: int,
    synthetic_scores: tuple[ScenarioScore, ...],
    waymo_native_scores: tuple[ScenarioScore, ...],
    waymo_scores: tuple[ScenarioScore, ...],
    asset_prefix: Path,
    lane_comparisons: tuple[PredictionBaselineComparison, ...] = (),
) -> str:
    lines = [
        "# ScenarioLens Portfolio Report",
        "",
        "## Executive Summary",
        "",
        "ScenarioLens is a laptop-friendly autonomous-driving evaluation project "
        "for discovering and explaining long-tail driving scenarios. It ranks "
        "scenarios using lightweight interaction metrics, ODD-relevant taxonomy "
        "tags, vulnerable-road-user counts, same-timestep proximity, path-conflict "
        "proximity, dynamics, a screened constant-velocity time-to-collision proxy, "
        "a constant-velocity prediction baseline with ADE/FDE-style errors, and "
        "a lane-aware comparison baseline for map-backed vehicle/cyclist targets.",
        "",
        "The current pipeline supports synthetic scenarios, ScenarioLens JSON, "
        "row-wise CSV ingestion, normalized Waymo Motion-shaped fixtures, and "
        "native Waymo Motion JSON, binary Scenario proto, and small TFRecord "
        "slice ingestion. Local slice preflight keeps raw downloaded data "
        "separate from the checked-in demo.",
        "",
        "## Current Coverage",
        "",
        f"- Synthetic scenarios analyzed: {synthetic_count}",
        f"- Native Waymo-shaped JSON scenarios analyzed: {waymo_native_count}",
        f"- Normalized Waymo-shaped scenarios analyzed: {waymo_like_count}",
        "- Unit tests cover schema I/O, ranking, taxonomy, ingestion, reporting, "
        "CLI flows, and SVG rendering.",
        "- Real lane-aware baseline diagnostic is checked in under "
        "`docs/reports/waymo_lane_aware_baseline_cross_shard.md`.",
        "- Baseline-debug casebook is checked in under "
        "`docs/reports/waymo_lane_aware_debug_casebook.md`.",
        "- Replay candidate plan is checked in under "
        "`docs/reports/waymo_replay_candidate_plan.md`.",
        "- Open-loop replay prototype is checked in under "
        "`docs/reports/waymo_open_loop_replay_prototype.md`.",
        "- Map-match threshold audit is checked in under "
        "`docs/reports/waymo_map_match_audit.md`.",
        "- Heading-aware lane-selection study is checked in under "
        "`docs/reports/waymo_heading_aware_lane_selection_study.md`.",
        "- Heading-aware debug casebook is checked in under "
        "`docs/reports/waymo_heading_aware_debug_casebook.md`.",
        "- Heading-aware replay candidate plan is checked in under "
        "`docs/reports/waymo_heading_aware_replay_candidate_plan.md`.",
        "- Baseline comparison report is generated under "
        "`docs/reports/lane_aware_baseline_study.md`.",
        "- Baseline ablation report is generated under "
        "`docs/reports/baseline_ablation_study.md`.",
        "- Static dashboard data contract is generated under `docs/demo/`.",
        "",
        "## Stack Alignment",
        "",
        "ScenarioLens uses a laptop-friendly subset of the public Waymo/autonomy "
        "ecosystem: Python for data and evaluation tooling, Waymo Motion "
        "`Scenario`-shaped records as the dataset boundary, a lightweight built-in "
        "reader for the Motion fields this project needs, and JAX/Waymax as the "
        "future simulation path.",
        "",
        "## Top Synthetic Scenarios",
        "",
    ]

    lines.extend(_score_section(synthetic_scores, asset_prefix))
    lines.extend(_lane_comparison_section(lane_comparisons))
    lines.extend(
        [
            "## Native Waymo Motion JSON Mini-Slice",
            "",
            "This section uses a tiny checked-in JSON record shaped like the "
            "public Waymo Motion `Scenario` proto. It exercises native field "
            "mapping for timestamps, object types, valid states, velocities, "
            "and the SDC ego-track index without requiring a dataset download.",
            "",
        ]
    )
    lines.extend(_score_section(waymo_native_scores, asset_prefix))
    lines.extend(
        [
            "## Normalized Waymo-Shaped Fixture Results",
            "",
            "These examples use a tiny checked-in CSV shaped like a normalized "
            "Waymo Motion extraction. The data is synthetic, but the field "
            "boundary exercises row-wise extraction for real Motion slices.",
            "",
        ]
    )
    lines.extend(_score_section(waymo_scores, asset_prefix))
    lines.extend(
        [
            "## Limitations",
            "",
            "- Checked-in Waymo examples are synthetic mini fixtures, not downloaded real validation shards.",
            "- The lightweight binary reader extracts the Motion fields ScenarioLens needs, not the full Waymo proto surface.",
            "- The TTC value is a screened constant-velocity proxy, not a certified safety metric.",
            "- The prediction baselines are intentionally simple; they are failure-mining screens, not benchmark claims.",
            "- The map-match audit is a threshold-sensitivity diagnostic, not a production map matcher.",
            "- The heading-aware lane selector is an ablation, not a replacement for the default scorer.",
            "- The heading-aware replay candidate plan is a queue for the next experiment, not completed simulation.",
            "- The current renderer is 2D and focuses on agent trajectories, map context, and baseline overlays, not traffic-light logic.",
            "",
            "## Next Work",
            "",
            "- Expand the documented local-slice recipe across more Waymo Motion validation shards.",
            "- Compare baseline ADE/FDE distributions across more validation shards.",
            "- Prototype nearest-lane vs heading-aware replay for the strongest candidate cases.",
            "- Graduate stable open-loop replay candidates into an optional Waymax/JAX path.",
            "- Add traffic-light and richer lane-context features from native Motion records.",
            "- Create curated scenario collections for pedestrian, cyclist, merge, and unprotected-turn cases.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _lane_comparison_section(
    comparisons: tuple[PredictionBaselineComparison, ...],
) -> list[str]:
    lines = [
        "## Lane-Aware Baseline Comparison",
        "",
        "This section compares the default constant-velocity predictor with a "
        "lightweight lane-aware predictor. Positive improvement means the "
        "lane-aware baseline lowered FDE while preserving constant-velocity "
        "fallback behavior for unsupported cases.",
        "",
        "| Rank | Scenario | CV FDE | Lane FDE | Improvement | Map used | Fallbacks |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not comparisons:
        lines.extend(["| n/a | n/a | n/a | n/a | n/a | n/a | n/a |", ""])
        return lines

    for rank, comparison in enumerate(comparisons, start=1):
        lines.append(
            "| "
            f"{rank} | `{comparison.scenario_id}` | "
            f"{_format_optional(comparison.constant_velocity_fde_m, 'm')} | "
            f"{_format_optional(comparison.lane_aware_fde_m, 'm')} | "
            f"{_format_optional(comparison.fde_improvement_m, 'm')} | "
            f"{comparison.map_used_count} | "
            f"{comparison.fallback_count} |"
        )
    lines.extend(
        [
            "",
            "Full report: `docs/reports/lane_aware_baseline_study.md`.",
            "Real-data diagnostic: "
            "`docs/reports/waymo_lane_aware_baseline_cross_shard.md`.",
            "Debug casebook: `docs/reports/waymo_lane_aware_debug_casebook.md`.",
            "Replay candidate plan: `docs/reports/waymo_replay_candidate_plan.md`.",
            "Open-loop replay prototype: "
            "`docs/reports/waymo_open_loop_replay_prototype.md`.",
            "Map-match threshold audit: "
            "`docs/reports/waymo_map_match_audit.md`.",
            "Heading-aware lane-selection study: "
            "`docs/reports/waymo_heading_aware_lane_selection_study.md`.",
            "Heading-aware debug casebook: "
            "`docs/reports/waymo_heading_aware_debug_casebook.md`.",
            "Heading-aware replay candidate plan: "
            "`docs/reports/waymo_heading_aware_replay_candidate_plan.md`.",
            "",
        ]
    )
    return lines


def _score_section(scores: tuple[ScenarioScore, ...], asset_prefix: Path) -> list[str]:
    lines: list[str] = [
        "| Rank | Scenario | Score | Tags |",
        "| ---: | --- | ---: | --- |",
    ]
    for rank, score in enumerate(scores, start=1):
        tags = ", ".join(score.tags)
        lines.append(
            f"| {rank} | `{score.scenario_id}` | {score.interaction_score:.3f} | {tags} |"
        )
    lines.append("")

    for rank, score in enumerate(scores, start=1):
        image_path = asset_prefix / f"{score.scenario_id}.svg"
        lines.extend(
            [
                f"### {rank}. `{score.scenario_id}`",
                "",
                f"![{score.scenario_id}]({image_path.as_posix()})",
                "",
                f"- Score: {score.interaction_score:.3f}",
                f"- Agents: {score.agent_count}",
                f"- Scored agents: {score.scoring_agent_count}",
                f"- Excluded tracks: {score.excluded_track_count}",
                f"- Low-quality tracks: {score.low_quality_track_count}",
                f"- Vulnerable road users: {score.vulnerable_road_user_count}",
                f"- Scored vulnerable road users: {score.scoring_vulnerable_road_user_count}",
                f"- SDC track present: {score.sdc_track_present}",
                f"- Prediction targets: {score.prediction_target_count}",
                f"- Objects of interest: {score.object_of_interest_count}",
                f"- Min distance: {_format_optional(score.min_pairwise_distance_m, 'm')}",
                f"- Min VRU distance: {_format_optional(score.min_vru_distance_m, 'm')}",
                f"- Min path distance: {_format_optional(score.min_path_distance_m, 'm')}",
                f"- Screened TTC proxy: {_format_optional(score.min_time_to_collision_s, 's')}",
                f"- Max speed: {_format_optional(score.max_speed_mps, 'm/s')}",
                f"- Ego max speed: {_format_optional(score.ego_max_speed_mps, 'm/s')}",
                f"- Robust max deceleration: {_format_optional(score.max_deceleration_mps2, 'm/s^2')}",
                f"- Prediction target source: {score.prediction_target_source}",
                f"- Baseline targets evaluated: {score.prediction_target_evaluated_count}",
                f"- Baseline ADE: {_format_optional(score.baseline_ade_m, 'm')}",
                f"- Baseline FDE: {_format_optional(score.baseline_fde_m, 'm')}",
                f"- Baseline miss rate: {_format_percent_optional(score.baseline_miss_rate)}",
                f"- Baseline failure score: {score.baseline_failure_score:.3f}",
                "- Component scores:",
            ]
        )
        for name, value in score.component_scores.items():
            lines.append(f"  - {name}: {value:.3f}")
        lines.append("- Why it matters:")
        for reason in score_reasons(score):
            lines.append(f"  - {reason}")
        lines.append("")

    return lines


def _format_optional(value: float | None, unit: str) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f} {unit}"


def _format_percent_optional(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"
