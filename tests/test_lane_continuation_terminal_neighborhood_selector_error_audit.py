import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_selector_error_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ERROR_AUDIT_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_error_audit,
    lane_continuation_terminal_neighborhood_selector_error_audit_markdown,
    lane_continuation_terminal_neighborhood_selector_error_audit_payload,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
)


class LaneContinuationTerminalNeighborhoodSelectorErrorAuditTest(unittest.TestCase):
    def test_payload_diagnoses_false_holds_and_counterfactual_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            payload = lane_continuation_terminal_neighborhood_selector_error_audit_payload(
                selector_transfer_manifest_path=_write_transfer_manifest(root),
                output_dir=root / "audit",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ERROR_AUDIT_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 5)
            self.assertEqual(aggregate["false_promote_count"], 0)
            self.assertEqual(aggregate["false_hold_count"], 2)
            self.assertEqual(aggregate["novel_false_hold_count"], 2)
            self.assertEqual(aggregate["heading_blocked_false_hold_count"], 2)
            self.assertEqual(aggregate["route_blocked_false_hold_count"], 0)
            self.assertEqual(aggregate["mean_false_hold_gain_m"], 32.505)

            policies = {
                policy["policy_label"]: policy
                for policy in payload["counterfactual_policies"]
            }
            self.assertEqual(policies["transferred_policy"]["false_hold_count"], 2)
            self.assertEqual(policies["relax_heading_to_0.70"]["false_hold_count"], 1)
            self.assertEqual(policies["relax_heading_to_0.70"]["false_promote_count"], 0)
            self.assertEqual(
                policies["relax_heading_0.70_route_25m"]["false_promote_count"],
                1,
            )

            false_holds = payload["false_hold_cases"]
            self.assertEqual(false_holds[0]["diagnosis"], "borderline heading gate miss")
            self.assertEqual(false_holds[1]["diagnosis"], "severe heading disagreement")
            self.assertIn("relax_heading_to_0.70", payload["recommendation"])

    def test_markdown_names_counterfactuals_and_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_selector_error_audit_payload(
                selector_transfer_manifest_path=_write_transfer_manifest(root),
                output_dir=root / "audit",
            )

            markdown = lane_continuation_terminal_neighborhood_selector_error_audit_markdown(
                payload
            )

            self.assertIn("Selector Error Audit", markdown)
            self.assertIn("Counterfactual Gate Sweep", markdown)
            self.assertIn("relax_heading_to_0.70", markdown)
            self.assertIn("severe heading disagreement", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)
            self.assertIn("not a route planner", markdown)

    def test_generate_error_audit_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "audit"
            public_report = root / "reports" / "selector_error_audit.md"

            result = generate_lane_continuation_terminal_neighborhood_selector_error_audit(
                selector_transfer_manifest_path=_write_transfer_manifest(root),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 5)
            self.assertEqual(result.false_hold_count, 2)
            self.assertEqual(result.false_promote_count, 0)
            self.assertEqual(result.counterfactual_policy_count, 5)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ERROR_AUDIT_FORMAT,
            )

    def test_terminal_neighborhood_selector_error_audit_cli_writes_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "audit"
            public_report = root / "reports" / "selector_error_audit.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-error-audit",
                    "--selector-transfer-manifest",
                    str(_write_transfer_manifest(root)),
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
                "Generated terminal-neighborhood selector error audit",
                result.stdout,
            )
            self.assertIn("5 case", result.stdout)
            self.assertIn("0 false promote", result.stdout)
            self.assertIn("2 false hold", result.stdout)
            self.assertIn("5 counterfactual policy", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_transfer_manifest(root: Path) -> Path:
    manifest = root / "selector_transfer_manifest.json"
    cases = [
        _case(
            rank=31,
            split="overlap_with_calibration",
            scenario_id="accepted_long_extension",
            track_id="1061",
            accepted=True,
            match_label="true_positive_recovery",
            promotes=True,
            heading=1.0,
            route_extension=228.779,
            gain=125.481,
            hold_flags=[],
        ),
        _case(
            rank=34,
            split="overlap_with_calibration",
            scenario_id="held_low_heading",
            track_id="3178",
            accepted=False,
            match_label="true_hold",
            promotes=False,
            heading=0.690,
            route_extension=72.451,
            gain=-15.163,
            hold_flags=["selected_heading_below_gate", "alternate_heading_below_gate"],
        ),
        _case(
            rank=35,
            split="novel_case",
            scenario_id="accepted_borderline_heading",
            track_id="987",
            accepted=True,
            match_label="false_hold",
            promotes=False,
            heading=0.886,
            route_extension=56.882,
            gain=26.119,
            hold_flags=["alternate_heading_below_gate"],
        ),
        _case(
            rank=36,
            split="novel_case",
            scenario_id="held_route_negative",
            track_id="116",
            accepted=False,
            match_label="true_hold",
            promotes=False,
            heading=0.823,
            route_extension=32.514,
            gain=-16.230,
            hold_flags=["alternate_heading_below_gate", "route_extension_below_gate"],
        ),
        _case(
            rank=42,
            split="novel_case",
            scenario_id="accepted_severe_heading",
            track_id="88",
            accepted=True,
            match_label="false_hold",
            promotes=False,
            heading=0.122,
            route_extension=70.140,
            gain=38.890,
            hold_flags=["selected_heading_below_gate", "alternate_heading_below_gate"],
        ),
    ]
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
                "ready": True,
                "training_scope": {"training_case_count": 4},
                "validation_scope": {
                    "validation_case_count": 5,
                    "overlap_case_count": 2,
                    "novel_case_count": 3,
                    "replay_gate_accepted_count": 3,
                    "replay_gate_held_count": 2,
                    "perturbation_trial_count": 20,
                },
                "transfer_policy_result": {
                    "policy": {
                        "max_alternate_distance_m": 5.0,
                        "min_heading_alignment": 0.95,
                        "min_route_extension_m": 40.0,
                        "require_chain_extension": True,
                    },
                    "aggregate": {
                        "case_count": 5,
                        "selector_false_promote_count": 0,
                        "selector_false_hold_count": 2,
                    },
                    "cases": cases,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _case(
    rank: int,
    split: str,
    scenario_id: str,
    track_id: str,
    accepted: bool,
    match_label: str,
    promotes: bool,
    heading: float,
    route_extension: float,
    gain: float,
    hold_flags: list[str],
) -> dict[str, object]:
    return {
        "rank": rank,
        "validation_split": split,
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
        "selected_lane_distance_m": 0.25,
        "alternate_lane_distance_m": 2.0,
        "selected_heading_alignment": heading,
        "alternate_heading_alignment": heading,
        "minimum_heading_alignment": heading,
        "selected_route_remaining_m": 20.0,
        "alternate_route_remaining_m": 20.0 + route_extension,
        "route_extension_m": route_extension,
        "chain_extended": True,
        "replay_gain_m": gain,
        "replay_gate_label": (
            "accept_for_selector_experiment"
            if accepted
            else "hold_recovery_regressed"
        ),
        "replay_gate_accepted": accepted,
        "selector_label": (
            "promote_terminal_neighborhood_alternate"
            if promotes
            else "hold_for_terminal_neighborhood_context"
        ),
        "selector_promotes": promotes,
        "selector_matches_replay_gate": promotes == accepted,
        "selector_gate_match_label": match_label,
        "selector_hold_flags": hold_flags,
    }
