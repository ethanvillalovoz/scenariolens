from __future__ import annotations

import csv
import json
import struct
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
WAYMO_MAP_PROTO_URL = (
    "https://github.com/waymo-research/waymo-open-dataset/blob/master/"
    "src/waymo_open_dataset/protos/map.proto"
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
NATIVE_TFRECORD_SHARD_MARKERS = (".tfrecord-", ".tfrecords-")
NATIVE_SUPPORTED_SUFFIXES = (
    NATIVE_JSON_SUFFIXES
    | NATIVE_JSONL_SUFFIXES
    | NATIVE_PROTO_SUFFIXES
    | NATIVE_TFRECORD_SUFFIXES
)
NATIVE_SUPPORTED_INPUT_PATTERNS = tuple(
    sorted(NATIVE_SUPPORTED_SUFFIXES | {".tfrecord-*-of-*"})
)
MAX_MAP_FEATURES_PER_SCENARIO = 240
MAX_LINK_CLOSURE_FEATURES_PER_SCENARIO = 240
MAX_LINK_CLOSURE_HOPS = 5
MAX_MAP_POINTS_PER_FEATURE = 80

TRAFFIC_SIGNAL_STATE_NAMES = {
    0: "LANE_STATE_UNKNOWN",
    1: "LANE_STATE_ARROW_STOP",
    2: "LANE_STATE_ARROW_CAUTION",
    3: "LANE_STATE_ARROW_GO",
    4: "LANE_STATE_STOP",
    5: "LANE_STATE_CAUTION",
    6: "LANE_STATE_GO",
    7: "LANE_STATE_FLASHING_STOP",
    8: "LANE_STATE_FLASHING_CAUTION",
}
LANE_TYPE_NAMES = {
    0: "TYPE_UNDEFINED",
    1: "TYPE_FREEWAY",
    2: "TYPE_SURFACE_STREET",
    3: "TYPE_BIKE_LANE",
}

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


@dataclass(frozen=True)
class WaymoMotionSliceReport:
    """Preflight summary for a local Waymo Motion slice path."""

    input_path: str
    exists: bool
    is_directory: bool
    file_count: int
    supported_file_count: int
    unsupported_file_count: int
    total_bytes: int
    supported_suffix_counts: dict[str, int]
    unsupported_suffix_counts: dict[str, int]
    sample_supported_files: tuple[str, ...]
    optional_package_available: bool
    tensorflow_available: bool
    notes: tuple[str, ...]


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
            "Native Waymo Motion ingestion supports protobuf-shaped JSON, binary "
            "Scenario protos, and TFRecord shards without extra dependencies."
        ),
    )


def inspect_waymo_motion_slice(
    input_path: str | Path,
    sample_limit: int = 8,
) -> WaymoMotionSliceReport:
    """Inspect a local Waymo Motion slice before ingestion."""

    path = Path(input_path)
    optional_package_available = find_spec(OPTIONAL_PACKAGE) is not None
    tensorflow_available = find_spec(OPTIONAL_TF_PACKAGE) is not None

    if not path.exists():
        return WaymoMotionSliceReport(
            input_path=str(path),
            exists=False,
            is_directory=False,
            file_count=0,
            supported_file_count=0,
            unsupported_file_count=0,
            total_bytes=0,
            supported_suffix_counts={},
            unsupported_suffix_counts={},
            sample_supported_files=(),
            optional_package_available=optional_package_available,
            tensorflow_available=tensorflow_available,
            notes=("Input path does not exist.",),
        )

    files = _all_files(path)
    supported_files: list[Path] = []
    supported_suffix_counts: dict[str, int] = {}
    unsupported_suffix_counts: dict[str, int] = {}
    total_bytes = 0

    for file_path in files:
        total_bytes += file_path.stat().st_size
        suffix = _suffix_label(file_path)
        if is_native_motion_file(file_path):
            supported_files.append(file_path)
            supported_suffix_counts[suffix] = supported_suffix_counts.get(suffix, 0) + 1
        else:
            unsupported_suffix_counts[suffix] = unsupported_suffix_counts.get(suffix, 0) + 1

    notes = _preflight_notes(
        supported_suffix_counts=supported_suffix_counts,
        supported_file_count=len(supported_files),
        optional_package_available=optional_package_available,
        tensorflow_available=tensorflow_available,
    )

    return WaymoMotionSliceReport(
        input_path=str(path),
        exists=True,
        is_directory=path.is_dir(),
        file_count=len(files),
        supported_file_count=len(supported_files),
        unsupported_file_count=len(files) - len(supported_files),
        total_bytes=total_bytes,
        supported_suffix_counts=dict(sorted(supported_suffix_counts.items())),
        unsupported_suffix_counts=dict(sorted(unsupported_suffix_counts.items())),
        sample_supported_files=tuple(
            _display_path(file_path, root=path) for file_path in supported_files[:sample_limit]
        ),
        optional_package_available=optional_package_available,
        tensorflow_available=tensorflow_available,
        notes=notes,
    )


def waymo_motion_slice_ready(report: WaymoMotionSliceReport) -> bool:
    """Return whether the inspected slice is ingestable in this environment."""

    return report.exists and report.supported_file_count > 0


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
    public Scenario proto field names, plus binary Scenario protobuf and
    TFRecord shard files.
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


def native_motion_format_label(path: str | Path) -> str | None:
    """Return the supported input format label for a native Motion file path."""

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in NATIVE_JSON_SUFFIXES:
        return suffix
    if suffix in NATIVE_JSONL_SUFFIXES:
        return suffix
    if suffix in NATIVE_PROTO_SUFFIXES:
        return suffix
    if suffix in NATIVE_TFRECORD_SUFFIXES:
        return suffix
    if any(marker in file_path.name.lower() for marker in NATIVE_TFRECORD_SHARD_MARKERS):
        return ".tfrecord"
    return None


def is_native_motion_file(path: str | Path) -> bool:
    """Return whether a path looks like a supported native Motion input file."""

    return native_motion_format_label(path) is not None


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
                if candidate.is_file() and is_native_motion_file(candidate)
            )
        )
        if not files:
            raise ValueError(
                f"No supported Waymo Motion files found under {path}. "
                f"Supported suffixes: {', '.join(NATIVE_SUPPORTED_INPUT_PATTERNS)}"
            )
        return files
    if not path.exists():
        raise FileNotFoundError(f"Waymo Motion input does not exist: {path}")
    if not is_native_motion_file(path):
        raise ValueError(
            f"Unsupported Waymo Motion input suffix: {path.suffix}. "
            f"Supported suffixes: {', '.join(NATIVE_SUPPORTED_INPUT_PATTERNS)}"
        )
    return (path,)


def _all_files(path: Path) -> tuple[Path, ...]:
    if path.is_dir():
        return tuple(sorted(candidate for candidate in path.rglob("*") if candidate.is_file()))
    return (path,)


def _suffix_label(path: Path) -> str:
    return native_motion_format_label(path) or path.suffix.lower() or "(no suffix)"


def _display_path(path: Path, root: Path) -> str:
    if root.is_dir():
        return path.relative_to(root).as_posix()
    return path.name


def _preflight_notes(
    supported_suffix_counts: dict[str, int],
    supported_file_count: int,
    optional_package_available: bool,
    tensorflow_available: bool,
) -> tuple[str, ...]:
    notes: list[str] = []
    if supported_file_count == 0:
        notes.append(
            "No supported Waymo Motion files found. Supported suffixes: "
            + ", ".join(NATIVE_SUPPORTED_INPUT_PATTERNS)
        )
    if any(suffix in supported_suffix_counts for suffix in NATIVE_JSON_SUFFIXES):
        notes.append("JSON inputs can be ingested without optional packages.")
    if any(suffix in supported_suffix_counts for suffix in NATIVE_JSONL_SUFFIXES):
        notes.append("JSONL/NDJSON inputs can be ingested without optional packages.")
    if any(suffix in supported_suffix_counts for suffix in NATIVE_PROTO_SUFFIXES):
        notes.append("Binary Scenario protobuf inputs use the built-in lightweight parser.")
    if any(suffix in supported_suffix_counts for suffix in NATIVE_TFRECORD_SUFFIXES):
        notes.append("TFRecord inputs use the built-in lightweight reader.")
    return tuple(notes)


def _load_native_motion_file(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    format_label = native_motion_format_label(path)
    if format_label in NATIVE_JSON_SUFFIXES:
        return _load_motion_json(path, max_scenarios=max_scenarios)
    if format_label in NATIVE_JSONL_SUFFIXES:
        return _load_motion_jsonl(path, max_scenarios=max_scenarios)
    if format_label in NATIVE_PROTO_SUFFIXES:
        return _load_motion_proto(path)
    if format_label in NATIVE_TFRECORD_SUFFIXES:
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
    current_time_index = _optional_int_field(
        mapping,
        ("current_time_index", "currentTimeIndex"),
        f"scenario {scenario_id}",
    )

    tracks: list[AgentTrack] = []
    track_id_by_index: dict[int, str] = {}
    for track_index, track_payload in enumerate(tracks_payload):
        if not isinstance(track_payload, dict):
            raise ValueError(f"scenario {scenario_id}: track {track_index} is not an object")
        track_id = _track_id(track_payload, track_index)
        track_id_by_index[track_index] = track_id
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
        metadata=_waymo_metadata(
            mapping=mapping,
            track_id_by_index=track_id_by_index,
            sdc_track_index=sdc_track_index,
            current_time_index=current_time_index,
        ),
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


def _waymo_metadata(
    mapping: dict[str, Any],
    track_id_by_index: dict[int, str],
    sdc_track_index: int | None,
    current_time_index: int | None,
) -> dict[str, object]:
    tracks_to_predict = _field(mapping, "tracks_to_predict", "tracksToPredict", default=[])
    prediction_track_ids = tuple(
        track_id
        for prediction in tracks_to_predict
        if isinstance(prediction, dict)
        if (
            track_id := _prediction_track_id(
                prediction,
                track_id_by_index=track_id_by_index,
            )
        )
        is not None
    )

    objects_of_interest = _field(
        mapping,
        "objects_of_interest",
        "objectsOfInterest",
        default=[],
    )
    object_track_ids = tuple(
        str(value) for value in objects_of_interest if value is not None
    )

    metadata: dict[str, object] = {}
    if sdc_track_index is not None:
        metadata["waymo_sdc_track_index"] = sdc_track_index
    if current_time_index is not None:
        metadata["waymo_current_time_index"] = current_time_index
    if prediction_track_ids:
        metadata["waymo_tracks_to_predict_track_ids"] = list(prediction_track_ids)
    if object_track_ids:
        metadata["waymo_objects_of_interest_track_ids"] = list(object_track_ids)
    map_features = _waymo_map_features(mapping)
    if map_features:
        metadata["waymo_map_features"] = map_features
        metadata["waymo_map_summary"] = _waymo_map_summary(map_features)
    dynamic_map_summary = _waymo_dynamic_map_summary(mapping)
    if dynamic_map_summary["timestep_count"]:
        metadata["waymo_dynamic_map_summary"] = dynamic_map_summary
    return metadata


def _prediction_track_id(
    prediction: dict[str, Any],
    track_id_by_index: dict[int, str],
) -> str | None:
    track_index = _field(prediction, "track_index", "trackIndex")
    if track_index is None:
        return None
    try:
        return track_id_by_index[int(track_index)]
    except (KeyError, TypeError, ValueError):
        return None


def _waymo_map_features(mapping: dict[str, Any]) -> list[dict[str, object]]:
    payload = _field(mapping, "map_features", "mapFeatures", default=[])
    if not isinstance(payload, list):
        return []
    features: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        feature = _map_feature_from_mapping(item)
        if feature is not None:
            features.append(feature)
    return _cap_map_features_with_lane_link_closure(features)


def _cap_map_features_with_lane_link_closure(
    features: list[dict[str, object]],
) -> list[dict[str, object]]:
    if len(features) <= MAX_MAP_FEATURES_PER_SCENARIO:
        return features

    primary = features[:MAX_MAP_FEATURES_PER_SCENARIO]
    by_id = {
        feature_id: feature
        for feature in features
        if (feature_id := _map_feature_id(feature)) is not None
    }
    selected_ids = {
        feature_id
        for feature in primary
        if (feature_id := _map_feature_id(feature)) is not None
    }
    closure_features: list[dict[str, object]] = []
    frontier = primary
    for _ in range(MAX_LINK_CLOSURE_HOPS):
        next_frontier: list[dict[str, object]] = []
        for feature in frontier:
            for target_id in _lane_link_target_ids(feature):
                if target_id in selected_ids or target_id not in by_id:
                    continue
                linked_feature = by_id[target_id]
                closure_features.append(linked_feature)
                selected_ids.add(target_id)
                next_frontier.append(linked_feature)
                if len(closure_features) >= MAX_LINK_CLOSURE_FEATURES_PER_SCENARIO:
                    return primary + closure_features
        if not next_frontier:
            break
        frontier = next_frontier
    if not closure_features:
        return primary
    return primary + closure_features


def _map_feature_id(feature: dict[str, object]) -> str | None:
    feature_id = feature.get("feature_id")
    return str(feature_id) if feature_id is not None else None


def _lane_link_target_ids(feature: dict[str, object]) -> tuple[str, ...]:
    if feature.get("kind") != "lane":
        return ()
    targets: list[str] = []
    for field_name in ("entry_lanes", "exit_lanes"):
        for value in _as_list(feature.get(field_name)):
            targets.append(str(value))
    return tuple(targets)


def _waymo_map_summary(map_features: list[dict[str, object]]) -> dict[str, object]:
    kind_counts: dict[str, int] = {}
    lane_type_counts: dict[str, int] = {}
    speed_limits: list[float] = []
    entry_link_count = 0
    exit_link_count = 0
    neighbor_link_count = 0

    for feature in map_features:
        kind = str(feature.get("kind", "unknown"))
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if kind != "lane":
            continue
        lane_type = feature.get("feature_type")
        if lane_type is not None:
            lane_type_name = str(lane_type)
            lane_type_counts[lane_type_name] = lane_type_counts.get(lane_type_name, 0) + 1
        speed_limit = _optional_float(feature.get("speed_limit_mph"))
        if speed_limit is not None:
            speed_limits.append(speed_limit)
        entry_link_count += len(_as_list(feature.get("entry_lanes")))
        exit_link_count += len(_as_list(feature.get("exit_lanes")))
        neighbor_link_count += int(feature.get("left_neighbor_count", 0) or 0)
        neighbor_link_count += int(feature.get("right_neighbor_count", 0) or 0)

    lane_count = kind_counts.get("lane", 0)
    route_link_count = entry_link_count + exit_link_count + neighbor_link_count
    link_targets = {
        target_id
        for feature in map_features
        if feature.get("kind") == "lane"
        for target_id in _lane_link_target_ids(feature)
    }
    feature_ids = {
        feature_id
        for feature in map_features
        if (feature_id := _map_feature_id(feature)) is not None
    }
    return {
        "feature_count": len(map_features),
        "kind_counts": dict(sorted(kind_counts.items())),
        "lane_count": lane_count,
        "lane_type_counts": dict(sorted(lane_type_counts.items())),
        "lane_speed_limit_count": len(speed_limits),
        "mean_lane_speed_limit_mph": _mean_rounded(speed_limits),
        "entry_link_count": entry_link_count,
        "exit_link_count": exit_link_count,
        "neighbor_link_count": neighbor_link_count,
        "route_link_count": route_link_count,
        "materialized_link_target_count": len(link_targets & feature_ids),
        "has_route_context": route_link_count > 0,
    }


def _waymo_dynamic_map_summary(mapping: dict[str, Any]) -> dict[str, object]:
    payload = _field(mapping, "dynamic_map_states", "dynamicMapStates", default=[])
    if not isinstance(payload, list):
        payload = []

    state_counts: dict[str, int] = {}
    controlled_lanes: set[str] = set()
    lane_state_count = 0
    stop_point_count = 0
    observed_timestep_count = 0

    for dynamic_state in payload:
        if not isinstance(dynamic_state, dict):
            continue
        lane_states = _field(dynamic_state, "lane_states", "laneStates", default=[])
        if not isinstance(lane_states, list):
            continue
        if lane_states:
            observed_timestep_count += 1
        for lane_state in lane_states:
            if not isinstance(lane_state, dict):
                continue
            lane_state_count += 1
            lane_id = _field(lane_state, "lane", default=None)
            if lane_id is not None:
                controlled_lanes.add(str(lane_id))
            state_name = _traffic_signal_state_name(
                _field(lane_state, "state", default=None)
            )
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
            stop_point = _field(lane_state, "stop_point", "stopPoint", default=None)
            if _point_from_mapping(stop_point) is not None:
                stop_point_count += 1

    return {
        "timestep_count": len(payload),
        "observed_timestep_count": observed_timestep_count,
        "lane_state_count": lane_state_count,
        "controlled_lane_count": len(controlled_lanes),
        "stop_point_count": stop_point_count,
        "state_counts": dict(sorted(state_counts.items())),
        "stop_state_count": sum(
            count for state, count in state_counts.items() if "STOP" in state
        ),
        "caution_state_count": sum(
            count for state, count in state_counts.items() if "CAUTION" in state
        ),
        "go_state_count": sum(
            count for state, count in state_counts.items() if state.endswith("_GO")
        ),
        "unknown_state_count": state_counts.get("LANE_STATE_UNKNOWN", 0),
    }


def _map_feature_from_mapping(mapping: dict[str, Any]) -> dict[str, object] | None:
    feature_id = _field(mapping, "id", default=None)
    feature_specs = (
        ("lane", "lane", ("polyline",), "type"),
        ("road_line", "roadLine", ("polyline",), "type"),
        ("road_edge", "roadEdge", ("polyline",), "type"),
        ("crosswalk", "crosswalk", ("polygon",), None),
        ("speed_bump", "speedBump", ("polygon",), None),
        ("driveway", "driveway", ("polygon",), None),
    )
    for kind, camel_name, point_fields, type_field in feature_specs:
        payload = _field(mapping, kind, camel_name, default=None)
        if not isinstance(payload, dict):
            continue
        points = _points_from_mapping(payload, point_fields)
        if len(points) < 2:
            return None
        feature: dict[str, object] = {
            "kind": kind,
            "points": points[:MAX_MAP_POINTS_PER_FEATURE],
        }
        if feature_id is not None:
            feature["feature_id"] = str(feature_id)
        if type_field is not None:
            feature_type = _field(payload, type_field, default=None)
            if feature_type is not None:
                feature["feature_type"] = (
                    _lane_type_name(feature_type)
                    if kind == "lane"
                    else str(feature_type)
                )
        if kind == "lane":
            speed_limit = _optional_float(
                _field(payload, "speed_limit_mph", "speedLimitMph", default=None)
            )
            if speed_limit is not None:
                feature["speed_limit_mph"] = round(speed_limit, 3)
            interpolating = _optional_bool(
                _field(payload, "interpolating", default=None)
            )
            if interpolating is not None:
                feature["interpolating"] = interpolating
            entry_lanes = _int_list_field(payload, "entry_lanes", "entryLanes")
            if entry_lanes:
                feature["entry_lanes"] = entry_lanes
            exit_lanes = _int_list_field(payload, "exit_lanes", "exitLanes")
            if exit_lanes:
                feature["exit_lanes"] = exit_lanes
            left_neighbor_count = _list_length_field(
                payload,
                "left_neighbors",
                "leftNeighbors",
            )
            if left_neighbor_count:
                feature["left_neighbor_count"] = left_neighbor_count
            right_neighbor_count = _list_length_field(
                payload,
                "right_neighbors",
                "rightNeighbors",
            )
            if right_neighbor_count:
                feature["right_neighbor_count"] = right_neighbor_count
        return feature
    return None


def _points_from_mapping(
    mapping: dict[str, Any],
    point_fields: tuple[str, ...],
) -> list[list[float]]:
    values: Any = None
    for field_name in point_fields:
        values = _field(mapping, field_name, default=None)
        if values is not None:
            break
    if not isinstance(values, list):
        return []
    points: list[list[float]] = []
    for point in values:
        parsed = _point_from_mapping(point)
        if parsed is not None:
            points.append(parsed)
    return points


def _point_from_mapping(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        x_value = _field(value, "x", default=None)
        y_value = _field(value, "y", default=None)
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        x_value = value[0]
        y_value = value[1]
    else:
        return None
    if x_value is None or y_value is None:
        return None
    try:
        return [round(float(x_value), 3), round(float(y_value), 3)]
    except (TypeError, ValueError):
        return None


def _traffic_signal_state_name(value: Any) -> str:
    if value is None or value == "":
        return "LANE_STATE_UNKNOWN"
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return "LANE_STATE_UNKNOWN"
        if stripped.isdigit():
            return TRAFFIC_SIGNAL_STATE_NAMES.get(int(stripped), f"LANE_STATE_{stripped}")
        return stripped.upper()
    try:
        return TRAFFIC_SIGNAL_STATE_NAMES.get(int(value), f"LANE_STATE_{int(value)}")
    except (TypeError, ValueError):
        return "LANE_STATE_UNKNOWN"


def _lane_type_name(value: Any) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return LANE_TYPE_NAMES.get(int(stripped), f"TYPE_LANE_{stripped}")
        return stripped
    try:
        return LANE_TYPE_NAMES.get(int(value), f"TYPE_LANE_{int(value)}")
    except (TypeError, ValueError):
        return str(value)


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
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
    return None


def _int_list_field(mapping: dict[str, Any], *names: str) -> list[int]:
    values = _field(mapping, *names, default=[])
    result: list[int] = []
    for value in _as_list(values):
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _list_length_field(mapping: dict[str, Any], *names: str) -> int:
    return len(_as_list(_field(mapping, *names, default=[])))


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _mean_rounded(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _load_motion_proto(path: Path) -> list[Scenario]:
    mapping = _scenario_mapping_from_proto_bytes(path.read_bytes())
    return [_scenario_from_waymo_mapping(mapping, source=f"waymo_motion_proto:{path.name}")]


def _load_motion_tfrecord(path: Path, max_scenarios: int | None = None) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for record_index, record in enumerate(_iter_tfrecord_records(path)):
        if max_scenarios is not None and len(scenarios) >= max_scenarios:
            break
        mapping = _scenario_mapping_from_proto_bytes(record)
        scenarios.append(
            _scenario_from_waymo_mapping(
                mapping,
                source=f"waymo_motion_tfrecord:{path.name}:{record_index}",
            )
        )
    return scenarios


def _iter_tfrecord_records(path: Path):
    with path.open("rb") as handle:
        record_index = 0
        while True:
            header = handle.read(12)
            if not header:
                break
            if len(header) != 12:
                raise ValueError(f"{path}: truncated TFRecord header at record {record_index}")
            length = struct.unpack("<Q", header[:8])[0]
            data = handle.read(length)
            if len(data) != length:
                raise ValueError(f"{path}: truncated TFRecord payload at record {record_index}")
            footer = handle.read(4)
            if len(footer) != 4:
                raise ValueError(f"{path}: truncated TFRecord footer at record {record_index}")
            yield data
            record_index += 1


def _scenario_mapping_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {"tracks": []}
    timestamps: list[float] = []
    objects_of_interest: list[int] = []
    tracks_to_predict: list[dict[str, int]] = []
    map_features: list[dict[str, Any]] = []
    dynamic_map_states: list[dict[str, Any]] = []

    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1:
            if wire_type == 1:
                timestamps.append(_wire_double(value))
            elif wire_type == 2:
                timestamps.extend(_packed_doubles(value))
        elif field_number == 2 and wire_type == 2:
            mapping["tracks"].append(_track_mapping_from_proto_bytes(value))
        elif field_number == 4:
            if wire_type == 0:
                objects_of_interest.append(value)
            elif wire_type == 2:
                objects_of_interest.extend(_packed_varints(value))
        elif field_number == 5 and wire_type == 2:
            mapping["scenario_id"] = value.decode("utf-8")
        elif field_number == 6 and wire_type == 0:
            mapping["sdc_track_index"] = value
        elif field_number == 7 and wire_type == 2:
            dynamic_map_states.append(_dynamic_map_state_from_proto_bytes(value))
        elif field_number == 8 and wire_type == 2:
            feature = _map_feature_mapping_from_proto_bytes(value)
            if feature is not None:
                map_features.append(feature)
        elif field_number == 10 and wire_type == 0:
            mapping["current_time_index"] = value
        elif field_number == 11 and wire_type == 2:
            tracks_to_predict.append(_required_prediction_from_proto_bytes(value))

    mapping["timestamps_seconds"] = timestamps
    if objects_of_interest:
        mapping["objects_of_interest"] = objects_of_interest
    if tracks_to_predict:
        mapping["tracks_to_predict"] = tracks_to_predict
    if dynamic_map_states:
        mapping["dynamic_map_states"] = dynamic_map_states
    if map_features:
        mapping["map_features"] = map_features
    return mapping


def _track_mapping_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {"states": []}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 0:
            mapping["id"] = value
        elif field_number == 2 and wire_type == 0:
            mapping["object_type"] = value
        elif field_number == 3 and wire_type == 2:
            mapping["states"].append(_state_mapping_from_proto_bytes(value))
    return mapping


def _state_mapping_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 2 and wire_type == 1:
            mapping["center_x"] = _wire_double(value)
        elif field_number == 3 and wire_type == 1:
            mapping["center_y"] = _wire_double(value)
        elif field_number == 9 and wire_type == 5:
            mapping["velocity_x"] = _wire_float(value)
        elif field_number == 10 and wire_type == 5:
            mapping["velocity_y"] = _wire_float(value)
        elif field_number == 11 and wire_type == 0:
            mapping["valid"] = bool(value)
    return mapping


def _required_prediction_from_proto_bytes(data: bytes) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 0:
            mapping["track_index"] = value
    return mapping


def _dynamic_map_state_from_proto_bytes(data: bytes) -> dict[str, Any]:
    lane_states: list[dict[str, Any]] = []
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 2:
            lane_states.append(_traffic_signal_lane_state_from_proto_bytes(value))
    return {"lane_states": lane_states}


def _traffic_signal_lane_state_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 0:
            mapping["lane"] = value
        elif field_number == 2 and wire_type == 0:
            mapping["state"] = _traffic_signal_state_name(value)
        elif field_number == 3 and wire_type == 2:
            mapping["stop_point"] = _map_point_from_proto_bytes(value)
    return mapping


def _map_feature_mapping_from_proto_bytes(data: bytes) -> dict[str, Any] | None:
    mapping: dict[str, Any] = {}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 0:
            mapping["id"] = value
        elif field_number == 3 and wire_type == 2:
            mapping["lane"] = _lane_mapping_from_proto_bytes(value)
        elif field_number == 4 and wire_type == 2:
            mapping["road_line"] = _line_mapping_from_proto_bytes(value)
        elif field_number == 5 and wire_type == 2:
            mapping["road_edge"] = _line_mapping_from_proto_bytes(value)
        elif field_number == 8 and wire_type == 2:
            mapping["crosswalk"] = {"polygon": _polygon_from_proto_bytes(value)}
        elif field_number == 9 and wire_type == 2:
            mapping["speed_bump"] = {"polygon": _polygon_from_proto_bytes(value)}
        elif field_number == 10 and wire_type == 2:
            mapping["driveway"] = {"polygon": _polygon_from_proto_bytes(value)}
    return mapping if _map_feature_from_mapping(mapping) is not None else None


def _lane_mapping_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {"polyline": []}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 1:
            mapping["speed_limit_mph"] = _wire_double(value)
        elif field_number == 2 and wire_type == 0:
            mapping["type"] = value
        elif field_number == 3 and wire_type == 0:
            mapping["interpolating"] = bool(value)
        elif field_number == 8 and wire_type == 2:
            mapping["polyline"].append(_map_point_from_proto_bytes(value))
        elif field_number == 9:
            _append_varints(mapping, "entry_lanes", wire_type, value)
        elif field_number == 10:
            _append_varints(mapping, "exit_lanes", wire_type, value)
        elif field_number == 11 and wire_type == 2:
            mapping.setdefault("left_neighbors", []).append({})
        elif field_number == 12 and wire_type == 2:
            mapping.setdefault("right_neighbors", []).append({})
    return mapping


def _line_mapping_from_proto_bytes(data: bytes) -> dict[str, Any]:
    mapping: dict[str, Any] = {"polyline": []}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 0:
            mapping["type"] = value
        elif field_number == 2 and wire_type == 2:
            mapping["polyline"].append(_map_point_from_proto_bytes(value))
    return mapping


def _polygon_from_proto_bytes(data: bytes) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 2:
            points.append(_map_point_from_proto_bytes(value))
    return points


def _map_point_from_proto_bytes(data: bytes) -> dict[str, float]:
    point: dict[str, float] = {}
    for field_number, wire_type, value in _iter_proto_fields(data):
        if field_number == 1 and wire_type == 1:
            point["x"] = _wire_double(value)
        elif field_number == 2 and wire_type == 1:
            point["y"] = _wire_double(value)
    return point


def _iter_proto_fields(data: bytes):
    offset = 0
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        field_number = key >> 3
        wire_type = key & 0b111
        if wire_type == 0:
            value, offset = _read_varint(data, offset)
        elif wire_type == 1:
            if offset + 8 > len(data):
                raise ValueError("truncated protobuf fixed64 field")
            value = data[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            length, offset = _read_varint(data, offset)
            if offset + length > len(data):
                raise ValueError("truncated protobuf length-delimited field")
            value = data[offset : offset + length]
            offset += length
        elif wire_type == 5:
            if offset + 4 > len(data):
                raise ValueError("truncated protobuf fixed32 field")
            value = data[offset : offset + 4]
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
        yield field_number, wire_type, value


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
        if shift >= 64:
            raise ValueError("protobuf varint is too long")
    raise ValueError("truncated protobuf varint")


def _wire_double(value: bytes) -> float:
    if len(value) != 8:
        raise ValueError("protobuf double field must be 8 bytes")
    return struct.unpack("<d", value)[0]


def _wire_float(value: bytes) -> float:
    if len(value) != 4:
        raise ValueError("protobuf float field must be 4 bytes")
    return struct.unpack("<f", value)[0]


def _packed_doubles(value: bytes) -> tuple[float, ...]:
    if len(value) % 8:
        raise ValueError("packed protobuf double field has invalid length")
    return tuple(_wire_double(value[index : index + 8]) for index in range(0, len(value), 8))


def _packed_varints(value: bytes) -> tuple[int, ...]:
    values: list[int] = []
    offset = 0
    while offset < len(value):
        item, offset = _read_varint(value, offset)
        values.append(item)
    return tuple(values)


def _append_varints(
    mapping: dict[str, Any],
    key: str,
    wire_type: int,
    value: int | bytes,
) -> None:
    target = mapping.setdefault(key, [])
    if not isinstance(target, list):
        return
    if wire_type == 0 and isinstance(value, int):
        target.append(value)
    elif wire_type == 2 and isinstance(value, bytes):
        target.extend(_packed_varints(value))


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
