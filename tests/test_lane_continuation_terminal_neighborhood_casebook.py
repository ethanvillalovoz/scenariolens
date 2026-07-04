import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_casebook import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
    generate_lane_continuation_terminal_neighborhood_casebook,
    lane_continuation_terminal_neighborhood_casebook_markdown,
    lane_continuation_terminal_neighborhood_casebook_payload,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_calibration import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
)


class LaneContinuationTerminalNeighborhoodCasebookTest(unittest.TestCase):
    def test_payload_writes_public_safe_svg_cards_from_calibration_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "casebook"

            payload = lane_continuation_terminal_neighborhood_casebook_payload(
                selector_calibration_manifest_path=_write_calibration_manifest(root),
                output_dir=output_dir,
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["visual_asset_count"], 2)
            self.assertEqual(aggregate["current_false_hold_count"], 1)
            self.assertEqual(aggregate["recommended_false_hold_count"], 0)
            self.assertEqual(aggregate["recommended_promote_count"], 1)

            first = payload["cases"][0]
            self.assertEqual(first["case_label"], "Case 01")
            self.assertIn("Calibration recovery", first["case_read"])
            card = output_dir / first["asset_path"]
            self.assertTrue(card.exists())
            card_text = card.read_text(encoding="utf-8")
            self.assertIn("<svg", card_text)
            self.assertIn("Route extension", card_text)
            self.assertIn("Replay gain", card_text)

    def test_markdown_links_visual_cards_and_names_limitations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_casebook_payload(
                selector_calibration_manifest_path=_write_calibration_manifest(root),
                output_dir=root / "casebook",
            )

            markdown = lane_continuation_terminal_neighborhood_casebook_markdown(payload)

            self.assertIn("Terminal-Neighborhood Selector Casebook", markdown)
            self.assertIn("![Case 01 selector diagnostic]", markdown)
            self.assertIn("Visual cards are derived metric diagrams", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)
            self.assertIn("not a Waymo benchmark claim", markdown)

    def test_generate_casebook_writes_manifest_report_public_report_and_assets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "casebook"
            public_report = root / "reports" / "terminal_casebook.md"

            result = generate_lane_continuation_terminal_neighborhood_casebook(
                selector_calibration_manifest_path=_write_calibration_manifest(root),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.asset_count, 2)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertTrue(
                (public_report.parent / "assets" / "terminal_selector_casebook_01.svg")
                .exists()
            )
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
            )

    def test_terminal_neighborhood_casebook_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "casebook"
            public_report = root / "reports" / "terminal_casebook.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-casebook",
                    "--selector-calibration-manifest",
                    str(_write_calibration_manifest(root)),
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
                "Generated terminal-neighborhood selector casebook",
                result.stdout,
            )
            self.assertIn("2 SVG card", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_calibration_manifest(root: Path) -> Path:
    manifest = root / "selector_calibration_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
                "ready": True,
                "terminal_neighborhood_replay_manifest": "terminal_replay/manifest.json",
                "terminal_neighborhood_audit_manifest": "terminal_audit/manifest.json",
                "topology_manifest": "topology/manifest.json",
                "source_scope": {
                    "replay_case_count": 2,
                    "replayed_case_count": 2,
                    "accepted_case_count": 1,
                    "held_case_count": 1,
                    "perturbation_trial_count": 8,
                },
                "current_policy": {
                    "max_alternate_distance_m": 5.0,
                    "min_heading_alignment": 0.95,
                    "min_route_extension_m": 50.0,
                },
                "aggregate": {
                    "case_count": 2,
                    "ready_case_count": 2,
                    "policy_count": 30,
                    "current_false_hold_count": 1,
                    "current_false_promote_count": 0,
                    "recommended_false_hold_count": 0,
                    "recommended_false_promote_count": 0,
                },
                "current_policy_result": {
                    "selector_replay_gate_match_count": 1,
                    "false_promote_count": 0,
                    "false_hold_count": 1,
                },
                "recommended_policy": {
                    "max_alternate_distance_m": 5.0,
                    "min_heading_alignment": 0.95,
                    "min_route_extension_m": 40.0,
                    "selector_promote_count": 1,
                    "selector_hold_count": 1,
                    "selector_replay_gate_match_count": 2,
                    "false_promote_count": 0,
                    "false_hold_count": 0,
                    "recommendation": "Use as a provisional calibration target.",
                },
                "cases": [
                    _case(
                        scenario_id="accepted_mid_extension",
                        track_id="816",
                        replay_accepted=True,
                        replay_gain=37.105,
                        route_extension=48.036,
                        current_decision="hold_for_terminal_neighborhood_context",
                        recommended_decision="promote_terminal_neighborhood_alternate",
                        changed=True,
                        flags=["route_extension_below_gate"],
                    ),
                    _case(
                        scenario_id="held_low_heading",
                        track_id="3178",
                        replay_accepted=False,
                        replay_gain=-15.163,
                        route_extension=72.451,
                        current_decision="hold_for_terminal_neighborhood_context",
                        recommended_decision="hold_for_terminal_neighborhood_context",
                        changed=False,
                        flags=[
                            "selected_heading_below_gate",
                            "alternate_heading_below_gate",
                        ],
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _case(
    scenario_id: str,
    track_id: str,
    replay_accepted: bool,
    replay_gain: float,
    route_extension: float,
    current_decision: str,
    recommended_decision: str,
    changed: bool,
    flags: list[str],
) -> dict[str, object]:
    return {
        "rank": 27,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "validation.tfrecord-00007-of-00150",
        "ready": True,
        "selected_feature_id": "155",
        "alternate_feature_id": "344",
        "selected_chain": ["155"],
        "alternate_chain": ["344", "346", "353"],
        "selected_link_count": 0,
        "alternate_link_count": 2,
        "selected_lane_distance_m": 0.223,
        "alternate_lane_distance_m": 0.988,
        "selected_heading_alignment": 0.997 if replay_accepted else 0.691,
        "alternate_heading_alignment": 0.984 if replay_accepted else 0.69,
        "minimum_heading_alignment": 0.984 if replay_accepted else 0.69,
        "selected_route_remaining_m": 14.029,
        "alternate_route_remaining_m": 62.065,
        "route_extension_m": route_extension,
        "chain_extended": True,
        "replay_gain_m": replay_gain,
        "replay_gate_label": (
            "accept_for_selector_experiment"
            if replay_accepted
            else "hold_recovery_regressed"
        ),
        "replay_gate_accepted": replay_accepted,
        "selector_hold_flags": flags,
        "selector_checks": {
            "alternate_distance_ok": True,
            "selected_heading_ok": replay_accepted,
            "alternate_heading_ok": replay_accepted,
            "route_extension_ok": route_extension >= 50.0,
            "chain_extension_ok": True,
        },
        "current_decision": current_decision,
        "recommended_decision": recommended_decision,
        "current_match_label": "false_hold" if replay_accepted else "true_hold",
        "recommended_match_label": (
            "true_positive_recovery" if replay_accepted else "true_hold"
        ),
        "changed_by_recommendation": changed,
    }


if __name__ == "__main__":
    unittest.main()
