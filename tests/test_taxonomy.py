import unittest

from scenariolens.schema import AgentTrack, Scenario, State
from scenariolens.taxonomy import infer_tags, normalize_tags, tag_weight


class TaxonomyTest(unittest.TestCase):
    def test_normalize_tags_maps_aliases_in_stable_order(self) -> None:
        tags = normalize_tags(("merge", "pedestrian", "custom_case", "crossing"))

        self.assertEqual(
            tags,
            (
                "vulnerable_road_user",
                "pedestrian_crossing",
                "merge_conflict",
                "custom_case",
            ),
        )

    def test_infer_tags_adds_vru_and_cyclist_categories(self) -> None:
        scenario = Scenario(
            scenario_id="test_cyclist",
            tracks=(
                AgentTrack(
                    agent_id="ego",
                    agent_type="vehicle",
                    states=(State(t=0, x=0, y=0),),
                ),
                AgentTrack(
                    agent_id="bike_1",
                    agent_type="cyclist",
                    states=(State(t=0, x=2, y=1),),
                ),
            ),
        )

        self.assertEqual(
            infer_tags(scenario),
            ("vulnerable_road_user", "cyclist_interaction"),
        )

    def test_tag_weight_ignores_unknown_tags(self) -> None:
        self.assertEqual(
            tag_weight(("merge_conflict", "unknown_case")),
            2.0,
        )


if __name__ == "__main__":
    unittest.main()

