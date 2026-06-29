import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.baseline_debug import generate_baseline_debug_casebook
from scenariolens.io import save_scenarios
from scenariolens.map_match_audit import (
    MAP_MATCH_AUDIT_FORMAT,
    generate_map_match_audit,
    map_match_audit_markdown,
    map_match_audit_payload,
)
from scenariolens.schema import AgentTrack, Scenario, State


class MapMatchAuditTest(unittest.TestCase):
    def test_map_match_audit_sweeps_thresholds_without_changing_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_debug_casebook(root)

            payload = map_match_audit_payload(
                debug_manifest_path=debug_manifest,
                output_dir=root / "audit",
                thresholds_m=(10.0, 3.5),
                case_count=1,
            )

            self.assertEqual(payload["format"], MAP_MATCH_AUDIT_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["case_count"], 1)

            case = payload["cases"][0]
            self.assertEqual(case["default_map_used_count"], 0)
            self.assertEqual(case["default_fallback_count"], 1)

            track = case["track_audit"][0]
            self.assertEqual(track["first_matched_threshold_m"], 10.0)

            sweeps = {row["threshold_m"]: row for row in case["threshold_sweep"]}
            self.assertEqual(sweeps[3.5]["label"], "all_targets_fallback")
            self.assertEqual(sweeps[10.0]["map_used_count"], 1)
            self.assertLess(sweeps[10.0]["fde_improvement_m"], 0.0)

            recommendation = case["recommendation"]
            self.assertEqual(recommendation["label"], "keep_default_threshold")

            markdown = map_match_audit_markdown(payload)
            self.assertIn("Map-Match Audit", markdown)
            self.assertIn("Threshold sweep", markdown)
            self.assertIn("not a matcher change", markdown)
            self.assertIn("keep_default_threshold", markdown)

    def test_generate_map_match_audit_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            debug_manifest = _write_debug_casebook(root)
            output_dir = root / "audit"
            public_report = root / "reports" / "map_match.md"

            result = generate_map_match_audit(
                debug_manifest_path=debug_manifest,
                output_dir=output_dir,
                thresholds_m=(3.5, 10.0),
                case_count=1,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], MAP_MATCH_AUDIT_FORMAT)
            self.assertTrue(Path(manifest["cases"][0]["local_packet_path"]).exists())
            self.assertIn("Audit Summary", public_report.read_text())


def _write_debug_casebook(root: Path) -> Path:
    input_path = root / "offset_lane.json"
    debug_dir = root / "debug"
    scenario = Scenario(
        scenario_id="offset_lane_case",
        ego_track_id=None,
        source="unit_fixture",
        metadata={
            "waymo_current_time_index": 1,
            "waymo_tracks_to_predict_track_ids": ["veh"],
            "waymo_map_features": [
                {
                    "kind": "lane",
                    "points": [[0.0, 0.0], [10.0, 0.0]],
                }
            ],
        },
        tracks=(
            AgentTrack(
                agent_id="veh",
                agent_type="vehicle",
                states=(
                    State(t=0.0, x=0.0, y=6.0, vx=1.0, vy=0.0),
                    State(t=1.0, x=1.0, y=6.0, vx=1.0, vy=0.0),
                    State(t=2.0, x=2.0, y=6.0, vx=1.0, vy=0.0),
                ),
            ),
        ),
    )
    save_scenarios(input_path, (scenario,))
    result = generate_baseline_debug_casebook(
        output_dir=debug_dir,
        input_path=input_path,
        scenario_ids=("offset_lane_case",),
        input_format="scenariolens-json",
        max_scenarios=None,
    )
    return result.manifest_path


if __name__ == "__main__":
    unittest.main()
