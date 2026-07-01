from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite

from scenariolens.schema import AgentTrack, AgentType, Scenario, State

DEFAULT_MISS_THRESHOLD_M = 2.0
LANE_MATCH_THRESHOLD_M = 3.5
MIN_LANE_AWARE_SPEED_MPS = 0.25
HEADING_AWARE_MIN_ALIGNMENT = 0.5
HEADING_AWARE_ALIGNMENT_PENALTY_M = 3.5


@dataclass(frozen=True)
class PredictionTrackResult:
    """Constant-velocity forecast result for one evaluated track."""

    track_id: str
    agent_type: AgentType
    anchor_time_s: float
    horizon_s: float
    future_state_count: int
    ade_m: float
    fde_m: float
    miss: bool
    predicted_states: tuple[State, ...]
    baseline_name: str = "constant_velocity"
    map_used: bool = False
    fallback_reason: str | None = None


@dataclass(frozen=True)
class PredictionBaselineSummary:
    """Aggregate error summary for the lightweight trajectory baseline."""

    target_source: str
    requested_target_count: int
    evaluated_track_count: int
    ade_m: float | None
    fde_m: float | None
    max_fde_m: float | None
    miss_rate: float | None
    failure_score: float
    track_results: tuple[PredictionTrackResult, ...]
    baseline_name: str = "constant_velocity"
    map_used_count: int = 0
    fallback_count: int = 0


@dataclass(frozen=True)
class PredictionBaselineTrackComparison:
    """Per-track comparison between constant-velocity and lane-aware forecasts."""

    track_id: str
    agent_type: AgentType
    constant_velocity_ade_m: float
    constant_velocity_fde_m: float
    lane_aware_ade_m: float
    lane_aware_fde_m: float
    fde_improvement_m: float
    lane_map_used: bool
    lane_fallback_reason: str | None


@dataclass(frozen=True)
class PredictionBaselineComparison:
    """Scenario-level comparison for the two lightweight prediction baselines."""

    scenario_id: str
    target_source: str
    requested_target_count: int
    evaluated_track_count: int
    constant_velocity_ade_m: float | None
    constant_velocity_fde_m: float | None
    constant_velocity_miss_rate: float | None
    lane_aware_ade_m: float | None
    lane_aware_fde_m: float | None
    lane_aware_miss_rate: float | None
    fde_improvement_m: float | None
    map_used_count: int
    fallback_count: int
    track_results: tuple[PredictionBaselineTrackComparison, ...]


@dataclass(frozen=True)
class _LaneProjection:
    lane: tuple[tuple[float, float], ...]
    distance_m: float
    arc_length_m: float
    segment_index: int
    segment_dx: float
    segment_dy: float
    segment_length_m: float


def constant_velocity_baseline(
    scenario: Scenario,
    miss_threshold_m: float = DEFAULT_MISS_THRESHOLD_M,
) -> PredictionBaselineSummary:
    """Evaluate a constant-velocity predictor on likely prediction targets.

    For Waymo Motion records, this uses `tracks_to_predict` and forecasts from
    `current_time_index`. For small fixtures without Waymo metadata, it falls
    back to non-ego tracks so the CLI and dashboard remain useful.
    """

    target_ids, target_source = _prediction_target_ids(scenario)
    tracks_by_id = {track.agent_id: track for track in scenario.tracks}
    results = tuple(
        result
        for track_id in target_ids
        if (track := tracks_by_id.get(track_id)) is not None
        if (
            result := _evaluate_track(
                track=track,
                scenario=scenario,
                miss_threshold_m=miss_threshold_m,
            )
        )
        is not None
    )

    return _summarize_results(
        target_source=target_source,
        requested_target_count=len(target_ids),
        results=results,
        baseline_name="constant_velocity",
        map_used_count=0,
        fallback_count=0,
    )


def lane_aware_baseline(
    scenario: Scenario,
    miss_threshold_m: float = DEFAULT_MISS_THRESHOLD_M,
    lane_match_threshold_m: float = LANE_MATCH_THRESHOLD_M,
    lane_selection: str = "nearest",
    lane_heading_min_alignment: float = HEADING_AWARE_MIN_ALIGNMENT,
    baseline_name: str = "lane_aware",
) -> PredictionBaselineSummary:
    """Evaluate a lightweight lane-following forecast when map context exists.

    Vehicles and cyclists are matched to the nearest lane polyline. If no
    usable lane exists, the target is a pedestrian, or the anchor velocity is
    not informative, the evaluator falls back to the constant-velocity forecast
    for that track. The function intentionally keeps the same target-selection
    semantics as `constant_velocity_baseline`.
    """

    target_ids, target_source = _prediction_target_ids(scenario)
    tracks_by_id = {track.agent_id: track for track in scenario.tracks}
    results: list[PredictionTrackResult] = []
    map_used_count = 0
    fallback_count = 0

    for track_id in target_ids:
        track = tracks_by_id.get(track_id)
        if track is None:
            continue
        result, fallback_reason = _evaluate_lane_aware_track(
            track=track,
            scenario=scenario,
            miss_threshold_m=miss_threshold_m,
            lane_match_threshold_m=lane_match_threshold_m,
            lane_selection=lane_selection,
            lane_heading_min_alignment=lane_heading_min_alignment,
            baseline_name=baseline_name,
        )
        if result is None:
            fallback = _evaluate_track(
                track=track,
                scenario=scenario,
                miss_threshold_m=miss_threshold_m,
                baseline_name=baseline_name,
                map_used=False,
                fallback_reason=fallback_reason,
            )
            if fallback is None:
                continue
            result = fallback
            fallback_count += 1
        elif result.map_used:
            map_used_count += 1
        results.append(result)

    return _summarize_results(
        target_source=target_source,
        requested_target_count=len(target_ids),
        results=tuple(results),
        baseline_name=baseline_name,
        map_used_count=map_used_count,
        fallback_count=fallback_count,
    )


def heading_aware_lane_baseline(
    scenario: Scenario,
    miss_threshold_m: float = DEFAULT_MISS_THRESHOLD_M,
    lane_match_threshold_m: float = LANE_MATCH_THRESHOLD_M,
    lane_heading_min_alignment: float = HEADING_AWARE_MIN_ALIGNMENT,
) -> PredictionBaselineSummary:
    """Evaluate lane following with heading-aware lane selection.

    This variant keeps the same fallback discipline as the default lane-aware
    baseline, but when several lane polylines are close to the target it prefers
    lanes whose local tangent is aligned with the target's anchor velocity. It
    is an experiment for diagnosing nearest-lane regressions, not the default
    scoring baseline.
    """

    return lane_aware_baseline(
        scenario,
        miss_threshold_m=miss_threshold_m,
        lane_match_threshold_m=lane_match_threshold_m,
        lane_selection="heading",
        lane_heading_min_alignment=lane_heading_min_alignment,
        baseline_name="lane_aware_heading",
    )


def compare_prediction_baselines(
    scenario: Scenario,
    miss_threshold_m: float = DEFAULT_MISS_THRESHOLD_M,
) -> PredictionBaselineComparison:
    """Compare constant-velocity and lane-aware baselines on one scenario."""

    constant = constant_velocity_baseline(
        scenario,
        miss_threshold_m=miss_threshold_m,
    )
    lane = lane_aware_baseline(
        scenario,
        miss_threshold_m=miss_threshold_m,
    )
    lane_by_track = {result.track_id: result for result in lane.track_results}
    track_rows: list[PredictionBaselineTrackComparison] = []

    for constant_result in constant.track_results:
        lane_result = lane_by_track.get(constant_result.track_id)
        if lane_result is None:
            continue
        track_rows.append(
            PredictionBaselineTrackComparison(
                track_id=constant_result.track_id,
                agent_type=constant_result.agent_type,
                constant_velocity_ade_m=constant_result.ade_m,
                constant_velocity_fde_m=constant_result.fde_m,
                lane_aware_ade_m=lane_result.ade_m,
                lane_aware_fde_m=lane_result.fde_m,
                fde_improvement_m=round(
                    constant_result.fde_m - lane_result.fde_m,
                    3,
                ),
                lane_map_used=lane_result.map_used,
                lane_fallback_reason=lane_result.fallback_reason,
            )
        )

    return PredictionBaselineComparison(
        scenario_id=scenario.scenario_id,
        target_source=constant.target_source,
        requested_target_count=constant.requested_target_count,
        evaluated_track_count=len(track_rows),
        constant_velocity_ade_m=constant.ade_m,
        constant_velocity_fde_m=constant.fde_m,
        constant_velocity_miss_rate=constant.miss_rate,
        lane_aware_ade_m=lane.ade_m,
        lane_aware_fde_m=lane.fde_m,
        lane_aware_miss_rate=lane.miss_rate,
        fde_improvement_m=_optional_delta(constant.fde_m, lane.fde_m),
        map_used_count=lane.map_used_count,
        fallback_count=lane.fallback_count,
        track_results=tuple(track_rows),
    )


def _summarize_results(
    target_source: str,
    requested_target_count: int,
    results: tuple[PredictionTrackResult, ...],
    baseline_name: str,
    map_used_count: int,
    fallback_count: int,
) -> PredictionBaselineSummary:
    if not results:
        return PredictionBaselineSummary(
            target_source=target_source,
            requested_target_count=requested_target_count,
            evaluated_track_count=0,
            ade_m=None,
            fde_m=None,
            max_fde_m=None,
            miss_rate=None,
            failure_score=0.0,
            track_results=(),
            baseline_name=baseline_name,
            map_used_count=0,
            fallback_count=0,
        )

    total_future_states = sum(result.future_state_count for result in results)
    ade = sum(result.ade_m * result.future_state_count for result in results)
    fde_values = tuple(result.fde_m for result in results)
    miss_rate = sum(result.miss for result in results) / len(results)
    mean_ade = ade / total_future_states
    mean_fde = sum(fde_values) / len(fde_values)
    max_fde = max(fde_values)

    return PredictionBaselineSummary(
        target_source=target_source,
        requested_target_count=requested_target_count,
        evaluated_track_count=len(results),
        ade_m=round(mean_ade, 3),
        fde_m=round(mean_fde, 3),
        max_fde_m=round(max_fde, 3),
        miss_rate=round(miss_rate, 3),
        failure_score=_failure_score(
            ade_m=mean_ade,
            fde_m=mean_fde,
            max_fde_m=max_fde,
            miss_rate=miss_rate,
            evaluated_track_count=len(results),
        ),
        track_results=results,
        baseline_name=baseline_name,
        map_used_count=map_used_count,
        fallback_count=fallback_count,
    )


def _prediction_target_ids(scenario: Scenario) -> tuple[tuple[str, ...], str]:
    waymo_targets = _metadata_track_ids(scenario, "waymo_tracks_to_predict_track_ids")
    if waymo_targets:
        return waymo_targets, "waymo_tracks_to_predict"

    non_ego = tuple(
        track.agent_id
        for track in scenario.tracks
        if scenario.ego_track_id is None or track.agent_id != scenario.ego_track_id
    )
    if non_ego:
        return non_ego, "non_ego_tracks"
    return tuple(track.agent_id for track in scenario.tracks), "all_tracks"


def _evaluate_track(
    track: AgentTrack,
    scenario: Scenario,
    miss_threshold_m: float,
    baseline_name: str = "constant_velocity",
    map_used: bool = False,
    fallback_reason: str | None = None,
) -> PredictionTrackResult | None:
    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return None

    anchor_index = _anchor_index(states, scenario)
    anchor = states[anchor_index]
    future_states = tuple(
        state for state in states[anchor_index + 1 :] if state.t > anchor.t
    )
    if not future_states:
        return None

    predictions = tuple(_predict_state(anchor, actual.t) for actual in future_states)
    errors = tuple(
        _state_error(predicted, actual)
        for predicted, actual in zip(predictions, future_states)
    )
    if not errors:
        return None

    fde = errors[-1]
    return PredictionTrackResult(
        track_id=track.agent_id,
        agent_type=track.agent_type,
        anchor_time_s=round(anchor.t, 3),
        horizon_s=round(future_states[-1].t - anchor.t, 3),
        future_state_count=len(future_states),
        ade_m=round(sum(errors) / len(errors), 3),
        fde_m=round(fde, 3),
        miss=fde > miss_threshold_m,
        predicted_states=(anchor, *predictions),
        baseline_name=baseline_name,
        map_used=map_used,
        fallback_reason=fallback_reason,
    )


def _evaluate_lane_aware_track(
    track: AgentTrack,
    scenario: Scenario,
    miss_threshold_m: float,
    lane_match_threshold_m: float,
    lane_selection: str,
    lane_heading_min_alignment: float,
    baseline_name: str,
) -> tuple[PredictionTrackResult | None, str | None]:
    if track.agent_type not in {"vehicle", "cyclist"}:
        return None, "non_vehicle_or_cyclist_target"

    lanes = _lane_polylines(scenario)
    if not lanes:
        return None, "no_lane_map_features"

    states = tuple(sorted(track.states, key=lambda state: state.t))
    if len(states) < 2:
        return None, "insufficient_track_states"

    anchor_index = _anchor_index(states, scenario)
    anchor = states[anchor_index]
    future_states = tuple(
        state for state in states[anchor_index + 1 :] if state.t > anchor.t
    )
    if not future_states:
        return None, "no_future_states"

    anchor_speed = hypot(anchor.vx, anchor.vy)
    if not isfinite(anchor_speed) or anchor_speed < MIN_LANE_AWARE_SPEED_MPS:
        return None, "low_or_invalid_anchor_speed"

    projection, projection_fallback_reason = _select_lane_projection(
        anchor=anchor,
        lanes=lanes,
        lane_selection=lane_selection,
        lane_match_threshold_m=lane_match_threshold_m,
        lane_heading_min_alignment=lane_heading_min_alignment,
    )
    if projection is None:
        return None, projection_fallback_reason or "no_usable_lane_polyline"

    direction = _lane_direction(anchor, projection)
    predictions = tuple(
        _advance_along_lane(
            projection.lane,
            start_s=projection.arc_length_m,
            travel_m=anchor_speed * (actual.t - anchor.t) * direction,
            target_time_s=actual.t,
            speed_mps=anchor_speed,
        )
        for actual in future_states
    )
    errors = tuple(
        _state_error(predicted, actual)
        for predicted, actual in zip(predictions, future_states)
    )
    if not errors:
        return None, "no_prediction_errors"

    fde = errors[-1]
    return (
        PredictionTrackResult(
            track_id=track.agent_id,
            agent_type=track.agent_type,
            anchor_time_s=round(anchor.t, 3),
            horizon_s=round(future_states[-1].t - anchor.t, 3),
            future_state_count=len(future_states),
            ade_m=round(sum(errors) / len(errors), 3),
            fde_m=round(fde, 3),
            miss=fde > miss_threshold_m,
            predicted_states=(anchor, *predictions),
            baseline_name=baseline_name,
            map_used=True,
            fallback_reason=None,
        ),
        None,
    )


def _anchor_index(states: tuple[State, ...], scenario: Scenario) -> int:
    current_time_index = _metadata_int(scenario, "waymo_current_time_index")
    if current_time_index is not None:
        return min(max(current_time_index, 0), len(states) - 2)
    return min(max((len(states) - 1) // 2, 0), len(states) - 2)


def _predict_state(anchor: State, target_time_s: float) -> State:
    dt = target_time_s - anchor.t
    return State(
        t=target_time_s,
        x=anchor.x + (anchor.vx * dt),
        y=anchor.y + (anchor.vy * dt),
        vx=anchor.vx,
        vy=anchor.vy,
    )


def _lane_polylines(scenario: Scenario) -> tuple[tuple[tuple[float, float], ...], ...]:
    value = scenario.metadata.get("waymo_map_features", ())
    if not isinstance(value, list):
        return ()

    lanes: list[tuple[tuple[float, float], ...]] = []
    for feature in value:
        if not isinstance(feature, dict) or feature.get("kind") != "lane":
            continue
        points = _feature_points(feature)
        if len(points) >= 2:
            lanes.append(points)
    return tuple(lanes)


def _feature_points(feature: dict[str, object]) -> tuple[tuple[float, float], ...]:
    raw_points = feature.get("points", ())
    if not isinstance(raw_points, list):
        return ()

    points: list[tuple[float, float]] = []
    for point in raw_points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        try:
            x = float(point[0])
            y = float(point[1])
        except (TypeError, ValueError):
            continue
        if isfinite(x) and isfinite(y):
            points.append((x, y))
    return tuple(points)


def _nearest_lane_projection(
    x: float,
    y: float,
    lanes: tuple[tuple[tuple[float, float], ...], ...],
) -> _LaneProjection | None:
    best: _LaneProjection | None = None
    for lane in lanes:
        projection = _project_to_lane(x, y, lane)
        if projection is None:
            continue
        if best is None or projection.distance_m < best.distance_m:
            best = projection
    return best


def _select_lane_projection(
    anchor: State,
    lanes: tuple[tuple[tuple[float, float], ...], ...],
    lane_selection: str,
    lane_match_threshold_m: float,
    lane_heading_min_alignment: float,
) -> tuple[_LaneProjection | None, str | None]:
    if lane_selection == "nearest":
        projection = _nearest_lane_projection(anchor.x, anchor.y, lanes)
        if projection is None:
            return None, "no_usable_lane_polyline"
        if projection.distance_m > lane_match_threshold_m:
            return None, "target_too_far_from_lane"
        return projection, None

    if lane_selection != "heading":
        raise ValueError(
            "Unsupported lane selection mode: "
            f"{lane_selection}. Expected 'nearest' or 'heading'."
        )

    projections = tuple(
        projection
        for lane in lanes
        if (projection := _project_to_lane(anchor.x, anchor.y, lane)) is not None
    )
    if not projections:
        return None, "no_usable_lane_polyline"

    in_range = tuple(
        projection
        for projection in projections
        if projection.distance_m <= lane_match_threshold_m
    )
    if not in_range:
        return None, "target_too_far_from_lane"

    aligned = tuple(
        projection
        for projection in in_range
        if _lane_heading_alignment(anchor, projection) >= lane_heading_min_alignment
    )
    if not aligned:
        return None, "lane_heading_misaligned"

    return (
        min(aligned, key=lambda projection: _heading_selection_score(anchor, projection)),
        None,
    )


def _project_to_lane(
    x: float,
    y: float,
    lane: tuple[tuple[float, float], ...],
) -> _LaneProjection | None:
    best: _LaneProjection | None = None
    accumulated = 0.0
    for index, ((x1, y1), (x2, y2)) in enumerate(zip(lane, lane[1:])):
        dx = x2 - x1
        dy = y2 - y1
        length = hypot(dx, dy)
        if length <= 0.0:
            continue
        t = max(0.0, min(1.0, (((x - x1) * dx) + ((y - y1) * dy)) / (length * length)))
        px = x1 + (dx * t)
        py = y1 + (dy * t)
        distance = hypot(x - px, y - py)
        projection = _LaneProjection(
            lane=lane,
            distance_m=distance,
            arc_length_m=accumulated + (length * t),
            segment_index=index,
            segment_dx=dx,
            segment_dy=dy,
            segment_length_m=length,
        )
        if best is None or projection.distance_m < best.distance_m:
            best = projection
        accumulated += length
    return best


def _lane_heading_alignment(anchor: State, projection: _LaneProjection) -> float:
    anchor_speed = hypot(anchor.vx, anchor.vy)
    if anchor_speed <= 0.0 or projection.segment_length_m <= 0.0:
        return 0.0
    tangent_x = projection.segment_dx / projection.segment_length_m
    tangent_y = projection.segment_dy / projection.segment_length_m
    return abs(
        ((anchor.vx / anchor_speed) * tangent_x)
        + ((anchor.vy / anchor_speed) * tangent_y)
    )


def _heading_selection_score(anchor: State, projection: _LaneProjection) -> float:
    alignment = _lane_heading_alignment(anchor, projection)
    return projection.distance_m + (
        HEADING_AWARE_ALIGNMENT_PENALTY_M * (1.0 - alignment)
    )


def _lane_direction(anchor: State, projection: _LaneProjection) -> float:
    tangent_x = projection.segment_dx / projection.segment_length_m
    tangent_y = projection.segment_dy / projection.segment_length_m
    return -1.0 if ((anchor.vx * tangent_x) + (anchor.vy * tangent_y)) < 0.0 else 1.0


def _advance_along_lane(
    lane: tuple[tuple[float, float], ...],
    start_s: float,
    travel_m: float,
    target_time_s: float,
    speed_mps: float,
) -> State:
    target_s = max(0.0, min(_lane_length(lane), start_s + travel_m))
    accumulated = 0.0
    last_segment: tuple[float, float, float] | None = None

    for (x1, y1), (x2, y2) in zip(lane, lane[1:]):
        dx = x2 - x1
        dy = y2 - y1
        length = hypot(dx, dy)
        if length <= 0.0:
            continue
        last_segment = (dx, dy, length)
        if accumulated + length >= target_s:
            ratio = (target_s - accumulated) / length
            sign = 1.0 if travel_m >= 0.0 else -1.0
            return State(
                t=target_time_s,
                x=x1 + (dx * ratio),
                y=y1 + (dy * ratio),
                vx=(dx / length) * speed_mps * sign,
                vy=(dy / length) * speed_mps * sign,
            )
        accumulated += length

    end_x, end_y = lane[-1]
    if last_segment is None:
        return State(t=target_time_s, x=end_x, y=end_y, vx=0.0, vy=0.0)
    dx, dy, length = last_segment
    sign = 1.0 if travel_m >= 0.0 else -1.0
    return State(
        t=target_time_s,
        x=end_x,
        y=end_y,
        vx=(dx / length) * speed_mps * sign,
        vy=(dy / length) * speed_mps * sign,
    )


def _lane_length(lane: tuple[tuple[float, float], ...]) -> float:
    return sum(hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(lane, lane[1:]))


def _state_error(predicted: State, actual: State) -> float:
    return hypot(predicted.x - actual.x, predicted.y - actual.y)


def _optional_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 3)


def _failure_score(
    ade_m: float,
    fde_m: float,
    max_fde_m: float,
    miss_rate: float,
    evaluated_track_count: int,
) -> float:
    score = (
        (ade_m * 0.30)
        + (fde_m * 0.12)
        + (max_fde_m * 0.04)
        + (miss_rate * 2.50)
        + (min(evaluated_track_count, 6) * 0.15)
    )
    return round(min(score, 12.0), 3)


def _metadata_track_ids(scenario: Scenario, key: str) -> tuple[str, ...]:
    value = scenario.metadata.get(key, ())
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if item is not None)


def _metadata_int(scenario: Scenario, key: str) -> int | None:
    value = scenario.metadata.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
