import unittest
import tempfile
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    WAYMO_OPEN_CHALLENGES_URL,
    WAYMO_OPEN_DATASET_URL,
    adapter_status,
    ingest_waymo_motion,
    load_normalized_motion_csv,
    save_normalized_motion_csv_as_scenarios,
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


class WaymoMotionIngestTest(unittest.TestCase):
    def test_adapter_status_documents_planned_optional_adapter(self) -> None:
        status = adapter_status()

        self.assertEqual(status.adapter_name, "waymo_motion")
        self.assertFalse(status.implemented)
        self.assertEqual(status.dataset_url, WAYMO_OPEN_DATASET_URL)
        self.assertEqual(status.challenges_url, WAYMO_OPEN_CHALLENGES_URL)

    def test_ingest_waymo_motion_raises_clear_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError) as context:
            ingest_waymo_motion("input", "output", max_scenarios=1)

        self.assertIn("Native Waymo Motion ingestion is planned", str(context.exception))

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


if __name__ == "__main__":
    unittest.main()
