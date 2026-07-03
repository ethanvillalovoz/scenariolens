import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
    generate_lane_continuation_terminal_neighborhood_replay,
    lane_continuation_terminal_neighborhood_replay_markdown,
    lane_continuation_terminal_neighborhood_replay_payload,
)


class LaneContinuationTerminalNeighborhoodReplayTest(unittest.TestCase):
    def test_payload_replays_and_gates_nearby_recovery_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = _write_native_json_source(root)
            terminal_manifest = _write_terminal_manifest(root, source)

            payload = lane_continuation_terminal_neighborhood_replay_payload(
                terminal_neighborhood_manifest_path=terminal_manifest,
                output_dir=root / "terminal_replay",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["replayed_case_count"], 2)
            self.assertEqual(aggregate["accepted_case_count"], 1)
            self.assertEqual(aggregate["held_case_count"], 1)
            self.assertEqual(aggregate["nominal_improvement_case_count"], 1)
            self.assertEqual(aggregate["nominal_regression_case_count"], 1)

            accepted, held = payload["cases"]
            self.assertEqual(
                accepted["gate_decision"]["label"],
                "accept_for_selector_experiment",
            )
            self.assertEqual(accepted["alternate_chain"], ["2", "3"])
            self.assertGreater(accepted["nominal_gain_m"], 20.0)
            self.assertEqual(
                accepted["perturbation_stability"]["stable_gain_trial_count"],
                4,
            )
            self.assertEqual(
                held["gate_decision"]["label"],
                "hold_recovery_regressed",
            )
            self.assertLess(held["nominal_gain_m"], 0.0)

    def test_markdown_explains_scope_and_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_replay_payload(
                terminal_neighborhood_manifest_path=_write_terminal_manifest(
                    root,
                    _write_native_json_source(root),
                ),
                output_dir=root / "terminal_replay",
            )

            markdown = lane_continuation_terminal_neighborhood_replay_markdown(payload)

            self.assertIn("Terminal-Neighborhood Replay Gate", markdown)
            self.assertIn("accept_for_selector_experiment", markdown)
            self.assertIn("hold_recovery_regressed", markdown)
            self.assertIn("Raw map geometry published: no", markdown)
            self.assertIn("not a Waymo benchmark claim", markdown)

    def test_generate_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            terminal_manifest = _write_terminal_manifest(
                root,
                _write_native_json_source(root),
            )
            public_report = root / "reports" / "terminal_replay.md"

            result = generate_lane_continuation_terminal_neighborhood_replay(
                terminal_neighborhood_manifest_path=terminal_manifest,
                output_dir=root / "terminal_replay",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.replayed_case_count, 2)
            self.assertEqual(result.accepted_case_count, 1)
            self.assertEqual(result.held_case_count, 1)
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
            )
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())

    def test_terminal_neighborhood_replay_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            terminal_manifest = _write_terminal_manifest(
                root,
                _write_native_json_source(root),
            )
            output_dir = root / "terminal_replay"
            public_report = root / "reports" / "terminal_replay.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-replay",
                    "--terminal-neighborhood-manifest",
                    str(terminal_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={**os.environ, "PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated terminal-neighborhood replay", result.stdout)
            self.assertIn("1 accepted candidate", result.stdout)
            self.assertIn("1 held candidate", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_native_json_source(root: Path) -> Path:
    path = root / "scenarios.json"
    path.write_text(
        json.dumps(
            {
                "scenarios": [
                    _scenario_mapping(
                        scenario_id="accepted_recovery",
                        track_id=201,
                        states=[
                            (0.0, 2.0, 0.0, 13.0, 0.0),
                            (1.0, 9.0, 0.0, 13.0, 0.0),
                            (2.0, 20.0, 1.0, 13.0, 0.0),
                            (3.0, 35.0, 1.0, 13.0, 0.0),
                        ],
                        map_features=[
                            _lane_feature(1, 0.0, 10.0, 0.0),
                            _lane_feature(2, 0.0, 10.0, 1.0, exit_lanes=[3]),
                            _lane_feature(3, 10.0, 45.0, 1.0),
                        ],
                    ),
                    _scenario_mapping(
                        scenario_id="held_regression",
                        track_id=202,
                        states=[
                            (0.0, 2.0, 10.0, 13.0, 0.0),
                            (1.0, 9.0, 10.0, 13.0, 0.0),
                            (2.0, 10.0, 10.0, 0.0, 0.0),
                            (3.0, 10.0, 10.0, 0.0, 0.0),
                        ],
                        map_features=[
                            _lane_feature(10, 0.0, 10.0, 10.0),
                            _lane_feature(11, 0.0, 10.0, 15.0, exit_lanes=[12]),
                            _lane_feature(12, 10.0, 45.0, 15.0),
                        ],
                    ),
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_terminal_manifest(root: Path, source: Path) -> Path:
    path = root / "terminal_manifest.json"
    path.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
                "ready": True,
                "topology_manifest": "topology_manifest.json",
                "replay_manifest": "replay_manifest.json",
                "candidate_manifest": "candidate_manifest.json",
                "study_manifest": "study_manifest.json",
                "max_scenarios_per_source": 25,
                "max_hops": 2,
                "selected_terminal_case_count": 2,
                "cases": [
                    _terminal_case(
                        rank=1,
                        scenario_id="accepted_recovery",
                        track_id="201",
                        source=source,
                        selected_feature_id="1",
                        alternate_feature_id="2",
                    ),
                    _terminal_case(
                        rank=2,
                        scenario_id="held_regression",
                        track_id="202",
                        source=source,
                        selected_feature_id="10",
                        alternate_feature_id="11",
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _scenario_mapping(
    scenario_id: str,
    track_id: int,
    states: list[tuple[float, float, float, float, float]],
    map_features: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "scenarioId": scenario_id,
        "timestampsSeconds": [state[0] for state in states],
        "currentTimeIndex": 1,
        "tracksToPredict": [{"trackIndex": 0}],
        "mapFeatures": map_features,
        "tracks": [
            {
                "id": track_id,
                "objectType": "TYPE_VEHICLE",
                "states": [
                    {
                        "centerX": x,
                        "centerY": y,
                        "velocityX": vx,
                        "velocityY": vy,
                        "valid": True,
                    }
                    for _, x, y, vx, vy in states
                ],
            }
        ],
    }


def _lane_feature(
    feature_id: int,
    x0: float,
    x1: float,
    y: float,
    exit_lanes: list[int] | None = None,
) -> dict[str, object]:
    lane: dict[str, object] = {
        "speedLimitMph": 35.0,
        "type": "TYPE_SURFACE_STREET",
        "polyline": [
            {"x": x0, "y": y},
            {"x": x1, "y": y},
        ],
    }
    if exit_lanes:
        lane["exitLanes"] = exit_lanes
    return {"id": feature_id, "lane": lane}


def _terminal_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    source: Path,
    selected_feature_id: str,
    alternate_feature_id: str,
) -> dict[str, object]:
    return {
        "rank": rank,
        "ready": True,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source),
        "source_name": source.name,
        "input_format": "native",
        "diagnosis_label": "nearby_alternate_lane_recovery",
        "selected_feature_id": selected_feature_id,
        "best_alternate_feature_id": alternate_feature_id,
    }


if __name__ == "__main__":
    unittest.main()
