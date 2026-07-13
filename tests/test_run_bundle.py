from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.run_bundle import (
    RUN_BUNDLE_FORMAT,
    generate_run_bundle,
    resolve_run_inputs,
)
from scenariolens.samples import synthetic_scenarios


class RunBundleTest(unittest.TestCase):
    def test_generate_run_bundle_writes_reproducible_core_studies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            save_scenarios(input_path, synthetic_scenarios())

            first = generate_run_bundle(
                input_paths=(input_path,),
                output_dir=root / "run_a",
                max_scenarios=11,
                top=4,
                input_format="scenariolens-json",
            )
            second = generate_run_bundle(
                input_paths=(input_path,),
                output_dir=root / "run_b",
                max_scenarios=11,
                top=4,
                input_format="scenariolens-json",
            )

            self.assertTrue(first.ready)
            self.assertEqual(first.stage_count, 3)
            self.assertEqual(first.scenario_count, 11)
            self.assertEqual(first.analysis_digest, second.analysis_digest)

            payload = json.loads(first.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], RUN_BUNDLE_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["source_count"], 1)
            self.assertEqual(payload["scenario_count"], 11)
            self.assertEqual(len(payload["inputs"][0]["sha256"]), 64)
            self.assertEqual(
                [stage["stage_id"] for stage in payload["stages"]],
                ["baseline_comparison", "lane_selection", "lane_continuation"],
            )
            for stage in payload["stages"]:
                self.assertTrue((first.output_dir / stage["manifest"]).exists())
                self.assertTrue((first.output_dir / stage["report"]).exists())

            report = first.report_path.read_text(encoding="utf-8")
            self.assertIn("ScenarioLens Run Report", report)
            self.assertIn("Baseline Comparison", report)
            self.assertIn("Heading-Aware Lane Selection", report)
            self.assertIn("Lane Continuation", report)
            self.assertIn("not a Waymo benchmark", report)

    def test_resolve_run_inputs_expands_native_directory_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = root / "first.tfrecord"
            second = root / "second.json"
            ignored = root / "notes.txt"
            first.write_bytes(b"first")
            second.write_text("{}", encoding="utf-8")
            ignored.write_text("ignored", encoding="utf-8")

            resolved = resolve_run_inputs(
                (root, first),
                input_format="native",
            )

            self.assertEqual(resolved, (first, second))

    def test_run_bundle_rejects_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(FileNotFoundError, "does not exist"):
                generate_run_bundle(
                    input_paths=(root / "missing.json",),
                    output_dir=root / "run",
                    input_format="scenariolens-json",
                )

    def test_run_cli_writes_top_level_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            save_scenarios(input_path, synthetic_scenarios())
            output_dir = root / "run"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "run",
                    "--input",
                    str(input_path),
                    "--format",
                    "scenariolens-json",
                    "--output",
                    str(output_dir),
                    "--max-scenarios",
                    "11",
                    "--top",
                    "4",
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("ScenarioLens run ready", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "studies" / "lane_continuation").exists())


if __name__ == "__main__":
    unittest.main()
