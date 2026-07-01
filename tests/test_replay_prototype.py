import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import generate_baseline_comparison_study
from scenariolens.baseline_debug import (
    BASELINE_DEBUG_FORMAT,
    generate_baseline_debug_casebook,
)
from scenariolens.context_eval_set import generate_context_eval_set
from scenariolens.context_failure_study import CONTEXT_FAILURE_STUDY_FORMAT
from scenariolens.io import save_scenarios
from scenariolens.replay_candidates import (
    REPLAY_CANDIDATE_FORMAT,
    generate_replay_candidate_plan,
)
from scenariolens.replay_prototype import (
    REPLAY_PROTOTYPE_FORMAT,
    generate_replay_prototype,
    replay_prototype_markdown,
    replay_prototype_payload,
)
from scenariolens.samples import synthetic_scenarios


class ReplayPrototypeTest(unittest.TestCase):
    def test_replay_prototype_payload_replays_ready_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_candidate_plan(root)

            payload = replay_prototype_payload(
                candidate_manifest_path=candidate_manifest,
                output_dir=root / "prototype",
                top=2,
            )

            self.assertEqual(payload["format"], REPLAY_PROTOTYPE_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertGreaterEqual(payload["replayed_case_count"], 1)

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertGreaterEqual(aggregate["replay_track_count"], 1)
            self.assertGreaterEqual(aggregate["perturbation_trial_count"], 4)

            cases = payload["cases"]
            self.assertIsInstance(cases, list)
            for case in cases:
                self.assertTrue(case["ready"])
                self.assertIn("nominal", case)
                self.assertEqual(len(case["perturbation_trials"]), 4)
                self.assertIn("perturbation_stability", case)

            markdown = replay_prototype_markdown(payload)
            self.assertIn("Open-Loop Replay Prototype", markdown)
            self.assertIn("Perturbation trials", markdown)
            self.assertIn("not a closed-loop simulator", markdown)
            self.assertIn("not Waymax/JAX execution", markdown)

    def test_generate_replay_prototype_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_candidate_plan(root)
            output_dir = root / "prototype"
            public_report = root / "reports" / "prototype.md"

            result = generate_replay_prototype(
                candidate_manifest_path=candidate_manifest,
                output_dir=output_dir,
                top=2,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertGreaterEqual(result.case_count, 1)
            self.assertGreaterEqual(result.replay_track_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], REPLAY_PROTOTYPE_FORMAT)
            self.assertIn("Replay Summary", public_report.read_text())

            for case in manifest["cases"]:
                self.assertTrue(Path(case["local_packet_path"]).exists())
                self.assertTrue(Path(case["local_svg_path"]).exists())

    def test_replay_prototype_skips_heading_aware_candidate_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = root / "heading_debug.json"
            candidate_manifest = root / "heading_candidates.json"
            debug_manifest.write_text(
                json.dumps(
                    {
                        "format": BASELINE_DEBUG_FORMAT,
                        "ready": True,
                        "cases": [],
                    }
                ),
                encoding="utf-8",
            )
            candidate_manifest.write_text(
                json.dumps(
                    {
                        "format": REPLAY_CANDIDATE_FORMAT,
                        "source": str(debug_manifest),
                        "ready": True,
                        "candidates": [
                            {
                                "scenario_id": "heading_case",
                                "source_name": "fixture",
                                "comparison_mode": "heading_lane_selection",
                                "readiness": "ready_for_heading_improvement_replay",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = replay_prototype_payload(
                candidate_manifest_path=candidate_manifest,
                output_dir=root / "prototype",
                top=1,
            )

            self.assertFalse(payload["ready"])
            self.assertEqual(payload["selected_candidate_count"], 0)
            self.assertEqual(payload["skipped_candidate_count"], 1)
            skipped = payload["skipped_candidates"][0]
            self.assertEqual(skipped["comparison_mode"], "heading_lane_selection")
            self.assertIn("unsupported_replay_candidate_mode", skipped["reason"])

    def test_replay_prototype_supports_context_eval_candidate_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_context_candidate_plan(root)

            payload = replay_prototype_payload(
                candidate_manifest_path=candidate_manifest,
                output_dir=root / "context_prototype",
                top=2,
            )

            self.assertEqual(payload["format"], REPLAY_PROTOTYPE_FORMAT)
            self.assertEqual(payload["source_kind"], "context_eval_set")
            self.assertTrue(payload["ready"])
            self.assertGreaterEqual(payload["replayed_case_count"], 1)

            cases = payload["cases"]
            self.assertIsInstance(cases, list)
            self.assertTrue(
                any(
                    str(case["case_label"]).startswith("Context eval seed")
                    for case in cases
                )
            )

            markdown = replay_prototype_markdown(payload)
            self.assertIn("Context Open-Loop Replay Prototype", markdown)
            self.assertIn("Source kind: `context_eval_set`", markdown)
            self.assertIn("context-evaluation seeds", markdown)
            self.assertIn("Context-derived candidates", markdown)


def _write_candidate_plan(root: Path) -> Path:
    input_path = root / "synthetic.json"
    study_dir = root / "study"
    debug_dir = root / "debug"
    candidate_dir = root / "candidates"
    save_scenarios(input_path, synthetic_scenarios())
    study = generate_baseline_comparison_study(
        input_paths=(input_path,),
        output_dir=study_dir,
        input_format="scenariolens-json",
        max_scenarios=11,
        top=6,
    )
    debug = generate_baseline_debug_casebook(
        study_manifest_path=study.manifest_path,
        output_dir=debug_dir,
        case_count=3,
    )
    candidates = generate_replay_candidate_plan(
        debug_manifest_path=debug.manifest_path,
        output_dir=candidate_dir,
    )
    return candidates.manifest_path


def _write_context_candidate_plan(root: Path) -> Path:
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
            scenario_index=10,
        ),
        _context_failure_row(
            source=input_path,
            scenario_id="synthetic_dense_intersection_vru",
            cv_fde=3.0,
            lane_delta=0.0,
            fallback_count=3,
            scenario_index=6,
        ),
    ]
    context_failure_manifest.write_text(
        json.dumps(
            {
                "format": CONTEXT_FAILURE_STUDY_FORMAT,
                "ready": True,
                "source_count": 1,
                "scenario_count": 2,
                "input_format": "scenariolens-json",
                "max_scenarios_per_input": 11,
                "aggregate": {
                    "evaluated_target_count": 4,
                    "constant_velocity_fde_m": 4.415,
                    "constant_velocity_miss_rate": 0.5,
                },
                "hardest_context_failures": rows,
                "signal_context_failures": rows[:1],
                "route_context_failures": rows,
                "lane_regressions_with_context": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    eval_set = generate_context_eval_set(
        context_failure_manifest_path=context_failure_manifest,
        output_dir=root / "context_eval_set",
        top_per_group=2,
    )
    debug = generate_baseline_debug_casebook(
        study_manifest_path=eval_set.manifest_path,
        output_dir=root / "context_debug",
        case_count=2,
    )
    candidates = generate_replay_candidate_plan(
        debug_manifest_path=debug.manifest_path,
        output_dir=root / "context_candidates",
    )
    return candidates.manifest_path


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
        "evaluated_target_count": 2,
        "constant_velocity_fde_m": cv_fde,
        "constant_velocity_miss_rate": 1.0,
        "lane_aware_fde_m": cv_fde - lane_delta,
        "fde_improvement_m": lane_delta,
        "map_used_count": 1 if lane_delta else 0,
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
