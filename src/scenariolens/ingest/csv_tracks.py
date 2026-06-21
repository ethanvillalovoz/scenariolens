from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from scenariolens.io import VALID_AGENT_TYPES, save_scenarios
from scenariolens.schema import AgentTrack, AgentType, Scenario, State

REQUIRED_COLUMNS = ("scenario_id", "agent_id", "agent_type", "t", "x", "y")


@dataclass
class _ScenarioBuilder:
    scenario_id: str
    source: str = "csv"
    ego_track_id: str | None = None
    tags: set[str] = field(default_factory=set)
    tracks: dict[str, tuple[AgentType, list[State]]] = field(default_factory=dict)


def load_track_csv(path: str | Path) -> tuple[Scenario, ...]:
    rows = _read_rows(path)
    builders: dict[str, _ScenarioBuilder] = {}

    for index, row in enumerate(rows, start=2):
        scenario_id = _required(row, "scenario_id", index)
        agent_id = _required(row, "agent_id", index)
        agent_type = _agent_type(_required(row, "agent_type", index), index)
        builder = builders.setdefault(
            scenario_id,
            _ScenarioBuilder(scenario_id=scenario_id),
        )

        source = row.get("source", "").strip()
        if source:
            builder.source = source

        ego_track_id = row.get("ego_track_id", "").strip()
        if ego_track_id:
            builder.ego_track_id = ego_track_id

        builder.tags.update(_parse_tags(row.get("tags", "")))
        _append_state(builder, agent_id, agent_type, row, index)

    return tuple(_build_scenario(builder) for builder in builders.values())


def save_track_csv_as_scenarios(input_path: str | Path, output_path: str | Path) -> None:
    save_scenarios(output_path, load_track_csv(input_path))


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row")
        missing = tuple(column for column in REQUIRED_COLUMNS if column not in reader.fieldnames)
        if missing:
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing)}")
        return list(reader)


def _append_state(
    builder: _ScenarioBuilder,
    agent_id: str,
    agent_type: AgentType,
    row: dict[str, str],
    row_number: int,
) -> None:
    existing = builder.tracks.get(agent_id)
    if existing is None:
        states: list[State] = []
        builder.tracks[agent_id] = (agent_type, states)
    else:
        existing_type, states = existing
        if existing_type != agent_type:
            raise ValueError(
                f"Row {row_number}: agent {agent_id} changes type from "
                f"{existing_type} to {agent_type}"
            )

    builder.tracks[agent_id][1].append(
        State(
            t=_float(row, "t", row_number),
            x=_float(row, "x", row_number),
            y=_float(row, "y", row_number),
            vx=_float(row, "vx", row_number, default=0.0),
            vy=_float(row, "vy", row_number, default=0.0),
        )
    )


def _build_scenario(builder: _ScenarioBuilder) -> Scenario:
    tracks = tuple(
        AgentTrack(
            agent_id=agent_id,
            agent_type=agent_type,
            states=tuple(sorted(states, key=lambda state: state.t)),
        )
        for agent_id, (agent_type, states) in sorted(builder.tracks.items())
    )
    return Scenario(
        scenario_id=builder.scenario_id,
        source=builder.source,
        ego_track_id=builder.ego_track_id,
        tags=tuple(sorted(builder.tags)),
        tracks=tracks,
    )


def _required(row: dict[str, str], column: str, row_number: int) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ValueError(f"Row {row_number}: missing required column value: {column}")
    return value


def _agent_type(value: str, row_number: int) -> AgentType:
    if value not in VALID_AGENT_TYPES:
        raise ValueError(f"Row {row_number}: unsupported agent_type: {value}")
    return value  # type: ignore[return-value]


def _float(
    row: dict[str, str],
    column: str,
    row_number: int,
    default: float | None = None,
) -> float:
    value = row.get(column, "").strip()
    if not value and default is not None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: expected numeric value for {column}") from exc


def _parse_tags(value: str) -> tuple[str, ...]:
    normalized = value.replace("|", ";").replace(",", ";")
    return tuple(tag.strip() for tag in normalized.split(";") if tag.strip())
