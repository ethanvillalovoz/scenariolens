import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
)
from scenariolens.lane_continuation_route_context_guard import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
    generate_lane_continuation_route_context_guard,
    lane_continuation_route_context_guard_markdown,
    lane_continuation_route_context_guard_payload,
)


class LaneContinuationRouteContextGuardTest(unittest.TestCase):
    def test_payload_promotes_clean_context_and_holds_speed_minus_margin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            branch_selection_manifest = _write_branch_selection_manifest(root)
            branch_replay_manifest = _write_branch_replay_manifest(root)

            payload = lane_continuation_route_context_guard_payload(
                branch_selection_manifest_path=branch_selection_manifest,
                branch_replay_manifest_path=branch_replay_manifest,
                output_dir=root / "route_context_guard",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["guard_promote_count"], 1)
            self.assertEqual(aggregate["guard_hold_count"], 1)
            self.assertEqual(aggregate["guard_replay_gate_match_count"], 2)
            self.assertEqual(aggregate["guard_false_promote_count"], 0)
            self.assertEqual(aggregate["guard_false_hold_count"], 0)
            self.assertEqual(aggregate["speed_minus_margin_held_count"], 1)

            promote, hold = payload["cases"]
            self.assertEqual(
                promote["guard_label"],
                "promote_motion_context_candidate",
            )
            self.assertEqual(
                promote["guard_selected_chain"],
                ["235", "307", "306"],
            )
            self.assertTrue(promote["guard_matches_replay_gate"])
            self.assertEqual(
                hold["guard_label"],
                "hold_for_route_context_evidence",
            )
            self.assertEqual(hold["guard_selected_chain"], ["285", "120", "119"])
            self.assertIn("endpoint_alignment_drop", hold["route_context_flags"])
            self.assertIn("downstream_speed_limit_drop", hold["route_context_flags"])

    def test_markdown_explains_guard_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_route_context_guard_payload(
                branch_selection_manifest_path=_write_branch_selection_manifest(root),
                branch_replay_manifest_path=_write_branch_replay_manifest(root),
                output_dir=root / "route_context_guard",
            )

            markdown = lane_continuation_route_context_guard_markdown(payload)

            self.assertIn("Route-Context Guard Study", markdown)
            self.assertIn("promote_motion_context_candidate", markdown)
            self.assertIn("hold_for_route_context_evidence", markdown)
            self.assertIn("endpoint_alignment_drop", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_guard_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "route_context_guard"
            public_report = root / "reports" / "route_context_guard.md"

            result = generate_lane_continuation_route_context_guard(
                branch_selection_manifest_path=_write_branch_selection_manifest(root),
                branch_replay_manifest_path=_write_branch_replay_manifest(root),
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
                LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
            )

    def test_route_context_guard_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "route_context_guard"
            public_report = root / "reports" / "route_context_guard.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-route-context-guard",
                    "--branch-selection-manifest",
                    str(_write_branch_selection_manifest(root)),
                    "--branch-replay-manifest",
                    str(_write_branch_replay_manifest(root)),
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

            self.assertIn("Generated 2 route-context guard decision", result.stdout)
            self.assertIn("1 promoted candidate", result.stdout)
            self.assertIn("1 hold", result.stdout)
            self.assertIn("2 replay-gate match", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_branch_selection_manifest(root: Path) -> Path:
    manifest = root / "branch_selection_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
                "ready": True,
                "cases": [
                    _branch_case(
                        rank=1,
                        scenario_id="260785192cf6c991",
                        track_id="1754",
                        source_name="validation.tfrecord-00009-of-00150",
                        default_chain=["235", "241", "315"],
                        motion_chain=["235", "307", "306"],
                        motion_gain=37.766,
                        route_fit_delta=0.077,
                        endpoint_delta=-0.001,
                        speed_drop_delta=0.0,
                        route_remaining_delta=-37.679,
                    ),
                    _branch_case(
                        rank=4,
                        scenario_id="5c49e681a66c720",
                        track_id="2627",
                        source_name="validation.tfrecord-00010-of-00150",
                        default_chain=["285", "120", "119"],
                        motion_chain=["285", "286", "287"],
                        motion_gain=3.301,
                        route_fit_delta=0.2,
                        endpoint_delta=-0.234,
                        speed_drop_delta=0.286,
                        route_remaining_delta=-12.219,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _branch_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    source_name: str,
    default_chain: list[str],
    motion_chain: list[str],
    motion_gain: float,
    route_fit_delta: float,
    endpoint_delta: float,
    speed_drop_delta: float,
    route_remaining_delta: float,
) -> dict[str, object]:
    default_route_fit = -0.8
    default_endpoint = 1.0
    default_speed_drop = 0.0
    default_route_remaining = 110.0
    default_score = -0.25
    return {
        "rank": rank,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": source_name,
        "ready": True,
        "branchable": True,
        "verdict": "motion_context_selector_improves",
        "default_chain": default_chain,
        "motion_context_chain": motion_chain,
        "default_fde_m": 40.0,
        "motion_context_fde_m": round(40.0 - motion_gain, 3),
        "motion_context_recoverable_fde_m": motion_gain,
        "route_candidates": [
            {
                "feature_chain": default_chain,
                "is_default": True,
                "is_motion_context_selected": False,
                "motion_context_route_fit": default_route_fit,
                "motion_context_endpoint_alignment": default_endpoint,
                "motion_context_speed_limit_drop": default_speed_drop,
                "motion_context_score": default_score,
                "route_remaining_m": default_route_remaining,
            },
            {
                "feature_chain": motion_chain,
                "is_default": False,
                "is_motion_context_selected": True,
                "motion_context_route_fit": default_route_fit + route_fit_delta,
                "motion_context_endpoint_alignment": (
                    default_endpoint + endpoint_delta
                ),
                "motion_context_speed_limit_drop": (
                    default_speed_drop + speed_drop_delta
                ),
                "motion_context_score": default_score + 0.3,
                "route_remaining_m": default_route_remaining + route_remaining_delta,
            },
        ],
    }


def _write_branch_replay_manifest(root: Path) -> Path:
    manifest = root / "branch_replay_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
                "ready": True,
                "cases": [
                    _replay_case(
                        scenario_id="260785192cf6c991",
                        track_id="1754",
                        acceptance="accepted_for_selector_rollout",
                        route_context="accepted_no_route_context_followup",
                    ),
                    _replay_case(
                        scenario_id="5c49e681a66c720",
                        track_id="2627",
                        acceptance="needs_route_context_margin",
                        route_context="speed_minus_route_context_margin",
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
    scenario_id: str,
    track_id: str,
    acceptance: str,
    route_context: str,
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "track_id": track_id,
        "acceptance_decision": {
            "label": acceptance,
        },
        "route_context_margin_diagnostic": {
            "label": route_context,
        },
    }
