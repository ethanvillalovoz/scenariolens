from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AgentType = Literal["vehicle", "pedestrian", "cyclist", "unknown"]


@dataclass(frozen=True)
class State:
    """Single agent state in a local 2D scene frame."""

    t: float
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


@dataclass(frozen=True)
class AgentTrack:
    """Trajectory for one road user."""

    agent_id: str
    agent_type: AgentType
    states: tuple[State, ...]


@dataclass(frozen=True)
class Scenario:
    """Compact scenario representation used by local metrics and ranking."""

    scenario_id: str
    tracks: tuple[AgentTrack, ...]
    ego_track_id: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    source: str = "synthetic"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioScore:
    """Feature bundle used to explain why a scenario is worth reviewing."""

    scenario_id: str
    agent_count: int
    scoring_agent_count: int
    excluded_track_count: int
    low_quality_track_count: int
    vulnerable_road_user_count: int
    scoring_vulnerable_road_user_count: int
    sdc_track_present: bool
    prediction_target_count: int
    object_of_interest_count: int
    min_pairwise_distance_m: float | None
    min_vru_distance_m: float | None
    min_path_distance_m: float | None
    min_time_to_collision_s: float | None
    max_speed_mps: float | None
    ego_max_speed_mps: float | None
    max_deceleration_mps2: float | None
    prediction_target_source: str
    prediction_target_evaluated_count: int
    baseline_ade_m: float | None
    baseline_fde_m: float | None
    baseline_max_fde_m: float | None
    baseline_miss_rate: float | None
    baseline_failure_score: float
    taxonomy_score: float
    component_scores: dict[str, float]
    interaction_score: float
    tags: tuple[str, ...]
