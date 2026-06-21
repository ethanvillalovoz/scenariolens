import unittest

from scenariolens.samples import synthetic_scenarios
from scenariolens.visualize import scenario_bounds, scenario_svg


class VisualizeTest(unittest.TestCase):
    def test_scenario_bounds_cover_all_states(self) -> None:
        scenario = synthetic_scenarios()[0]
        min_x, min_y, max_x, max_y = scenario_bounds(scenario)

        for track in scenario.tracks:
            for state in track.states:
                self.assertLessEqual(min_x, state.x)
                self.assertLessEqual(min_y, state.y)
                self.assertGreaterEqual(max_x, state.x)
                self.assertGreaterEqual(max_y, state.y)

    def test_scenario_svg_contains_tracks_and_metadata(self) -> None:
        scenario = synthetic_scenarios()[0]
        svg = scenario_svg(scenario)

        self.assertIn("<svg", svg)
        self.assertIn("synthetic_pedestrian_crossing", svg)
        self.assertIn("ped_1", svg)
        self.assertIn("<polyline", svg)
        self.assertIn("#dc2626", svg)

    def test_scenario_svg_handles_single_track_baseline(self) -> None:
        scenario = synthetic_scenarios()[-1]
        svg = scenario_svg(scenario)

        self.assertIn("synthetic_open_road_baseline", svg)
        self.assertIn("ego", svg)
        self.assertIn("</svg>", svg)


if __name__ == "__main__":
    unittest.main()

