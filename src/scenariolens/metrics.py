from __future__ import annotations

from itertools import combinations
from math import hypot, inf

from scenariolens.schema import AgentTrack, Scenario, ScenarioScore, State


def distance(a: State, b: State) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def speed(state: State) -> float:
    return hypot(state.vx, state.vy)


def min_pairwise_distance(scenario: Scenario) -> float | None:
    """Return the closest same-timestep distance between any two tracks."""

    best = inf
    for left, right in combinations(scenario.tracks, 2):
        right_by_time = {state.t: state for state in right.states}
        for left_state in left.states:
            right_state = right_by_time.get(left_state.t)
            if right_state is not None:
                best = min(best, distance(left_state, right_state))
    return None if best == inf else best


def closing_time_to_collision(a: State, b: State) -> float | None:
    """Approximate TTC for two point agents under constant velocity.

    This is intentionally simple for the first milestone. It is a screening
    proxy, not a safety-certified collision metric.
    """

    rx = b.x - a.x
    ry = b.y - a.y
    rvx = b.vx - a.vx
    rvy = b.vy - a.vy
    relative_speed_sq = rvx * rvx + rvy * rvy
    if relative_speed_sq == 0:
        return None

    ttc = -((rx * rvx) + (ry * rvy)) / relative_speed_sq
    if ttc <= 0:
        return None
    return ttc


def min_time_to_collision(scenario: Scenario) -> float | None:
    best = inf
    for left, right in combinations(scenario.tracks, 2):
        right_by_time = {state.t: state for state in right.states}
        for left_state in left.states:
            right_state = right_by_time.get(left_state.t)
            if right_state is None:
                continue
            ttc = closing_time_to_collision(left_state, right_state)
            if ttc is not None:
                best = min(best, ttc)
    return None if best == inf else best


def vulnerable_road_user_count(tracks: tuple[AgentTrack, ...]) -> int:
    return sum(track.agent_type in {"pedestrian", "cyclist"} for track in tracks)


def interaction_score(
    min_distance_m: float | None,
    min_ttc_s: float | None,
    vru_count: int,
    agent_count: int,
) -> float:
    """Rank scenarios for review using lightweight interpretable features."""

    score = 0.0
    score += min(agent_count, 12) * 0.25
    score += vru_count * 1.5

    if min_distance_m is not None:
        score += max(0.0, 8.0 - min_distance_m)

    if min_ttc_s is not None:
        score += max(0.0, 6.0 - min_ttc_s) * 1.25

    return round(score, 3)


def score_scenario(scenario: Scenario) -> ScenarioScore:
    min_distance = min_pairwise_distance(scenario)
    min_ttc = min_time_to_collision(scenario)
    vru_count = vulnerable_road_user_count(scenario.tracks)
    score = interaction_score(
        min_distance_m=min_distance,
        min_ttc_s=min_ttc,
        vru_count=vru_count,
        agent_count=len(scenario.tracks),
    )
    return ScenarioScore(
        scenario_id=scenario.scenario_id,
        agent_count=len(scenario.tracks),
        vulnerable_road_user_count=vru_count,
        min_pairwise_distance_m=None if min_distance is None else round(min_distance, 3),
        min_time_to_collision_s=None if min_ttc is None else round(min_ttc, 3),
        interaction_score=score,
        tags=scenario.tags,
    )

