import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_calibration import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_calibration,
    lane_continuation_terminal_neighborhood_selector_calibration_markdown,
    lane_continuation_terminal_neighborhood_selector_calibration_payload,
)


class LaneContinuationTerminalNeighborhoodSelectorCalibrationTest(unittest.TestCase):
    def test_payload_recommends_less_conservative_route_extension_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            payload = lane_continuation_terminal_neighborhood_selector_calibration_payload(
                terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
                output_dir=root / "calibration",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 4)
            self.assertEqual(aggregate["policy_count"], 30)
            self.assertEqual(aggregate["current_false_hold_count"], 1)
            self.assertEqual(aggregate["current_false_promote_count"], 0)
            self.assertEqual(aggregate["recommended_false_hold_count"], 0)
            self.assertEqual(aggregate["recommended_false_promote_count"], 0)

            recommended = payload["recommended_policy"]
            self.assertEqual(recommended["max_alternate_distance_m"], 5.0)
            self.assertEqual(recommended["min_heading_alignment"], 0.95)
            self.assertEqual(recommended["min_route_extension_m"], 40.0)
            self.assertEqual(recommended["selector_promote_count"], 2)
            self.assertEqual(recommended["selector_hold_count"], 2)
            self.assertEqual(recommended["selector_replay_gate_match_count"], 4)

            route_to_policy = {
                (
                    policy["max_alternate_distance_m"],
                    policy["min_heading_alignment"],
                    policy["min_route_extension_m"],
                ): policy
                for policy in payload["policy_candidates"]
            }
            self.assertEqual(route_to_policy[(5.0, 0.95, 10.0)]["false_promote_count"], 1)
            changed = [
                case
                for case in payload["cases"]
                if case["changed_by_recommendation"]
            ]
            self.assertEqual(len(changed), 1)
            self.assertEqual(changed[0]["scenario_id"], "accepted_mid_extension")

    def test_markdown_names_scope_recommendation_and_negative_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_selector_calibration_payload(
                terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
                output_dir=root / "calibration",
            )

            markdown = (
                lane_continuation_terminal_neighborhood_selector_calibration_markdown(
                    payload
                )
            )

            self.assertIn("Terminal-Neighborhood Selector Calibration", markdown)
            self.assertIn("Route-extension gate search", markdown)
            self.assertIn("40.000 m", markdown)
            self.assertIn("false hold", markdown)
            self.assertIn("negative control", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_calibration_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "calibration"
            public_report = root / "reports" / "selector_calibration.md"

            result = generate_lane_continuation_terminal_neighborhood_selector_calibration(
                terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 4)
            self.assertEqual(result.policy_count, 30)
            self.assertEqual(result.current_false_hold_count, 1)
            self.assertEqual(result.recommended_false_hold_count, 0)
            self.assertEqual(result.recommended_false_promote_count, 0)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
            )

    def test_terminal_neighborhood_selector_calibration_cli_writes_run_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "calibration"
            public_report = root / "reports" / "selector_calibration.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-calibration",
                    "--terminal-neighborhood-replay-manifest",
                    str(_write_replay_manifest(root)),
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

            self.assertIn(
                "Generated terminal-neighborhood selector calibration",
                result.stdout,
            )
            self.assertIn("30 policy candidate", result.stdout)
            self.assertIn("current false hold(s): 1", result.stdout)
            self.assertIn("recommended false hold(s): 0", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_replay_manifest(root: Path) -> Path:
    manifest = root / "terminal_replay_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
                "ready": True,
                "terminal_neighborhood_manifest": "terminal/manifest.json",
                "topology_manifest": "topology/manifest.json",
                "replay_manifest": "replay/manifest.json",
                "aggregate": {
                    "case_count": 4,
                    "replayed_case_count": 4,
                    "accepted_case_count": 2,
                    "held_case_count": 2,
                    "perturbation_trial_count": 16,
                },
                "cases": [
                    _replay_case(
                        rank=21,
                        scenario_id="accepted_long_extension",
                        track_id="1061",
                        selected_feature_id="219",
                        alternate_feature_id="220",
                        selected_chain=["219"],
                        alternate_chain=["220", "210"],
                        selected_link_count=0,
                        alternate_link_count=1,
                        selected_heading=1.0,
                        alternate_heading=1.0,
                        alternate_distance=3.534,
                        selected_remaining=26.476,
                        alternate_remaining=255.255,
                        gain=125.481,
                        replay_label="accept_for_selector_experiment",
                        replay_accepted=True,
                    ),
                    _replay_case(
                        rank=27,
                        scenario_id="accepted_mid_extension",
                        track_id="816",
                        selected_feature_id="155",
                        alternate_feature_id="344",
                        selected_chain=["155"],
                        alternate_chain=["344", "346", "353"],
                        selected_link_count=0,
                        alternate_link_count=2,
                        selected_heading=0.997,
                        alternate_heading=0.984,
                        alternate_distance=0.988,
                        selected_remaining=14.029,
                        alternate_remaining=62.065,
                        gain=37.105,
                        replay_label="accept_for_selector_experiment",
                        replay_accepted=True,
                    ),
                    _replay_case(
                        rank=29,
                        scenario_id="held_short_extension",
                        track_id="150",
                        selected_feature_id="269",
                        alternate_feature_id="268",
                        selected_chain=["269"],
                        alternate_chain=["268", "265", "263"],
                        selected_link_count=0,
                        alternate_link_count=2,
                        selected_heading=0.975,
                        alternate_heading=0.974,
                        alternate_distance=2.509,
                        selected_remaining=27.667,
                        alternate_remaining=44.088,
                        gain=-9.087,
                        replay_label="hold_recovery_regressed",
                        replay_accepted=False,
                    ),
                    _replay_case(
                        rank=22,
                        scenario_id="held_low_heading",
                        track_id="3178",
                        selected_feature_id="333",
                        alternate_feature_id="331",
                        selected_chain=["333"],
                        alternate_chain=["331", "205"],
                        selected_link_count=0,
                        alternate_link_count=1,
                        selected_heading=0.691,
                        alternate_heading=0.69,
                        alternate_distance=2.533,
                        selected_remaining=23.515,
                        alternate_remaining=95.966,
                        gain=-15.163,
                        replay_label="hold_recovery_regressed",
                        replay_accepted=False,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _replay_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    selected_feature_id: str,
    alternate_feature_id: str,
    selected_chain: list[str],
    alternate_chain: list[str],
    selected_link_count: int,
    alternate_link_count: int,
    selected_heading: float,
    alternate_heading: float,
    alternate_distance: float,
    selected_remaining: float,
    alternate_remaining: float,
    gain: float,
    replay_label: str,
    replay_accepted: bool,
) -> dict[str, object]:
    return {
        "rank": rank,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "validation.tfrecord-00007-of-00150",
        "ready": True,
        "selected_feature_id": selected_feature_id,
        "alternate_feature_id": alternate_feature_id,
        "selected_chain": selected_chain,
        "alternate_chain": alternate_chain,
        "selected_link_count": selected_link_count,
        "alternate_link_count": alternate_link_count,
        "selected_lane_distance_m": 0.223,
        "alternate_lane_distance_m": alternate_distance,
        "selected_heading_alignment": selected_heading,
        "alternate_heading_alignment": alternate_heading,
        "selected_route_remaining_m": selected_remaining,
        "alternate_route_remaining_m": alternate_remaining,
        "nominal_gain_m": gain,
        "gate_decision": {
            "label": replay_label,
            "accepted": replay_accepted,
        },
    }


if __name__ == "__main__":
    unittest.main()
