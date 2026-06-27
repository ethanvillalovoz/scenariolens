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

    def test_waymo_motion_status_reports_native_adapter(self) -> None:
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
        self.assertIn("Implemented: True", result.stdout)

    def test_waymo_motion_preflight_reports_native_json_readiness(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenariolens.cli",
                "waymo-motion-preflight",
                "--input",
                "docs/examples/waymo_motion_native_sample.json",
            ],
            check=True,
            env={"PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        self.assertIn("Ready for ingestion: True", result.stdout)
        self.assertIn("Supported suffixes:", result.stdout)
        self.assertIn(".json: 1", result.stdout)

    def test_waymo_motion_preflight_returns_nonzero_for_missing_input(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenariolens.cli",
                "waymo-motion-preflight",
                "--input",
                "missing-waymo-dir",
            ],
            env={"PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Ready for ingestion: False", result.stdout)
        self.assertIn("Input path does not exist.", result.stdout)

    def test_waymo_motion_doctor_reports_ready_fixture(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenariolens.cli",
                "waymo-motion-doctor",
                "--input",
                "docs/examples/waymo_motion_native_sample.json",
                "--no-search-common-locations",
            ],
            check=True,
            env={"PYTHONPATH": "src"},
            capture_output=True,
            text=True,
        )

        self.assertIn("Ready for ingestion: True", result.stdout)
        self.assertIn("Optional package waymo_open_dataset:", result.stdout)
        self.assertIn("Next actions:", result.stdout)

    def test_ingest_waymo_motion_native_json(self) -> None:
        native_json = """{
          "scenarioId": "waymo_native_cli",
          "timestampsSeconds": [0.0, 0.1],
          "sdcTrackIndex": 0,
          "tracks": [
            {
              "id": 10,
              "objectType": "TYPE_VEHICLE",
              "states": [
                {"centerX": 0.0, "centerY": 0.0, "velocityX": 5.0, "velocityY": 0.0, "valid": true},
                {"centerX": 0.5, "centerY": 0.0, "velocityX": 5.0, "velocityY": 0.0, "valid": true}
              ]
            },
            {
              "id": 20,
              "objectType": "TYPE_CYCLIST",
              "states": [
                {"centerX": 1.0, "centerY": 1.5, "velocityX": 4.0, "velocityY": 0.0, "valid": true},
                {"centerX": 1.4, "centerY": 1.5, "velocityX": 4.0, "velocityY": 0.0, "valid": true}
              ]
            }
          ]
        }
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "waymo_native.json"
            output_path = Path(tmpdir) / "waymo.json"
            input_path.write_text(native_json, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "ingest-waymo-motion",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--max-scenarios",
                    "1",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Ingested 1 native Waymo Motion scenario(s)", result.stdout)
            self.assertIn("waymo_native_cli", output_path.read_text())

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

    def test_waymo_motion_validate_command_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "validation"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "waymo-motion-validate",
                    "--input",
                    "docs/examples/waymo_motion_native_sample.json",
                    "--output-dir",
                    str(output_dir),
                    "--max-scenarios",
                    "1",
                    "--top",
                    "1",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Validated 1 Waymo Motion scenario(s)", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "README.md").exists())
            self.assertTrue((output_dir / "scenarios.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "case_study.md").exists())
            self.assertEqual(len(tuple((output_dir / "assets").glob("*.svg"))), 1)

    def test_portfolio_report_command_writes_report_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "portfolio.md"
            assets = root / "assets"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "portfolio-report",
                    "--output",
                    str(output),
                    "--assets-dir",
                    str(assets),
                    "--top",
                    "1",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated portfolio report", result.stdout)
            self.assertIn("ScenarioLens Portfolio Report", output.read_text())
            self.assertGreaterEqual(len(tuple(assets.glob("*.svg"))), 1)

    def test_dashboard_data_command_writes_json_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "demo" / "scenarios.json"
            assets = root / "demo" / "assets"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "dashboard-data",
                    "--output",
                    str(output),
                    "--assets-dir",
                    str(assets),
                    "--limit",
                    "2",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated dashboard data", result.stdout)
            self.assertIn('"format": "scenariolens.dashboard.v1"', output.read_text())
            self.assertEqual(len(tuple(assets.glob("*.svg"))), 2)

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
