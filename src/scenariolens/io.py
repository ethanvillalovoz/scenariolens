from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scenariolens.schema import AgentTrack, AgentType, Scenario, State

FORMAT_VERSION = 1
VALID_AGENT_TYPES = {"vehicle", "pedestrian", "cyclist", "unknown"}


def scenario_to_dict(scenario: Scenario) -> dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "source": scenario.source,
        "ego_track_id": scenario.ego_track_id,
        "tags": list(scenario.tags),
        "metadata": scenario.metadata,
        "tracks": [
            {
                "agent_id": track.agent_id,
                "agent_type": track.agent_type,
                "states": [
                    {
                        "t": state.t,
                        "x": state.x,
                        "y": state.y,
                        "vx": state.vx,
                        "vy": state.vy,
                    }
                    for state in track.states
                ],
            }
            for track in scenario.tracks
        ],
    }


def scenario_from_dict(data: dict[str, Any]) -> Scenario:
    scenario_id = _required_str(data, "scenario_id")
    tracks = tuple(_track_from_dict(track) for track in _required_list(data, "tracks"))
    return Scenario(
        scenario_id=scenario_id,
        source=str(data.get("source", "external")),
        ego_track_id=_optional_str(data, "ego_track_id"),
        tags=tuple(str(tag) for tag in data.get("tags", ())),
        metadata=_optional_dict(data, "metadata"),
        tracks=tracks,
    )


def scenarios_to_payload(scenarios: tuple[Scenario, ...]) -> dict[str, Any]:
    return {
        "format": "scenariolens.scenarios",
        "version": FORMAT_VERSION,
        "scenarios": [scenario_to_dict(scenario) for scenario in scenarios],
    }


def scenarios_from_payload(payload: dict[str, Any]) -> tuple[Scenario, ...]:
    version = payload.get("version")
    if version != FORMAT_VERSION:
        raise ValueError(f"Unsupported ScenarioLens scenario format version: {version}")
    return tuple(
        scenario_from_dict(scenario)
        for scenario in _required_list(payload, "scenarios")
    )


def save_scenarios(path: str | Path, scenarios: tuple[Scenario, ...]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(scenarios_to_payload(scenarios), indent=2) + "\n",
        encoding="utf-8",
    )


def load_scenarios(path: str | Path) -> tuple[Scenario, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Scenario file must contain a JSON object")
    return scenarios_from_payload(payload)


def _track_from_dict(data: dict[str, Any]) -> AgentTrack:
    agent_type = _required_str(data, "agent_type")
    if agent_type not in VALID_AGENT_TYPES:
        raise ValueError(f"Unsupported agent_type: {agent_type}")
    return AgentTrack(
        agent_id=_required_str(data, "agent_id"),
        agent_type=agent_type,  # type: ignore[arg-type]
        states=tuple(_state_from_dict(state) for state in _required_list(data, "states")),
    )


def _state_from_dict(data: dict[str, Any]) -> State:
    return State(
        t=_required_float(data, "t"),
        x=_required_float(data, "x"),
        y=_required_float(data, "y"),
        vx=_optional_float(data, "vx", default=0.0),
        vy=_optional_float(data, "vy", default=0.0),
    )


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string field: {key}")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected string or null field: {key}")
    return value


def _required_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}")
    return value


def _optional_dict(data: dict[str, Any], key: str) -> dict[str, object]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected object field: {key}")
    return dict(value)


def _required_float(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric field: {key}")
    return float(value)


def _optional_float(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric field: {key}")
    return float(value)
