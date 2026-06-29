import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.failure_stability import (
    FAILURE_STABILITY_FORMAT,
    failure_stability_markdown,
    failure_stability_payload,
    generate_failure_stability_study,
)
from scenariolens.io import save_scenarios
from scenariolens.schema import AgentTrack, Scenario, State


class FailureStabilityTest(unittest.TestCase):
    def test_stability_payload_compares_windows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            save_scenarios(input_path, _study_scenarios())

            payload = failure_stability_payload(
                input_paths=(input_path,),
                output_dir=root / "study",
                input_format="scenariolens-json",
                max_scenarios=4,
                window_size=2,
                top_tags=5,
                min_tag_slices=1,
            )

            self.assertEqual(payload["format"], FAILURE_STABILITY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["slice_count"], 2)
            self.assertEqual(payload["scenario_count"], 4)
            self.assertEqual(payload["comparison_mode"], "single-input windowed comparison")
            self.assertGreater(len(payload["tag_stability"]), 0)

            markdown = failure_stability_markdown(payload)
            self.assertIn("Failure Distribution Stability Study", markdown)
            self.assertIn("## Slice Distribution", markdown)
            self.assertIn("## Tag Stability", markdown)
            self.assertIn("compares contiguous scenario windows", markdown)

    def test_generate_stability_study_writes_manifest_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "study"
            public_report = root / "reports" / "stability.md"
            save_scenarios(input_path, _study_scenarios())

            result = generate_failure_stability_study(
                input_paths=(input_path,),
                output_dir=output_dir,
                input_format="scenariolens-json",
                max_scenarios=4,
                window_size=2,
                top_tags=5,
                min_tag_slices=1,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.slice_count, 2)
            self.assertEqual(result.scenario_count, 4)
            self.assertEqual(manifest["format"], FAILURE_STABILITY_FORMAT)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Slice Distribution", public_report.read_text())

    def test_stability_payload_compares_repeated_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            left_input = root / "left.json"
            right_input = root / "right.json"
            scenarios = _study_scenarios()
            save_scenarios(left_input, scenarios[:2])
            save_scenarios(right_input, scenarios[2:])

            payload = failure_stability_payload(
                input_paths=(left_input, right_input),
                output_dir=root / "study",
                input_format="scenariolens-json",
                max_scenarios=2,
                window_size=99,
                top_tags=5,
                min_tag_slices=1,
            )

            self.assertEqual(payload["slice_count"], 2)
            self.assertEqual(payload["comparison_mode"], "cross-input comparison")
            self.assertEqual(len(payload["sources"]), 2)
            markdown = failure_stability_markdown(payload)
            self.assertIn("each downloaded shard", markdown)


def _study_scenarios() -> tuple[Scenario, ...]:
    return (
        _scenario(
            scenario_id="window_a_hard_pedestrian",
            tag="vulnerable_road_user",
            target_type="pedestrian",
            target_points=((0, 6, -3, 0, 1), (1, 6, -2, 0, 1), (2, 11, -1, 5, 1)),
        ),
        _scenario(
            scenario_id="window_a_vehicle",
            tag="dense_multi_agent",
            target_type="vehicle",
            target_points=((0, 20, 0, 3, 0), (1, 23, 0, 3, 0), (2, 26, 0, 3, 0)),
        ),
        _scenario(
            scenario_id="window_b_hard_vehicle",
            tag="objects_of_interest",
            target_type="vehicle",
            target_points=((0, 4, 4, 1, 0), (1, 5, 4, 1, 0), (2, 18, 4, 13, 0)),
        ),
        _scenario(
            scenario_id="window_b_cyclist",
            tag="vulnerable_road_user",
            target_type="cyclist",
            target_points=((0, -6, 1, 2, 0), (1, -4, 1, 2, 0), (2, -2, 1, 2, 0)),
        ),
    )


def _scenario(
    scenario_id: str,
    tag: str,
    target_type: str,
    target_points: tuple[tuple[float, float, float, float, float], ...],
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        ego_track_id="ego",
        tags=(tag, "tracks_to_predict"),
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
            _track("target", target_type, target_points),
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
