import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
    _acceptance_decision,
    _history_speed_prior_stability,
    _perturbation_stability,
    generate_lane_continuation_branch_replay,
    lane_continuation_branch_replay_markdown,
    lane_continuation_branch_replay_payload,
)
from scenariolens.lane_continuation_branch_selection import (
    generate_lane_continuation_branch_selection,
)
from tests.test_lane_continuation_branch_selection import _write_manifests


class LaneContinuationBranchReplayTest(unittest.TestCase):
    def test_payload_replays_motion_context_branch_perturbations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_selection_manifest = _write_branch_selection_manifest(root)

            payload = lane_continuation_branch_replay_payload(
                branch_selection_manifest_path=branch_selection_manifest,
                output_dir=root / "branch_replay",
                top=5,
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_BRANCH_REPLAY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 1)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["replayed_case_count"], 1)
            self.assertEqual(aggregate["perturbation_trial_count"], 4)
            self.assertEqual(aggregate["stable_motion_context_case_count"], 1)
            self.assertEqual(aggregate["stable_positive_trial_count"], 4)
            self.assertEqual(aggregate["accepted_branch_case_count"], 1)
            self.assertEqual(
                aggregate["history_speed_prior_accepted_case_count"],
                1,
            )
            self.assertEqual(aggregate["route_context_followup_case_count"], 0)
            self.assertGreater(aggregate["min_robustness_margin_m"], 1.0)
            self.assertGreater(
                aggregate["min_history_speed_prior_margin_m"],
                1.0,
            )

            case = payload["cases"][0]
            self.assertEqual(case["scenario_id"], "branch_case")
            self.assertEqual(case["motion_context_chain"], ["100", "300"])
            self.assertGreater(case["nominal_motion_context_gain_m"], 5.0)
            self.assertGreater(case["nominal_history_speed_prior_gain_m"], 5.0)
            self.assertEqual(
                case["perturbation_stability"]["label"],
                "stable_motion_context_branch",
            )
            self.assertEqual(
                case["acceptance_decision"]["label"],
                "accepted_for_selector_rollout",
            )
            self.assertEqual(
                case["history_speed_prior_stability"]["label"],
                "stable_history_speed_prior_branch",
            )
            self.assertEqual(
                case["history_speed_prior_acceptance_decision"]["label"],
                "accepted_for_selector_rollout",
            )
            self.assertIn(
                "history_speed_prior_gain_m",
                case["perturbation_trials"][0],
            )

            markdown = lane_continuation_branch_replay_markdown(payload)
            self.assertIn("Motion-Context Branch Replay Diagnostic", markdown)
            self.assertIn("Acceptance gate", markdown)
            self.assertIn("History speed-prior accepted cases", markdown)
            self.assertIn("accepted_for_selector_rollout", markdown)
            self.assertIn("stable_motion_context_branch", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_branch_replay_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_selection_manifest = _write_branch_selection_manifest(root)
            output_dir = root / "branch_replay"
            public_report = root / "reports" / "branch_replay.md"

            result = generate_lane_continuation_branch_replay(
                branch_selection_manifest_path=branch_selection_manifest,
                output_dir=output_dir,
                top=5,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 1)
            self.assertEqual(result.replayed_case_count, 1)
            self.assertEqual(result.stable_case_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
            )
            self.assertIn("Replay Summary", public_report.read_text())

    def test_lane_continuation_branch_replay_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_selection_manifest = _write_branch_selection_manifest(root)
            output_dir = root / "branch_replay"
            public_report = root / "reports" / "branch_replay.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-branch-replay",
                    "--branch-selection-manifest",
                    str(branch_selection_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top",
                    "5",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 1 branch replay diagnostic", result.stdout)
            self.assertIn("1 stable motion-context case", result.stdout)
            self.assertIn("1 accepted branch case", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())

    def test_acceptance_gate_flags_stable_branch_with_thin_gain_margin(self) -> None:
        trials = [
            {
                "ready": True,
                "label": "speed_minus_10pct",
                "branch_preserved": True,
                "positive_gain": False,
                "motion_context_gain_m": 0.75,
            },
            {
                "ready": True,
                "label": "speed_plus_10pct",
                "branch_preserved": True,
                "positive_gain": True,
                "motion_context_gain_m": 3.0,
            },
        ]

        stability = _perturbation_stability(
            nominal_gain=2.0,
            expected_chain=("100", "300"),
            trials=trials,
        )
        decision = _acceptance_decision(stability)

        self.assertEqual(stability["label"], "branch_stable_gain_sensitive")
        self.assertEqual(stability["worst_trial_label"], "speed_minus_10pct")
        self.assertLess(stability["robustness_margin_m"], 0.0)
        self.assertEqual(decision["label"], "needs_route_context_margin")
        self.assertFalse(decision["accepted"])

    def test_history_speed_prior_gate_can_resolve_margin_followup(self) -> None:
        trials = [
            {
                "ready": True,
                "label": "speed_minus_10pct",
                "branch_preserved": True,
                "positive_gain": False,
                "motion_context_gain_m": 0.75,
                "history_speed_prior_positive_gain": True,
                "history_speed_prior_gain_m": 1.35,
            },
            {
                "ready": True,
                "label": "speed_plus_10pct",
                "branch_preserved": True,
                "positive_gain": True,
                "motion_context_gain_m": 3.0,
                "history_speed_prior_positive_gain": True,
                "history_speed_prior_gain_m": 2.4,
            },
        ]

        base_stability = _perturbation_stability(
            nominal_gain=2.0,
            expected_chain=("100", "300"),
            trials=trials,
        )
        speed_prior_stability = _history_speed_prior_stability(
            nominal_gain=2.1,
            expected_chain=("100", "300"),
            trials=trials,
        )
        base_decision = _acceptance_decision(base_stability)
        speed_prior_decision = _acceptance_decision(speed_prior_stability)

        self.assertEqual(base_decision["label"], "needs_route_context_margin")
        self.assertEqual(
            speed_prior_stability["label"],
            "stable_history_speed_prior_branch",
        )
        self.assertEqual(
            speed_prior_stability["worst_trial_label"],
            "speed_minus_10pct",
        )
        self.assertGreaterEqual(speed_prior_stability["robustness_margin_m"], 0.0)
        self.assertEqual(
            speed_prior_decision["label"],
            "accepted_for_selector_rollout",
        )


def _write_branch_selection_manifest(root: Path) -> Path:
    diagnostics_manifest = _write_manifests(root)
    result = generate_lane_continuation_branch_selection(
        diagnostics_manifest_path=diagnostics_manifest,
        output_dir=root / "branch_selection",
        top=10,
        max_hops=2,
    )
    return result.manifest_path


if __name__ == "__main__":
    unittest.main()
