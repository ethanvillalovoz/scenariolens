import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation import LANE_CONTINUATION_STUDY_FORMAT
from scenariolens.lane_continuation_candidates import (
    LANE_CONTINUATION_CANDIDATES_FORMAT,
    generate_lane_continuation_candidate_plan,
    lane_continuation_candidate_markdown,
    lane_continuation_candidate_payload,
)


class LaneContinuationCandidatesTest(unittest.TestCase):
    def test_candidate_payload_groups_replay_and_topology_queues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            study_manifest = _write_study_manifest(root)

            payload = lane_continuation_candidate_payload(
                study_manifest_path=study_manifest,
                output_dir=root / "candidates",
                top_per_bucket=2,
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_CANDIDATES_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["candidate_count"], 3)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["improvement_control_count"], 1)
            self.assertEqual(aggregate["regression_debug_count"], 1)
            self.assertEqual(aggregate["topology_audit_count"], 1)
            self.assertEqual(aggregate["replay_candidate_count"], 2)

            readiness = {candidate["readiness"] for candidate in payload["candidates"]}
            self.assertIn("ready_for_continuation_improvement_replay", readiness)
            self.assertIn("ready_for_continuation_regression_replay", readiness)
            self.assertIn("needs_topology_audit", readiness)

            markdown = lane_continuation_candidate_markdown(payload)
            self.assertIn("Lane-Continuation Candidate Plan", markdown)
            self.assertIn("Replay Controls", markdown)
            self.assertIn("Topology Audit Queue", markdown)
            self.assertIn("not a completed Waymax/JAX integration", markdown)

    def test_generate_candidate_plan_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            study_manifest = _write_study_manifest(root)
            output_dir = root / "candidates"
            public_report = root / "reports" / "candidates.md"

            result = generate_lane_continuation_candidate_plan(
                study_manifest_path=study_manifest,
                output_dir=output_dir,
                top_per_bucket=2,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.candidate_count, 3)
            self.assertEqual(result.replay_candidate_count, 2)
            self.assertEqual(result.audit_candidate_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(manifest["format"], LANE_CONTINUATION_CANDIDATES_FORMAT)
            self.assertIn("Queue Summary", public_report.read_text())

    def test_lane_continuation_candidates_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            study_manifest = _write_study_manifest(root)
            output_dir = root / "candidates"
            public_report = root / "reports" / "candidates.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-candidates",
                    "--study-manifest",
                    str(study_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top-per-bucket",
                    "2",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 3 lane-continuation candidate", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_study_manifest(root: Path) -> Path:
    path = root / "lane_continuation_study.json"
    payload = {
        "format": LANE_CONTINUATION_STUDY_FORMAT,
        "ready": True,
        "source_count": 1,
        "scenario_count": 3,
        "candidate_case_count": 3,
        "candidate_track_count": 3,
        "aggregate": {
            "linked_lane_track_count": 2,
            "improved_over_nearest_count": 1,
            "regressed_vs_nearest_count": 1,
            "topology_gap_count": 1,
            "mean_lane_link_improvement_m": 10.0,
        },
        "top_improvements": [
            _track(
                scenario_id="improvement_case",
                track_id="veh_1",
                nearest_fde=80.0,
                lane_link_fde=10.0,
                improvement=70.0,
                feature_chain=("100", "200"),
                link_count=1,
                status="linked_lane_chain",
            )
        ],
        "top_regressions": [
            _track(
                scenario_id="regression_case",
                track_id="veh_2",
                nearest_fde=8.0,
                lane_link_fde=44.0,
                improvement=-36.0,
                feature_chain=("300", "400"),
                link_count=1,
                status="linked_lane_chain",
            )
        ],
        "top_topology_gaps": [
            _track(
                scenario_id="topology_case",
                track_id="veh_3",
                nearest_fde=120.0,
                lane_link_fde=120.0,
                improvement=0.0,
                feature_chain=("500",),
                link_count=0,
                status="linked_feature_missing",
            )
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _track(
    scenario_id: str,
    track_id: str,
    nearest_fde: float,
    lane_link_fde: float,
    improvement: float,
    feature_chain: tuple[str, ...],
    link_count: int,
    status: str,
) -> dict[str, object]:
    return {
        "source_input": "local.tfrecord",
        "source_name": "local.tfrecord",
        "scenario_id": scenario_id,
        "track_id": track_id,
        "constant_velocity_fde_m": lane_link_fde,
        "heading_lane_fde_m": nearest_fde,
        "nearest_lane_fde_m": nearest_fde,
        "lane_link_fde_m": lane_link_fde,
        "lane_link_improvement_over_nearest_m": improvement,
        "lane_link": {
            "status": status,
            "selected_feature_id": feature_chain[0],
            "feature_chain": list(feature_chain),
            "link_count": link_count,
            "base_remaining_m": 5.0,
            "route_remaining_m": 90.0 if link_count else 5.0,
            "horizon_travel_m": 60.0,
            "lane_end_clamp_risk_after": False if link_count else True,
        },
    }


if __name__ == "__main__":
    unittest.main()
