import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
