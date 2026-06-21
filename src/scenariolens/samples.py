from __future__ import annotations

from scenariolens.schema import AgentTrack, AgentType, Scenario, State


def _track(
    agent_id: str,
    agent_type: AgentType,
    points: tuple[tuple[float, float, float, float, float], ...],
) -> AgentTrack:
    return AgentTrack(
        agent_id=agent_id,
        agent_type=agent_type,
        states=tuple(State(t=t, x=x, y=y, vx=vx, vy=vy) for t, x, y, vx, vy in points),
    )


def synthetic_scenarios() -> tuple[Scenario, ...]:
    """Starter corpus for validating metrics before real data ingestion.

    The records are intentionally tiny, but each one represents a common
    autonomy-evaluation pattern we can later search for in real datasets.
    """

    return (
        Scenario(
            scenario_id="synthetic_pedestrian_crossing",
            ego_track_id="ego",
            tags=("pedestrian_crossing", "close_interaction"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 5, 0),
                        (1, 5, 0, 5, 0),
                        (2, 10, 0, 4, 0),
                    ),
                ),
                _track(
                    "ped_1",
                    "pedestrian",
                    (
                        (0, 8, -4, 0, 1.5),
                        (1, 8, -2.5, 0, 1.5),
                        (2, 8, -1, 0, 1.5),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_dense_merge",
            ego_track_id="ego",
            tags=("merge_conflict", "dense_multi_agent"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 8, 0),
                        (1, 8, 0, 8, 0),
                        (2, 16, 0.3, 8, 0.2),
                    ),
                ),
                _track(
                    "veh_1",
                    "vehicle",
                    (
                        (0, 12, 3.2, 6, -0.7),
                        (1, 18, 2.5, 6, -0.7),
                        (2, 24, 1.8, 6, -0.7),
                    ),
                ),
                _track(
                    "veh_2",
                    "vehicle",
                    (
                        (0, -7, 0, 9, 0),
                        (1, 2, 0, 9, 0),
                        (2, 11, 0, 9, 0),
                    ),
                ),
                _track(
                    "veh_3",
                    "vehicle",
                    (
                        (0, 22, -3.1, 7, 0.5),
                        (1, 29, -2.6, 7, 0.5),
                        (2, 36, -2.1, 7, 0.5),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_cyclist_close_pass",
            ego_track_id="ego",
            tags=("cyclist_interaction", "close_interaction"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 6, 0),
                        (1, 6, 0, 6, 0),
                        (2, 12, 0, 6, 0),
                    ),
                ),
                _track(
                    "cyclist_1",
                    "cyclist",
                    (
                        (0, 4, 1.7, 4.5, 0),
                        (1, 8.5, 1.5, 4.5, -0.1),
                        (2, 13, 1.3, 4.5, -0.1),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_unprotected_left_turn",
            ego_track_id="ego",
            tags=("unprotected_turn", "close_interaction"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, -4, -4, 2, 3),
                        (1, -2, -1, 2.5, 2.5),
                        (2, 1, 1, 3, 1.5),
                    ),
                ),
                _track(
                    "oncoming_1",
                    "vehicle",
                    (
                        (0, 10, 0, -6, 0),
                        (1, 4, 0, -6, 0),
                        (2, -2, 0, -6, 0),
                    ),
                ),
                _track(
                    "ped_1",
                    "pedestrian",
                    (
                        (0, 2, -3, 0, 1.2),
                        (1, 2, -1.8, 0, 1.2),
                        (2, 2, -0.6, 0, 1.2),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_blocked_lane_yield",
            ego_track_id="ego",
            tags=("blocked_lane", "merge_conflict"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 5, 0),
                        (1, 5, 0, 5, 0),
                        (2, 10, 0.8, 4, 0.8),
                    ),
                ),
                _track(
                    "stopped_van",
                    "vehicle",
                    (
                        (0, 13, 0, 0, 0),
                        (1, 13, 0, 0, 0),
                        (2, 13, 0, 0, 0),
                    ),
                ),
                _track(
                    "adjacent_1",
                    "vehicle",
                    (
                        (0, 6, 3.2, 5, 0),
                        (1, 11, 3.2, 5, 0),
                        (2, 16, 3.2, 5, 0),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_hard_braking_lead_vehicle",
            ego_track_id="ego",
            tags=("hard_braking", "stopped_vehicle", "close_interaction"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 9, 0),
                        (1, 9, 0, 7, 0),
                        (2, 15, 0, 4, 0),
                    ),
                ),
                _track(
                    "lead_1",
                    "vehicle",
                    (
                        (0, 18, 0, 8, 0),
                        (1, 23, 0, 2, 0),
                        (2, 24, 0, 0, 0),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_dense_intersection_vru",
            ego_track_id="ego",
            tags=("pedestrian_crossing", "cyclist_interaction", "dense_multi_agent"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, -6, 0, 4, 0),
                        (1, -2, 0, 4, 0),
                        (2, 2, 0, 4, 0),
                    ),
                ),
                _track(
                    "veh_cross",
                    "vehicle",
                    (
                        (0, 0, -6, 0, 5),
                        (1, 0, -1, 0, 5),
                        (2, 0, 4, 0, 5),
                    ),
                ),
                _track(
                    "ped_1",
                    "pedestrian",
                    (
                        (0, 3, -2, -0.8, 1.1),
                        (1, 2.2, -0.9, -0.8, 1.1),
                        (2, 1.4, 0.2, -0.8, 1.1),
                    ),
                ),
                _track(
                    "cyclist_1",
                    "cyclist",
                    (
                        (0, -3, 2.5, 4, -0.4),
                        (1, 1, 2.1, 4, -0.4),
                        (2, 5, 1.7, 4, -0.4),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_occluded_pedestrian",
            ego_track_id="ego",
            tags=("pedestrian_crossing", "blocked_lane", "close_interaction"),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 4, 0),
                        (1, 4, 0, 4, 0),
                        (2, 8, 0, 3, 0),
                    ),
                ),
                _track(
                    "parked_truck",
                    "vehicle",
                    (
                        (0, 6, -2.2, 0, 0),
                        (1, 6, -2.2, 0, 0),
                        (2, 6, -2.2, 0, 0),
                    ),
                ),
                _track(
                    "ped_1",
                    "pedestrian",
                    (
                        (0, 6.5, -3.5, 0, 1.4),
                        (1, 6.5, -2.1, 0, 1.4),
                        (2, 6.5, -0.7, 0, 1.4),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_easy_following",
            ego_track_id="ego",
            tags=("low_interaction",),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 7, 0),
                        (1, 7, 0, 7, 0),
                        (2, 14, 0, 7, 0),
                    ),
                ),
                _track(
                    "veh_1",
                    "vehicle",
                    (
                        (0, 30, 0, 7, 0),
                        (1, 37, 0, 7, 0),
                        (2, 44, 0, 7, 0),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_open_road_baseline",
            ego_track_id="ego",
            tags=("low_interaction",),
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    (
                        (0, 0, 0, 10, 0),
                        (1, 10, 0, 10, 0),
                        (2, 20, 0, 10, 0),
                    ),
                ),
            ),
        ),
    )
