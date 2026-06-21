from __future__ import annotations

import csv
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, AgentType, Scenario, State

WAYMO_OPEN_DATASET_URL = "https://waymo.com/open/"
WAYMO_OPEN_CHALLENGES_URL = "https://waymo.com/open/challenges/"
OPTIONAL_PACKAGE = "waymo_open_dataset"
NORMALIZED_REQUIRED_COLUMNS = (
    "scenario_id",
    "track_id",
    "object_type",
    "timestep",
    "center_x",
    "center_y",
)

OBJECT_TYPE_MAP = {
    "TYPE_VEHICLE": "vehicle",
    "VEHICLE": "vehicle",
    "vehicle": "vehicle",
    "TYPE_PEDESTRIAN": "pedestrian",
    "PEDESTRIAN": "pedestrian",
    "pedestrian": "pedestrian",
    "TYPE_CYCLIST": "cyclist",
    "CYCLIST": "cyclist",
    "cyclist": "cyclist",
    "TYPE_OTHER": "unknown",
    "OTHER": "unknown",
    "UNKNOWN": "unknown",
    "unknown": "unknown",
}


@dataclass(frozen=True)
class WaymoMotionAdapterStatus:
    """Current readiness state for the optional Waymo Motion adapter."""

    adapter_name: str
    implemented: bool
    optional_package: str
    optional_package_available: bool
    dataset_url: str
    challenges_url: str
    message: str


@dataclass
class _ScenarioBuilder:
    scenario_id: str
    source: str = "waymo_motion_normalized"
    ego_track_id: str | None = None
    tags: set[str] = field(default_factory=set)
    tracks: dict[str, tuple[AgentType, list[State]]] = field(default_factory=dict)


def adapter_status() -> WaymoMotionAdapterStatus:
    package_available = find_spec(OPTIONAL_PACKAGE) is not None
    return WaymoMotionAdapterStatus(
        adapter_name="waymo_motion",
        implemented=False,
        optional_package=OPTIONAL_PACKAGE,
        optional_package_available=package_available,
        dataset_url=WAYMO_OPEN_DATASET_URL,
        challenges_url=WAYMO_OPEN_CHALLENGES_URL,
        message=(
            "Native Waymo Motion ingestion is planned. Normalized CSV ingestion "
            "is available with `ingest-waymo-motion --format normalized-csv`."
        ),
    )


def ingest_waymo_motion(
    input_path: str | Path,
    output_path: str | Path,
    max_scenarios: int | None = None,
) -> None:
    """Placeholder for future Waymo Motion Dataset conversion.

    The real implementation should convert a tiny Motion Dataset slice into
    ScenarioLens JSON without making Waymo dependencies mandatory for the core
    package.
    """

    status = adapter_status()
    raise NotImplementedError(
        f"{status.message} Requested input={input_path}, output={output_path}, "
        f"max_scenarios={max_scenarios}."
    )


def load_normalized_motion_csv(
    input_path: str | Path,
    max_scenarios: int | None = None,
) -> tuple[Scenario, ...]:
    """Load a Waymo Motion-shaped normalized CSV extraction.

    This is not a native TFRecord/protobuf parser. It accepts a lightweight CSV
    shape that mirrors key Motion fields after extraction.
    """

    scenarios = _scenarios_from_rows(_read_motion_rows(Path(input_path)))
    if max_scenarios is not None:
        scenarios = scenarios[:max_scenarios]
    return scenarios


def save_normalized_motion_csv_as_scenarios(
    input_path: str | Path,
    output_path: str | Path,
    max_scenarios: int | None = None,
) -> None:
    save_scenarios(output_path, load_normalized_motion_csv(input_path, max_scenarios))


def _read_motion_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Normalized Waymo Motion CSV must include a header row")
        missing = tuple(
            column for column in NORMALIZED_REQUIRED_COLUMNS if column not in reader.fieldnames
        )
        if missing:
            raise ValueError(
                "Normalized Waymo Motion CSV is missing required columns: "
                + ", ".join(missing)
            )
        return [(index, row) for index, row in enumerate(reader, start=2)]


def _scenarios_from_rows(rows: list[tuple[int, dict[str, str]]]) -> tuple[Scenario, ...]:
    builders: dict[str, _ScenarioBuilder] = {}
    for row_number, row in rows:
        scenario_id = _required(row, "scenario_id", row_number)
        builder = builders.setdefault(
            scenario_id,
            _ScenarioBuilder(scenario_id=scenario_id),
        )
        source = row.get("source", "").strip()
        if source:
            builder.source = source

        ego_track_id = _ego_track_id(row)
        if ego_track_id:
            builder.ego_track_id = ego_track_id

        builder.tags.update(_parse_tags(row.get("tags", "")))
        track_id = _required(row, "track_id", row_number)
        object_type = _object_type(_required(row, "object_type", row_number), row_number)
        _append_state(builder, track_id, object_type, row, row_number)

    return tuple(_build_scenario(builder) for builder in builders.values())


def _append_state(
    builder: _ScenarioBuilder,
    track_id: str,
    agent_type: AgentType,
    row: dict[str, str],
    row_number: int,
) -> None:
    existing = builder.tracks.get(track_id)
    if existing is None:
        states: list[State] = []
        builder.tracks[track_id] = (agent_type, states)
    else:
        existing_type, states = existing
        if existing_type != agent_type:
            raise ValueError(
                f"Row {row_number}: track {track_id} changes type from "
                f"{existing_type} to {agent_type}"
            )
    builder.tracks[track_id][1].append(
        State(
            t=_float(row, "timestep", row_number),
            x=_float(row, "center_x", row_number),
            y=_float(row, "center_y", row_number),
            vx=_float(row, "velocity_x", row_number, default=0.0),
            vy=_float(row, "velocity_y", row_number, default=0.0),
        )
    )


def _build_scenario(builder: _ScenarioBuilder) -> Scenario:
    tracks = tuple(
        AgentTrack(
            agent_id=track_id,
            agent_type=agent_type,
            states=tuple(sorted(states, key=lambda state: state.t)),
        )
        for track_id, (agent_type, states) in sorted(builder.tracks.items())
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


def _object_type(value: str, row_number: int) -> AgentType:
    normalized = OBJECT_TYPE_MAP.get(value.strip())
    if normalized is None:
        raise ValueError(f"Row {row_number}: unsupported object_type: {value}")
    return normalized  # type: ignore[return-value]


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


def _ego_track_id(row: dict[str, str]) -> str:
    ego_track_id = row.get("ego_track_id", "").strip()
    if ego_track_id:
        return ego_track_id
    is_sdc = row.get("is_sdc", "").strip().lower()
    if is_sdc in {"1", "true", "yes"}:
        return row.get("track_id", "").strip()
    return ""


def _parse_tags(value: str) -> tuple[str, ...]:
    normalized = value.replace("|", ";").replace(",", ";")
    return tuple(tag.strip() for tag in normalized.split(";") if tag.strip())
