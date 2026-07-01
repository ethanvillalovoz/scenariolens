import json
import struct
import unittest
import tempfile
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    WAYMO_OPEN_CHALLENGES_URL,
    WAYMO_OPEN_DATASET_URL,
    adapter_status,
    ingest_waymo_motion,
    inspect_waymo_motion_slice,
    load_waymo_motion,
    load_normalized_motion_csv,
    save_normalized_motion_csv_as_scenarios,
    save_waymo_motion_as_scenarios,
    waymo_motion_slice_ready,
)
from scenariolens.io import load_scenarios


NORMALIZED_FIXTURE = """scenario_id,track_id,object_type,timestep,center_x,center_y,velocity_x,velocity_y,is_sdc,tags,source
waymo_like_001,sdc,TYPE_VEHICLE,0,0,0,5,0,true,unprotected_turn|pedestrian_crossing,waymo_motion_normalized_fixture
waymo_like_001,sdc,TYPE_VEHICLE,1,5,0,5,0,true,unprotected_turn|pedestrian_crossing,waymo_motion_normalized_fixture
waymo_like_001,ped_42,TYPE_PEDESTRIAN,0,4,-2,0,1,false,pedestrian_crossing,waymo_motion_normalized_fixture
waymo_like_001,ped_42,TYPE_PEDESTRIAN,1,4,-1,0,1,false,pedestrian_crossing,waymo_motion_normalized_fixture
waymo_like_002,sdc,TYPE_VEHICLE,0,0,0,7,0,true,merge_conflict,waymo_motion_normalized_fixture
waymo_like_002,veh_7,TYPE_VEHICLE,0,5,3,5,-0.5,false,merge_conflict,waymo_motion_normalized_fixture
"""

NATIVE_JSON_FIXTURE = """{
  "scenarioId": "waymo_native_001",
  "timestampsSeconds": [0.0, 0.1, 0.2],
  "sdcTrackIndex": 0,
  "objectsOfInterest": [7],
  "tracksToPredict": [{"trackIndex": 1}],
  "mapFeatures": [
    {
      "id": 1001,
      "lane": {
        "speedLimitMph": 35.0,
        "type": "TYPE_SURFACE_STREET",
        "entryLanes": [9001],
        "exitLanes": [9002],
        "leftNeighbors": [{"featureId": 1003}],
        "polyline": [
          {"x": -1.0, "y": 0.0},
          {"x": 1.0, "y": 0.0}
        ]
      }
    },
    {
      "id": 1002,
      "crosswalk": {
        "polygon": [
          {"x": -0.2, "y": -1.0},
          {"x": 0.4, "y": -1.0},
          {"x": 0.4, "y": 1.0},
          {"x": -0.2, "y": 1.0}
        ]
      }
    }
  ],
  "dynamicMapStates": [
    {
      "laneStates": [
        {
          "lane": 1001,
          "state": "LANE_STATE_STOP",
          "stopPoint": {"x": 0.5, "y": 0.0}
        }
      ]
    },
    {
      "laneStates": [
        {
          "lane": 1001,
          "state": "LANE_STATE_GO",
          "stopPoint": {"x": 0.5, "y": 0.0}
        }
      ]
    }
  ],
  "tracks": [
    {
      "id": 42,
      "objectType": "TYPE_VEHICLE",
      "states": [
        {"centerX": 0.0, "centerY": 0.0, "velocityX": 5.0, "velocityY": 0.0, "valid": true},
        {"centerX": 0.5, "centerY": 0.0, "velocityX": 5.0, "velocityY": 0.0, "valid": true},
        {"centerX": 1.0, "centerY": 0.0, "velocityX": 5.0, "velocityY": 0.0, "valid": true}
      ]
    },
    {
      "id": 7,
      "objectType": "TYPE_PEDESTRIAN",
      "states": [
        {"centerX": 0.5, "centerY": -1.0, "velocityX": 0.0, "velocityY": 1.0, "valid": true},
        {"centerX": 0.5, "centerY": -0.9, "velocityX": 0.0, "velocityY": 1.0, "valid": false},
        {"centerX": 0.5, "centerY": -0.8, "velocityX": 0.0, "velocityY": 1.0, "valid": true}
      ]
    }
  ]
}
"""

NATIVE_SNAKE_CASE_FIXTURE = """{
  "scenario_id": "waymo_native_002",
  "timestamps_seconds": [0.0],
  "sdc_track_index": 0,
  "tracks": [
    {
      "id": 1,
      "object_type": "TYPE_VEHICLE",
      "states": [
        {"center_x": 0.0, "center_y": 0.0, "velocity_x": 3.0, "velocity_y": 0.0, "valid": true}
      ]
    }
  ]
}
"""


def _jsonl(*payloads: str) -> str:
    return "\n".join(json.dumps(json.loads(payload)) for payload in payloads) + "\n"


def _key(field_number: int, wire_type: int) -> bytes:
    return _varint((field_number << 3) | wire_type)


def _varint(value: int) -> bytes:
    chunks = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            chunks.append(byte | 0x80)
        else:
            chunks.append(byte)
            return bytes(chunks)


def _length_delimited(field_number: int, payload: bytes) -> bytes:
    return _key(field_number, 2) + _varint(len(payload)) + payload


def _double(field_number: int, value: float) -> bytes:
    return _key(field_number, 1) + struct.pack("<d", value)


def _float(field_number: int, value: float) -> bytes:
    return _key(field_number, 5) + struct.pack("<f", value)


def _int32(field_number: int, value: int) -> bytes:
    return _key(field_number, 0) + _varint(value)


def _string(field_number: int, value: str) -> bytes:
    return _length_delimited(field_number, value.encode("utf-8"))


def _state_proto(x: float, y: float, vx: float, vy: float, valid: bool = True) -> bytes:
    return b"".join(
        (
            _double(2, x),
            _double(3, y),
            _float(9, vx),
            _float(10, vy),
            _int32(11, int(valid)),
        )
    )


def _track_proto(track_id: int, object_type: int, *states: bytes) -> bytes:
    return b"".join(
        (
            _int32(1, track_id),
            _int32(2, object_type),
            *(_length_delimited(3, state) for state in states),
        )
    )


def _map_point_proto(x: float, y: float) -> bytes:
    return b"".join((_double(1, x), _double(2, y)))


def _lane_proto(*points: bytes) -> bytes:
    return b"".join(
        (
            _double(1, 35.0),
            _int32(2, 2),
            *(_length_delimited(8, point) for point in points),
            _int32(9, 9001),
            _int32(10, 9002),
            _length_delimited(11, b""),
        )
    )


def _map_feature_proto(feature_id: int, lane: bytes) -> bytes:
    return b"".join((_int32(1, feature_id), _length_delimited(3, lane)))


def _traffic_signal_lane_state_proto(
    lane_id: int,
    state: int,
    stop_point: bytes,
) -> bytes:
    return b"".join(
        (
            _int32(1, lane_id),
            _int32(2, state),
            _length_delimited(3, stop_point),
        )
    )


def _dynamic_map_state_proto(*lane_states: bytes) -> bytes:
    return b"".join(_length_delimited(1, lane_state) for lane_state in lane_states)


def _scenario_proto() -> bytes:
    vehicle = _track_proto(
        10,
        1,
        _state_proto(0.0, 0.0, 5.0, 0.0),
        _state_proto(0.5, 0.0, 5.0, 0.0),
    )
    pedestrian = _track_proto(
        20,
        2,
        _state_proto(0.5, -1.0, 0.0, 1.0),
        _state_proto(0.5, -0.9, 0.0, 1.0),
    )
    prediction = _int32(1, 1)
    lane = _lane_proto(_map_point_proto(-1.0, 0.0), _map_point_proto(1.0, 0.0))
    map_feature = _map_feature_proto(1001, lane)
    signal_state = _dynamic_map_state_proto(
        _traffic_signal_lane_state_proto(1001, 4, _map_point_proto(0.5, 0.0))
    )
    return b"".join(
        (
            _double(1, 0.0),
            _double(1, 0.1),
            _length_delimited(2, vehicle),
            _length_delimited(2, pedestrian),
            _int32(4, 20),
            _string(5, "waymo_binary_fixture"),
            _int32(6, 0),
            _length_delimited(7, signal_state),
            _length_delimited(8, map_feature),
            _length_delimited(11, prediction),
        )
    )


def _tfrecord(payload: bytes) -> bytes:
    return struct.pack("<Q", len(payload)) + b"\x00\x00\x00\x00" + payload + b"\x00\x00\x00\x00"


class WaymoMotionIngestTest(unittest.TestCase):
    def test_adapter_status_documents_native_adapter(self) -> None:
        status = adapter_status()

        self.assertEqual(status.adapter_name, "waymo_motion")
        self.assertTrue(status.implemented)
        self.assertEqual(status.dataset_url, WAYMO_OPEN_DATASET_URL)
        self.assertEqual(status.challenges_url, WAYMO_OPEN_CHALLENGES_URL)
        self.assertIn("protobuf-shaped JSON", status.message)

    def test_inspect_waymo_motion_slice_reports_supported_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            motion_dir = root / "motion"
            motion_dir.mkdir()
            (motion_dir / "scenario.json").write_text(
                NATIVE_JSON_FIXTURE,
                encoding="utf-8",
            )
            (motion_dir / "README.txt").write_text("ignore me", encoding="utf-8")

            report = inspect_waymo_motion_slice(motion_dir)

        self.assertTrue(report.exists)
        self.assertTrue(report.is_directory)
        self.assertEqual(report.file_count, 2)
        self.assertEqual(report.supported_file_count, 1)
        self.assertEqual(report.unsupported_file_count, 1)
        self.assertEqual(report.supported_suffix_counts[".json"], 1)
        self.assertEqual(report.unsupported_suffix_counts[".txt"], 1)
        self.assertEqual(report.sample_supported_files, ("scenario.json",))
        self.assertTrue(waymo_motion_slice_ready(report))

    def test_inspect_waymo_motion_slice_supports_waymo_tfrecord_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shard = root / "validation.tfrecord-00007-of-00150"
            shard.write_bytes(b"placeholder")

            report = inspect_waymo_motion_slice(root)

        self.assertEqual(report.supported_file_count, 1)
        self.assertEqual(report.supported_suffix_counts[".tfrecord"], 1)
        self.assertEqual(report.sample_supported_files, ("validation.tfrecord-00007-of-00150",))
        self.assertTrue(waymo_motion_slice_ready(report))
        self.assertIn("TFRecord inputs use the built-in lightweight reader.", report.notes)

    def test_load_waymo_motion_reads_waymo_tfrecord_shard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "validation.tfrecord-00007-of-00150"
            path.write_bytes(_tfrecord(_scenario_proto()))

            scenarios = load_waymo_motion(path)

        self.assertEqual(len(scenarios), 1)
        scenario = scenarios[0]
        self.assertEqual(scenario.scenario_id, "waymo_binary_fixture")
        self.assertEqual(scenario.ego_track_id, "10")
        self.assertIn("objects_of_interest", scenario.tags)
        self.assertIn("tracks_to_predict", scenario.tags)
        self.assertEqual(scenario.metadata["waymo_tracks_to_predict_track_ids"], ["20"])
        self.assertEqual(scenario.metadata["waymo_objects_of_interest_track_ids"], ["20"])
        self.assertEqual(scenario.metadata["waymo_map_features"][0]["kind"], "lane")
        self.assertEqual(scenario.metadata["waymo_map_summary"]["route_link_count"], 3)
        self.assertEqual(
            scenario.metadata["waymo_dynamic_map_summary"]["state_counts"],
            {"LANE_STATE_STOP": 1},
        )
        self.assertEqual({track.agent_type for track in scenario.tracks}, {"vehicle", "pedestrian"})

    def test_inspect_waymo_motion_slice_reports_missing_input(self) -> None:
        report = inspect_waymo_motion_slice("missing-waymo-dir")

        self.assertFalse(report.exists)
        self.assertFalse(waymo_motion_slice_ready(report))
        self.assertIn("Input path does not exist.", report.notes)

    def test_load_waymo_motion_reads_protobuf_shaped_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.json"
            path.write_text(NATIVE_JSON_FIXTURE, encoding="utf-8")
            scenarios = load_waymo_motion(path)

        self.assertEqual(len(scenarios), 1)
        scenario = scenarios[0]
        self.assertEqual(scenario.scenario_id, "waymo_native_001")
        self.assertEqual(scenario.ego_track_id, "42")
        self.assertEqual(scenario.source, "waymo_motion_json:scenario.json")
        self.assertIn("objects_of_interest", scenario.tags)
        self.assertIn("tracks_to_predict", scenario.tags)
        self.assertEqual(scenario.metadata["waymo_tracks_to_predict_track_ids"], ["7"])
        self.assertEqual(scenario.metadata["waymo_objects_of_interest_track_ids"], ["7"])
        self.assertEqual(
            [feature["kind"] for feature in scenario.metadata["waymo_map_features"]],
            ["lane", "crosswalk"],
        )
        self.assertEqual(scenario.metadata["waymo_map_features"][0]["entry_lanes"], [9001])
        self.assertEqual(scenario.metadata["waymo_map_summary"]["route_link_count"], 3)
        self.assertEqual(
            scenario.metadata["waymo_dynamic_map_summary"]["state_counts"],
            {"LANE_STATE_GO": 1, "LANE_STATE_STOP": 1},
        )
        self.assertEqual(
            scenario.metadata["waymo_dynamic_map_summary"]["stop_point_count"],
            2,
        )
        pedestrian = next(track for track in scenario.tracks if track.agent_id == "7")
        self.assertEqual(pedestrian.agent_type, "pedestrian")
        self.assertEqual(len(pedestrian.states), 2)

    def test_load_waymo_motion_supports_snake_case_jsonl_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenarios.jsonl"
            path.write_text(
                _jsonl(NATIVE_JSON_FIXTURE, NATIVE_SNAKE_CASE_FIXTURE),
                encoding="utf-8",
            )
            scenarios = load_waymo_motion(path, max_scenarios=1)

        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].scenario_id, "waymo_native_001")

    def test_ingest_waymo_motion_writes_scenariolens_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "scenario.json"
            output_path = Path(tmpdir) / "scenarios.json"
            input_path.write_text(NATIVE_JSON_FIXTURE, encoding="utf-8")

            ingest_waymo_motion(input_path, output_path)
            scenarios = load_scenarios(output_path)

        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].scenario_id, "waymo_native_001")

    def test_save_waymo_motion_as_scenarios_honors_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "scenarios.jsonl"
            output_path = Path(tmpdir) / "scenarios.json"
            input_path.write_text(
                _jsonl(NATIVE_JSON_FIXTURE, NATIVE_SNAKE_CASE_FIXTURE),
                encoding="utf-8",
            )

            save_waymo_motion_as_scenarios(input_path, output_path, max_scenarios=1)
            scenarios = load_scenarios(output_path)

        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].scenario_id, "waymo_native_001")

    def test_load_normalized_motion_csv_maps_waymo_object_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "normalized.csv"
            path.write_text(NORMALIZED_FIXTURE, encoding="utf-8")
            scenarios = load_normalized_motion_csv(path)

        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0].scenario_id, "waymo_like_001")
        self.assertEqual(scenarios[0].ego_track_id, "sdc")
        self.assertIn("pedestrian_crossing", scenarios[0].tags)
        agent_types = {track.agent_type for track in scenarios[0].tracks}
        self.assertEqual(agent_types, {"vehicle", "pedestrian"})

    def test_save_normalized_motion_csv_as_scenarios_honors_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "normalized.csv"
            output_path = Path(tmpdir) / "scenarios.json"
            input_path.write_text(NORMALIZED_FIXTURE, encoding="utf-8")

            save_normalized_motion_csv_as_scenarios(
                input_path,
                output_path,
                max_scenarios=1,
            )
            scenarios = load_scenarios(output_path)

        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].source, "waymo_motion_normalized_fixture")

    def test_load_normalized_motion_csv_rejects_unknown_object_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.csv"
            path.write_text(
                "scenario_id,track_id,object_type,timestep,center_x,center_y\n"
                "bad,a,TYPE_SPACESHIP,0,0,0\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_normalized_motion_csv(path)

    def test_load_waymo_motion_rejects_unsupported_native_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.txt"
            path.write_text("{}", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_waymo_motion(path)


if __name__ == "__main__":
    unittest.main()
