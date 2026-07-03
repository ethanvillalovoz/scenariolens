import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector,
    lane_continuation_terminal_neighborhood_selector_markdown,
    lane_continuation_terminal_neighborhood_selector_payload,
)


class LaneContinuationTerminalNeighborhoodSelectorTest(unittest.TestCase):
    def test_payload_promotes_geometry_clean_case_and_holds_low_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)

            payload = lane_continuation_terminal_neighborhood_selector_payload(
                terminal_neighborhood_replay_manifest_path=replay_manifest,
                output_dir=root / "selector",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["ready_case_count"], 2)
            self.assertEqual(aggregate["selector_promote_count"], 1)
            self.assertEqual(aggregate["selector_hold_count"], 1)
            self.assertEqual(aggregate["replay_gate_accepted_count"], 1)
            self.assertEqual(aggregate["selector_replay_gate_match_count"], 2)
            self.assertEqual(aggregate["selector_false_promote_count"], 0)
            self.assertEqual(aggregate["selector_false_hold_count"], 0)

            promoted, held = payload["cases"]
            self.assertEqual(
                promoted["selector_label"],
                "promote_terminal_neighborhood_alternate",
            )
            self.assertEqual(promoted["selector_selected_feature_id"], "220")
            self.assertTrue(promoted["selector_matches_replay_gate"])
            self.assertEqual(promoted["selector_gate_match_label"], "true_positive_recovery")
            self.assertEqual(
                held["selector_label"],
                "hold_for_terminal_neighborhood_context",
            )
            self.assertEqual(held["selector_selected_feature_id"], "333")
            self.assertIn("selected_heading_below_gate", held["selector_hold_flags"])
            self.assertIn("alternate_heading_below_gate", held["selector_hold_flags"])
            self.assertTrue(held["selector_matches_replay_gate"])

    def test_markdown_explains_non_oracle_selector_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_selector_payload(
                terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
                output_dir=root / "selector",
            )

            markdown = lane_continuation_terminal_neighborhood_selector_markdown(payload)

            self.assertIn("Terminal-Neighborhood Selector Experiment", markdown)
            self.assertIn("promote_terminal_neighborhood_alternate", markdown)
            self.assertIn("hold_for_terminal_neighborhood_context", markdown)
            self.assertIn("Replay-gate labels validate the selector", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_selector_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "selector"
            public_report = root / "reports" / "selector.md"

            result = generate_lane_continuation_terminal_neighborhood_selector(
                terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
                output_dir=output_dir,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.promoted_case_count, 1)
            self.assertEqual(result.held_case_count, 1)
            self.assertEqual(result.replay_gate_match_count, 2)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_FORMAT,
            )

    def test_terminal_neighborhood_selector_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "selector"
            public_report = root / "reports" / "selector.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector",
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

            self.assertIn("Generated terminal-neighborhood selector", result.stdout)
            self.assertIn("1 promoted candidate", result.stdout)
            self.assertIn("1 held candidate", result.stdout)
            self.assertIn("2 replay-gate match", result.stdout)
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
                    "case_count": 2,
                    "replayed_case_count": 2,
                    "accepted_case_count": 1,
                    "held_case_count": 1,
                    "perturbation_trial_count": 8,
                },
                "cases": [
                    _replay_case(
                        rank=12,
                        scenario_id="2f366a31ab03f8b",
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
                        rank=13,
                        scenario_id="74a5b3325a534a87",
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
