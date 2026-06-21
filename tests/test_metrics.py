import unittest

from scenariolens.metrics import (
    interaction_components,
    max_deceleration,
    min_pairwise_distance,
    min_path_distance,
    min_vru_distance,
    score_scenario,
)
from scenariolens.samples import synthetic_scenarios


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
            ),
        )
        self.assertGreater(components["dynamics"], 0.0)


if __name__ == "__main__":
    unittest.main()
