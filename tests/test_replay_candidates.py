import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import generate_baseline_comparison_study
from scenariolens.baseline_debug import generate_baseline_debug_casebook
from scenariolens.io import save_scenarios
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


if __name__ == "__main__":
    unittest.main()
