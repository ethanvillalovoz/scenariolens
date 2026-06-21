import tempfile
import unittest
from pathlib import Path

from scenariolens.ingest.csv_tracks import load_track_csv, save_track_csv_as_scenarios
from scenariolens.io import load_scenarios


CSV_FIXTURE = """scenario_id,agent_id,agent_type,t,x,y,vx,vy,ego_track_id,tags,source
city_merge,ego,vehicle,1,5,0,5,0,ego,merge_conflict|close_interaction,csv_fixture
city_merge,ego,vehicle,0,0,0,5,0,ego,merge_conflict|close_interaction,csv_fixture
city_merge,veh_1,vehicle,0,6,3,4,-0.5,ego,merge_conflict,csv_fixture
city_merge,veh_1,vehicle,1,10,2.5,4,-0.5,ego,merge_conflict,csv_fixture
vru_crossing,ego,vehicle,0,0,0,4,0,ego,pedestrian_crossing,csv_fixture
vru_crossing,ped_1,pedestrian,0,3,-2,0,1,ego,pedestrian_crossing,csv_fixture
"""


class CsvTracksIngestTest(unittest.TestCase):
    def test_load_track_csv_groups_rows_into_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tracks.csv"
            path.write_text(CSV_FIXTURE, encoding="utf-8")
            scenarios = load_track_csv(path)

        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0].scenario_id, "city_merge")
        self.assertEqual(scenarios[0].source, "csv_fixture")
        self.assertEqual(scenarios[0].ego_track_id, "ego")
        self.assertIn("merge_conflict", scenarios[0].tags)

    def test_load_track_csv_sorts_states_by_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tracks.csv"
            path.write_text(CSV_FIXTURE, encoding="utf-8")
            scenarios = load_track_csv(path)

        ego = next(track for track in scenarios[0].tracks if track.agent_id == "ego")
        self.assertEqual(tuple(state.t for state in ego.states), (0.0, 1.0))

    def test_save_track_csv_as_scenarios_writes_scenariolens_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "tracks.csv"
            output_path = Path(tmpdir) / "scenarios.json"
            input_path.write_text(CSV_FIXTURE, encoding="utf-8")

            save_track_csv_as_scenarios(input_path, output_path)
            scenarios = load_scenarios(output_path)

        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[1].scenario_id, "vru_crossing")

    def test_load_track_csv_rejects_missing_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.csv"
            path.write_text("scenario_id,agent_id\nfoo,bar\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_track_csv(path)

    def test_load_track_csv_rejects_unknown_agent_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.csv"
            path.write_text(
                "scenario_id,agent_id,agent_type,t,x,y\nfoo,a,spaceship,0,0,0\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_track_csv(path)


if __name__ == "__main__":
    unittest.main()

