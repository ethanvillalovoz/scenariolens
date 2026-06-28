import unittest

from scenariolens.metrics import (
    closing_time_to_collision,
    interaction_components,
    max_deceleration,
    min_pairwise_distance,
    min_path_distance,
    min_vru_distance,
    score_scenario,
    scoring_context,
)
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class MetricsTest(unittest.TestCase):
    def test_min_pairwise_distance_detects_close_crossing(self) -> None:
        crossing = synthetic_scenarios()[0]

        self.assertAlmostEqual(min_pairwise_distance(crossing), 2.2360679775)

    def test_close_vru_scenario_ranks_above_easy_following(self) -> None:
        scenarios = {scenario.scenario_id: scenario for scenario in synthetic_scenarios()}

        crossing_score = score_scenario(scenarios["synthetic_pedestrian_crossing"])
        following_score = score_scenario(scenarios["synthetic_easy_following"])

        self.assertGreater(
            crossing_score.interaction_score,
            following_score.interaction_score,
        )
        self.assertEqual(crossing_score.vulnerable_road_user_count, 1)
        self.assertIn("pedestrian_crossing", crossing_score.tags)
        self.assertGreater(crossing_score.taxonomy_score, 0.0)
        self.assertGreater(crossing_score.component_scores["vru_proximity"], 0.0)

    def test_vru_distance_targets_vehicle_to_vru_pairs(self) -> None:
        scenarios = {scenario.scenario_id: scenario for scenario in synthetic_scenarios()}

        self.assertAlmostEqual(
            min_vru_distance(scenarios["synthetic_pedestrian_crossing"]),
            2.2360679775,
        )

    def test_path_distance_can_find_cross_time_conflicts(self) -> None:
        scenarios = {scenario.scenario_id: scenario for scenario in synthetic_scenarios()}

        self.assertLessEqual(
            min_path_distance(scenarios["synthetic_unprotected_left_turn"]),
            min_pairwise_distance(scenarios["synthetic_unprotected_left_turn"]),
        )

    def test_max_deceleration_detects_hard_braking(self) -> None:
        scenarios = {scenario.scenario_id: scenario for scenario in synthetic_scenarios()}

        self.assertGreaterEqual(
            max_deceleration(scenarios["synthetic_hard_braking_lead_vehicle"]),
            3.0,
        )

    def test_interaction_components_are_explainable(self) -> None:
        components = interaction_components(
            min_distance_m=2.0,
            min_ttc_s=1.0,
            vru_count=1,
            agent_count=4,
            taxonomy_score=3.0,
            min_vru_distance_m=2.0,
            min_path_distance_m=1.0,
            max_deceleration_mps2=5.0,
        )

        self.assertEqual(
            tuple(components),
            (
                "density",
                "vru",
                "taxonomy",
                "proximity",
                "ttc",
                "vru_proximity",
                "path_conflict",
                "dynamics",
                "baseline_failure",
            ),
        )
        self.assertGreater(components["dynamics"], 0.0)

    def test_scoring_context_filters_low_quality_and_far_tracks(self) -> None:
        scenario = Scenario(
            scenario_id="quality_filter",
            ego_track_id="ego",
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0))),
                _track("ped_near", "pedestrian", ((0, 2, 0, 0, 1), (1, 2, 1, 0, 1))),
                _track("veh_far", "vehicle", ((0, 500, 0, 5, 0), (1, 505, 0, 5, 0))),
                _track("bad_single_state", "vehicle", ((0, 1, 1, 0, 0),)),
            ),
        )

        context = scoring_context(scenario)

        self.assertEqual(
            {track.agent_id for track in context.tracks},
            {"ego", "ped_near"},
        )
        self.assertEqual(context.excluded_track_count, 2)
        self.assertEqual(context.low_quality_track_count, 1)
        self.assertTrue(context.sdc_track_present)

    def test_score_scenario_reports_real_data_credibility_fields(self) -> None:
        scenario = Scenario(
            scenario_id="waymo_metadata",
            ego_track_id="ego",
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0))),
                _track("target", "pedestrian", ((0, 2, 0, 0, 1), (1, 2, 1, 0, 1))),
                _track("far", "vehicle", ((0, 500, 0, 5, 0), (1, 505, 0, 5, 0))),
            ),
            metadata={
                "waymo_tracks_to_predict_track_ids": ["target"],
                "waymo_objects_of_interest_track_ids": ["target"],
            },
        )

        score = score_scenario(scenario)

        self.assertEqual(score.agent_count, 3)
        self.assertEqual(score.scoring_agent_count, 2)
        self.assertEqual(score.excluded_track_count, 1)
        self.assertEqual(score.vulnerable_road_user_count, 1)
        self.assertEqual(score.scoring_vulnerable_road_user_count, 1)
        self.assertTrue(score.sdc_track_present)
        self.assertEqual(score.prediction_target_count, 1)
        self.assertEqual(score.object_of_interest_count, 1)
        self.assertEqual(score.prediction_target_source, "waymo_tracks_to_predict")
        self.assertEqual(score.prediction_target_evaluated_count, 1)
        self.assertIsNotNone(score.baseline_ade_m)
        self.assertIn("baseline_failure", score.component_scores)

    def test_closing_time_to_collision_requires_future_conflict(self) -> None:
        left = State(t=0, x=0, y=0, vx=5, vy=0)
        right = State(t=0, x=0, y=10, vx=5, vy=0)

        self.assertIsNone(closing_time_to_collision(left, right))


def _track(
    agent_id: str,
    agent_type: str,
    points: tuple[tuple[float, float, float, float, float], ...],
) -> AgentTrack:
    return AgentTrack(
        agent_id=agent_id,
        agent_type=agent_type,  # type: ignore[arg-type]
        states=tuple(State(t=t, x=x, y=y, vx=vx, vy=vy) for t, x, y, vx, vy in points),
    )


if __name__ == "__main__":
    unittest.main()
