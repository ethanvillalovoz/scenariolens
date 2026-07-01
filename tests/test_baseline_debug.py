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
from scenariolens.context_eval_set import generate_context_eval_set
from scenariolens.context_failure_study import CONTEXT_FAILURE_STUDY_FORMAT
from scenariolens.io import save_scenarios
from scenariolens.lane_selection_study import generate_lane_selection_study
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

    def test_debug_casebook_accepts_lane_selection_study_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            study_dir = root / "lane_study"
            debug_dir = root / "heading_debug"
            public_report = root / "reports" / "heading_debug_casebook.md"
            save_scenarios(input_path, synthetic_scenarios())
            study = generate_lane_selection_study(
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
            self.assertEqual(manifest["source_kind"], "lane_selection_study")
            self.assertIn("Heading-Aware Debug Casebook", public_report.read_text())

            labels = [case["case_label"] for case in manifest["cases"]]
            self.assertIn("Largest heading improvement", labels)
            self.assertIn("Largest heading regression", labels)
            self.assertIn("Heading fallback-heavy case", labels)

            for case in manifest["cases"]:
                summary = case["summary"]
                self.assertIn("nearest_lane_fde_m", summary)
                self.assertIn("heading_lane_fde_m", summary)
                self.assertIn("heading_vs_nearest_fde_improvement_m", summary)
                svg = (debug_dir / case["svg_path"]).read_text(encoding="utf-8")
                self.assertIn("baseline-constant_velocity", svg)
                self.assertIn("baseline-lane_aware", svg)
                self.assertIn("baseline-lane_aware_heading", svg)

                track = case["track_diagnostics"][0]
                self.assertIn("nearest_lane_fde_m", track)
                self.assertIn("heading_lane_fde_m", track)
                self.assertIn("heading_lane_match", track)

    def test_debug_casebook_accepts_context_eval_set_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            eval_manifest = _write_context_eval_set(root)
            debug_dir = root / "context_debug"
            public_report = root / "reports" / "context_debug_casebook.md"

            result = generate_baseline_debug_casebook(
                study_manifest_path=eval_manifest,
                output_dir=debug_dir,
                case_count=2,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(manifest["format"], BASELINE_DEBUG_FORMAT)
            self.assertEqual(manifest["source_kind"], "context_eval_set")
            self.assertIn("Context Eval Debug Casebook", public_report.read_text())

            labels = [case["case_label"] for case in manifest["cases"]]
            self.assertEqual(labels, ["Context eval seed 1", "Context eval seed 2"])

            for case in manifest["cases"]:
                self.assertIn("Selected from the context evaluation set", case["selection_reason"])
                svg = (debug_dir / case["svg_path"]).read_text(encoding="utf-8")
                self.assertIn("baseline-constant_velocity", svg)
                self.assertIn("baseline-lane_aware", svg)

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


def _write_context_eval_set(root: Path) -> Path:
    input_path = root / "synthetic.json"
    save_scenarios(input_path, synthetic_scenarios())
    context_failure_manifest = root / "context_failure_manifest.json"
    rows = [
        _context_failure_row(
            source=input_path,
            scenario_id="synthetic_curved_lane_prediction",
            cv_fde=5.83,
            lane_delta=4.0,
            fallback_count=0,
            scenario_index=12,
        ),
        _context_failure_row(
            source=input_path,
            scenario_id="synthetic_dense_intersection_vru",
            cv_fde=3.0,
            lane_delta=-2.0,
            fallback_count=2,
            scenario_index=1,
        ),
    ]
    payload = {
        "format": CONTEXT_FAILURE_STUDY_FORMAT,
        "ready": True,
        "source_count": 1,
        "scenario_count": 2,
        "input_format": "scenariolens-json",
        "max_scenarios_per_input": 11,
        "aggregate": {
            "evaluated_target_count": 6,
            "constant_velocity_fde_m": 4.415,
            "constant_velocity_miss_rate": 0.5,
        },
        "hardest_context_failures": rows,
        "signal_context_failures": rows[:1],
        "route_context_failures": rows,
        "lane_regressions_with_context": rows[1:],
    }
    context_failure_manifest.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    eval_set = generate_context_eval_set(
        context_failure_manifest_path=context_failure_manifest,
        output_dir=root / "context_eval_set",
        top_per_group=2,
    )
    return eval_set.manifest_path


def _context_failure_row(
    source: Path,
    scenario_id: str,
    cv_fde: float,
    lane_delta: float,
    fallback_count: int,
    scenario_index: int,
) -> dict[str, object]:
    return {
        "source_input": str(source),
        "source_name": source.name,
        "source_index": 1,
        "scenario_index": scenario_index,
        "scenario_id": scenario_id,
        "score": 25.0,
        "evaluated_target_count": 3,
        "constant_velocity_fde_m": cv_fde,
        "constant_velocity_miss_rate": 1.0,
        "lane_aware_fde_m": cv_fde - lane_delta,
        "fde_improvement_m": lane_delta,
        "map_used_count": 1,
        "fallback_count": fallback_count,
        "map_feature_count": 3,
        "lane_count": 1,
        "signal_lane_state_count": 4,
        "signal_stop_state_count": 2,
        "route_link_count": 3,
        "entry_link_count": 1,
        "exit_link_count": 1,
        "neighbor_link_count": 1,
        "top_signal_state": "LANE_STATE_STOP (2)",
    }


if __name__ == "__main__":
    unittest.main()
