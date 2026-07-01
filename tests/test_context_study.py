import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.context_study import (
    CONTEXT_STUDY_FORMAT,
    context_study_markdown,
    context_study_payload,
    generate_context_study,
)
from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class ContextStudyTest(unittest.TestCase):
    def test_context_payload_aggregates_map_signal_and_route_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            left = root / "left.json"
            right = root / "right.json"
            save_scenarios(left, (_context_rich_scenario(),))
            save_scenarios(right, (_plain_scenario(),))

            payload = context_study_payload(
                input_paths=(left, right),
                output_dir=root / "context",
                max_scenarios=10,
                top=3,
                input_format="scenariolens-json",
            )

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(payload["format"], CONTEXT_STUDY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["source_count"], 2)
            self.assertEqual(payload["scenario_count"], 2)
            self.assertEqual(aggregate["map_context_scenario_count"], 1)
            self.assertEqual(aggregate["signal_context_scenario_count"], 1)
            self.assertEqual(aggregate["route_context_scenario_count"], 1)
            self.assertEqual(aggregate["map_feature_count"], 2)
            self.assertEqual(aggregate["lane_count"], 1)
            self.assertEqual(aggregate["signal_lane_state_count"], 3)
            self.assertEqual(aggregate["route_link_count"], 3)
            self.assertEqual(
                payload["signal_state_counts"],
                {"LANE_STATE_GO": 1, "LANE_STATE_STOP": 2},
            )
            self.assertEqual(payload["top_signal_dense_scenarios"][0]["scenario_id"], "context_rich")

            markdown = context_study_markdown(payload)
            self.assertIn("Waymo Map and Signal Context Study", markdown)
            self.assertIn("Traffic Signal Summary", markdown)
            self.assertIn("Route-Context Scenarios", markdown)
            self.assertIn("LANE_STATE_STOP", markdown)

    def test_generate_context_study_writes_manifest_report_and_public_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "context"
            public_report = root / "reports" / "context.md"
            save_scenarios(input_path, (_context_rich_scenario(),))

            result = generate_context_study(
                input_paths=(input_path,),
                output_dir=output_dir,
                input_format="scenariolens-json",
                max_scenarios=10,
                top=2,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.source_count, 1)
            self.assertEqual(result.scenario_count, 1)
            self.assertEqual(manifest["format"], CONTEXT_STUDY_FORMAT)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Static Map Summary", public_report.read_text())

    def test_context_study_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "context"
            public_report = root / "reports" / "context.md"
            save_scenarios(input_path, (_context_rich_scenario(),))

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "context-study",
                    "--input",
                    str(input_path),
                    "--format",
                    "scenariolens-json",
                    "--output-dir",
                    str(output_dir),
                    "--max-scenarios",
                    "10",
                    "--top",
                    "2",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Analyzed 1 scenario", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _context_rich_scenario() -> Scenario:
    return Scenario(
        scenario_id="context_rich",
        source="fixture",
        ego_track_id="ego",
        tags=("map_context", "traffic_signal_context", "tracks_to_predict"),
        metadata={
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "feature_id": "1001",
                    "feature_type": "TYPE_SURFACE_STREET",
                    "points": [[0.0, 0.0], [10.0, 0.0]],
                    "speed_limit_mph": 35.0,
                    "entry_lanes": [9001],
                    "exit_lanes": [9002],
                    "left_neighbor_count": 1,
                },
                {
                    "kind": "crosswalk",
                    "feature_id": "2001",
                    "points": [[1.0, -1.0], [2.0, -1.0], [2.0, 1.0], [1.0, 1.0]],
                },
            ],
            "waymo_map_summary": {
                "feature_count": 2,
                "kind_counts": {"crosswalk": 1, "lane": 1},
                "lane_count": 1,
                "lane_type_counts": {"TYPE_SURFACE_STREET": 1},
                "lane_speed_limit_count": 1,
                "mean_lane_speed_limit_mph": 35.0,
                "entry_link_count": 1,
                "exit_link_count": 1,
                "neighbor_link_count": 1,
                "route_link_count": 3,
                "has_route_context": True,
            },
            "waymo_dynamic_map_summary": {
                "timestep_count": 2,
                "observed_timestep_count": 2,
                "lane_state_count": 3,
                "controlled_lane_count": 1,
                "stop_point_count": 3,
                "state_counts": {"LANE_STATE_GO": 1, "LANE_STATE_STOP": 2},
                "stop_state_count": 2,
                "caution_state_count": 0,
                "go_state_count": 1,
                "unknown_state_count": 0,
            },
        },
        tracks=(
            _track("ego", "vehicle"),
            _track("target", "vehicle"),
        ),
    )


def _plain_scenario() -> Scenario:
    return Scenario(
        scenario_id="plain",
        source="fixture",
        ego_track_id="ego",
        tracks=(_track("ego", "vehicle"),),
    )


def _track(agent_id: str, agent_type: str) -> AgentTrack:
    return AgentTrack(
        agent_id=agent_id,
        agent_type=agent_type,  # type: ignore[arg-type]
        states=(
            State(t=0.0, x=0.0, y=0.0, vx=1.0, vy=0.0),
            State(t=1.0, x=1.0, y=0.0, vx=1.0, vy=0.0),
        ),
    )


if __name__ == "__main__":
    unittest.main()
