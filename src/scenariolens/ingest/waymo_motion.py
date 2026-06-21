from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, AgentType, Scenario, State

WAYMO_OPEN_DATASET_URL = "https://waymo.com/open/"
WAYMO_OPEN_CHALLENGES_URL = "https://waymo.com/open/challenges/"
WAYMO_SCENARIO_PROTO_URL = (
    "https://github.com/waymo-research/waymo-open-dataset/blob/master/"
    "src/waymo_open_dataset/protos/scenario.proto"
)
OPTIONAL_PACKAGE = "waymo_open_dataset"
OPTIONAL_TF_PACKAGE = "tensorflow"
NORMALIZED_REQUIRED_COLUMNS = (
    "scenario_id",
    "track_id",
    "object_type",
    "timestep",
    "center_x",
    "center_y",
)
NATIVE_JSON_SUFFIXES = {".json"}
NATIVE_JSONL_SUFFIXES = {".jsonl", ".ndjson"}
NATIVE_PROTO_SUFFIXES = {".pb", ".bin"}
NATIVE_TFRECORD_SUFFIXES = {".tfrecord", ".tfrecords"}
NATIVE_SUPPORTED_SUFFIXES = (
    NATIVE_JSON_SUFFIXES
    | NATIVE_JSONL_SUFFIXES
    | NATIVE_PROTO_SUFFIXES
    | NATIVE_TFRECORD_SUFFIXES
)

OBJECT_TYPE_MAP = {
    0: "unknown",
    1: "vehicle",
    2: "pedestrian",
    3: "cyclist",
    4: "unknown",
    "0": "unknown",
    "1": "vehicle",
    "2": "pedestrian",
    "3": "cyclist",
    "4": "unknown",
    "TYPE_UNSET": "unknown",
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
        implemented=True,
        optional_package=OPTIONAL_PACKAGE,
        optional_package_available=package_available,
        dataset_url=WAYMO_OPEN_DATASET_URL,
        challenges_url=WAYMO_OPEN_CHALLENGES_URL,
        message=(
            "Native Waymo Motion ingestion supports protobuf-shaped JSON without "
            "extra dependencies. Binary protobuf and TFRecord inputs are optional "
            "and require Waymo/TensorFlow packages."
        ),
    )


def ingest_waymo_motion(
    input_path: str | Path,
    output_path: str | Path,
    max_scenarios: int | None = None,
) -> None:
    """Convert native Waymo Motion records into ScenarioLens JSON."""

    save_scenarios(output_path, load_waymo_motion(input_path, max_scenarios))


def load_waymo_motion(
    input_path: str | Path,
    max_scenarios: int | None = None,
) -> tuple[Scenario, ...]:
    """Load a small native Waymo Motion slice.

    Dependency-free ingestion accepts JSON or JSONL records that mirror the
    public Scenario proto field names. Binary protobuf and TFRecord files use
    optional Waymo/TensorFlow packages when available.
    """

    path = Path(input_path)
    scenarios: list[Scenario] = []
    for file_path in _native_input_files(path):
        remaining = None if max_scenarios is None else max_scenarios - len(scenarios)
        if remaining is not None and remaining <= 0:
            return tuple(scenarios)
        scenarios.extend(_load_native_motion_file(file_path, max_scenarios=remaining))
    return tuple(scenarios)


def save_waymo_motion_as_scenarios(
    input_path: str | Path,
    output_path: str | Path,
    max_scenarios: int | None = None,
) -> None:
    save_scenarios(output_path, load_waymo_motion(input_path, max_scenarios))


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
    return _object_type_value(value, f"Row {row_number}")


def _object_type_value(value: Any, context: str) -> AgentType:
    key = value.strip() if isinstance(value, str) else value
    normalized = OBJECT_TYPE_MAP.get(key)
    if normalized is None:
        raise ValueError(f"{context}: unsupported object_type: {value}")
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


def _native_input_files(path: Path) -> tuple[Path, ...]:
    if path.is_dir():
        files = tuple(
            sorted(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file()
                and candidate.suffix.lower() in NATIVE_SUPPORTED_SUFFIXES
            )
        )
        if not files:
            raise ValueError(
                f"No supported Waymo Motion files found under {path}. "
                f"Supported suffixes: {', '.join(sorted(NATIVE_SUPPORTED_SUFFIXES))}"
            )
        return files
    if not path.exists():
        raise FileNotFoundError(f"Waymo Motion input does not exist: {path}")
    if path.suffix.lower() not in NATIVE_SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported Waymo Motion input suffix: {path.suffix}. "
            f"Supported suffixes: {', '.join(sorted(NATIVE_SUPPORTED_SUFFIXES))}"
        )
    return (path,)


def _load_native_motion_file(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    suffix = path.suffix.lower()
    if suffix in NATIVE_JSON_SUFFIXES:
        return _load_motion_json(path, max_scenarios=max_scenarios)
    if suffix in NATIVE_JSONL_SUFFIXES:
        return _load_motion_jsonl(path, max_scenarios=max_scenarios)
    if suffix in NATIVE_PROTO_SUFFIXES:
        return _load_motion_proto(path)
    if suffix in NATIVE_TFRECORD_SUFFIXES:
        return _load_motion_tfrecord(path, max_scenarios=max_scenarios)
    raise ValueError(f"Unsupported Waymo Motion input suffix: {path.suffix}")


def _load_motion_json(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mappings = _scenario_mappings_from_payload(payload, path)
    if max_scenarios is not None:
        mappings = mappings[:max_scenarios]
    return [
        _scenario_from_waymo_mapping(mapping, source=f"waymo_motion_json:{path.name}")
        for mapping in mappings
    ]


def _load_motion_jsonl(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    scenarios: list[Scenario] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if max_scenarios is not None and len(scenarios) >= max_scenarios:
                break
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            for mapping in _scenario_mappings_from_payload(payload, path):
                scenarios.append(
                    _scenario_from_waymo_mapping(
                        mapping,
                        source=f"waymo_motion_jsonl:{path.name}:{line_number}",
                    )
                )
                if max_scenarios is not None and len(scenarios) >= max_scenarios:
                    break
    return scenarios


def _scenario_mappings_from_payload(payload: Any, path: Path) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        mappings = payload
    elif isinstance(payload, dict):
        nested = _field(payload, "scenarios")
        if nested is None:
            nested = _field(payload, "scenario")
        mappings = nested if nested is not None else [payload]
    else:
        raise ValueError(f"{path}: expected Waymo Scenario JSON object or list")

    if not isinstance(mappings, list):
        mappings = [mappings]
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            raise ValueError(f"{path}: scenario entry {index} is not a JSON object")
    return mappings


def _scenario_from_waymo_mapping(
    mapping: dict[str, Any],
    source: str,
) -> Scenario:
    scenario_id = str(
        _required_field(mapping, ("scenario_id", "scenarioId"), "scenario")
    )
    tracks_payload = _required_list_field(mapping, ("tracks",), scenario_id)
    timestamps = _timestamps(mapping)
    sdc_track_index = _optional_int_field(
        mapping,
        ("sdc_track_index", "sdcTrackIndex"),
        f"scenario {scenario_id}",
    )

    tracks: list[AgentTrack] = []
    for track_index, track_payload in enumerate(tracks_payload):
        if not isinstance(track_payload, dict):
            raise ValueError(f"scenario {scenario_id}: track {track_index} is not an object")
        track_id = _track_id(track_payload, track_index)
        object_type = _object_type_value(
            _field(track_payload, "object_type", "objectType", default="TYPE_OTHER"),
            f"scenario {scenario_id} track {track_id}",
        )
        states = _states_from_waymo_track(
            track_payload,
            timestamps=timestamps,
            scenario_id=scenario_id,
            track_id=track_id,
        )
        if states:
            tracks.append(
                AgentTrack(
                    agent_id=track_id,
                    agent_type=object_type,
                    states=tuple(states),
                )
            )

    if not tracks:
        raise ValueError(f"scenario {scenario_id}: no valid tracks found")

    ego_track_id = None
    if sdc_track_index is not None:
        if sdc_track_index < 0 or sdc_track_index >= len(tracks_payload):
            raise ValueError(
                f"scenario {scenario_id}: sdc_track_index {sdc_track_index} "
                "is outside the tracks array"
            )
        ego_track_id = _track_id(tracks_payload[sdc_track_index], sdc_track_index)

    return Scenario(
        scenario_id=scenario_id,
        source=str(_field(mapping, "source", default=source)),
        ego_track_id=ego_track_id,
        tags=_waymo_tags(mapping),
        tracks=tuple(sorted(tracks, key=lambda track: track.agent_id)),
    )


def _timestamps(mapping: dict[str, Any]) -> tuple[float, ...]:
    values = _field(mapping, "timestamps_seconds", "timestampsSeconds", default=[])
    if not isinstance(values, list):
        raise ValueError("scenario timestamps must be a list")
    return tuple(_float_value(value, "scenario timestamp") for value in values)


def _states_from_waymo_track(
    track_payload: dict[str, Any],
    timestamps: tuple[float, ...],
    scenario_id: str,
    track_id: str,
) -> list[State]:
    states_payload = _field(track_payload, "states", default=[])
    if not isinstance(states_payload, list):
        raise ValueError(f"scenario {scenario_id} track {track_id}: states must be a list")

    states: list[State] = []
    for state_index, state_payload in enumerate(states_payload):
        if not isinstance(state_payload, dict):
            raise ValueError(
                f"scenario {scenario_id} track {track_id}: "
                f"state {state_index} is not an object"
            )
        if not _bool_field(state_payload, ("valid",), default=True):
            continue
        context = f"scenario {scenario_id} track {track_id} state {state_index}"
        states.append(
            State(
                t=timestamps[state_index] if state_index < len(timestamps) else float(state_index),
                x=_float_value(
                    _required_field(state_payload, ("center_x", "centerX"), context),
                    f"{context} center_x",
                ),
                y=_float_value(
                    _required_field(state_payload, ("center_y", "centerY"), context),
                    f"{context} center_y",
                ),
                vx=_float_value(
                    _field(state_payload, "velocity_x", "velocityX", default=0.0),
                    f"{context} velocity_x",
                ),
                vy=_float_value(
                    _field(state_payload, "velocity_y", "velocityY", default=0.0),
                    f"{context} velocity_y",
                ),
            )
        )
    return states


def _waymo_tags(mapping: dict[str, Any]) -> tuple[str, ...]:
    tags = set(_parse_tags(str(_field(mapping, "tags", default=""))))
    if _field(mapping, "objects_of_interest", "objectsOfInterest", default=[]):
        tags.add("objects_of_interest")
    if _field(mapping, "tracks_to_predict", "tracksToPredict", default=[]):
        tags.add("tracks_to_predict")
    if _field(mapping, "dynamic_map_states", "dynamicMapStates", default=[]):
        tags.add("traffic_signal_context")
    if _field(mapping, "map_features", "mapFeatures", default=[]):
        tags.add("map_context")
    return tuple(sorted(tags))


def _load_motion_proto(path: Path) -> list[Scenario]:
    scenario_pb2, message_to_dict = _waymo_proto_helpers()
    scenario = scenario_pb2.Scenario()
    scenario.ParseFromString(path.read_bytes())
    mapping = message_to_dict(scenario, preserving_proto_field_name=True)
    return [_scenario_from_waymo_mapping(mapping, source=f"waymo_motion_proto:{path.name}")]


def _load_motion_tfrecord(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    scenario_pb2, message_to_dict = _waymo_proto_helpers()
    try:
        import tensorflow as tf  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Reading Waymo Motion TFRecord files requires optional package "
            f"`{OPTIONAL_TF_PACKAGE}`. JSON ingestion works without it."
        ) from exc

    scenarios: list[Scenario] = []
    for record_index, record in enumerate(tf.data.TFRecordDataset(str(path))):
        if max_scenarios is not None and len(scenarios) >= max_scenarios:
            break
        scenario = scenario_pb2.Scenario()
        scenario.ParseFromString(bytes(record.numpy()))
        mapping = message_to_dict(scenario, preserving_proto_field_name=True)
        scenarios.append(
            _scenario_from_waymo_mapping(
                mapping,
                source=f"waymo_motion_tfrecord:{path.name}:{record_index}",
            )
        )
    return scenarios


def _waymo_proto_helpers() -> tuple[Any, Any]:
    try:
        from google.protobuf.json_format import MessageToDict
        from waymo_open_dataset.protos import scenario_pb2
    except ImportError as exc:
        raise RuntimeError(
            "Reading binary Waymo Motion protobuf inputs requires optional "
            f"package `{OPTIONAL_PACKAGE}`. Use protobuf-shaped JSON for the "
            "dependency-free path."
        ) from exc
    return scenario_pb2, MessageToDict


def _field(mapping: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in mapping:
            return mapping[name]
    return default


def _required_field(
    mapping: dict[str, Any],
    names: tuple[str, ...],
    context: str,
) -> Any:
    value = _field(mapping, *names)
    if value is None or value == "":
        raise ValueError(f"{context}: missing required field: {names[0]}")
    return value


def _required_list_field(
    mapping: dict[str, Any],
    names: tuple[str, ...],
    context: str,
) -> list[Any]:
    value = _required_field(mapping, names, context)
    if not isinstance(value, list):
        raise ValueError(f"{context}: expected list field: {names[0]}")
    return value


def _optional_int_field(
    mapping: dict[str, Any],
    names: tuple[str, ...],
    context: str,
) -> int | None:
    value = _field(mapping, *names)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context}: expected integer field: {names[0]}") from exc


def _track_id(track_payload: dict[str, Any], track_index: int) -> str:
    value = _field(track_payload, "id", default=track_index)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _bool_field(
    mapping: dict[str, Any],
    names: tuple[str, ...],
    default: bool,
) -> bool:
    value = _field(mapping, *names)
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
            return False
    raise ValueError(f"expected boolean value for {names[0]}")


def _float_value(value: Any, context: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context}: expected numeric value") from exc
