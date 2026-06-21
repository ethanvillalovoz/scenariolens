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
