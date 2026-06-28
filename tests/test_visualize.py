import unittest

from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import AgentTrack, Scenario, State
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
        self.assertIn("scenario-plot-clip", svg)
        self.assertIn("track-pedestrian", svg)
        self.assertIn("baseline-prediction", svg)
        self.assertIn("latest", svg)

    def test_scenario_svg_handles_single_track_baseline(self) -> None:
        scenario = synthetic_scenarios()[-1]
        svg = scenario_svg(scenario)

        self.assertIn("synthetic_open_road_baseline", svg)
        self.assertIn("ego", svg)
        self.assertIn("</svg>", svg)

    def test_scenario_svg_uses_scored_context_for_dense_real_slices(self) -> None:
        scenario = Scenario(
            scenario_id="dense_real_slice",
            ego_track_id="ego",
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0))),
                _track("near_ped", "pedestrian", ((0, 2, 0, 0, 1), (1, 2, 1, 0, 1))),
                _track("far_vehicle", "vehicle", ((0, 500, 0, 5, 0), (1, 505, 0, 5, 0))),
            ),
        )

        svg = scenario_svg(scenario)

        self.assertIn("2 scored of 3 agents", svg)
        self.assertIn("near_ped", svg)
        self.assertNotIn("far_vehicle", svg)

    def test_scenario_svg_renders_waymo_map_features(self) -> None:
        scenario = Scenario(
            scenario_id="map_context",
            ego_track_id="ego",
            tracks=(
                _track("ego", "vehicle", ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0))),
                _track("ped", "pedestrian", ((0, 2, 0, 0, 1), (1, 2, 1, 0, 1))),
            ),
            metadata={
                "waymo_map_features": [
                    {
                        "kind": "lane",
                        "points": [[-2.0, 0.0], [6.0, 0.0]],
                    },
                    {
                        "kind": "crosswalk",
                        "points": [[1.5, -1.0], [2.5, -1.0], [2.5, 1.0], [1.5, 1.0]],
                    },
                ]
            },
        )

        svg = scenario_svg(scenario)

        self.assertIn("map-feature map-lane", svg)
        self.assertIn("map-feature map-crosswalk", svg)


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
