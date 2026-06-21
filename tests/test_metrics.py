import unittest

from scenariolens.metrics import min_pairwise_distance, score_scenario
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


if __name__ == "__main__":
    unittest.main()
