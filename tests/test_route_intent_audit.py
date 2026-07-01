import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.replay_prototype import REPLAY_PROTOTYPE_FORMAT
from scenariolens.route_intent_audit import (
    ROUTE_INTENT_AUDIT_FORMAT,
    generate_route_intent_audit,
    route_intent_audit_markdown,
    route_intent_audit_payload,
)
from scenariolens.schema import AgentTrack, Scenario, State


class RouteIntentAuditTest(unittest.TestCase):
    def test_route_intent_audit_flags_stable_lane_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)

            payload = route_intent_audit_payload(
                replay_manifest_path=replay_manifest,
                output_dir=root / "route_intent",
                case_count=1,
            )

            self.assertEqual(payload["format"], ROUTE_INTENT_AUDIT_FORMAT)
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["audited_case_count"], 1)
            self.assertEqual(aggregate["audited_track_count"], 1)
            self.assertEqual(aggregate["route_intent_candidate_count"], 1)

            case = payload["cases"][0]
            self.assertEqual(case["primary_diagnosis"]["label"], "route_intent_prior_needed")
            track = case["track_audits"][0]
            self.assertLess(track["nearest_vs_constant_fde_delta_m"], 0.0)
            self.assertEqual(track["diagnosis"]["label"], "route_intent_prior_needed")
            self.assertGreaterEqual(track["nearest_lane"]["lane_tangent_change_deg"], 80.0)

            markdown = route_intent_audit_markdown(payload)
            self.assertIn("Route/Intent Audit", markdown)
            self.assertIn("route_intent_prior_needed", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw Waymo files committed: no", markdown)

    def test_generate_route_intent_audit_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)
            output_dir = root / "route_intent"
            public_report = root / "reports" / "route_intent.md"

            result = generate_route_intent_audit(
                replay_manifest_path=replay_manifest,
                output_dir=output_dir,
                case_count=1,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 1)
            self.assertEqual(result.audited_track_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], ROUTE_INTENT_AUDIT_FORMAT)
            self.assertTrue(Path(manifest["cases"][0]["local_packet_path"]).exists())
            self.assertIn("Audit Summary", public_report.read_text())

    def test_route_intent_audit_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)
            output_dir = root / "route_intent"
            public_report = root / "reports" / "route_intent.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "route-intent-audit",
                    "--replay-manifest",
                    str(replay_manifest),
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

            self.assertIn("Generated 1 route/intent audit case", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_replay_manifest(root: Path) -> Path:
    input_path = root / "route_intent_fixture.json"
    scenario = Scenario(
        scenario_id="route_intent_fixture",
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "feature_id": "lane_turn",
                    "feature_type": "TYPE_SURFACE_STREET",
                    "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 10.0]],
                    "entry_lanes": [1],
                    "exit_lanes": [2],
                    "left_neighbor_count": 1,
                }
            ],
            "waymo_map_summary": {
                "lane_count": 1,
                "entry_link_count": 1,
                "exit_link_count": 1,
                "neighbor_link_count": 1,
                "route_link_count": 3,
                "has_route_context": True,
            },
        },
        tracks=(
            AgentTrack(
                agent_id="veh",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=0.0, y=0.0, vx=1.0, vy=0.0),
                    State(t=1.0, x=1.0, y=0.0, vx=1.0, vy=0.0),
                    State(t=2.0, x=2.0, y=0.0, vx=1.0, vy=0.0),
                ),
            ),
        ),
    )
    save_scenarios(input_path, (scenario,))
    replay_manifest = root / "replay_manifest.json"
    replay_manifest.write_text(
        json.dumps(
            {
                "format": REPLAY_PROTOTYPE_FORMAT,
                "ready": True,
                "source_kind": "context_eval_set",
                "cases": [
                    {
                        "ready": True,
                        "rank": 1,
                        "case_label": "Context eval seed 1",
                        "scenario_id": "route_intent_fixture",
                        "source_input": str(input_path),
                        "source_name": input_path.name,
                        "input_format": "scenariolens-json",
                        "readiness": "ready_for_regression_replay",
                        "nominal": {
                            "constant_velocity_fde_m": 0.0,
                            "lane_aware_fde_m": 1.414,
                            "fde_improvement_m": -1.414,
                        },
                        "track_replays": [
                            {
                                "track_id": "veh",
                                "agent_type": "vehicle",
                                "constant_velocity_fde_m": 0.0,
                                "lane_aware_fde_m": 1.414,
                                "fde_improvement_m": -1.414,
                                "lane_map_used": True,
                                "lane_fallback_reason": None,
                            }
                        ],
                        "perturbation_stability": {
                            "label": "stable_regression_warning",
                            "valid_trial_count": 4,
                            "sign_preserving_trial_count": 4,
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return replay_manifest


if __name__ == "__main__":
    unittest.main()
