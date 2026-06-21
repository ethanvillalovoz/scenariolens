import json
import unittest
import tempfile
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    WAYMO_OPEN_CHALLENGES_URL,
    WAYMO_OPEN_DATASET_URL,
    adapter_status,
    ingest_waymo_motion,
    load_waymo_motion,
    load_normalized_motion_csv,
    save_normalized_motion_csv_as_scenarios,
    save_waymo_motion_as_scenarios,
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


class WaymoMotionIngestTest(unittest.TestCase):
    def test_adapter_status_documents_native_adapter(self) -> None:
        status = adapter_status()

        self.assertEqual(status.adapter_name, "waymo_motion")
        self.assertTrue(status.implemented)
        self.assertEqual(status.dataset_url, WAYMO_OPEN_DATASET_URL)
        self.assertEqual(status.challenges_url, WAYMO_OPEN_CHALLENGES_URL)
        self.assertIn("protobuf-shaped JSON", status.message)

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
