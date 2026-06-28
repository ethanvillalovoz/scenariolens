import unittest

from scenariolens.prediction import (
    compare_prediction_baselines,
    constant_velocity_baseline,
    lane_aware_baseline,
)
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class PredictionBaselineTest(unittest.TestCase):
    def test_uses_waymo_prediction_targets_and_current_time_index(self) -> None:
        scenario = Scenario(
            scenario_id="waymo_prediction_target",
            ego_track_id="ego",
            metadata={
                "waymo_current_time_index": 1,
                "waymo_tracks_to_predict_track_ids": ["target"],
            },
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0), (2, 10, 0, 5, 0)),
                ),
                _track(
                    "target",
                    "vehicle",
                    ((0, 0, 3, 4, 0), (1, 4, 3, 4, 0), (2, 4.5, 3, 0, 0)),
                ),
                _track(
                    "ignored",
                    "cyclist",
                    ((0, 0, 8, 10, 0), (1, 10, 8, 10, 0), (2, 20, 8, 10, 0)),
                ),
            ),
        )

        summary = constant_velocity_baseline(scenario)

        self.assertEqual(summary.target_source, "waymo_tracks_to_predict")
        self.assertEqual(summary.requested_target_count, 1)
        self.assertEqual(summary.evaluated_track_count, 1)
        self.assertEqual(summary.track_results[0].track_id, "target")
        self.assertEqual(summary.track_results[0].anchor_time_s, 1)
        self.assertAlmostEqual(summary.fde_m or 0.0, 3.5)
        self.assertEqual(summary.miss_rate, 1.0)
        self.assertGreater(summary.failure_score, 4.0)

    def test_falls_back_to_non_ego_tracks_for_fixtures(self) -> None:
        scenario = Scenario(
            scenario_id="fixture",
            ego_track_id="ego",
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 2, 0), (1, 2, 0, 2, 0))),
                _track("ped", "pedestrian", ((0, 3, -2, 0, 1), (1, 3, -1, 0, 1))),
            ),
        )

        summary = constant_velocity_baseline(scenario)

        self.assertEqual(summary.target_source, "non_ego_tracks")
        self.assertEqual(summary.evaluated_track_count, 1)
        self.assertEqual(summary.ade_m, 0.0)
        self.assertEqual(summary.fde_m, 0.0)
        self.assertEqual(summary.miss_rate, 0.0)

    def test_lane_aware_baseline_improves_curved_lane_fixture(self) -> None:
        scenario = _scenario_by_id("synthetic_curved_lane_prediction")

        constant = constant_velocity_baseline(scenario)
        lane = lane_aware_baseline(scenario)
        comparison = compare_prediction_baselines(scenario)

        self.assertEqual(lane.baseline_name, "lane_aware")
        self.assertEqual(lane.map_used_count, 1)
        self.assertEqual(lane.fallback_count, 0)
        self.assertLess(lane.fde_m or 999.0, constant.fde_m or 0.0)
        self.assertGreater(comparison.fde_improvement_m or 0.0, 3.0)
        self.assertTrue(comparison.track_results[0].lane_map_used)

    def test_lane_aware_baseline_falls_back_for_pedestrians(self) -> None:
        scenario = Scenario(
            scenario_id="pedestrian_with_lane",
            ego_track_id="ego",
            metadata={
                "waymo_current_time_index": 0,
                "waymo_tracks_to_predict_track_ids": ["ped"],
                "waymo_map_features": [
                    {"kind": "lane", "points": [[0.0, 0.0], [10.0, 0.0]]}
                ],
            },
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 1, 0), (1, 1, 0, 1, 0))),
                _track("ped", "pedestrian", ((0, 3, -1, 0, 1), (1, 3, 0, 0, 1))),
            ),
        )

        summary = lane_aware_baseline(scenario)

        self.assertEqual(summary.map_used_count, 0)
        self.assertEqual(summary.fallback_count, 1)
        self.assertEqual(summary.track_results[0].fallback_reason, "non_vehicle_or_cyclist_target")
        self.assertEqual(summary.fde_m, 0.0)

    def test_lane_aware_baseline_falls_back_without_map(self) -> None:
        scenario = Scenario(
            scenario_id="vehicle_without_map",
            metadata={
                "waymo_current_time_index": 0,
                "waymo_tracks_to_predict_track_ids": ["target"],
            },
            tracks=(
                _track("target", "vehicle", ((0, 0, 0, 2, 0), (1, 2, 0, 2, 0))),
            ),
        )

        summary = lane_aware_baseline(scenario)

        self.assertEqual(summary.map_used_count, 0)
        self.assertEqual(summary.fallback_count, 1)
        self.assertEqual(summary.track_results[0].fallback_reason, "no_lane_map_features")


def _scenario_by_id(scenario_id: str) -> Scenario:
    for scenario in synthetic_scenarios():
        if scenario.scenario_id == scenario_id:
            return scenario
    raise AssertionError(f"Missing synthetic scenario: {scenario_id}")


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
