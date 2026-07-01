import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.lane_selection_study import (
    LANE_SELECTION_STUDY_FORMAT,
    generate_lane_selection_study,
    lane_selection_study_markdown,
    lane_selection_study_payload,
)
from scenariolens.schema import AgentTrack, Scenario, State


class LaneSelectionStudyTest(unittest.TestCase):
    def test_payload_compares_nearest_and_heading_aware_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "lane_selection.json"
            save_scenarios(input_path, _study_scenarios())

            payload = lane_selection_study_payload(
                input_paths=(input_path,),
                output_dir=root / "study",
                max_scenarios=None,
                top=3,
                input_format="scenariolens-json",
            )

            self.assertEqual(payload["format"], LANE_SELECTION_STUDY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["scenario_count"], 2)

            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["evaluated_target_count"], 2)
            self.assertGreater(
                aggregate["heading_vs_nearest_fde_improvement_m"],
                0.0,
            )
            self.assertEqual(aggregate["heading_fallback_count"], 1)

            reasons = payload["heading_fallback_reasons"]
            self.assertEqual(reasons["lane_heading_misaligned"], 1)

            markdown = lane_selection_study_markdown(payload)
            self.assertIn("Heading-Aware Lane Selection Study", markdown)
            self.assertIn("not a production map matcher", markdown)
            self.assertIn("lane_heading_misaligned", markdown)

    def test_generate_lane_selection_study_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "lane_selection.json"
            output_dir = root / "study"
            public_report = root / "reports" / "lane_selection.md"
            save_scenarios(input_path, _study_scenarios())

            result = generate_lane_selection_study(
                input_paths=(input_path,),
                output_dir=output_dir,
                max_scenarios=None,
                top=3,
                input_format="scenariolens-json",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.source_count, 1)
            self.assertEqual(result.scenario_count, 2)
            self.assertEqual(result.evaluated_target_count, 2)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], LANE_SELECTION_STUDY_FORMAT)


def _study_scenarios() -> tuple[Scenario, ...]:
    return (_crossing_lane_choice(), _misaligned_lane_choice())


def _crossing_lane_choice() -> Scenario:
    return Scenario(
        scenario_id="crossing_lane_choice",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["target"],
            "waymo_map_features": [
                {"kind": "lane", "points": [[1.0, -5.0], [1.0, 5.0]]},
                {"kind": "lane", "points": [[0.0, 0.0], [10.0, 0.0]]},
            ],
        },
        tracks=(
            _track(
                "target",
                "vehicle",
                (
                    (0, 0, 0.2, 1, 0),
                    (1, 1, 0.2, 1, 0),
                    (2, 2, 0.2, 1, 0),
                    (3, 3, 0.2, 1, 0),
                ),
            ),
        ),
    )


def _misaligned_lane_choice() -> Scenario:
    return Scenario(
        scenario_id="misaligned_lane_choice",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["target"],
            "waymo_map_features": [
                {"kind": "lane", "points": [[1.0, -5.0], [1.0, 5.0]]}
            ],
        },
        tracks=(
            _track(
                "target",
                "vehicle",
                (
                    (0, 0, 0.2, 1, 0),
                    (1, 1, 0.2, 1, 0),
                    (2, 2, 0.2, 1, 0),
                ),
            ),
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
