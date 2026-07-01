import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import generate_baseline_comparison_study
from scenariolens.baseline_debug import generate_baseline_debug_casebook
from scenariolens.context_eval_set import generate_context_eval_set
from scenariolens.context_failure_study import CONTEXT_FAILURE_STUDY_FORMAT
from scenariolens.io import save_scenarios
from scenariolens.lane_selection_study import generate_lane_selection_study
from scenariolens.replay_candidates import (
    REPLAY_CANDIDATE_FORMAT,
    generate_replay_candidate_plan,
    replay_candidate_markdown,
    replay_candidate_payload,
)
from scenariolens.samples import synthetic_scenarios


class ReplayCandidatesTest(unittest.TestCase):
    def test_replay_candidate_payload_ranks_debug_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_debug_casebook(root)

            payload = replay_candidate_payload(
                debug_manifest_path=debug_manifest,
                output_dir=root / "replay",
            )

            self.assertEqual(payload["format"], REPLAY_CANDIDATE_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 3)
            self.assertEqual(payload["candidate_count"], 3)

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertGreaterEqual(aggregate["replay_ready_count"], 1)
            self.assertGreaterEqual(aggregate["local_overlay_present_count"], 1)

            candidates = payload["candidates"]
            self.assertIsInstance(candidates, list)
            readiness_values = {candidate["readiness"] for candidate in candidates}
            self.assertIn("ready_for_improvement_replay", readiness_values)
            self.assertIn("needs_map_match_audit", readiness_values)

            markdown = replay_candidate_markdown(payload)
            self.assertIn("Replay Candidate Plan", markdown)
            self.assertIn("Ranked Candidates", markdown)
            self.assertIn("Waymax/JAX", markdown)
            self.assertIn("not a completed Waymax/JAX integration", markdown)

    def test_generate_replay_candidate_plan_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_debug_casebook(root)
            output_dir = root / "replay"
            public_report = root / "reports" / "replay.md"

            result = generate_replay_candidate_plan(
                debug_manifest_path=debug_manifest,
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.candidate_count, 3)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], REPLAY_CANDIDATE_FORMAT)
            self.assertIn("Queue Summary", public_report.read_text())

    def test_replay_candidate_payload_supports_heading_aware_debug_casebook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_heading_debug_casebook(root)

            payload = replay_candidate_payload(
                debug_manifest_path=debug_manifest,
                output_dir=root / "heading_replay",
            )

            self.assertEqual(payload["format"], REPLAY_CANDIDATE_FORMAT)
            self.assertEqual(payload["source_kind"], "lane_selection_study")
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 3)
            self.assertEqual(payload["candidate_count"], 3)

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(aggregate["heading_selection_candidate_count"], 3)
            self.assertGreaterEqual(aggregate["fallback_audit_count"], 1)

            candidates = payload["candidates"]
            self.assertIsInstance(candidates, list)
            readiness_values = {candidate["readiness"] for candidate in candidates}
            self.assertIn("needs_heading_map_match_audit", readiness_values)
            for candidate in candidates:
                self.assertEqual(candidate["comparison_mode"], "heading_lane_selection")
                evidence = candidate["evidence"]
                self.assertIn("nearest_lane_fde_m", evidence)
                self.assertIn("heading_lane_fde_m", evidence)

            markdown = replay_candidate_markdown(payload)
            self.assertIn("Heading-Aware Replay Candidate Plan", markdown)
            self.assertIn("Nearest-lane FDE", markdown)
            self.assertIn("Heading-aware FDE", markdown)
            self.assertIn("not a completed Waymax/JAX integration", markdown)

    def test_replay_candidate_payload_supports_context_eval_debug_casebook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_context_eval_debug_casebook(root)

            payload = replay_candidate_payload(
                debug_manifest_path=debug_manifest,
                output_dir=root / "context_replay",
            )

            self.assertEqual(payload["format"], REPLAY_CANDIDATE_FORMAT)
            self.assertEqual(payload["source_kind"], "context_eval_set")
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 2)
            self.assertEqual(payload["candidate_count"], 2)

            markdown = replay_candidate_markdown(payload)
            self.assertIn("Context Replay Candidate Plan", markdown)
            self.assertIn("context eval debug casebook", markdown)
            self.assertIn("Context-derived candidates", markdown)


def _write_debug_casebook(root: Path) -> Path:
    input_path = root / "synthetic.json"
    study_dir = root / "study"
    debug_dir = root / "debug"
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
    return debug.manifest_path


def _write_heading_debug_casebook(root: Path) -> Path:
    input_path = root / "synthetic.json"
    study_dir = root / "lane_selection_study"
    debug_dir = root / "heading_debug"
    save_scenarios(input_path, synthetic_scenarios())
    study = generate_lane_selection_study(
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
    return debug.manifest_path


def _write_context_eval_debug_casebook(root: Path) -> Path:
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
    debug = generate_baseline_debug_casebook(
        study_manifest_path=eval_set.manifest_path,
        output_dir=root / "context_debug",
        case_count=2,
    )
    return debug.manifest_path


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
