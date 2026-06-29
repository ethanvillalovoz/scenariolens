import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_compare_study import (
    BASELINE_COMPARISON_STUDY_FORMAT,
    baseline_comparison_study_markdown,
    baseline_comparison_study_payload,
    generate_baseline_comparison_study,
)
from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class BaselineComparisonStudyTest(unittest.TestCase):
    def test_study_payload_aggregates_repeated_json_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            left_input = root / "left.json"
            right_input = root / "right.json"
            save_scenarios(
                left_input,
                (_lane_following_win(), _pedestrian_fallback()),
            )
            save_scenarios(right_input, (_lane_following_regression(),))

            payload = baseline_comparison_study_payload(
                input_paths=(left_input, right_input),
                output_dir=root / "study",
                max_scenarios=10,
                top=2,
                input_format="scenariolens-json",
            )

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(payload["format"], BASELINE_COMPARISON_STUDY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["source_count"], 2)
            self.assertEqual(payload["scenario_count"], 3)
            self.assertEqual(aggregate["evaluated_target_count"], 3)
            self.assertEqual(aggregate["map_used_count"], 2)
            self.assertEqual(aggregate["fallback_count"], 1)
            self.assertEqual(
                payload["fallback_reasons"],
                {"non_vehicle_or_cyclist_target": 1},
            )
            improvements = payload["top_improvements"]
            regressions = payload["top_regressions"]
            self.assertIsInstance(improvements, list)
            self.assertIsInstance(regressions, list)
            self.assertEqual(improvements[0]["scenario_id"], "lane_following_win")
            self.assertEqual(regressions[0]["scenario_id"], "lane_following_regression")

            markdown = baseline_comparison_study_markdown(payload)
            self.assertIn("Real Waymo Lane-Aware Baseline Study", markdown)
            self.assertIn("Per-Source Summary", markdown)
            self.assertIn("non_vehicle_or_cyclist_target", markdown)
            self.assertIn("Largest Lane-Aware Improvements", markdown)
            self.assertIn("Largest Lane-Aware Regressions", markdown)
            self.assertIn("naive lane-following", markdown)

    def test_generate_study_writes_manifest_report_and_public_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "study"
            public_report = root / "reports" / "lane_aware.md"
            save_scenarios(
                input_path,
                (_lane_following_win(), _lane_following_regression()),
            )

            result = generate_baseline_comparison_study(
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
            self.assertEqual(result.scenario_count, 2)
            self.assertEqual(result.evaluated_target_count, 2)
            self.assertEqual(manifest["format"], BASELINE_COMPARISON_STUDY_FORMAT)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Per-Source Summary", public_report.read_text())


def _lane_following_win() -> Scenario:
    return _lane_scenario(
        scenario_id="lane_following_win",
        target_points=((0, 0, 0, 5, 0), (1, 0, 5, 0, 5), (2, 0, 10, 0, 5)),
    )


def _lane_following_regression() -> Scenario:
    return _lane_scenario(
        scenario_id="lane_following_regression",
        target_points=((0, 0, 0, 5, 0), (1, 5, 0, 5, 0), (2, 10, 0, 5, 0)),
    )


def _lane_scenario(
    scenario_id: str,
    target_points: tuple[tuple[float, float, float, float, float], ...],
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        ego_track_id="ego",
        tags=("tracks_to_predict",),
        metadata={
            "waymo_current_time_index": 0,
            "waymo_tracks_to_predict_track_ids": ["target"],
            "waymo_map_features": [
                {"kind": "lane", "points": [[0.0, 0.0], [0.0, 12.0]]}
            ],
        },
        tracks=(
            _track("ego", "vehicle", ((0, -5, 0, 5, 0), (1, 0, 0, 5, 0))),
            _track("target", "vehicle", target_points),
        ),
    )


def _pedestrian_fallback() -> Scenario:
    return Scenario(
        scenario_id="pedestrian_fallback",
        ego_track_id="ego",
        metadata={
            "waymo_current_time_index": 0,
            "waymo_tracks_to_predict_track_ids": ["ped"],
        },
        tracks=(
            _track("ego", "vehicle", ((0, -5, 0, 5, 0), (1, 0, 0, 5, 0))),
            _track("ped", "pedestrian", ((0, 3, -1, 0, 1), (1, 3, 0, 0, 1))),
        ),
    )


def _track(
    agent_id: str,
    agent_type: str,
    points: tuple[tuple[float, float, float, float, float], ...],
) -> AgentTrack:
    return AgentTrack(
        agent_id=agent_id,
        agent_type=agent_type,  # type: ignore[arg-type]
        states=tuple(
            State(t=t, x=x, y=y, vx=vx, vy=vy)
            for t, x, y, vx, vy in points
        ),
    )


if __name__ == "__main__":
    unittest.main()
