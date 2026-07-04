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
    generate_lane_continuation_terminal_neighborhood_selector_calibration,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_transfer,
    lane_continuation_terminal_neighborhood_selector_transfer_markdown,
    lane_continuation_terminal_neighborhood_selector_transfer_payload,
)


class LaneContinuationTerminalNeighborhoodSelectorTransferTest(unittest.TestCase):
    def test_payload_validates_recommended_policy_on_broader_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            calibration = _write_calibration_manifest(root)

            payload = lane_continuation_terminal_neighborhood_selector_transfer_payload(
                selector_calibration_manifest_path=calibration,
                terminal_neighborhood_replay_manifest_path=(
                    _write_validation_replay_manifest(root)
                ),
                output_dir=root / "transfer",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
            )
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["policy_source"], "recommended")
            self.assertEqual(payload["training_scope"]["training_case_count"], 4)
            self.assertEqual(payload["validation_scope"]["validation_case_count"], 5)
            self.assertEqual(payload["validation_scope"]["overlap_case_count"], 2)
            self.assertEqual(payload["validation_scope"]["novel_case_count"], 3)

            current = payload["current_policy_result"]["aggregate"]
            transfer = payload["transfer_policy_result"]["aggregate"]
            novel = payload["novel_aggregate"]
            policy = payload["transfer_policy_result"]["policy"]

            self.assertEqual(policy["min_route_extension_m"], 40.0)
            self.assertEqual(current["selector_false_hold_count"], 2)
            self.assertEqual(transfer["selector_replay_gate_match_count"], 4)
            self.assertEqual(transfer["selector_false_promote_count"], 0)
            self.assertEqual(transfer["selector_false_hold_count"], 1)
            self.assertEqual(novel["case_count"], 3)
            self.assertEqual(novel["selector_false_promote_count"], 0)
            self.assertEqual(novel["selector_false_hold_count"], 1)
            self.assertIn("Keep the default selector unchanged", payload["recommendation"])

            splits = {
                (case["scenario_id"], case["track_id"]): case["validation_split"]
                for case in payload["transfer_policy_result"]["cases"]
            }
            self.assertEqual(
                splits[("accepted_long_extension", "1061")],
                "overlap_with_calibration",
            )
            self.assertEqual(
                splits[("accepted_novel_low_heading", "987")],
                "novel_case",
            )

    def test_markdown_names_transfer_scope_and_remaining_false_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_selector_transfer_payload(
                selector_calibration_manifest_path=_write_calibration_manifest(root),
                terminal_neighborhood_replay_manifest_path=(
                    _write_validation_replay_manifest(root)
                ),
                output_dir=root / "transfer",
            )

            markdown = lane_continuation_terminal_neighborhood_selector_transfer_markdown(
                payload
            )

            self.assertIn("Selector Transfer Validation", markdown)
            self.assertIn("Novel validation cases: 3", markdown)
            self.assertIn("False promotions", markdown)
            self.assertIn("False holds", markdown)
            self.assertIn("false holds", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)
            self.assertIn("not a route planner", markdown)

    def test_generate_transfer_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "transfer"
            public_report = root / "reports" / "selector_transfer.md"

            result = generate_lane_continuation_terminal_neighborhood_selector_transfer(
                selector_calibration_manifest_path=_write_calibration_manifest(root),
                terminal_neighborhood_replay_manifest_path=(
                    _write_validation_replay_manifest(root)
                ),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.validation_case_count, 5)
            self.assertEqual(result.overlap_case_count, 2)
            self.assertEqual(result.novel_case_count, 3)
            self.assertEqual(result.transfer_match_count, 4)
            self.assertEqual(result.transfer_false_promote_count, 0)
            self.assertEqual(result.transfer_false_hold_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
            )

    def test_terminal_neighborhood_selector_transfer_cli_writes_run_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "transfer"
            public_report = root / "reports" / "selector_transfer.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-transfer",
                    "--selector-calibration-manifest",
                    str(_write_calibration_manifest(root)),
                    "--terminal-neighborhood-replay-manifest",
                    str(_write_validation_replay_manifest(root)),
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
                "Generated terminal-neighborhood selector transfer validation",
                result.stdout,
            )
            self.assertIn("5 validation case", result.stdout)
            self.assertIn("3 novel", result.stdout)
            self.assertIn("0 false promote", result.stdout)
            self.assertIn("1 false hold", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_calibration_manifest(root: Path) -> Path:
    output_dir = root / "calibration"
    result = generate_lane_continuation_terminal_neighborhood_selector_calibration(
        terminal_neighborhood_replay_manifest_path=_write_training_replay_manifest(root),
        output_dir=output_dir,
    )
    return result.manifest_path


def _write_training_replay_manifest(root: Path) -> Path:
    manifest = root / "training_replay_manifest.json"
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
                        selected_heading=0.984,
                        alternate_heading=0.984,
                        alternate_distance=0.988,
                        selected_remaining=32.851,
                        alternate_remaining=77.900,
                        gain=37.105,
                        replay_label="accept_for_selector_experiment",
                        replay_accepted=True,
                    ),
                    _replay_case(
                        rank=29,
                        scenario_id="held_short_extension",
                        track_id="150",
                        selected_heading=0.974,
                        alternate_heading=0.974,
                        alternate_distance=2.509,
                        selected_remaining=14.029,
                        alternate_remaining=44.000,
                        gain=-9.087,
                        replay_label="hold_recovery_regressed",
                        replay_accepted=False,
                    ),
                    _replay_case(
                        rank=22,
                        scenario_id="held_low_heading",
                        track_id="3178",
                        selected_heading=0.691,
                        alternate_heading=0.690,
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


def _write_validation_replay_manifest(root: Path) -> Path:
    manifest = root / "validation_replay_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
                "ready": True,
                "terminal_neighborhood_manifest": "terminal_200/manifest.json",
                "topology_manifest": "topology_200/manifest.json",
                "replay_manifest": "replay_200/manifest.json",
                "aggregate": {
                    "case_count": 5,
                    "replayed_case_count": 5,
                    "accepted_case_count": 3,
                    "held_case_count": 2,
                    "perturbation_trial_count": 20,
                },
                "cases": [
                    _replay_case(
                        rank=31,
                        scenario_id="accepted_long_extension",
                        track_id="1061",
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
                        rank=34,
                        scenario_id="held_low_heading",
                        track_id="3178",
                        selected_heading=0.691,
                        alternate_heading=0.690,
                        alternate_distance=2.533,
                        selected_remaining=23.515,
                        alternate_remaining=95.966,
                        gain=-15.163,
                        replay_label="hold_recovery_regressed",
                        replay_accepted=False,
                    ),
                    _replay_case(
                        rank=35,
                        scenario_id="accepted_novel_route_transfer",
                        track_id="987",
                        selected_heading=0.984,
                        alternate_heading=0.984,
                        alternate_distance=1.250,
                        selected_remaining=18.000,
                        alternate_remaining=63.000,
                        gain=26.119,
                        replay_label="accept_for_selector_experiment",
                        replay_accepted=True,
                    ),
                    _replay_case(
                        rank=36,
                        scenario_id="accepted_novel_low_heading",
                        track_id="987",
                        selected_heading=0.886,
                        alternate_heading=0.886,
                        alternate_distance=4.719,
                        selected_remaining=20.000,
                        alternate_remaining=84.000,
                        gain=16.623,
                        replay_label="accept_for_selector_experiment",
                        replay_accepted=True,
                    ),
                    _replay_case(
                        rank=37,
                        scenario_id="held_novel_negative",
                        track_id="116",
                        selected_heading=0.823,
                        alternate_heading=0.823,
                        alternate_distance=0.269,
                        selected_remaining=21.000,
                        alternate_remaining=96.000,
                        gain=-16.230,
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
        "selected_feature_id": f"selected_{rank}",
        "alternate_feature_id": f"alternate_{rank}",
        "selected_chain": [f"selected_{rank}"],
        "alternate_chain": [f"alternate_{rank}", f"next_{rank}"],
        "selected_link_count": 0,
        "alternate_link_count": 1,
        "selected_lane_distance_m": 0.250,
        "alternate_lane_distance_m": alternate_distance,
        "selected_heading_alignment": selected_heading,
        "alternate_heading_alignment": alternate_heading,
        "selected_route_remaining_m": selected_remaining,
        "alternate_route_remaining_m": alternate_remaining,
        "nominal_gain_m": gain,
        "gate_decision": {
            "label": replay_label,
            "accepted": replay_accepted,
            "reason": "fixture replay label",
            "next_action": "fixture next action",
        },
    }
