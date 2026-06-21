import unittest

from scenariolens.samples import synthetic_scenarios
from scenariolens.taxonomy import infer_tags


class SamplesTest(unittest.TestCase):
    def test_synthetic_corpus_has_enough_milestone_coverage(self) -> None:
        self.assertGreaterEqual(len(synthetic_scenarios()), 10)

    def test_synthetic_scenario_ids_are_unique(self) -> None:
        ids = [scenario.scenario_id for scenario in synthetic_scenarios()]

        self.assertEqual(len(ids), len(set(ids)))

    def test_dense_scenario_infers_dense_multi_agent_tag(self) -> None:
        scenarios = {scenario.scenario_id: scenario for scenario in synthetic_scenarios()}

        self.assertIn(
            "dense_multi_agent",
            infer_tags(scenarios["synthetic_dense_intersection_vru"]),
        )


if __name__ == "__main__":
    unittest.main()
