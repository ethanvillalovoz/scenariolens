import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_branch_coverage import (
    LANE_CONTINUATION_BRANCH_COVERAGE_FORMAT,
    generate_lane_continuation_branch_coverage,
    lane_continuation_branch_coverage_markdown,
    lane_continuation_branch_coverage_payload,
)
from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
)
from scenariolens.lane_continuation_candidates import (
    LANE_CONTINUATION_CANDIDATES_FORMAT,
)
from scenariolens.lane_continuation_diagnostics import (
    LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.lane_continuation_route_context_guard import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
)


class LaneContinuationBranchCoverageTest(unittest.TestCase):
    def test_payload_builds_branch_funnel_and_expansion_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = _write_manifests(root)

            payload = lane_continuation_branch_coverage_payload(
                candidate_manifest_path=paths["candidates"],
                replay_manifest_path=paths["replay"],
                diagnostics_manifest_path=paths["diagnostics"],
                branch_selection_manifest_path=paths["branch_selection"],
                branch_replay_manifest_path=paths["branch_replay"],
                route_context_guard_manifest_path=paths["route_guard"],
                output_dir=root / "branch_coverage",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_BRANCH_COVERAGE_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["candidate_count"], 4)
            self.assertEqual(aggregate["branchable_case_count"], 1)
            self.assertEqual(aggregate["single_chain_case_count"], 1)
            self.assertEqual(aggregate["topology_blocker_count"], 1)
            self.assertEqual(aggregate["route_guard_promote_count"], 1)
            self.assertEqual(aggregate["route_guard_hold_count"], 1)
            self.assertEqual(aggregate["expansion_queue_count"], 3)

            bottlenecks = {row["label"]: row for row in payload["bottlenecks"]}
            self.assertIn("topology_parser_gap", bottlenecks)
            self.assertIn("single_chain_no_branch_choice", bottlenecks)
            self.assertIn("route_context_margin_hold", bottlenecks)
            queue_types = [row["queue_type"] for row in payload["expansion_queue"]]
            self.assertEqual(queue_types[0], "route_context_margin")
            self.assertIn("topology_parser_gap", queue_types)

    def test_markdown_names_scope_and_bottlenecks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = _write_manifests(root)
            payload = lane_continuation_branch_coverage_payload(
                candidate_manifest_path=paths["candidates"],
                replay_manifest_path=paths["replay"],
                diagnostics_manifest_path=paths["diagnostics"],
                branch_selection_manifest_path=paths["branch_selection"],
                branch_replay_manifest_path=paths["branch_replay"],
                route_context_guard_manifest_path=paths["route_guard"],
                output_dir=root / "branch_coverage",
            )

            markdown = lane_continuation_branch_coverage_markdown(payload)

            self.assertIn("Branch Coverage Audit", markdown)
            self.assertIn("topology_parser_gap", markdown)
            self.assertIn("single_chain_no_branch_choice", markdown)
            self.assertIn("route_context_margin", markdown)
            self.assertIn("not a Waymo benchmark claim", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

            expanded_payload = {
                **payload,
                "aggregate": {
                    **payload["aggregate"],
                    "candidate_top_per_bucket": 10,
                },
            }
            expanded_markdown = lane_continuation_branch_coverage_markdown(
                expanded_payload
            )
            self.assertIn("Expanded Branch Coverage Audit", expanded_markdown)
            self.assertIn("route-context negative controls", expanded_markdown)

    def test_generate_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = _write_manifests(root)
            public_report = root / "reports" / "branch_coverage.md"

            result = generate_lane_continuation_branch_coverage(
                candidate_manifest_path=paths["candidates"],
                replay_manifest_path=paths["replay"],
                diagnostics_manifest_path=paths["diagnostics"],
                branch_selection_manifest_path=paths["branch_selection"],
                branch_replay_manifest_path=paths["branch_replay"],
                route_context_guard_manifest_path=paths["route_guard"],
                output_dir=root / "branch_coverage",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.candidate_count, 4)
            self.assertEqual(result.branchable_case_count, 1)
            self.assertEqual(result.topology_blocker_count, 1)
            self.assertEqual(result.expansion_queue_count, 3)
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_BRANCH_COVERAGE_FORMAT,
            )
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())

    def test_branch_coverage_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = _write_manifests(root)
            output_dir = root / "branch_coverage"
            public_report = root / "reports" / "branch_coverage.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-branch-coverage",
                    "--candidate-manifest",
                    str(paths["candidates"]),
                    "--replay-manifest",
                    str(paths["replay"]),
                    "--diagnostics-manifest",
                    str(paths["diagnostics"]),
                    "--branch-selection-manifest",
                    str(paths["branch_selection"]),
                    "--branch-replay-manifest",
                    str(paths["branch_replay"]),
                    "--route-context-guard-manifest",
                    str(paths["route_guard"]),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={**os.environ, "PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated branch coverage audit", result.stdout)
            self.assertIn("4 candidate", result.stdout)
            self.assertIn("1 branchable", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_manifests(root: Path) -> dict[str, Path]:
    paths = {
        "candidates": root / "candidates.json",
        "replay": root / "replay.json",
        "diagnostics": root / "diagnostics.json",
        "branch_selection": root / "branch_selection.json",
        "branch_replay": root / "branch_replay.json",
        "route_guard": root / "route_guard.json",
    }
    _write_json(
        paths["candidates"],
        {
            "format": LANE_CONTINUATION_CANDIDATES_FORMAT,
            "ready": True,
            "top_per_bucket": 2,
            "candidates": [
                _candidate("improvement_case", "10", "improvement_replay_control"),
                _candidate("branch_case", "20", "regression_replay_debug"),
                _candidate("single_chain_case", "30", "regression_replay_debug"),
                _candidate("topology_case", "40", "topology_audit"),
            ],
        },
    )
    _write_json(
        paths["replay"],
        {
            "format": LANE_CONTINUATION_REPLAY_FORMAT,
            "ready": True,
            "selected_candidate_count": 4,
            "aggregate": {"replayed_case_count": 3},
            "cases": [
                _case("improvement_case", "10", "improvement_replay_control"),
                _case("branch_case", "20", "regression_replay_debug"),
                _case("single_chain_case", "30", "regression_replay_debug"),
                _case("topology_case", "40", "topology_audit"),
            ],
        },
    )
    _write_json(
        paths["diagnostics"],
        {
            "format": LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
            "ready": True,
            "top": 3,
            "diagnostics": [
                _diagnostic(
                    "branch_case",
                    "20",
                    "regression_replay_debug",
                    "stable_route_choice_regression",
                ),
                _diagnostic(
                    "single_chain_case",
                    "30",
                    "regression_replay_debug",
                    "stable_route_choice_regression",
                ),
                _diagnostic(
                    "topology_case",
                    "40",
                    "topology_audit",
                    "missing_linked_feature",
                ),
            ],
        },
    )
    _write_json(
        paths["branch_selection"],
        {
            "format": LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
            "ready": True,
            "cases": [
                {
                    "rank": 1,
                    "scenario_id": "branch_case",
                    "track_id": "20",
                    "source_name": "validation.tfrecord-00001-of-00150",
                    "branchable": True,
                    "verdict": "motion_context_selector_improves",
                    "oracle_recoverable_fde_m": 5.0,
                    "why_it_matters": "A branchable case improves with context.",
                    "next_actions": ["Replay this branch under perturbation."],
                },
                {
                    "rank": 2,
                    "scenario_id": "single_chain_case",
                    "track_id": "30",
                    "source_name": "validation.tfrecord-00002-of-00150",
                    "branchable": False,
                    "verdict": "single_chain_no_branch_choice",
                    "oracle_recoverable_fde_m": 0.0,
                    "why_it_matters": "No alternate continuation is exposed.",
                    "next_actions": ["Improve topology coverage."],
                },
            ],
        },
    )
    _write_json(
        paths["branch_replay"],
        {
            "format": LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
            "ready": True,
            "cases": [_case("branch_case", "20", "regression_replay_debug")],
        },
    )
    _write_json(
        paths["route_guard"],
        {
            "format": LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
            "ready": True,
            "cases": [
                {
                    "rank": 1,
                    "scenario_id": "branch_case",
                    "track_id": "20",
                    "source_name": "validation.tfrecord-00001-of-00150",
                    "guard_label": "promote_motion_context_candidate",
                    "guard_reason": "Route context is clean.",
                    "first_next_action": "Keep this branch in the queue.",
                },
                {
                    "rank": 2,
                    "scenario_id": "single_chain_case",
                    "track_id": "30",
                    "source_name": "validation.tfrecord-00002-of-00150",
                    "guard_label": "hold_for_route_context_evidence",
                    "guard_reason": "Endpoint alignment dropped.",
                    "first_next_action": "Add route-context evidence.",
                },
            ],
        },
    )
    return paths


def _candidate(scenario_id: str, track_id: str, bucket: str) -> dict[str, object]:
    return {
        "rank": int(track_id),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "bucket": bucket,
        "source_name": f"validation.tfrecord-000{int(track_id) // 10}-of-00150",
        "why_it_matters": "This case exercises the branch coverage funnel.",
    }


def _case(scenario_id: str, track_id: str, bucket: str) -> dict[str, object]:
    return {
        "rank": int(track_id),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "bucket": bucket,
        "source_name": f"validation.tfrecord-000{int(track_id) // 10}-of-00150",
    }


def _diagnostic(
    scenario_id: str,
    track_id: str,
    bucket: str,
    label: str,
) -> dict[str, object]:
    return {
        "rank": int(track_id),
        "scenario_id": scenario_id,
        "track_id": track_id,
        "bucket": bucket,
        "source_name": f"validation.tfrecord-000{int(track_id) // 10}-of-00150",
        "diagnosis_label": label,
        "why_it_matters": "The diagnostic labels the branch expansion blocker.",
        "next_actions": ["Use this diagnostic in the next expansion pass."],
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
