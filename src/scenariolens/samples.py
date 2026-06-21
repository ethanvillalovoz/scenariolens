from __future__ import annotations

from scenariolens.schema import AgentTrack, Scenario, State


def synthetic_scenarios() -> tuple[Scenario, ...]:
    """Small starter corpus for validating metrics before real data ingestion."""

    return (
        Scenario(
            scenario_id="synthetic_pedestrian_crossing",
            ego_track_id="ego",
            tags=("pedestrian", "crossing", "close_interaction"),
            tracks=(
                AgentTrack(
                    agent_id="ego",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=0, y=0, vx=5, vy=0),
                        State(t=1, x=5, y=0, vx=5, vy=0),
                        State(t=2, x=10, y=0, vx=4, vy=0),
                    ),
                ),
                AgentTrack(
                    agent_id="ped_1",
                    agent_type="pedestrian",
                    states=(
                        State(t=0, x=8, y=-4, vx=0, vy=1.5),
                        State(t=1, x=8, y=-2.5, vx=0, vy=1.5),
                        State(t=2, x=8, y=-1, vx=0, vy=1.5),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_dense_merge",
            ego_track_id="ego",
            tags=("vehicle", "merge", "multi_agent"),
            tracks=(
                AgentTrack(
                    agent_id="ego",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=0, y=0, vx=8, vy=0),
                        State(t=1, x=8, y=0, vx=8, vy=0),
                        State(t=2, x=16, y=0.3, vx=8, vy=0.2),
                    ),
                ),
                AgentTrack(
                    agent_id="veh_1",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=12, y=3.2, vx=6, vy=-0.7),
                        State(t=1, x=18, y=2.5, vx=6, vy=-0.7),
                        State(t=2, x=24, y=1.8, vx=6, vy=-0.7),
                    ),
                ),
                AgentTrack(
                    agent_id="veh_2",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=-7, y=0, vx=9, vy=0),
                        State(t=1, x=2, y=0, vx=9, vy=0),
                        State(t=2, x=11, y=0, vx=9, vy=0),
                    ),
                ),
            ),
        ),
        Scenario(
            scenario_id="synthetic_easy_following",
            ego_track_id="ego",
            tags=("vehicle", "low_interaction"),
            tracks=(
                AgentTrack(
                    agent_id="ego",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=0, y=0, vx=7, vy=0),
                        State(t=1, x=7, y=0, vx=7, vy=0),
                        State(t=2, x=14, y=0, vx=7, vy=0),
                    ),
                ),
                AgentTrack(
                    agent_id="veh_1",
                    agent_type="vehicle",
                    states=(
                        State(t=0, x=30, y=0, vx=7, vy=0),
                        State(t=1, x=37, y=0, vx=7, vy=0),
                        State(t=2, x=44, y=0, vx=7, vy=0),
                    ),
                ),
            ),
        ),
    )

