from __future__ import annotations

from itertools import combinations
from math import hypot, inf

from scenariolens.schema import AgentTrack, Scenario, ScenarioScore, State
from scenariolens.taxonomy import infer_tags, tag_weight


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


def min_path_distance(scenario: Scenario) -> float | None:
    """Return closest distance between any two tracks at any sampled states."""

    best = inf
    for left, right in combinations(scenario.tracks, 2):
        for left_state in left.states:
            for right_state in right.states:
                best = min(best, distance(left_state, right_state))
    return None if best == inf else best


def min_vru_distance(scenario: Scenario) -> float | None:
    """Return closest same-timestep vehicle-to-VRU distance."""

    vehicles = tuple(track for track in scenario.tracks if track.agent_type == "vehicle")
    vrus = tuple(
        track for track in scenario.tracks if track.agent_type in {"pedestrian", "cyclist"}
    )
    best = inf
    for vehicle in vehicles:
        for vru in vrus:
            vru_by_time = {state.t: state for state in vru.states}
            for vehicle_state in vehicle.states:
                vru_state = vru_by_time.get(vehicle_state.t)
                if vru_state is not None:
                    best = min(best, distance(vehicle_state, vru_state))
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


def max_track_speed(track: AgentTrack) -> float | None:
    if not track.states:
        return None
    return max(speed(state) for state in track.states)


def max_scenario_speed(scenario: Scenario) -> float | None:
    speeds = tuple(
        track_speed
        for track in scenario.tracks
        if (track_speed := max_track_speed(track)) is not None
    )
    return None if not speeds else max(speeds)


def ego_max_speed(scenario: Scenario) -> float | None:
    if scenario.ego_track_id is None:
        return None
    for track in scenario.tracks:
        if track.agent_id == scenario.ego_track_id:
            return max_track_speed(track)
    return None


def max_deceleration(scenario: Scenario) -> float | None:
    """Return largest positive speed drop per second across sampled tracks."""

    best = 0.0
    found = False
    for track in scenario.tracks:
        states = tuple(sorted(track.states, key=lambda state: state.t))
        for previous, current in zip(states, states[1:]):
            dt = current.t - previous.t
            if dt <= 0:
                continue
            decel = (speed(previous) - speed(current)) / dt
            if decel > best:
                best = decel
            found = True
    return None if not found else best


def interaction_components(
    min_distance_m: float | None,
    min_ttc_s: float | None,
    vru_count: int,
    agent_count: int,
    taxonomy_score: float = 0.0,
    min_vru_distance_m: float | None = None,
    min_path_distance_m: float | None = None,
    max_deceleration_mps2: float | None = None,
) -> dict[str, float]:
    """Break scenario ranking into interpretable score components."""

    components = {
        "density": round(min(agent_count, 12) * 0.25, 3),
        "vru": round(vru_count * 1.5, 3),
        "taxonomy": round(taxonomy_score, 3),
        "proximity": 0.0,
        "ttc": 0.0,
        "vru_proximity": 0.0,
        "path_conflict": 0.0,
        "dynamics": 0.0,
    }

    if min_distance_m is not None:
        components["proximity"] = round(max(0.0, 8.0 - min_distance_m), 3)

    if min_ttc_s is not None:
        components["ttc"] = round(max(0.0, 6.0 - min_ttc_s) * 1.25, 3)

    if min_vru_distance_m is not None:
        components["vru_proximity"] = round(
            max(0.0, 7.0 - min_vru_distance_m) * 0.75,
            3,
        )

    if min_path_distance_m is not None:
        components["path_conflict"] = round(
            max(0.0, 5.0 - min_path_distance_m) * 0.5,
            3,
        )

    if max_deceleration_mps2 is not None:
        components["dynamics"] = round(
            min(max(0.0, max_deceleration_mps2 - 2.5) * 0.8, 6.0),
            3,
        )

    return components


def interaction_score(
    min_distance_m: float | None,
    min_ttc_s: float | None,
    vru_count: int,
    agent_count: int,
    taxonomy_score: float = 0.0,
    min_vru_distance_m: float | None = None,
    min_path_distance_m: float | None = None,
    max_deceleration_mps2: float | None = None,
) -> float:
    """Rank scenarios for review using lightweight interpretable features."""

    components = interaction_components(
        min_distance_m=min_distance_m,
        min_ttc_s=min_ttc_s,
        vru_count=vru_count,
        agent_count=agent_count,
        taxonomy_score=taxonomy_score,
        min_vru_distance_m=min_vru_distance_m,
        min_path_distance_m=min_path_distance_m,
        max_deceleration_mps2=max_deceleration_mps2,
    )
    return round(sum(components.values()), 3)


def score_scenario(scenario: Scenario) -> ScenarioScore:
    min_distance = min_pairwise_distance(scenario)
    min_vru = min_vru_distance(scenario)
    min_path = min_path_distance(scenario)
    min_ttc = min_time_to_collision(scenario)
    max_speed = max_scenario_speed(scenario)
    max_ego_speed = ego_max_speed(scenario)
    max_decel = max_deceleration(scenario)
    vru_count = vulnerable_road_user_count(scenario.tracks)
    tags = infer_tags(scenario)
    taxonomy_score = tag_weight(tags)
    components = interaction_components(
        min_distance_m=min_distance,
        min_ttc_s=min_ttc,
        vru_count=vru_count,
        agent_count=len(scenario.tracks),
        taxonomy_score=taxonomy_score,
        min_vru_distance_m=min_vru,
        min_path_distance_m=min_path,
        max_deceleration_mps2=max_decel,
    )
    score = round(sum(components.values()), 3)
    return ScenarioScore(
        scenario_id=scenario.scenario_id,
        agent_count=len(scenario.tracks),
        vulnerable_road_user_count=vru_count,
        min_pairwise_distance_m=None if min_distance is None else round(min_distance, 3),
        min_vru_distance_m=None if min_vru is None else round(min_vru, 3),
        min_path_distance_m=None if min_path is None else round(min_path, 3),
        min_time_to_collision_s=None if min_ttc is None else round(min_ttc, 3),
        max_speed_mps=None if max_speed is None else round(max_speed, 3),
        ego_max_speed_mps=None if max_ego_speed is None else round(max_ego_speed, 3),
        max_deceleration_mps2=None if max_decel is None else round(max_decel, 3),
        taxonomy_score=taxonomy_score,
        component_scores=components,
        interaction_score=score,
        tags=tags,
    )
