import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.context_failure_study import (
    CONTEXT_FAILURE_STUDY_FORMAT,
    context_failure_study_markdown,
    context_failure_study_payload,
    generate_context_failure_study,
)
from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class ContextFailureStudyTest(unittest.TestCase):
    def test_context_failure_payload_joins_context_and_baseline_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            left = root / "left.json"
            right = root / "right.json"
            save_scenarios(left, (_signal_route_failure(),))
            save_scenarios(right, (_plain_failure(),))

            payload = context_failure_study_payload(
                input_paths=(left, right),
                output_dir=root / "context_failure",
                max_scenarios=10,
                top=3,
                input_format="scenariolens-json",
            )

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(payload["format"], CONTEXT_FAILURE_STUDY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["source_count"], 2)
            self.assertEqual(payload["scenario_count"], 2)
            self.assertEqual(aggregate["signal_context_scenario_count"], 1)
            self.assertEqual(aggregate["route_context_scenario_count"], 1)
            self.assertGreater(aggregate["evaluated_target_count"], 0)
            group_labels = {group["label"] for group in payload["context_groups"]}
            self.assertIn("Traffic signal context", group_labels)
            self.assertIn("No parsed signal states", group_labels)
            hardest = payload["hardest_context_failures"]
            self.assertEqual(hardest[0]["scenario_id"], "signal_route_failure")

            markdown = context_failure_study_markdown(payload)
            self.assertIn("Context-Joined Failure Study", markdown)
            self.assertIn("Context Buckets", markdown)
            self.assertIn("Signal-Context Failures", markdown)
            self.assertIn("Lane-Aware Regressions With Context", markdown)

    def test_generate_context_failure_study_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "context_failure"
            public_report = root / "reports" / "context_failure.md"
            save_scenarios(input_path, (_signal_route_failure(),))

            result = generate_context_failure_study(
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
            self.assertEqual(manifest["format"], CONTEXT_FAILURE_STUDY_FORMAT)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Hardest Context-Rich", public_report.read_text())

    def test_context_failure_study_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "context_failure"
            public_report = root / "reports" / "context_failure.md"
            save_scenarios(input_path, (_signal_route_failure(),))

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "context-failure-study",
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

            self.assertIn("Joined context and failure metrics for 1 scenario", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _signal_route_failure() -> Scenario:
    return Scenario(
        scenario_id="signal_route_failure",
        source="fixture",
        ego_track_id="ego",
        tags=("map_context", "traffic_signal_context", "tracks_to_predict"),
        metadata={
            "waymo_current_time_index": 0,
            "waymo_tracks_to_predict_track_ids": ["target"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "points": [[0.0, 0.0], [15.0, 0.0]],
                    "speed_limit_mph": 35.0,
                    "entry_lanes": [10],
                    "exit_lanes": [11],
                    "left_neighbor_count": 1,
                }
            ],
            "waymo_map_summary": {
                "feature_count": 1,
                "kind_counts": {"lane": 1},
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
            _track("ego", ((0, -5, 0, 5, 0), (1, 0, 0, 5, 0), (2, 5, 0, 5, 0))),
            _track(
                "target",
                (
                    (0, 0, 0, 5, 0),
                    (1, 2, 4, 5, 0),
                    (2, 2, 9, 5, 0),
                    (3, 2, 14, 5, 0),
                ),
            ),
        ),
    )


def _plain_failure() -> Scenario:
    return Scenario(
        scenario_id="plain_failure",
        source="fixture",
        ego_track_id="ego",
        metadata={
            "waymo_current_time_index": 0,
            "waymo_tracks_to_predict_track_ids": ["target"],
        },
        tracks=(
            _track("ego", ((0, -5, 0, 5, 0), (1, 0, 0, 5, 0), (2, 5, 0, 5, 0))),
            _track(
                "target",
                (
                    (0, 0, 0, 4, 0),
                    (1, 4, 0, 4, 0),
                    (2, 8, 0, 4, 0),
                    (3, 12, 0, 4, 0),
                ),
            ),
        ),
    )


def _track(
    agent_id: str,
    points: tuple[tuple[float, float, float, float, float], ...],
) -> AgentTrack:
    return AgentTrack(
        agent_id=agent_id,
        agent_type="vehicle",
        states=tuple(State(t=t, x=x, y=y, vx=vx, vy=vy) for t, x, y, vx, vy in points),
    )


if __name__ == "__main__":
    unittest.main()
