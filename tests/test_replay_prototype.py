import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import generate_baseline_comparison_study
from scenariolens.baseline_debug import generate_baseline_debug_casebook
from scenariolens.io import save_scenarios
from scenariolens.replay_candidates import generate_replay_candidate_plan
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


if __name__ == "__main__":
    unittest.main()
