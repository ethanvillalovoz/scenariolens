from __future__ import annotations

from pathlib import Path

from scenariolens.ingest.waymo_motion import load_normalized_motion_csv
from scenariolens.report import ranked_scores, score_reasons
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario, ScenarioScore
from scenariolens.visualize import scenario_svg

DEFAULT_WAYMO_NORMALIZED_PATH = Path("docs/examples/waymo_motion_normalized.csv")


def generate_portfolio_report(
    output_path: str | Path,
    assets_dir: str | Path,
    waymo_normalized_path: str | Path = DEFAULT_WAYMO_NORMALIZED_PATH,
    top_n: int = 3,
) -> None:
    """Generate a checked-in portfolio report and its SVG assets."""

    target = Path(output_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)

    synthetic = synthetic_scenarios()
    waymo_like = load_normalized_motion_csv(waymo_normalized_path)

    synthetic_scores = ranked_scores(synthetic)[:top_n]
    waymo_scores = ranked_scores(waymo_like)[:top_n]

    scenario_lookup = {
        scenario.scenario_id: scenario
        for scenario in (*synthetic, *waymo_like)
    }
    for score in (*synthetic_scores, *waymo_scores):
        scenario = scenario_lookup[score.scenario_id]
        (assets / f"{score.scenario_id}.svg").write_text(
            scenario_svg(scenario),
            encoding="utf-8",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        portfolio_markdown(
            synthetic_count=len(synthetic),
            waymo_like_count=len(waymo_like),
            synthetic_scores=synthetic_scores,
            waymo_scores=waymo_scores,
            asset_prefix=assets.relative_to(target.parent),
        ),
        encoding="utf-8",
    )


def portfolio_markdown(
    synthetic_count: int,
    waymo_like_count: int,
    synthetic_scores: tuple[ScenarioScore, ...],
    waymo_scores: tuple[ScenarioScore, ...],
    asset_prefix: Path,
) -> str:
    lines = [
        "# ScenarioLens Portfolio Report",
        "",
        "## Executive Summary",
        "",
        "ScenarioLens is a laptop-friendly autonomous-driving evaluation project "
        "for discovering and explaining long-tail driving scenarios. It ranks "
        "scenarios using lightweight interaction metrics, ODD-relevant taxonomy "
        "tags, vulnerable-road-user counts, closest-agent distance, and a simple "
        "constant-velocity time-to-collision proxy.",
        "",
        "The current pipeline supports synthetic scenarios, ScenarioLens JSON, "
        "row-wise CSV ingestion, and a normalized Waymo Motion-shaped fixture. "
        "The native Waymo Motion parser is intentionally left as an optional "
        "future adapter so the core project stays dependency-free and easy to run.",
        "",
        "## Current Coverage",
        "",
        f"- Synthetic scenarios analyzed: {synthetic_count}",
        f"- Normalized Waymo-shaped scenarios analyzed: {waymo_like_count}",
        "- Unit tests cover schema I/O, ranking, taxonomy, ingestion, reporting, "
        "CLI flows, and SVG rendering.",
        "",
        "## Top Synthetic Scenarios",
        "",
    ]

    lines.extend(_score_section(synthetic_scores, asset_prefix))
    lines.extend(
        [
            "## Normalized Waymo-Shaped Fixture Results",
            "",
            "These examples use a tiny checked-in CSV shaped like a normalized "
            "Waymo Motion extraction. The data is synthetic, but the field "
            "boundary exercises the adapter path planned for real Motion slices.",
            "",
        ]
    )
    lines.extend(_score_section(waymo_scores, asset_prefix))
    lines.extend(
        [
            "## Limitations",
            "",
            "- Current scenario data is synthetic or normalized-fixture data, not a native Waymo slice.",
            "- Native Waymo Motion TFRecord/protobuf parsing is not implemented yet.",
            "- The TTC value is a simple constant-velocity screening proxy, not a certified safety metric.",
            "- The current renderer is 2D and focuses on agent trajectories, not map lanes or traffic lights.",
            "",
            "## Next Work",
            "",
            "- Add native Waymo Motion mini-slice ingestion behind the existing adapter boundary.",
            "- Add map/lane context once real Motion records are available.",
            "- Add richer interaction metrics such as deceleration, crossing conflict, and trajectory overlap.",
            "- Create curated scenario collections for pedestrian, cyclist, merge, and unprotected-turn cases.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


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
                f"- Vulnerable road users: {score.vulnerable_road_user_count}",
                f"- Min distance: {_format_optional(score.min_pairwise_distance_m, 'm')}",
                f"- Min TTC proxy: {_format_optional(score.min_time_to_collision_s, 's')}",
                "- Why it matters:",
            ]
        )
        for reason in score_reasons(score):
            lines.append(f"  - {reason}")
        lines.append("")

    return lines


def _format_optional(value: float | None, unit: str) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f} {unit}"

