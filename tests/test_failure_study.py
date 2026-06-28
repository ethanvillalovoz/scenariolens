import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.failure_study import (
    FAILURE_STUDY_FORMAT,
    failure_study_markdown,
    failure_study_payload,
    generate_failure_study,
)
from scenariolens.io import save_scenarios
from scenariolens.metrics import score_scenario
from scenariolens.schema import AgentTrack, Scenario, State


class FailureStudyTest(unittest.TestCase):
    def test_failure_study_payload_groups_failures_by_tag(self) -> None:
        scores = tuple(score_scenario(scenario) for scenario in _study_scenarios())

        payload = failure_study_payload(
            input_path=Path("slice.json"),
            output_dir=Path("out"),
            input_format="scenariolens-json",
            max_scenarios=2,
            top=2,
            min_tag_count=1,
            ready=True,
            preflight=None,
            scores=scores,
        )

        self.assertEqual(payload["format"], FAILURE_STUDY_FORMAT)
        self.assertEqual(payload["scenario_count"], 2)
        self.assertGreater(
            payload["aggregate"]["baseline"]["evaluated_target_total"],
            0,
        )
        tags = {row["tag"]: row for row in payload["tag_failures"]}
        self.assertIn("pedestrian_crossing", tags)
        self.assertGreater(tags["pedestrian_crossing"]["mean_fde_m"], 0.0)
        self.assertGreaterEqual(len(payload["hardest_scenarios"]), 2)
        self.assertIn("baseline_failure", {
            row["component"] for row in payload["component_failures"]
        })

    def test_failure_study_markdown_includes_public_safe_sections(self) -> None:
        scores = tuple(score_scenario(scenario) for scenario in _study_scenarios())
        payload = failure_study_payload(
            input_path=Path("slice.json"),
            output_dir=Path("out"),
            input_format="scenariolens-json",
            max_scenarios=2,
            top=1,
            min_tag_count=1,
            ready=True,
            preflight=None,
            scores=scores,
        )

        markdown = failure_study_markdown(payload)

        self.assertIn("# ScenarioLens Real-Slice Failure Study", markdown)
        self.assertIn("## Failure By Tag", markdown)
        self.assertIn("## Failure By Score Component", markdown)
        self.assertIn("## Hardest Baseline-Failure Scenarios", markdown)
        self.assertIn("Raw scenario data committed: no", markdown)

    def test_failure_study_markdown_handles_no_evaluated_targets(self) -> None:
        scenario = Scenario(
            scenario_id="no_future_targets",
            tracks=(
                AgentTrack(
                    agent_id="ego",
                    agent_type="vehicle",
                    states=(State(t=0, x=0, y=0),),
                ),
            ),
            ego_track_id="ego",
        )
        payload = failure_study_payload(
            input_path=Path("slice.json"),
            output_dir=Path("out"),
            input_format="scenariolens-json",
            max_scenarios=1,
            top=1,
            min_tag_count=1,
            ready=True,
            preflight=None,
            scores=(score_scenario(scenario),),
        )

        markdown = failure_study_markdown(payload)

        self.assertIn("no_future_targets", markdown)
        self.assertIn("| `no_future_targets` |", markdown)
        self.assertIn("| n/a | n/a |", markdown)

    def test_generate_failure_study_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "scenarios.json"
            output_dir = root / "study"
            public_report = root / "public" / "failure_study.md"
            save_scenarios(input_path, _study_scenarios())

            result = generate_failure_study(
                input_path=input_path,
                output_dir=output_dir,
                input_format="scenariolens-json",
                max_scenarios=2,
                top=1,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.scenario_count, 2)
            self.assertEqual(manifest["format"], FAILURE_STUDY_FORMAT)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Failure By Tag", public_report.read_text(encoding="utf-8"))


def _study_scenarios() -> tuple[Scenario, ...]:
    return (
        Scenario(
            scenario_id="hard_pedestrian_failure",
            ego_track_id="ego",
            tags=("pedestrian_crossing", "close_interaction"),
            metadata={
                "waymo_current_time_index": 1,
                "waymo_tracks_to_predict_track_ids": ["target_ped"],
            },
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0), (2, 10, 0, 5, 0)),
                ),
                _track(
                    "target_ped",
                    "pedestrian",
                    ((0, 6, -3, 0, 1), (1, 6, -2, 0, 1), (2, 9, -2, 3, 0)),
                ),
            ),
        ),
        Scenario(
            scenario_id="easy_vehicle_target",
            ego_track_id="ego",
            tags=("low_interaction",),
            metadata={
                "waymo_current_time_index": 1,
                "waymo_tracks_to_predict_track_ids": ["target_vehicle"],
            },
            tracks=(
                _track(
                    "ego",
                    "vehicle",
                    ((0, 0, 0, 5, 0), (1, 5, 0, 5, 0), (2, 10, 0, 5, 0)),
                ),
                _track(
                    "target_vehicle",
                    "vehicle",
                    ((0, 20, 0, 4, 0), (1, 24, 0, 4, 0), (2, 28, 0, 4, 0)),
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
