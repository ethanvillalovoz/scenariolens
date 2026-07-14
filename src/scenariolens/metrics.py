from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from itertools import combinations
from math import hypot, inf, isfinite

from scenariolens.prediction import constant_velocity_baseline
from scenariolens.schema import AgentTrack, Scenario, ScenarioScore, State
from scenariolens.taxonomy import infer_tags, tag_weight

MIN_TRACK_STATES = 2
MAX_REASONABLE_VELOCITY_MPS = 65.0
MAX_REASONABLE_STEP_SPEED_MPS = 85.0
SCORING_CONTEXT_RADIUS_M = 80.0
MIN_TTC_HORIZON_S = 0.2
MAX_TTC_HORIZON_S = 8.0
TTC_CONFLICT_DISTANCE_M = 2.5
ROBUST_DECEL_PERCENTILE = 0.95
MAX_REASONABLE_DECEL_MPS2 = 12.0


@dataclass(frozen=True)
class ScoringContext:
    """Subset of a scenario used for calibrated interaction scoring."""

    tracks: tuple[AgentTrack, ...]
    excluded_track_count: int
    low_quality_track_count: int
    sdc_track_present: bool
    prediction_target_count: int
    object_of_interest_count: int


_Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class _TrackSpatialIndex:
    agent_id: str
    points_by_x: tuple[_Point, ...]
    x_coordinates: tuple[float, ...]
    min_x: float
    max_x: float
    min_y: float
    max_y: float


def distance(a: State, b: State) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def speed(state: State) -> float:
    return hypot(state.vx, state.vy)


def min_pairwise_distance(scenario: Scenario) -> float | None:
    """Return the closest same-timestep distance between any two tracks."""

    return _min_pairwise_distance(scenario.tracks)


def _min_pairwise_distance(tracks: tuple[AgentTrack, ...]) -> float | None:
    best = inf
    for left, right in combinations(tracks, 2):
        right_by_time = {state.t: state for state in right.states}
        for left_state in left.states:
            right_state = right_by_time.get(left_state.t)
            if right_state is not None:
                best = min(best, distance(left_state, right_state))
    return None if best == inf else best


def min_path_distance(scenario: Scenario) -> float | None:
    """Return closest distance between any two tracks at any sampled states."""

    return _min_path_distance(scenario.tracks)


def _min_path_distance(tracks: tuple[AgentTrack, ...]) -> float | None:
    indexes = tuple(_track_spatial_index(track) for track in tracks)
    best = inf
    for left, right in combinations(indexes, 2):
        best = min(best, _spatial_index_distance(left, right, upper_bound=best))
        if best == 0.0:
            break
    return None if best == inf else best


def min_vru_distance(scenario: Scenario) -> float | None:
    """Return closest same-timestep vehicle-to-VRU distance."""

    return _min_vru_distance(scenario.tracks)


def _min_vru_distance(tracks: tuple[AgentTrack, ...]) -> float | None:
    vehicles = tuple(track for track in tracks if track.agent_type == "vehicle")
    vrus = tuple(
        track for track in tracks if track.agent_type in {"pedestrian", "cyclist"}
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
    if relative_speed_sq < 0.25:
        return None

    ttc = -((rx * rvx) + (ry * rvy)) / relative_speed_sq
    if ttc < MIN_TTC_HORIZON_S or ttc > MAX_TTC_HORIZON_S:
        return None

    closest_distance = hypot(rx + rvx * ttc, ry + rvy * ttc)
    if closest_distance > TTC_CONFLICT_DISTANCE_M:
        return None
    return ttc


def min_time_to_collision(scenario: Scenario) -> float | None:
    return _min_time_to_collision(scenario.tracks)


def _min_time_to_collision(tracks: tuple[AgentTrack, ...]) -> float | None:
    best = inf
    for left, right in combinations(tracks, 2):
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
    """Return robust positive speed drop per second across sampled tracks."""

    return _max_deceleration(scenario.tracks)


def _max_deceleration(tracks: tuple[AgentTrack, ...]) -> float | None:
    decelerations: list[float] = []
    for track in tracks:
        states = tuple(sorted(track.states, key=lambda state: state.t))
        for previous, current in zip(states, states[1:]):
            dt = current.t - previous.t
            if dt <= 0:
                continue
            decel = (speed(previous) - speed(current)) / dt
            if 0.0 < decel <= MAX_REASONABLE_DECEL_MPS2:
                decelerations.append(decel)
    if not decelerations:
        return None
    return _percentile(tuple(sorted(decelerations)), ROBUST_DECEL_PERCENTILE)


def scoring_context(scenario: Scenario) -> ScoringContext:
    """Return a quality-filtered, ego-centered scenario view for scoring."""

    quality_tracks = tuple(track for track in scenario.tracks if _track_is_quality(track))
    low_quality_count = len(scenario.tracks) - len(quality_tracks)
    quality_by_id = {track.agent_id: track for track in quality_tracks}
    spatial_by_id = {
        track.agent_id: _track_spatial_index(track) for track in quality_tracks
    }
    sdc_track_present = (
        scenario.ego_track_id is not None and scenario.ego_track_id in quality_by_id
    )

    prediction_target_ids = _metadata_track_ids(
        scenario,
        "waymo_tracks_to_predict_track_ids",
    )
    object_interest_ids = _metadata_track_ids(
        scenario,
        "waymo_objects_of_interest_track_ids",
    )
    anchor_ids = tuple(
        track_id
        for track_id in (
            *((scenario.ego_track_id,) if scenario.ego_track_id else ()),
            *prediction_target_ids,
            *object_interest_ids,
        )
        if track_id in quality_by_id
    )

    if anchor_ids:
        anchors = tuple(quality_by_id[track_id] for track_id in dict.fromkeys(anchor_ids))
        anchor_indexes = tuple(spatial_by_id[track.agent_id] for track in anchors)
        selected = tuple(
            track
            for track in quality_tracks
            if track.agent_id in anchor_ids
            or any(
                _spatial_indexes_within_distance(
                    spatial_by_id[track.agent_id],
                    anchor,
                    threshold=SCORING_CONTEXT_RADIUS_M,
                )
                for anchor in anchor_indexes
            )
        )
    else:
        selected = quality_tracks

    if len(selected) < 2 and len(quality_tracks) >= 2:
        selected = quality_tracks

    return ScoringContext(
        tracks=selected,
        excluded_track_count=len(scenario.tracks) - len(selected),
        low_quality_track_count=low_quality_count,
        sdc_track_present=sdc_track_present,
        prediction_target_count=len(prediction_target_ids),
        object_of_interest_count=len(object_interest_ids),
    )


def interaction_components(
    min_distance_m: float | None,
    min_ttc_s: float | None,
    vru_count: int,
    agent_count: int,
    taxonomy_score: float = 0.0,
    min_vru_distance_m: float | None = None,
    min_path_distance_m: float | None = None,
    max_deceleration_mps2: float | None = None,
    baseline_failure_score: float | None = None,
) -> dict[str, float]:
    """Break scenario ranking into interpretable score components."""

    components = {
        "density": round(min(agent_count, 12) * 0.25, 3),
        "vru": round(min(vru_count, 6) * 1.5, 3),
        "taxonomy": round(taxonomy_score, 3),
        "proximity": 0.0,
        "ttc": 0.0,
        "vru_proximity": 0.0,
        "path_conflict": 0.0,
        "dynamics": 0.0,
        "baseline_failure": 0.0,
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

    if baseline_failure_score is not None:
        components["baseline_failure"] = round(
            min(max(0.0, baseline_failure_score), 12.0),
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
    baseline_failure_score: float | None = None,
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
        baseline_failure_score=baseline_failure_score,
    )
    return round(sum(components.values()), 3)


def score_scenario(scenario: Scenario) -> ScenarioScore:
    context = scoring_context(scenario)
    min_distance = _min_pairwise_distance(context.tracks)
    min_vru = _min_vru_distance(context.tracks)
    min_path = _min_path_distance(context.tracks)
    min_ttc = _min_time_to_collision(context.tracks)
    max_speed = _max_scenario_speed(context.tracks)
    max_ego_speed = ego_max_speed(scenario)
    max_decel = _max_deceleration(context.tracks)
    vru_count = vulnerable_road_user_count(scenario.tracks)
    scoring_vru_count = vulnerable_road_user_count(context.tracks)
    tags = infer_tags(scenario)
    taxonomy_score = tag_weight(tags)
    baseline = constant_velocity_baseline(scenario)
    components = interaction_components(
        min_distance_m=min_distance,
        min_ttc_s=min_ttc,
        vru_count=scoring_vru_count,
        agent_count=len(context.tracks),
        taxonomy_score=taxonomy_score,
        min_vru_distance_m=min_vru,
        min_path_distance_m=min_path,
        max_deceleration_mps2=max_decel,
        baseline_failure_score=baseline.failure_score,
    )
    score = round(sum(components.values()), 3)
    return ScenarioScore(
        scenario_id=scenario.scenario_id,
        agent_count=len(scenario.tracks),
        scoring_agent_count=len(context.tracks),
        excluded_track_count=context.excluded_track_count,
        low_quality_track_count=context.low_quality_track_count,
        vulnerable_road_user_count=vru_count,
        scoring_vulnerable_road_user_count=scoring_vru_count,
        sdc_track_present=context.sdc_track_present,
        prediction_target_count=context.prediction_target_count,
        object_of_interest_count=context.object_of_interest_count,
        min_pairwise_distance_m=None if min_distance is None else round(min_distance, 3),
        min_vru_distance_m=None if min_vru is None else round(min_vru, 3),
        min_path_distance_m=None if min_path is None else round(min_path, 3),
        min_time_to_collision_s=None if min_ttc is None else round(min_ttc, 3),
        max_speed_mps=None if max_speed is None else round(max_speed, 3),
        ego_max_speed_mps=None if max_ego_speed is None else round(max_ego_speed, 3),
        max_deceleration_mps2=None if max_decel is None else round(max_decel, 3),
        prediction_target_source=baseline.target_source,
        prediction_target_evaluated_count=baseline.evaluated_track_count,
        baseline_ade_m=baseline.ade_m,
        baseline_fde_m=baseline.fde_m,
        baseline_max_fde_m=baseline.max_fde_m,
        baseline_miss_rate=baseline.miss_rate,
        baseline_failure_score=baseline.failure_score,
        taxonomy_score=taxonomy_score,
        component_scores=components,
        interaction_score=score,
        tags=tags,
    )


def _max_scenario_speed(tracks: tuple[AgentTrack, ...]) -> float | None:
    speeds = tuple(
        track_speed
        for track in tracks
        if (track_speed := max_track_speed(track)) is not None
    )
    return None if not speeds else max(speeds)


def _track_is_quality(track: AgentTrack) -> bool:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < MIN_TRACK_STATES:
        return False
    for state in states:
        if not all(isfinite(value) for value in (state.t, state.x, state.y, state.vx, state.vy)):
            return False
        if speed(state) > MAX_REASONABLE_VELOCITY_MPS:
            return False
    for previous, current in zip(states, states[1:]):
        dt = current.t - previous.t
        if dt <= 0:
            continue
        if distance(previous, current) / dt > MAX_REASONABLE_STEP_SPEED_MPS:
            return False
    return states[-1].t > states[0].t


def _metadata_track_ids(scenario: Scenario, key: str) -> tuple[str, ...]:
    value = scenario.metadata.get(key, ())
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if item is not None)


def _min_track_distance_to_any(
    track: AgentTrack,
    anchors: tuple[AgentTrack, ...],
) -> float:
    return _min_spatial_distance_to_any(
        _track_spatial_index(track),
        tuple(_track_spatial_index(anchor) for anchor in anchors),
    )


def _min_spatial_distance_to_any(
    track: _TrackSpatialIndex,
    anchors: tuple[_TrackSpatialIndex, ...],
) -> float:
    best = inf
    for anchor in anchors:
        if track.agent_id == anchor.agent_id:
            return 0.0
        best = min(best, _spatial_index_distance(track, anchor, upper_bound=best))
    return best


def _min_track_distance(left: AgentTrack, right: AgentTrack) -> float:
    return _spatial_index_distance(
        _track_spatial_index(left),
        _track_spatial_index(right),
    )


def _track_spatial_index(track: AgentTrack) -> _TrackSpatialIndex:
    points = tuple(sorted((state.x, state.y) for state in track.states))
    if not points:
        return _TrackSpatialIndex(
            agent_id=track.agent_id,
            points_by_x=(),
            x_coordinates=(),
            min_x=inf,
            max_x=-inf,
            min_y=inf,
            max_y=-inf,
        )
    y_coordinates = tuple(point[1] for point in points)
    return _TrackSpatialIndex(
        agent_id=track.agent_id,
        points_by_x=points,
        x_coordinates=tuple(point[0] for point in points),
        min_x=points[0][0],
        max_x=points[-1][0],
        min_y=min(y_coordinates),
        max_y=max(y_coordinates),
    )


def _spatial_index_distance(
    left: _TrackSpatialIndex,
    right: _TrackSpatialIndex,
    upper_bound: float = inf,
) -> float:
    if not left.points_by_x or not right.points_by_x:
        return inf
    if _bounding_box_distance(left, right) >= upper_bound:
        return upper_bound
    if len(left.points_by_x) <= len(right.points_by_x):
        queries = left.points_by_x
        target = right
    else:
        queries = right.points_by_x
        target = left

    best = upper_bound
    for x, y in queries:
        if best == inf:
            position = bisect_left(target.x_coordinates, x)
            for candidate_index in (position - 1, position):
                if 0 <= candidate_index < len(target.points_by_x):
                    candidate_x, candidate_y = target.points_by_x[candidate_index]
                    best = min(best, hypot(x - candidate_x, y - candidate_y))
        left_index = bisect_left(target.x_coordinates, x - best)
        right_index = bisect_right(target.x_coordinates, x + best)
        for candidate_index in range(left_index, right_index):
            candidate_x, candidate_y = target.points_by_x[candidate_index]
            delta_x = x - candidate_x
            delta_y = y - candidate_y
            if abs(delta_x) >= best or abs(delta_y) >= best:
                continue
            best = min(best, hypot(delta_x, delta_y))
        if best == 0.0:
            return 0.0
    return best


def _spatial_indexes_within_distance(
    left: _TrackSpatialIndex,
    right: _TrackSpatialIndex,
    *,
    threshold: float,
) -> bool:
    if not left.points_by_x or not right.points_by_x:
        return False
    if _bounding_box_distance(left, right) > threshold:
        return False
    if len(left.points_by_x) <= len(right.points_by_x):
        queries = left.points_by_x
        target = right
    else:
        queries = right.points_by_x
        target = left

    for x, y in queries:
        left_index = bisect_left(target.x_coordinates, x - threshold)
        right_index = bisect_right(target.x_coordinates, x + threshold)
        for candidate_index in range(left_index, right_index):
            candidate_x, candidate_y = target.points_by_x[candidate_index]
            if abs(y - candidate_y) > threshold:
                continue
            if hypot(x - candidate_x, y - candidate_y) <= threshold:
                return True
    return False


def _bounding_box_distance(
    left: _TrackSpatialIndex,
    right: _TrackSpatialIndex,
) -> float:
    delta_x = max(left.min_x - right.max_x, right.min_x - left.max_x, 0.0)
    delta_y = max(left.min_y - right.max_y, right.min_y - left.max_y, 0.0)
    return hypot(delta_x, delta_y)


def _percentile(sorted_values: tuple[float, ...], percentile: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    index = int(round((len(sorted_values) - 1) * percentile))
    return sorted_values[index]
