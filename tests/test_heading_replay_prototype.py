import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_debug import BASELINE_DEBUG_FORMAT
from scenariolens.heading_replay_prototype import (
    HEADING_REPLAY_PROTOTYPE_FORMAT,
    heading_replay_prototype_markdown,
    heading_replay_prototype_payload,
)
from scenariolens.io import save_scenarios
from scenariolens.replay_candidates import REPLAY_CANDIDATE_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State


class HeadingReplayPrototypeTest(unittest.TestCase):
    def test_heading_replay_payload_replays_ready_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_heading_candidate_fixture(root)

            payload = heading_replay_prototype_payload(
                candidate_manifest_path=candidate_manifest,
                output_dir=root / "prototype",
                top=1,
            )

            self.assertEqual(payload["format"], HEADING_REPLAY_PROTOTYPE_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["selected_candidate_count"], 1)
            self.assertEqual(payload["replayed_case_count"], 1)

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(aggregate["replay_track_count"], 1)
            self.assertEqual(aggregate["perturbation_trial_count"], 4)
            self.assertGreaterEqual(aggregate["sign_preserving_trial_count"], 1)

            case = payload["cases"][0]
            nominal = case["nominal"]
            self.assertGreater(
                nominal["heading_vs_nearest_fde_improvement_m"],
                1.0,
            )
            self.assertEqual(nominal["nominal_selector_winner"], "heading_aware")
            self.assertEqual(len(case["perturbation_trials"]), 4)
            self.assertIn("perturbation_stability", case)

            markdown = heading_replay_prototype_markdown(payload)
            self.assertIn("Heading-Aware Replay Prototype", markdown)
            self.assertIn("nearest-lane and heading-aware", markdown)
            self.assertIn("not Waymax/JAX execution", markdown)

    def test_heading_replay_cli_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_heading_candidate_fixture(root)
            output_dir = root / "prototype"
            public_report = root / "reports" / "heading_replay.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "heading-replay-prototype",
                    "--candidate-manifest",
                    str(candidate_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top",
                    "1",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            manifest = json.loads((output_dir / "manifest.json").read_text())
            self.assertIn("Generated 1 heading replay case", result.stdout)
            self.assertEqual(manifest["format"], HEADING_REPLAY_PROTOTYPE_FORMAT)
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())
            self.assertIn("Replay Summary", public_report.read_text())


def _write_heading_candidate_fixture(root: Path) -> Path:
    scenario_path = root / "heading_fixture.json"
    debug_manifest = root / "heading_debug_manifest.json"
    candidate_manifest = root / "heading_candidate_manifest.json"
    scenario = _heading_lane_choice_scenario()
    save_scenarios(scenario_path, (scenario,))

    source_name = scenario_path.name
    debug_manifest.write_text(
        json.dumps(
            {
                "format": BASELINE_DEBUG_FORMAT,
                "source_kind": "lane_selection_study",
                "ready": True,
                "output_dir": str(root / "debug"),
                "max_scenarios": 5,
                "cases": [
                    {
                        "ready": True,
                        "case_label": "Largest heading improvement",
                        "source_input": str(scenario_path),
                        "source_name": source_name,
                        "input_format": "scenariolens-json",
                        "scenario_id": scenario.scenario_id,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    candidate_manifest.write_text(
        json.dumps(
            {
                "format": REPLAY_CANDIDATE_FORMAT,
                "source": str(debug_manifest),
                "ready": True,
                "candidates": [
                    {
                        "scenario_id": scenario.scenario_id,
                        "source_name": source_name,
                        "case_label": "Largest heading improvement",
                        "comparison_mode": "heading_lane_selection",
                        "readiness": "ready_for_heading_improvement_replay",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return candidate_manifest


def _heading_lane_choice_scenario() -> Scenario:
    return Scenario(
        scenario_id="heading_lane_choice_fixture",
        source="unit",
        ego_track_id="ego",
        tags=("map_context", "tracks_to_predict"),
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["target"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "points": [[0.0, -20.0], [0.0, 20.0]],
                },
                {
                    "kind": "lane",
                    "points": [[-20.0, 0.0], [20.0, 0.0]],
                },
            ],
        },
        tracks=(
            AgentTrack(
                agent_id="ego",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=-8.0, y=-4.0, vx=4.0, vy=0.0),
                    State(t=1.0, x=-4.0, y=-4.0, vx=4.0, vy=0.0),
                    State(t=2.0, x=0.0, y=-4.0, vx=4.0, vy=0.0),
                    State(t=3.0, x=4.0, y=-4.0, vx=4.0, vy=0.0),
                ),
            ),
            AgentTrack(
                agent_id="target",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=-5.0, y=0.3, vx=5.0, vy=0.0),
                    State(t=1.0, x=0.0, y=0.3, vx=5.0, vy=0.0),
                    State(t=2.0, x=5.0, y=0.3, vx=5.0, vy=0.0),
                    State(t=3.0, x=10.0, y=0.3, vx=5.0, vy=0.0),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
