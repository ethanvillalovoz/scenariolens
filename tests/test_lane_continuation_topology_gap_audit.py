import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scenariolens.ingest.waymo_motion import MAX_MAP_FEATURES_PER_SCENARIO
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.lane_continuation_topology_gap_audit import (
    LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
    generate_lane_continuation_topology_gap_audit,
    lane_continuation_topology_gap_audit_markdown,
    lane_continuation_topology_gap_audit_payload,
    _raw_inventory_cache,
    _raw_scenario_mappings,
)


class LaneContinuationTopologyGapAuditTest(unittest.TestCase):
    def test_payload_classifies_cap_recovery_and_terminal_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = _write_native_json_source(root)
            replay_manifest = _write_replay_manifest(root, source)

            payload = lane_continuation_topology_gap_audit_payload(
                replay_manifest_path=replay_manifest,
                output_dir=root / "topology_gap_audit",
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 2)
            self.assertEqual(aggregate["cap_recovered_case_count"], 1)
            self.assertEqual(aggregate["cap_recoverable_case_count"], 0)
            self.assertEqual(aggregate["terminal_confirmed_case_count"], 1)
            self.assertEqual(aggregate["capped_map_at_limit_count"], 1)
            self.assertEqual(aggregate["raw_source_pass_count"], 1)
            self.assertEqual(aggregate["raw_scenario_inventory_count"], 2)

            cap_case, terminal_case = payload["cases"]
            self.assertEqual(cap_case["diagnosis_label"], "cap_recovered_link_target")
            self.assertEqual(cap_case["raw_lane_feature_count"], MAX_MAP_FEATURES_PER_SCENARIO + 2)
            self.assertEqual(
                cap_case["capped_lane_feature_count"],
                MAX_MAP_FEATURES_PER_SCENARIO + 1,
            )
            target = cap_case["link_target_presence"][0]
            self.assertEqual(target["target_id"], str(MAX_MAP_FEATURES_PER_SCENARIO + 2))
            self.assertTrue(target["present_in_capped_map"])
            self.assertTrue(target["present_in_raw_map"])
            self.assertTrue(target["beyond_cap"])
            self.assertEqual(
                terminal_case["diagnosis_label"],
                "terminal_lane_confirmed",
            )

    def test_markdown_explains_scope_and_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = lane_continuation_topology_gap_audit_payload(
                replay_manifest_path=_write_replay_manifest(
                    root,
                    _write_native_json_source(root),
                ),
                output_dir=root / "topology_gap_audit",
            )

            markdown = lane_continuation_topology_gap_audit_markdown(payload)

            self.assertIn("Topology Gap Audit", markdown)
            self.assertIn("cap_recovered_link_target", markdown)
            self.assertIn("terminal_lane_confirmed", markdown)
            self.assertIn("Raw scenario data committed: no", markdown)
            self.assertIn("Batched raw-source passes", markdown)
            self.assertIn("not a Waymo benchmark claim", markdown)

    def test_generate_writes_manifest_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(
                root,
                _write_native_json_source(root),
            )
            public_report = root / "reports" / "topology_gap_audit.md"

            result = generate_lane_continuation_topology_gap_audit(
                replay_manifest_path=replay_manifest,
                output_dir=root / "topology_gap_audit",
                public_report_path=public_report,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.cap_recovered_count, 1)
            self.assertEqual(result.cap_recoverable_count, 0)
            self.assertEqual(result.terminal_confirmed_count, 1)
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TOPOLOGY_GAP_AUDIT_FORMAT,
            )
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())

    def test_raw_inventory_batches_cases_from_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = _write_native_json_source(root)
            replay = json.loads(
                _write_replay_manifest(root, source).read_text(encoding="utf-8")
            )

            with patch(
                "scenariolens.lane_continuation_topology_gap_audit._raw_scenario_mappings",
                wraps=_raw_scenario_mappings,
            ) as scan:
                cache = _raw_inventory_cache(
                    replay_cases=replay["cases"],
                    max_scenarios=None,
                )

            self.assertEqual(scan.call_count, 1)
            self.assertEqual(len(cache), 2)
            self.assertTrue(
                cache[(str(source), "native", "cap_gap_case", None)]["ready"]
            )
            self.assertTrue(
                cache[(str(source), "native", "terminal_case", None)]["ready"]
            )

    def test_topology_gap_audit_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            replay_manifest = _write_replay_manifest(
                root,
                _write_native_json_source(root),
            )
            output_dir = root / "topology_gap_audit"
            public_report = root / "reports" / "topology_gap_audit.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-topology-gap-audit",
                    "--replay-manifest",
                    str(replay_manifest),
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

            self.assertIn("Generated topology gap audit", result.stdout)
            self.assertIn("1 recovered", result.stdout)
            self.assertIn("0 cap-recoverable", result.stdout)
            self.assertIn("1 terminal confirmation", result.stdout)
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
                        scenario_id="cap_gap_case",
                        track_id=1466,
                        selected_lane_id=1,
                        exit_lanes=[MAX_MAP_FEATURES_PER_SCENARIO + 2],
                        map_features=_cap_gap_features(),
                    ),
                    _scenario_mapping(
                        scenario_id="terminal_case",
                        track_id=1061,
                        selected_lane_id=10,
                        exit_lanes=[],
                        map_features=[
                            _lane_feature(
                                feature_id=10,
                                x0=0.0,
                                x1=10.0,
                                y=0.0,
                                exit_lanes=[],
                            )
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


def _write_replay_manifest(root: Path, source: Path) -> Path:
    path = root / "replay_manifest.json"
    path.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_REPLAY_FORMAT,
                "ready": True,
                "candidate_manifest": "candidate_manifest.json",
                "study_manifest": "study_manifest.json",
                "cases": [
                    _replay_case(
                        rank=1,
                        scenario_id="cap_gap_case",
                        track_id="1466",
                        source=source,
                        status="linked_feature_missing",
                        selected_feature_id="1",
                        route_remaining_m=10.0,
                        horizon_travel_m=80.0,
                    ),
                    _replay_case(
                        rank=2,
                        scenario_id="terminal_case",
                        track_id="1061",
                        source=source,
                        status="no_exit_lanes",
                        selected_feature_id="10",
                        route_remaining_m=10.0,
                        horizon_travel_m=60.0,
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
    selected_lane_id: int,
    exit_lanes: list[int],
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
                        "centerX": 1.0,
                        "centerY": 0.0,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 9.0,
                        "centerY": 0.0,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 30.0,
                        "centerY": 0.0,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                    {
                        "centerX": 60.0,
                        "centerY": 0.0,
                        "velocityX": 5.0,
                        "velocityY": 0.0,
                        "valid": True,
                    },
                ],
            }
        ],
    }


def _cap_gap_features() -> list[dict[str, object]]:
    features = [
        _lane_feature(
            feature_id=1,
            x0=0.0,
            x1=10.0,
            y=0.0,
            exit_lanes=[MAX_MAP_FEATURES_PER_SCENARIO + 2],
        )
    ]
    for feature_id in range(2, MAX_MAP_FEATURES_PER_SCENARIO + 3):
        features.append(
            _lane_feature(
                feature_id=feature_id,
                x0=0.0,
                x1=10.0,
                y=1000.0 + feature_id,
                exit_lanes=[],
            )
        )
    return features


def _lane_feature(
    feature_id: int,
    x0: float,
    x1: float,
    y: float,
    exit_lanes: list[int],
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


def _replay_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    source: Path,
    status: str,
    selected_feature_id: str,
    route_remaining_m: float,
    horizon_travel_m: float,
) -> dict[str, object]:
    return {
        "rank": rank,
        "bucket": "topology_audit",
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_input": str(source),
        "source_name": source.name,
        "input_format": "native",
        "nominal": {
            "lane_link_status": status,
            "selected_feature_id": selected_feature_id,
            "feature_chain": [selected_feature_id],
            "route_remaining_m": route_remaining_m,
            "horizon_travel_m": horizon_travel_m,
        },
    }


if __name__ == "__main__":
    unittest.main()
