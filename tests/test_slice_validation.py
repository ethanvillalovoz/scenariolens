import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.slice_validation import (
    VALIDATION_FORMAT,
    validate_waymo_motion_slice,
)


class SliceValidationTest(unittest.TestCase):
    def test_validate_waymo_motion_slice_writes_reproducible_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "validation"

            result = validate_waymo_motion_slice(
                input_path="docs/examples/waymo_motion_native_sample.json",
                output_dir=output_dir,
                max_scenarios=1,
                top=1,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.scenario_count, 1)
            self.assertEqual(result.reported_count, 1)
            self.assertEqual(manifest["format"], VALIDATION_FORMAT)
            self.assertTrue(result.preflight_path.exists())
            self.assertTrue(result.summary_path.exists())
            self.assertTrue(result.case_study_path and result.case_study_path.exists())
            self.assertTrue(result.scenarios_path and result.scenarios_path.exists())
            self.assertTrue(result.report_path and result.report_path.exists())
            self.assertTrue(result.assets_dir and result.assets_dir.exists())
            self.assertEqual(len(tuple(result.assets_dir.glob("*.svg"))), 1)
            self.assertIn("waymo_native_sample_interaction", result.report_path.read_text())
            self.assertEqual(manifest["scenario_count"], 1)
            self.assertIn("aggregate_metrics", manifest)
            self.assertEqual(manifest["outputs"]["case_study"], "case_study.md")
            self.assertEqual(manifest["outputs"]["report"], "report.md")
            self.assertEqual(manifest["top_scenarios"][0]["rank"], 1)
            self.assertIn("prediction_baseline", manifest["aggregate_metrics"])
            self.assertIn("Aggregate Findings", result.case_study_path.read_text())
            self.assertIn("Prediction baseline", result.case_study_path.read_text())

    def test_validate_waymo_motion_slice_records_not_ready_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "validation"

            result = validate_waymo_motion_slice(
                input_path="missing-waymo-dir",
                output_dir=output_dir,
                max_scenarios=1,
                top=1,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertFalse(result.ready)
            self.assertEqual(result.scenario_count, 0)
            self.assertTrue(result.preflight_path.exists())
            self.assertTrue(result.summary_path.exists())
            self.assertIsNone(result.case_study_path)
            self.assertIsNone(result.scenarios_path)
            self.assertIsNone(result.report_path)
            self.assertIsNone(result.assets_dir)
            self.assertFalse(manifest["ready"])
            self.assertIn("Input path does not exist.", result.summary_path.read_text())


if __name__ == "__main__":
    unittest.main()
