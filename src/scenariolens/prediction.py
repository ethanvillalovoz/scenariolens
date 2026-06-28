from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from scenariolens.schema import AgentTrack, AgentType, Scenario, State

DEFAULT_MISS_THRESHOLD_M = 2.0


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

    if not results:
        return PredictionBaselineSummary(
            target_source=target_source,
            requested_target_count=len(target_ids),
            evaluated_track_count=0,
            ade_m=None,
            fde_m=None,
            max_fde_m=None,
            miss_rate=None,
            failure_score=0.0,
            track_results=(),
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
        requested_target_count=len(target_ids),
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


def _state_error(predicted: State, actual: State) -> float:
    return hypot(predicted.x - actual.x, predicted.y - actual.y)


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
