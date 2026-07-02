import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_diagnostics import (
    LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
    generate_lane_continuation_route_diagnostics,
    lane_continuation_diagnostics_markdown,
    lane_continuation_diagnostics_payload,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT


class LaneContinuationDiagnosticsTest(unittest.TestCase):
    def test_diagnostics_payload_classifies_regression_and_topology_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)

            payload = lane_continuation_diagnostics_payload(
                replay_manifest_path=replay_manifest,
                output_dir=root / "diagnostics",
                top=10,
            )

            self.assertEqual(payload["format"], LANE_CONTINUATION_DIAGNOSTICS_FORMAT)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["diagnostic_count"], 2)
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["regression_diagnostic_count"], 1)
            self.assertEqual(aggregate["topology_diagnostic_count"], 1)
            self.assertEqual(aggregate["stable_regression_count"], 1)
            self.assertEqual(aggregate["missing_link_count"], 1)

            labels = {row["diagnosis_label"] for row in payload["diagnostics"]}
            self.assertIn("stable_route_choice_regression", labels)
            self.assertIn("missing_linked_feature", labels)

            markdown = lane_continuation_diagnostics_markdown(payload)
            self.assertIn("Lane-Continuation Route Diagnostics", markdown)
            self.assertIn("Stable Regression Diagnostics", markdown)
            self.assertIn("Topology Diagnostics", markdown)
            self.assertIn("not a route planner", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)

    def test_generate_diagnostics_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)
            output_dir = root / "diagnostics"
            public_report = root / "reports" / "diagnostics.md"

            result = generate_lane_continuation_route_diagnostics(
                replay_manifest_path=replay_manifest,
                output_dir=output_dir,
                top=10,
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.diagnostic_count, 2)
            self.assertEqual(result.regression_count, 1)
            self.assertEqual(result.topology_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
            )
            self.assertIn("Diagnostic Summary", public_report.read_text())

    def test_lane_continuation_route_diagnostics_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(root)
            output_dir = root / "diagnostics"
            public_report = root / "reports" / "diagnostics.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-route-diagnostics",
                    "--replay-manifest",
                    str(replay_manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top",
                    "10",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 2 lane-continuation diagnostic", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_replay_manifest(root: Path) -> Path:
    path = root / "lane_replay_manifest.json"
    payload = {
        "format": LANE_CONTINUATION_REPLAY_FORMAT,
        "ready": True,
        "candidate_manifest": str(root / "candidate_manifest.json"),
        "study_manifest": str(root / "study_manifest.json"),
        "aggregate": {
            "replayed_case_count": 1,
            "topology_probe_count": 1,
        },
        "cases": [
            _case(
                bucket="regression_replay_debug",
                scenario_id="regression_case",
                track_id="veh_1",
                lane_link_status="linked_lane_chain",
                lane_link_count=2,
                lane_link_improvement=-25.0,
                lane_link_vs_cv=4.0,
                clamp_after=False,
                stability_label="stable_regression_warning",
            ),
            _case(
                bucket="topology_audit",
                scenario_id="topology_case",
                track_id="veh_2",
                lane_link_status="linked_feature_missing",
                lane_link_count=0,
                lane_link_improvement=0.0,
                lane_link_vs_cv=-40.0,
                clamp_after=True,
                stability_label="not_evaluable",
            ),
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _case(
    bucket: str,
    scenario_id: str,
    track_id: str,
    lane_link_status: str,
    lane_link_count: int,
    lane_link_improvement: float,
    lane_link_vs_cv: float,
    clamp_after: bool,
    stability_label: str,
) -> dict[str, object]:
    return {
        "ready": True,
        "bucket": bucket,
        "readiness": "ready",
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "local_fixture.json",
        "nominal": {
            "constant_velocity_fde_m": 30.0,
            "nearest_lane_fde_m": 10.0,
            "heading_lane_fde_m": 10.0,
            "lane_link_fde_m": 10.0 - lane_link_improvement,
            "lane_link_improvement_over_nearest_m": lane_link_improvement,
            "lane_link_improvement_over_constant_m": lane_link_vs_cv,
            "lane_link_status": lane_link_status,
            "lane_link_count": lane_link_count,
            "feature_chain": ["100", "200"] if lane_link_count else ["100"],
            "base_remaining_m": 5.0,
            "route_remaining_m": 80.0 if lane_link_count else 5.0,
            "horizon_travel_m": 60.0,
            "lane_end_clamp_risk_after": clamp_after,
        },
        "perturbation_stability": {
            "label": stability_label,
            "valid_trial_count": 4 if bucket == "regression_replay_debug" else 0,
            "sign_preserving_trial_count": 4 if bucket == "regression_replay_debug" else 0,
            "max_delta_swing_m": 3.0 if bucket == "regression_replay_debug" else None,
        },
    }


if __name__ == "__main__":
    unittest.main()
