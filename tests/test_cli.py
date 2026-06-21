import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTest(unittest.TestCase):
    def test_export_synthetic_then_report_from_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "synthetic.json"
            export_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "export-synthetic",
                    "--output",
                    str(input_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )
            report_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "report",
                    "--input",
                    str(input_path),
                    "--format",
                    "json",
                    "--limit",
                    "1",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Exported 10 scenario(s)", export_result.stdout)
            self.assertIn('"reported_count": 1', report_result.stdout)

    def test_ingest_csv_then_render_from_input(self) -> None:
        csv_text = (
            "scenario_id,agent_id,agent_type,t,x,y,vx,vy,ego_track_id,tags\n"
            "csv_case,ego,vehicle,0,0,0,4,0,ego,merge_conflict\n"
            "csv_case,ego,vehicle,1,4,0,4,0,ego,merge_conflict\n"
            "csv_case,veh_1,vehicle,0,6,2,3,-0.5,ego,merge_conflict\n"
            "csv_case,veh_1,vehicle,1,9,1.5,3,-0.5,ego,merge_conflict\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "tracks.csv"
            json_path = Path(tmpdir) / "scenarios.json"
            svg_path = Path(tmpdir) / "csv_case.svg"
            csv_path.write_text(csv_text, encoding="utf-8")

            ingest_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "ingest-csv",
                    "--input",
                    str(csv_path),
                    "--output",
                    str(json_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "render",
                    "--input",
                    str(json_path),
                    "--scenario",
                    "csv_case",
                    "--output",
                    str(svg_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Ingested 1 scenario(s)", ingest_result.stdout)
            self.assertIn("csv_case", svg_path.read_text())

    def test_waymo_motion_status_reports_planned_adapter(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenariolens.cli",
                "waymo-motion-status",
            ],
            check=True,
            env={"PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        self.assertIn("Adapter: waymo_motion", result.stdout)
        self.assertIn("Implemented: False", result.stdout)

    def test_ingest_waymo_motion_returns_clear_nonzero_placeholder(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenariolens.cli",
                "ingest-waymo-motion",
                "--input",
                "data/raw/waymo",
                "--output",
                "data/processed/waymo.json",
                "--max-scenarios",
                "1",
            ],
            env={"PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Native Waymo Motion ingestion is planned", result.stderr)

    def test_ingest_waymo_motion_normalized_csv(self) -> None:
        csv_text = (
            "scenario_id,track_id,object_type,timestep,center_x,center_y,"
            "velocity_x,velocity_y,is_sdc,tags,source\n"
            "waymo_like,sdc,TYPE_VEHICLE,0,0,0,5,0,true,merge_conflict,fixture\n"
            "waymo_like,sdc,TYPE_VEHICLE,1,5,0,5,0,true,merge_conflict,fixture\n"
            "waymo_like,ped_1,TYPE_PEDESTRIAN,0,4,-2,0,1,false,"
            "pedestrian_crossing,fixture\n"
            "waymo_like,ped_1,TYPE_PEDESTRIAN,1,4,-1,0,1,false,"
            "pedestrian_crossing,fixture\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "waymo_normalized.csv"
            output_path = Path(tmpdir) / "waymo.json"
            input_path.write_text(csv_text, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "ingest-waymo-motion",
                    "--format",
                    "normalized-csv",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Ingested 1 normalized Waymo Motion scenario(s)", result.stdout)
            self.assertIn("waymo_like", output_path.read_text())

    def test_render_single_scenario_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "scenario.svg"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "render",
                    "--scenario",
                    "synthetic_cyclist_close_pass",
                    "--output",
                    str(output),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.stdout, "")
            self.assertIn("synthetic_cyclist_close_pass", output.read_text())

    def test_render_top_scenarios_to_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "gallery"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "render",
                    "--top",
                    "2",
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Rendered 2 scenario(s)", result.stdout)
            self.assertEqual(len(tuple(output_dir.glob("*.svg"))), 2)

    def test_render_from_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "synthetic.json"
            output_path = Path(tmpdir) / "rendered.svg"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "export-synthetic",
                    "--output",
                    str(input_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "render",
                    "--input",
                    str(input_path),
                    "--scenario",
                    "synthetic_unprotected_left_turn",
                    "--output",
                    str(output_path),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("synthetic_unprotected_left_turn", output_path.read_text())


if __name__ == "__main__":
    unittest.main()
