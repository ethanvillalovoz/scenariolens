import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import generate_baseline_comparison_study
from scenariolens.baseline_debug import (
    BASELINE_DEBUG_FORMAT,
    baseline_debug_casebook_markdown,
    generate_baseline_debug_casebook,
)
from scenariolens.io import save_scenarios
from scenariolens.samples import synthetic_scenarios


class BaselineDebugTest(unittest.TestCase):
    def test_debug_casebook_selects_study_cases_and_writes_svg_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            study_dir = root / "study"
            debug_dir = root / "debug"
            public_report = root / "reports" / "debug_casebook.md"
            save_scenarios(input_path, synthetic_scenarios())
            study = generate_baseline_comparison_study(
                input_paths=(input_path,),
                output_dir=study_dir,
                input_format="scenariolens-json",
                max_scenarios=11,
                top=6,
            )

            result = generate_baseline_debug_casebook(
                study_manifest_path=study.manifest_path,
                output_dir=debug_dir,
                case_count=3,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 3)
            self.assertEqual(manifest["format"], BASELINE_DEBUG_FORMAT)
            self.assertEqual(manifest["source_kind"], "baseline_compare_study")
            self.assertTrue(public_report.exists())
            self.assertIn("local SVG overlays", public_report.read_text())

            labels = [case["case_label"] for case in manifest["cases"]]
            self.assertIn("Largest improvement", labels)
            self.assertIn("Largest regression", labels)
            self.assertIn("Fallback-heavy case", labels)

            for case in manifest["cases"]:
                svg_path = debug_dir / case["svg_path"]
                case_manifest = debug_dir / case["manifest_path"]
                self.assertTrue(svg_path.exists())
                self.assertTrue(case_manifest.exists())
                svg = svg_path.read_text(encoding="utf-8")
                self.assertIn("baseline-constant_velocity", svg)
                self.assertIn("baseline-lane_aware", svg)

            local_markdown = baseline_debug_casebook_markdown(manifest, public_safe=False)
            self.assertIn("Local SVG overlay", local_markdown)
            self.assertIn("Metric-only error timeline", local_markdown)

    def test_debug_casebook_supports_direct_scenario_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            debug_dir = root / "debug"
            save_scenarios(input_path, synthetic_scenarios())

            result = generate_baseline_debug_casebook(
                input_path=input_path,
                scenario_ids=("synthetic_curved_lane_prediction",),
                input_format="scenariolens-json",
                output_dir=debug_dir,
                max_scenarios=11,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 1)
            self.assertEqual(
                manifest["cases"][0]["scenario_id"],
                "synthetic_curved_lane_prediction",
            )
            self.assertIn("track_diagnostics", manifest["cases"][0])


if __name__ == "__main__":
    unittest.main()
