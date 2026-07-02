import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_rollout import (
    LANE_CONTINUATION_BRANCH_ROLLOUT_FORMAT,
    generate_lane_continuation_branch_rollout_gate,
    lane_continuation_branch_rollout_markdown,
    lane_continuation_branch_rollout_payload,
)


class LaneContinuationBranchRolloutTest(unittest.TestCase):
    def test_payload_promotes_accepted_and_holds_margin_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_replay_manifest = _write_branch_replay_manifest(root)

            payload = lane_continuation_branch_rollout_payload(
                branch_replay_manifest_path=branch_replay_manifest,
                output_dir=root / "branch_rollout",
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_BRANCH_ROLLOUT_FORMAT)
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["replayed_case_count"], 2)
            self.assertEqual(aggregate["promoted_case_count"], 1)
            self.assertEqual(aggregate["held_route_context_case_count"], 1)
            self.assertEqual(aggregate["held_selector_stability_case_count"], 0)
            self.assertEqual(aggregate["speed_minus_margin_hold_count"], 1)
            self.assertEqual(aggregate["oracle_matched_hold_count"], 1)
            self.assertEqual(aggregate["max_hold_priority_score"], 5.182)
            self.assertEqual(aggregate["max_hold_gap_to_gate_m"], 0.443)

            promote, hold = payload["cases"]
            self.assertEqual(
                promote["decision"],
                "promote_for_broader_selector_eval",
            )
            self.assertTrue(promote["promotion_ready"])
            self.assertEqual(
                hold["decision"],
                "hold_for_route_context_margin",
            )
            self.assertFalse(hold["promotion_ready"])
            self.assertIn("route-context", hold["decision_reason"])
            self.assertEqual(
                hold["first_next_action"],
                "Add route-context features that can explain reduced-speed branch intent.",
            )

    def test_markdown_names_promote_and_hold_queues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_branch_rollout_payload(
                branch_replay_manifest_path=_write_branch_replay_manifest(root),
                output_dir=root / "branch_rollout",
            )

            markdown = lane_continuation_branch_rollout_markdown(payload)

            self.assertIn("Branch Rollout Gate", markdown)
            self.assertIn("Promote Queue", markdown)
            self.assertIn("Hold Queue", markdown)
            self.assertIn("promote_for_broader_selector_eval", markdown)
            self.assertIn("hold_for_route_context_margin", markdown)
            self.assertIn("speed_minus_route_context_margin", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_rollout_gate_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_replay_manifest = _write_branch_replay_manifest(root)
            output_dir = root / "branch_rollout"
            public_report = root / "reports" / "branch_rollout.md"

            result = generate_lane_continuation_branch_rollout_gate(
                branch_replay_manifest_path=branch_replay_manifest,
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.promoted_case_count, 1)
            self.assertEqual(result.held_route_context_case_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_BRANCH_ROLLOUT_FORMAT,
            )
            self.assertIn("Rollout Summary", public_report.read_text())

    def test_lane_continuation_branch_rollout_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_replay_manifest = _write_branch_replay_manifest(root)
            output_dir = root / "branch_rollout"
            public_report = root / "reports" / "branch_rollout.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-branch-rollout-gate",
                    "--branch-replay-manifest",
                    str(branch_replay_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 2 branch rollout decision", result.stdout)
            self.assertIn("1 promoted candidate", result.stdout)
            self.assertIn("1 route-context hold", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_branch_replay_manifest(root: Path) -> Path:
    manifest = root / "branch_replay_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
                "branch_selection_manifest": "branch_selection/manifest.json",
                "replay_manifest": "replay/manifest.json",
                "ready": True,
                "case_count": 2,
                "minimum_stable_gain_m": 1.0,
                "aggregate": {
                    "replayed_case_count": 2,
                    "perturbation_trial_count": 8,
                },
                "cases": [
                    {
                        "rank": 1,
                        "scenario_id": "260785192cf6c991",
                        "track_id": "1754",
                        "source_name": "validation.tfrecord-00009-of-00150",
                        "ready": True,
                        "default_chain": ["235", "241", "315"],
                        "motion_context_chain": ["235", "307", "306"],
                        "nominal_motion_context_gain_m": 37.766,
                        "perturbation_stability": {
                            "label": "stable_motion_context_branch",
                            "min_gain_m": 32.588,
                            "robustness_margin_m": 31.588,
                        },
                        "acceptance_decision": {
                            "label": "accepted_for_selector_rollout",
                            "accepted": True,
                            "next_action": (
                                "Evaluate this selector behavior on a broader "
                                "branchable continuation queue."
                            ),
                        },
                        "history_speed_prior_stability": {
                            "label": "stable_history_speed_prior_branch",
                            "robustness_margin_m": 31.588,
                        },
                        "history_speed_prior_acceptance_decision": {
                            "label": "accepted_for_selector_rollout",
                            "accepted": True,
                        },
                        "route_context_margin_diagnostic": {
                            "label": "accepted_no_route_context_followup",
                            "priority_score": 0.0,
                            "robustness_gap_to_gate_m": 0.0,
                            "selected_matches_oracle": True,
                            "speed_prior_resolved_margin": False,
                            "next_actions": [
                                "Broaden the branch replay queue with the same acceptance gate.",
                                "Keep this case as a positive control for selector rollout checks.",
                            ],
                        },
                    },
                    {
                        "rank": 4,
                        "scenario_id": "5c49e681a66c720",
                        "track_id": "2627",
                        "source_name": "validation.tfrecord-00010-of-00150",
                        "ready": True,
                        "default_chain": ["285", "120", "119"],
                        "motion_context_chain": ["285", "286", "287"],
                        "nominal_motion_context_gain_m": 3.301,
                        "perturbation_stability": {
                            "label": "branch_stable_gain_sensitive",
                            "min_gain_m": 0.557,
                            "robustness_margin_m": -0.443,
                        },
                        "acceptance_decision": {
                            "label": "needs_route_context_margin",
                            "accepted": False,
                            "next_action": (
                                "Add richer route context or speed-prior "
                                "calibration before treating this branch as robust."
                            ),
                        },
                        "history_speed_prior_stability": {
                            "label": "history_speed_prior_branch_stable_gain_sensitive",
                            "robustness_margin_m": -3.099,
                        },
                        "history_speed_prior_acceptance_decision": {
                            "label": "needs_route_context_margin",
                            "accepted": False,
                        },
                        "route_context_margin_diagnostic": {
                            "label": "speed_minus_route_context_margin",
                            "priority_score": 5.182,
                            "robustness_gap_to_gate_m": 0.443,
                            "selected_matches_oracle": True,
                            "speed_prior_resolved_margin": False,
                            "next_actions": [
                                "Add route-context features that can explain reduced-speed branch intent.",
                                "Test turn-lane, downstream topology, and traffic-control context before selector rollout.",
                            ],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest
