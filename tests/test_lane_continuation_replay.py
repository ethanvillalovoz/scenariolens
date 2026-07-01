import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.lane_continuation_candidates import (
    LANE_CONTINUATION_CANDIDATES_FORMAT,
)
from scenariolens.lane_continuation_replay import (
    LANE_CONTINUATION_REPLAY_FORMAT,
    generate_lane_continuation_replay_prototype,
    lane_continuation_replay_markdown,
    lane_continuation_replay_payload,
)
from scenariolens.schema import AgentTrack, Scenario, State


class LaneContinuationReplayTest(unittest.TestCase):
    def test_replay_payload_executes_replay_and_topology_queues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_candidate_manifest(root)

            payload = lane_continuation_replay_payload(
                candidate_manifest_path=candidate_manifest,
                output_dir=root / "replay",
                top_per_bucket=1,
                input_format="scenariolens-json",
                max_scenarios_per_source=10,
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_REPLAY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 3)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["replayed_case_count"], 2)
            self.assertEqual(aggregate["topology_probe_count"], 1)
            self.assertEqual(aggregate["perturbation_trial_count"], 8)
            self.assertGreaterEqual(aggregate["nominal_improvement_count"], 1)
            self.assertGreaterEqual(aggregate["nominal_regression_count"], 1)
            self.assertGreaterEqual(aggregate["topology_blocker_count"], 1)

            by_bucket = {case["bucket"]: case for case in payload["cases"]}
            improvement = by_bucket["improvement_replay_control"]
            regression = by_bucket["regression_replay_debug"]
            topology = by_bucket["topology_audit"]

            self.assertGreater(
                improvement["nominal"]["lane_link_improvement_over_nearest_m"],
                5.0,
            )
            self.assertLess(
                regression["nominal"]["lane_link_improvement_over_nearest_m"],
                -1.0,
            )
            self.assertEqual(topology["conclusion"]["label"], "topology_blocker")
            self.assertEqual(topology["nominal"]["lane_link_count"], 0)

            markdown = lane_continuation_replay_markdown(payload)
            self.assertIn("Lane-Continuation Replay Prototype", markdown)
            self.assertIn("Topology Probes", markdown)
            self.assertIn("not Waymax/JAX execution", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_replay_prototype_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_candidate_manifest(root)
            output_dir = root / "replay"
            public_report = root / "reports" / "lane_replay.md"

            result = generate_lane_continuation_replay_prototype(
                candidate_manifest_path=candidate_manifest,
                output_dir=output_dir,
                top_per_bucket=1,
                input_format="scenariolens-json",
                max_scenarios_per_source=10,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 3)
            self.assertEqual(result.replay_case_count, 2)
            self.assertEqual(result.topology_case_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], LANE_CONTINUATION_REPLAY_FORMAT)
            packet_path = Path(manifest["cases"][0]["local_packet_path"])
            self.assertTrue(packet_path.exists())
            self.assertIn("Replay Summary", public_report.read_text())

    def test_lane_continuation_replay_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_manifest = _write_candidate_manifest(root)
            output_dir = root / "replay"
            public_report = root / "reports" / "lane_replay.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-replay-prototype",
                    "--candidate-manifest",
                    str(candidate_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top-per-bucket",
                    "1",
                    "--format",
                    "scenariolens-json",
                    "--max-scenarios-per-source",
                    "10",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 3 lane-continuation replay/audit", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_candidate_manifest(root: Path) -> Path:
    input_path = root / "lane_replay_fixture.json"
    save_scenarios(
        input_path,
        (
            _lane_scenario(
                scenario_id="improvement_case",
                exit_points=((5.0, 0.0), (15.0, 0.0)),
            ),
            _lane_scenario(
                scenario_id="regression_case",
                exit_points=((5.0, 0.0), (5.0, 10.0)),
            ),
            _lane_scenario(
                scenario_id="topology_case",
                exit_points=None,
            ),
        ),
    )
    path = root / "lane_candidates.json"
    payload = {
        "format": LANE_CONTINUATION_CANDIDATES_FORMAT,
        "ready": True,
        "study_manifest": str(root / "study_manifest.json"),
        "candidates": [
            _candidate(
                bucket="improvement_replay_control",
                readiness="ready_for_continuation_improvement_replay",
                scenario_id="improvement_case",
                source_input=input_path,
            ),
            _candidate(
                bucket="regression_replay_debug",
                readiness="ready_for_continuation_regression_replay",
                scenario_id="regression_case",
                source_input=input_path,
            ),
            _candidate(
                bucket="topology_audit",
                readiness="needs_topology_audit",
                scenario_id="topology_case",
                source_input=input_path,
            ),
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _candidate(
    bucket: str,
    readiness: str,
    scenario_id: str,
    source_input: Path,
) -> dict[str, object]:
    return {
        "bucket": bucket,
        "readiness": readiness,
        "scenario_id": scenario_id,
        "track_id": "veh",
        "source_input": str(source_input),
        "source_name": source_input.name,
        "why_it_matters": "fixture candidate",
        "evidence": {
            "nearest_lane_fde_m": 8.0,
            "lane_link_fde_m": 1.0,
            "lane_link_improvement_over_nearest_m": 7.0,
        },
    }


def _lane_scenario(
    scenario_id: str,
    exit_points: tuple[tuple[float, float], tuple[float, float]] | None,
) -> Scenario:
    lane_features = [
        {
            "kind": "lane",
            "feature_id": "100",
            "feature_type": "TYPE_SURFACE_STREET",
            "points": [[0.0, 0.0], [5.0, 0.0]],
            "exit_lanes": [200] if exit_points is not None else [],
        }
    ]
    if exit_points is not None:
        lane_features.append(
            {
                "kind": "lane",
                "feature_id": "200",
                "feature_type": "TYPE_SURFACE_STREET",
                "points": [[x, y] for x, y in exit_points],
                "entry_lanes": [100],
            }
        )
    return Scenario(
        scenario_id=scenario_id,
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": lane_features,
        },
        tracks=(
            AgentTrack(
                agent_id="veh",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=1.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=1.0, x=4.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=2.0, x=7.0, y=0.0, vx=3.0, vy=0.0),
                    State(t=4.0, x=13.0, y=0.0, vx=3.0, vy=0.0),
                ),
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
