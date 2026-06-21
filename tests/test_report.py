import json
import unittest

from scenariolens.report import json_report, markdown_report, ranked_scores, score_reasons
from scenariolens.samples import synthetic_scenarios


class ReportTest(unittest.TestCase):
    def test_ranked_scores_are_descending(self) -> None:
        scores = ranked_scores(synthetic_scenarios())

        self.assertEqual(
            list(scores),
            sorted(scores, key=lambda score: score.interaction_score, reverse=True),
        )

    def test_markdown_report_includes_explanations(self) -> None:
        report = markdown_report(synthetic_scenarios(), limit=3)

        self.assertIn("# ScenarioLens Scenario Report", report)
        self.assertIn("Why it matters", report)
        self.assertIn("synthetic_dense_intersection_vru", report)

    def test_json_report_is_machine_readable(self) -> None:
        payload = json.loads(json_report(synthetic_scenarios(), limit=2))

        self.assertEqual(payload["reported_count"], 2)
        self.assertGreaterEqual(payload["scenario_count"], 10)
        self.assertIn("reasons", payload["scenarios"][0])

    def test_score_reasons_falls_back_for_baseline(self) -> None:
        baseline = ranked_scores(synthetic_scenarios())[-1]

        self.assertEqual(
            score_reasons(baseline),
            ("included as a low-interaction baseline",),
        )


if __name__ == "__main__":
    unittest.main()
