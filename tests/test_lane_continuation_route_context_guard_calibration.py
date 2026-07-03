import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_route_context_guard import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
)
from scenariolens.lane_continuation_route_context_guard_calibration import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_CALIBRATION_FORMAT,
    generate_lane_continuation_route_context_guard_calibration,
    lane_continuation_route_context_guard_calibration_markdown,
    lane_continuation_route_context_guard_calibration_payload,
)


class LaneContinuationRouteContextGuardCalibrationTest(unittest.TestCase):
    def test_payload_recommends_least_relaxed_gate_without_false_promotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            payload = lane_continuation_route_context_guard_calibration_payload(
                route_context_guard_manifest_path=_write_guard_manifest(root),
                output_dir=root / "calibration",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_CALIBRATION_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 3)
            self.assertEqual(aggregate["policy_count"], 7)
            self.assertEqual(aggregate["current_false_hold_count"], 1)
            self.assertEqual(aggregate["recommended_false_hold_count"], 0)
            self.assertEqual(aggregate["recommended_false_promote_count"], 0)

            recommended = payload["recommended_policy"]
            self.assertEqual(recommended["endpoint_alignment_delta_gate"], -0.25)
            self.assertEqual(recommended["promote_count"], 2)
            self.assertEqual(recommended["hold_count"], 1)
            self.assertEqual(recommended["match_count"], 3)

            endpoint_to_policy = {
                policy["endpoint_alignment_delta_gate"]: policy
                for policy in payload["policy_candidates"]
            }
            self.assertEqual(endpoint_to_policy[-0.3]["false_promote_count"], 1)
            changed = [
                case
                for case in payload["cases"]
                if case["changed_by_recommendation"]
            ]
            self.assertEqual(len(changed), 1)
            self.assertEqual(changed[0]["scenario_id"], "accepted_false_hold")

    def test_markdown_names_scope_recommendation_and_negative_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_route_context_guard_calibration_payload(
                route_context_guard_manifest_path=_write_guard_manifest(root),
                output_dir=root / "calibration",
            )

            markdown = lane_continuation_route_context_guard_calibration_markdown(
                payload
            )

            self.assertIn("Route-Context Guard Calibration", markdown)
            self.assertIn("Endpoint-alignment gate", markdown)
            self.assertIn("-0.250", markdown)
            self.assertIn("false hold", markdown)
            self.assertIn("negative control", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_markdown_validates_current_gate_when_negative_control_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_route_context_guard_calibration_payload(
                route_context_guard_manifest_path=_write_guard_manifest_with_match(
                    root
                ),
                output_dir=root / "calibration",
            )

            markdown = lane_continuation_route_context_guard_calibration_markdown(
                payload
            )

            self.assertEqual(payload["aggregate"]["current_false_hold_count"], 0)
            self.assertEqual(payload["aggregate"]["current_false_promote_count"], 0)
            self.assertEqual(
                payload["recommended_policy"]["endpoint_alignment_delta_gate"],
                -0.05,
            )
            self.assertIn("validates the route-context guard", markdown)
            self.assertIn("0 false holds", markdown)
            self.assertIn("1 replay-held negative control", markdown)
            self.assertNotIn("has no replay-rejected negative controls", markdown)

    def test_generate_calibration_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "calibration"
            public_report = root / "reports" / "calibration.md"

            result = generate_lane_continuation_route_context_guard_calibration(
                route_context_guard_manifest_path=_write_guard_manifest(root),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 3)
            self.assertEqual(result.policy_count, 7)
            self.assertEqual(result.current_false_hold_count, 1)
            self.assertEqual(result.recommended_false_hold_count, 0)
            self.assertEqual(result.recommended_false_promote_count, 0)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_CALIBRATION_FORMAT,
            )

    def test_route_context_guard_calibration_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "calibration"
            public_report = root / "reports" / "calibration.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-route-context-guard-calibration",
                    "--route-context-guard-manifest",
                    str(_write_guard_manifest(root)),
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

            self.assertIn("Generated route-context guard calibration", result.stdout)
            self.assertIn("7 policy candidate", result.stdout)
            self.assertIn("current false hold(s): 1", result.stdout)
            self.assertIn("recommended false hold(s): 0", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_guard_manifest(root: Path) -> Path:
    manifest = root / "route_context_guard_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
                "ready": True,
                "branch_selection_manifest": "branch_selection/manifest.json",
                "branch_replay_manifest": "branch_replay/manifest.json",
                "guard_policy": {
                    "route_fit_delta_gate": 0.0,
                    "endpoint_alignment_delta_gate": -0.05,
                    "speed_limit_drop_delta_gate": 0.1,
                },
                "cases": [
                    _guard_case(
                        scenario_id="accepted_current_promote",
                        endpoint_delta=-0.01,
                        replay_label="accepted_for_selector_rollout",
                        guard_label="promote_motion_context_candidate",
                        gain=40.84,
                    ),
                    _guard_case(
                        scenario_id="accepted_false_hold",
                        endpoint_delta=-0.235706,
                        replay_label="accepted_for_selector_rollout",
                        guard_label="hold_for_route_context_evidence",
                        gain=39.762,
                    ),
                    _guard_case(
                        scenario_id="replay_held_negative",
                        endpoint_delta=-0.27,
                        replay_label="needs_route_context_margin",
                        guard_label="hold_for_route_context_evidence",
                        gain=4.2,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_guard_manifest_with_match(root: Path) -> Path:
    manifest = root / "route_context_guard_manifest_with_match.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
                "ready": True,
                "branch_selection_manifest": "branch_selection/manifest.json",
                "branch_replay_manifest": "branch_replay/manifest.json",
                "guard_policy": {
                    "route_fit_delta_gate": 0.0,
                    "endpoint_alignment_delta_gate": -0.05,
                    "speed_limit_drop_delta_gate": 0.1,
                },
                "cases": [
                    _guard_case(
                        scenario_id="accepted_current_promote",
                        endpoint_delta=-0.01,
                        replay_label="accepted_for_selector_rollout",
                        guard_label="promote_motion_context_candidate",
                        gain=37.766,
                    ),
                    _guard_case(
                        scenario_id="held_negative_control",
                        endpoint_delta=-0.23,
                        replay_label="needs_route_context_margin",
                        guard_label="hold_for_route_context_evidence",
                        gain=3.301,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _guard_case(
    scenario_id: str,
    endpoint_delta: float,
    replay_label: str,
    guard_label: str,
    gain: float,
) -> dict[str, object]:
    return {
        "rank": 1,
        "scenario_id": scenario_id,
        "track_id": "track_1",
        "source_name": "validation.tfrecord-00007-of-00150",
        "ready": True,
        "guard_label": guard_label,
        "replay_acceptance_label": replay_label,
        "replay_route_context_label": "accepted_no_route_context_followup",
        "route_fit_delta": 0.5,
        "endpoint_alignment_delta": endpoint_delta,
        "speed_limit_drop_delta": 0.0,
        "motion_context_gain_m": gain,
    }


if __name__ == "__main__":
    unittest.main()
