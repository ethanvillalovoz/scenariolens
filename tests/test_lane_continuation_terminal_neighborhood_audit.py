import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
    generate_lane_continuation_terminal_neighborhood_audit,
    lane_continuation_terminal_neighborhood_audit_markdown,
    lane_continuation_terminal_neighborhood_audit_payload,
)
from scenariolens.lane_continuation_topology_gap_audit import (
    LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
)


class LaneContinuationTerminalNeighborhoodAuditTest(unittest.TestCase):
    def test_payload_classifies_terminal_neighborhood_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = _write_native_json_source(root)
            topology_manifest = _write_topology_manifest(root, source)

            payload = lane_continuation_terminal_neighborhood_audit_payload(
                topology_manifest_path=topology_manifest,
                output_dir=root / "terminal_neighborhood_audit",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 3)
            self.assertEqual(aggregate["nearby_recovery_case_count"], 1)
            self.assertEqual(aggregate["directional_gap_case_count"], 1)
            self.assertEqual(aggregate["true_terminal_case_count"], 1)
            self.assertEqual(aggregate["selected_lane_issue_case_count"], 1)

            labels = {
                case["scenario_id"]: case["diagnosis_label"]
                for case in payload["cases"]
            }
            self.assertEqual(
                labels,
                {
                    "alternate_recovery_case": "nearby_alternate_lane_recovery",
                    "directional_case": "directional_link_mismatch",
                    "terminal_case": "true_terminal_or_map_boundary",
                },
            )
            alternate = payload["cases"][0]
            self.assertEqual(alternate["best_alternate_feature_id"], "2")
            self.assertEqual(alternate["linked_alternate_count"], 1)
            self.assertTrue(alternate["nearby_lanes"][0]["recovery_candidate"])

    def test_markdown_explains_scope_and_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_terminal_neighborhood_audit_payload(
                topology_manifest_path=_write_topology_manifest(
                    root,
                    _write_native_json_source(root),
                ),
                output_dir=root / "terminal_neighborhood_audit",
            )

            markdown = lane_continuation_terminal_neighborhood_audit_markdown(payload)

            self.assertIn("Terminal Neighborhood Audit", markdown)
            self.assertIn("nearby_alternate_lane_recovery", markdown)
            self.assertIn("directional_link_mismatch", markdown)
            self.assertIn("true_terminal_or_map_boundary", markdown)
            self.assertIn("Raw map geometry published: no", markdown)
            self.assertIn("not a Waymo benchmark claim", markdown)

    def test_generate_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            topology_manifest = _write_topology_manifest(
                root,
                _write_native_json_source(root),
            )
            public_report = root / "reports" / "terminal_neighborhood.md"

            result = generate_lane_continuation_terminal_neighborhood_audit(
                topology_manifest_path=topology_manifest,
                output_dir=root / "terminal_neighborhood_audit",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 3)
            self.assertEqual(result.nearby_recovery_count, 1)
            self.assertEqual(result.directional_gap_count, 1)
            self.assertEqual(result.true_terminal_count, 1)
            self.assertEqual(result.selected_lane_issue_count, 1)
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_AUDIT_FORMAT,
            )
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())

    def test_terminal_neighborhood_audit_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            topology_manifest = _write_topology_manifest(
                root,
                _write_native_json_source(root),
            )
            output_dir = root / "terminal_neighborhood_audit"
            public_report = root / "reports" / "terminal_neighborhood.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-audit",
                    "--topology-manifest",
                    str(topology_manifest),
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

            self.assertIn("Generated terminal-neighborhood audit", result.stdout)
            self.assertIn("1 nearby recovery candidate", result.stdout)
            self.assertIn("1 directional gap", result.stdout)
            self.assertIn("1 true terminal/map-boundary", result.stdout)
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
                        scenario_id="alternate_recovery_case",
                        track_id=101,
                        y=0.0,
                        map_features=[
                            _lane_feature(1, 0.0, 10.0, 0.0),
                            _lane_feature(2, 0.0, 10.0, 1.0, exit_lanes=[3]),
                            _lane_feature(3, 10.0, 40.0, 1.0),
                        ],
                    ),
                    _scenario_mapping(
                        scenario_id="directional_case",
                        track_id=102,
                        y=20.0,
                        map_features=[
                            _lane_feature(10, 0.0, 10.0, 20.0, entry_lanes=[11]),
                            _lane_feature(11, -20.0, 0.0, 20.0),
                        ],
                    ),
                    _scenario_mapping(
                        scenario_id="terminal_case",
                        track_id=103,
                        y=40.0,
                        map_features=[
                            _lane_feature(20, 0.0, 10.0, 40.0),
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


def _write_topology_manifest(root: Path, source: Path) -> Path:
    replay_manifest = root / "replay_manifest.json"
    replay_manifest.write_text(
        json.dumps({"max_scenarios_per_source": 25}, indent=2) + "\n",
        encoding="utf-8",
    )
    path = root / "topology_manifest.json"
    path.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
                "ready": True,
                "replay_manifest": str(replay_manifest),
                "candidate_manifest": "candidate_manifest.json",
                "study_manifest": "study_manifest.json",
                "case_count": 3,
                "cases": [
                    _topology_case(
                        rank=1,
                        scenario_id="alternate_recovery_case",
                        track_id="101",
                        source=source,
                        selected_feature_id="1",
                        status="no_exit_lanes",
                        link_field="exit_lanes",
                        horizon_travel_m=30.0,
                    ),
                    _topology_case(
                        rank=2,
                        scenario_id="directional_case",
                        track_id="102",
                        source=source,
                        selected_feature_id="10",
                        status="no_exit_lanes",
                        link_field="exit_lanes",
                        horizon_travel_m=30.0,
                    ),
                    _topology_case(
                        rank=3,
                        scenario_id="terminal_case",
                        track_id="103",
                        source=source,
                        selected_feature_id="20",
                        status="no_exit_lanes",
                        link_field="exit_lanes",
                        horizon_travel_m=30.0,
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
    y: float,
    map_features: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "scenarioId": scenario_id,
        "timestampsSeconds": [0.0, 1.0, 2.0, 3.0],
        "currentTimeIndex": 1,
        "tracksToPredict": [{"trackIndex": 0}],
        "mapFeatures": map_features,
        "tracks": [
            {
                "id": track_id,
                "objectType": "TYPE_VEHICLE",
                "states": [
                    {
                        "centerX": 2.0,
                        "centerY": y,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 9.0,
                        "centerY": y,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 20.0,
                        "centerY": y,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 35.0,
                        "centerY": y,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
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
    entry_lanes: list[int] | None = None,
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
    if entry_lanes:
        lane["entryLanes"] = entry_lanes
    return {"id": feature_id, "lane": lane}


def _topology_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    source: Path,
    selected_feature_id: str,
    status: str,
    link_field: str,
    horizon_travel_m: float,
) -> dict[str, object]:
    return {
        "rank": rank,
        "ready": True,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source),
        "source_name": source.name,
        "input_format": "native",
        "diagnosis_label": "terminal_lane_confirmed",
        "lane_link_status": status,
        "selected_feature_id": selected_feature_id,
        "link_field": link_field,
        "horizon_travel_m": horizon_travel_m,
        "route_gap_to_horizon_m": horizon_travel_m - 1.0,
    }


if __name__ == "__main__":
    unittest.main()
