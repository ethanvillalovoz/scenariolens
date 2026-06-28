from __future__ import annotations

import json
from dataclasses import asdict

from scenariolens.metrics import score_scenario
from scenariolens.schema import Scenario, ScenarioScore
from scenariolens.taxonomy import TAG_BY_NAME


def ranked_scores(scenarios: tuple[Scenario, ...]) -> tuple[ScenarioScore, ...]:
    return tuple(
        sorted(
            (score_scenario(scenario) for scenario in scenarios),
            key=lambda item: item.interaction_score,
            reverse=True,
        )
    )


def score_reasons(score: ScenarioScore) -> tuple[str, ...]:
    reasons: list[str] = []

    if score.vulnerable_road_user_count:
        reasons.append(
            f"contains {score.vulnerable_road_user_count} vulnerable road user(s)"
        )

    if score.prediction_target_count:
        reasons.append(f"includes {score.prediction_target_count} Waymo prediction target(s)")

    if score.object_of_interest_count:
        reasons.append(f"includes {score.object_of_interest_count} object(s) of interest")

    if score.min_pairwise_distance_m is not None and score.min_pairwise_distance_m <= 2.5:
        reasons.append(
            f"minimum agent distance is {score.min_pairwise_distance_m:.3f} m"
        )

    if score.min_time_to_collision_s is not None and score.min_time_to_collision_s <= 1.5:
        reasons.append(
            f"screened constant-velocity TTC proxy is {score.min_time_to_collision_s:.3f} s"
        )

    if score.min_vru_distance_m is not None and score.min_vru_distance_m <= 3.0:
        reasons.append(
            f"closest vehicle-to-VRU distance is {score.min_vru_distance_m:.3f} m"
        )

    if score.min_path_distance_m is not None and score.min_path_distance_m <= 2.0:
        reasons.append(f"agent paths come within {score.min_path_distance_m:.3f} m")

    if (
        score.max_deceleration_mps2 is not None
        and score.max_deceleration_mps2 >= 3.0
    ):
        reasons.append(
            f"robust max deceleration is {score.max_deceleration_mps2:.3f} m/s^2"
        )

    if score.baseline_failure_score >= 1.0:
        if score.baseline_fde_m is not None:
            reasons.append(
                "constant-velocity baseline FDE is "
                f"{score.baseline_fde_m:.3f} m across "
                f"{score.prediction_target_evaluated_count} target(s)"
            )
        if score.baseline_miss_rate is not None and score.baseline_miss_rate > 0.0:
            reasons.append(
                f"baseline miss rate is {score.baseline_miss_rate * 100:.1f}%"
            )

    if score.agent_count >= 4:
        reasons.append(
            f"dense scene with {score.agent_count} tracked agents "
            f"({score.scoring_agent_count} scored)"
        )

    high_weight_tags = tuple(
        tag
        for tag in score.tags
        if tag in TAG_BY_NAME and TAG_BY_NAME[tag].weight >= 2.0
    )
    if high_weight_tags:
        labels = ", ".join(TAG_BY_NAME[tag].label for tag in high_weight_tags)
        reasons.append(f"high-value taxonomy tags: {labels}")

    if not reasons:
        reasons.append("included as a low-interaction baseline")

    return tuple(reasons)


def scores_as_dicts(scores: tuple[ScenarioScore, ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, score in enumerate(scores, start=1):
        row = asdict(score)
        row["rank"] = rank
        row["reasons"] = score_reasons(score)
        rows.append(row)
    return rows


def json_report(scenarios: tuple[Scenario, ...], limit: int | None = None) -> str:
    scores = ranked_scores(scenarios)
    if limit is not None:
        scores = scores[:limit]
    payload = {
        "scenario_count": len(scenarios),
        "reported_count": len(scores),
        "scenarios": scores_as_dicts(scores),
    }
    return json.dumps(payload, indent=2)


def markdown_report(scenarios: tuple[Scenario, ...], limit: int | None = None) -> str:
    scores = ranked_scores(scenarios)
    if limit is not None:
        scores = scores[:limit]

    lines = [
        "# ScenarioLens Scenario Report",
        "",
        f"Scenarios analyzed: {len(scenarios)}",
        f"Scenarios reported: {len(scores)}",
        "",
        "| Rank | Scenario | Score | Tags |",
        "| ---: | --- | ---: | --- |",
    ]

    for rank, score in enumerate(scores, start=1):
        tags = ", ".join(score.tags) if score.tags else "none"
        lines.append(
            f"| {rank} | `{score.scenario_id}` | {score.interaction_score:.3f} | {tags} |"
        )

    lines.extend(["", "## Scenario Notes", ""])

    for rank, score in enumerate(scores, start=1):
        lines.extend(
            [
                f"### {rank}. `{score.scenario_id}`",
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
                f"- Baseline max FDE: {_format_optional(score.baseline_max_fde_m, 'm')}",
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

    return "\n".join(lines).rstrip() + "\n"


def _format_optional(value: float | None, unit: str) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f} {unit}"


def _format_percent_optional(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"
