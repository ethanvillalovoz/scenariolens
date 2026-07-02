import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
    generate_lane_continuation_branch_selection,
    lane_continuation_branch_selection_markdown,
    lane_continuation_branch_selection_payload,
)
from scenariolens.lane_continuation_diagnostics import (
    LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State


class LaneContinuationBranchSelectionTest(unittest.TestCase):
    def test_payload_reports_oracle_branch_upper_bound_and_single_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics_manifest = _write_manifests(root)

            payload = lane_continuation_branch_selection_payload(
                diagnostics_manifest_path=diagnostics_manifest,
                output_dir=root / "branch_selection",
                top=10,
                max_hops=2,
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["branchable_case_count"], 1)
            self.assertEqual(aggregate["single_chain_case_count"], 1)
            self.assertEqual(aggregate["oracle_improved_case_count"], 1)
            self.assertEqual(aggregate["motion_context_improved_case_count"], 1)
            self.assertEqual(
                aggregate["motion_context_oracle_match_branchable_count"],
                1,
            )

            by_id = {case["scenario_id"]: case for case in payload["cases"]}
            branched = by_id["branch_case"]
            self.assertEqual(branched["route_candidate_count"], 2)
            self.assertEqual(branched["default_chain"], ["100", "200"])
            self.assertEqual(branched["motion_context_chain"], ["100", "300"])
            self.assertEqual(branched["oracle_chain"], ["100", "300"])
            self.assertEqual(
                branched["verdict"],
                "motion_context_selector_improves",
            )
            self.assertGreater(branched["motion_context_recoverable_fde_m"], 5.0)
            self.assertGreater(branched["oracle_recoverable_fde_m"], 5.0)

            single = by_id["single_chain_case"]
            self.assertFalse(single["branchable"])
            self.assertEqual(single["verdict"], "single_chain_no_branch_choice")

            markdown = lane_continuation_branch_selection_markdown(payload)
            self.assertIn("Lane-Continuation Branch Selection Diagnostic", markdown)
            self.assertIn("oracle upper bound", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_branch_selection_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics_manifest = _write_manifests(root)
            output_dir = root / "branch_selection"
            public_report = root / "reports" / "branch_selection.md"

            result = generate_lane_continuation_branch_selection(
                diagnostics_manifest_path=diagnostics_manifest,
                output_dir=output_dir,
                top=10,
                max_hops=2,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.branchable_count, 1)
            self.assertEqual(result.motion_context_improved_count, 1)
            self.assertEqual(result.oracle_improved_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
            )
            self.assertIn("Branch Sweep Summary", public_report.read_text())

    def test_lane_continuation_branch_selection_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics_manifest = _write_manifests(root)
            output_dir = root / "branch_selection"
            public_report = root / "reports" / "branch_selection.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-branch-selection",
                    "--diagnostics-manifest",
                    str(diagnostics_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top",
                    "10",
                    "--max-hops",
                    "2",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 2 branch-selection diagnostic", result.stdout)
            self.assertIn("1 motion-context improvement", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_manifests(root: Path) -> Path:
    input_path = root / "branch_fixture.json"
    save_scenarios(
        input_path,
        (
            _branch_scenario(),
            _single_chain_scenario(),
        ),
    )

    replay_manifest = root / "replay_manifest.json"
    replay_manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_REPLAY_FORMAT,
                "ready": True,
                "max_scenarios_per_source": 10,
                "aggregate": {
                    "replayed_case_count": 2,
                    "topology_probe_count": 0,
                },
                "cases": [
                    _replay_case(
                        scenario_id="branch_case",
                        source_input=input_path,
                        feature_chain=["100", "200"],
                        lane_link_fde=12.0,
                    ),
                    _replay_case(
                        scenario_id="single_chain_case",
                        source_input=input_path,
                        feature_chain=["500", "600"],
                        lane_link_fde=0.0,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diagnostics_manifest = root / "diagnostics_manifest.json"
    diagnostics_manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
                "ready": True,
                "replay_manifest": str(replay_manifest),
                "diagnostics": [
                    _diagnostic("branch_case", "stable_route_choice_regression"),
                    _diagnostic("single_chain_case", "stable_route_choice_regression"),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return diagnostics_manifest


def _replay_case(
    scenario_id: str,
    source_input: Path,
    feature_chain: list[str],
    lane_link_fde: float,
) -> dict[str, object]:
    return {
        "ready": True,
        "bucket": "regression_replay_debug",
        "scenario_id": scenario_id,
        "track_id": "veh",
        "source_input": str(source_input),
        "source_name": source_input.name,
        "input_format": "scenariolens-json",
        "nominal": {
            "nearest_lane_fde_m": 4.0,
            "lane_link_fde_m": lane_link_fde,
            "lane_link_improvement_over_nearest_m": 4.0 - lane_link_fde,
            "lane_link_improvement_over_constant_m": 0.0,
            "lane_link_status": "linked_lane_chain",
            "lane_link_count": len(feature_chain) - 1,
            "feature_chain": feature_chain,
        },
    }


def _diagnostic(scenario_id: str, label: str) -> dict[str, object]:
    return {
        "rank": 1 if scenario_id == "branch_case" else 2,
        "bucket": "regression_replay_debug",
        "scenario_id": scenario_id,
        "track_id": "veh",
        "source_name": "branch_fixture.json",
        "diagnosis_label": label,
    }


def _branch_scenario() -> Scenario:
    return Scenario(
        scenario_id="branch_case",
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "feature_id": "100",
                    "points": [[0.0, 0.0], [5.0, 0.0]],
                    "exit_lanes": [200, 300],
                    "speed_limit_mph": 35.0,
                },
                {
                    "kind": "lane",
                    "feature_id": "200",
                    "points": [[5.0, 0.0], [15.0, 0.0]],
                    "entry_lanes": [100],
                    "speed_limit_mph": 35.0,
                },
                {
                    "kind": "lane",
                    "feature_id": "300",
                    "points": [[5.0, 0.0], [5.0, 12.0]],
                    "entry_lanes": [100],
                    "speed_limit_mph": 10.0,
                },
            ],
        },
        tracks=(
            AgentTrack(
                agent_id="veh",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=1.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=1.0, x=4.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=2.0, x=5.0, y=3.0, vx=0.0, vy=3.0),
                    State(t=4.0, x=5.0, y=9.0, vx=0.0, vy=3.0),
                ),
            ),
        ),
    )


def _single_chain_scenario() -> Scenario:
    return Scenario(
        scenario_id="single_chain_case",
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "feature_id": "500",
                    "points": [[0.0, 0.0], [5.0, 0.0]],
                    "exit_lanes": [600],
                },
                {
                    "kind": "lane",
                    "feature_id": "600",
                    "points": [[5.0, 0.0], [15.0, 0.0]],
                    "entry_lanes": [500],
                },
            ],
        },
        tracks=(
            AgentTrack(
                agent_id="veh",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=1.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=1.0, x=4.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=2.0, x=7.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=4.0, x=13.0, y=0.0, vx=3.0, vy=0.0),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
