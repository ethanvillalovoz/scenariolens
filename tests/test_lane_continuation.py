import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.ingest.waymo_motion import MAX_MAP_FEATURES_PER_SCENARIO
from scenariolens.io import save_scenarios
from scenariolens.lane_continuation import (
    LANE_CONTINUATION_FORMAT,
    LANE_CONTINUATION_STUDY_FORMAT,
    generate_lane_continuation_prototype,
    generate_lane_continuation_study,
    lane_continuation_markdown,
    lane_continuation_payload,
    lane_continuation_study_payload,
    lane_continuation_study_markdown,
    lane_link_baseline,
)
from scenariolens.prediction import lane_aware_baseline
from scenariolens.route_intent_audit import ROUTE_INTENT_AUDIT_FORMAT
from scenariolens.schema import AgentTrack, Scenario, State


class LaneContinuationTest(unittest.TestCase):
    def test_lane_link_baseline_follows_exit_lane(self) -> None:
        scenario = _linked_lane_scenario()

        nearest = lane_aware_baseline(scenario)
        linked = lane_link_baseline(scenario)

        self.assertEqual(nearest.map_used_count, 1)
        self.assertEqual(linked.map_used_count, 1)
        self.assertGreater(nearest.fde_m or 0.0, 7.0)
        self.assertIsNotNone(linked.fde_m)
        self.assertLess(linked.fde_m, 0.1)

    def test_lane_continuation_payload_reports_link_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audit_manifest = _write_audit_manifest(root)

            payload = lane_continuation_payload(
                audit_manifest_path=audit_manifest,
                output_dir=root / "lane_continuation",
                case_count=1,
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["map_feature_cap"], MAX_MAP_FEATURES_PER_SCENARIO)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["evaluated_case_count"], 1)
            self.assertEqual(aggregate["evaluated_track_count"], 1)
            self.assertEqual(aggregate["linked_lane_track_count"], 1)
            self.assertEqual(aggregate["improved_over_nearest_count"], 1)
            self.assertEqual(aggregate["still_clamped_count"], 0)

            case = payload["cases"][0]
            self.assertEqual(case["primary_conclusion"]["label"], "lane_link_improvement")
            track = case["track_results"][0]
            self.assertEqual(track["conclusion"]["label"], "lane_link_improvement")
            self.assertGreater(track["lane_link_improvement_over_nearest_m"], 7.0)
            self.assertEqual(track["lane_link"]["feature_chain"], ["100", "200"])

            markdown = lane_continuation_markdown(payload)
            self.assertIn("Lane-Link Continuation Prototype", markdown)
            self.assertIn("lane_link_improvement", markdown)
            self.assertIn("Waymo map feature cap", markdown)
            self.assertIn("not route planning", markdown)
            self.assertIn("Raw Waymo files committed: no", markdown)

    def test_generate_lane_continuation_prototype_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audit_manifest = _write_audit_manifest(root)
            output_dir = root / "lane_continuation"
            public_report = root / "reports" / "lane_continuation.md"

            result = generate_lane_continuation_prototype(
                audit_manifest_path=audit_manifest,
                output_dir=output_dir,
                case_count=1,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 1)
            self.assertEqual(result.evaluated_track_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], LANE_CONTINUATION_FORMAT)
            self.assertTrue(Path(manifest["cases"][0]["local_packet_path"]).exists())
            self.assertIn("Prototype Summary", public_report.read_text())

    def test_lane_continuation_study_payload_ranks_validation_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "linked_lane_fixture.json"
            save_scenarios(input_path, (_linked_lane_scenario(),))

            payload = lane_continuation_study_payload(
                input_paths=(input_path,),
                output_dir=root / "lane_continuation_study",
                max_scenarios=10,
                top=3,
                input_format="scenariolens-json",
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_STUDY_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["candidate_case_count"], 1)
            self.assertEqual(payload["candidate_track_count"], 1)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["linked_lane_track_count"], 1)
            self.assertEqual(aggregate["improved_over_nearest_count"], 1)
            self.assertEqual(aggregate["topology_gap_count"], 0)
            improvement = payload["top_improvements"][0]
            self.assertEqual(improvement["scenario_id"], "linked_lane_fixture")
            self.assertGreater(improvement["lane_link_improvement_over_nearest_m"], 7.0)

            markdown = lane_continuation_study_markdown(payload)
            self.assertIn("Lane-Continuation Validation Study", markdown)
            self.assertIn("Largest Lane-Link Improvements", markdown)
            self.assertIn("not route planning", markdown)

    def test_generate_lane_continuation_study_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "linked_lane_fixture.json"
            save_scenarios(input_path, (_linked_lane_scenario(),))
            output_dir = root / "lane_continuation_study"
            public_report = root / "reports" / "lane_continuation_study.md"

            result = generate_lane_continuation_study(
                input_paths=(input_path,),
                output_dir=output_dir,
                max_scenarios=10,
                top=3,
                input_format="scenariolens-json",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.source_count, 1)
            self.assertEqual(result.scenario_count, 1)
            self.assertEqual(result.candidate_track_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], LANE_CONTINUATION_STUDY_FORMAT)
            self.assertIn("Validation Study", public_report.read_text())

    def test_lane_continuation_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            audit_manifest = _write_audit_manifest(root)
            output_dir = root / "lane_continuation"
            public_report = root / "reports" / "lane_continuation.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-prototype",
                    "--audit-manifest",
                    str(audit_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--case-count",
                    "1",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 1 lane-continuation case", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())

    def test_lane_continuation_study_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "linked_lane_fixture.json"
            save_scenarios(input_path, (_linked_lane_scenario(),))
            output_dir = root / "lane_continuation_study"
            public_report = root / "reports" / "lane_continuation_study.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-study",
                    "--input",
                    str(input_path),
                    "--format",
                    "scenariolens-json",
                    "--output-dir",
                    str(output_dir),
                    "--max-scenarios",
                    "10",
                    "--top",
                    "3",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("lane-continuation candidate target", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_audit_manifest(root: Path) -> Path:
    input_path = root / "linked_lane_fixture.json"
    save_scenarios(input_path, (_linked_lane_scenario(),))
    audit_manifest = root / "route_intent_audit.json"
    audit_manifest.write_text(
        json.dumps(
            {
                "format": ROUTE_INTENT_AUDIT_FORMAT,
                "ready": True,
                "source_kind": "context_eval_set",
                "cases": [
                    {
                        "ready": True,
                        "rank": 1,
                        "case_label": "Linked lane seed",
                        "scenario_id": "linked_lane_fixture",
                        "source_input": str(input_path),
                        "source_name": input_path.name,
                        "input_format": "scenariolens-json",
                        "primary_diagnosis": {
                            "label": "lane_continuity_or_route_link_needed",
                        },
                        "track_audits": [
                            {
                                "track_id": "veh",
                                "diagnosis": {
                                    "label": "lane_continuity_or_route_link_needed",
                                },
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return audit_manifest


def _linked_lane_scenario() -> Scenario:
    return Scenario(
        scenario_id="linked_lane_fixture",
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "feature_id": "100",
                    "feature_type": "TYPE_SURFACE_STREET",
                    "points": [[0.0, 0.0], [5.0, 0.0]],
                    "exit_lanes": [200],
                },
                {
                    "kind": "lane",
                    "feature_id": "200",
                    "feature_type": "TYPE_SURFACE_STREET",
                    "points": [[5.0, 0.0], [15.0, 0.0]],
                    "entry_lanes": [100],
                },
            ],
            "waymo_map_summary": {
                "lane_count": 2,
                "entry_link_count": 1,
                "exit_link_count": 1,
                "neighbor_link_count": 0,
                "route_link_count": 2,
                "has_route_context": True,
            },
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
