import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.context_eval_set import (
    CONTEXT_EVAL_SET_FORMAT,
    context_eval_set_markdown,
    context_eval_set_payload,
    generate_context_eval_set,
)
from scenariolens.context_failure_study import CONTEXT_FAILURE_STUDY_FORMAT


class ContextEvalSetTest(unittest.TestCase):
    def test_context_eval_set_payload_groups_ranked_context_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = _write_context_failure_manifest(root)

            payload = context_eval_set_payload(
                context_failure_manifest_path=manifest,
                output_dir=root / "eval_set",
                top_per_group=2,
            )

            self.assertEqual(payload["format"], CONTEXT_EVAL_SET_FORMAT)
            self.assertTrue(payload["ready"])

            aggregate = payload["aggregate"]
            self.assertIsInstance(aggregate, dict)
            self.assertEqual(aggregate["group_count"], 5)
            self.assertEqual(aggregate["signal_case_count"], 2)
            self.assertEqual(aggregate["route_case_count"], 1)
            self.assertEqual(aggregate["lane_regression_case_count"], 1)
            self.assertEqual(aggregate["fallback_stress_case_count"], 2)
            self.assertEqual(aggregate["unique_scenario_count"], 4)

            group_ids = {group["group_id"] for group in payload["groups"]}
            self.assertIn("context_rich_failures", group_ids)
            self.assertIn("signal_context_failures", group_ids)
            self.assertIn("route_topology_failures", group_ids)
            self.assertIn("lane_aware_regressions", group_ids)
            self.assertIn("fallback_stress_cases", group_ids)

            seed_cases = payload["deduplicated_cases"]
            self.assertIsInstance(seed_cases, list)
            self.assertEqual(len(seed_cases), 4)
            self.assertIn("selection_groups", seed_cases[0])

            markdown = context_eval_set_markdown(payload)
            self.assertIn("Context Evaluation Set", markdown)
            self.assertIn("not an official Waymo benchmark", markdown)
            self.assertIn("Acceptance checks", markdown)
            self.assertIn("Deduplicated Seed Set", markdown)

    def test_generate_context_eval_set_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = _write_context_failure_manifest(root)
            output_dir = root / "eval_set"
            public_report = root / "reports" / "context_eval_set.md"

            result = generate_context_eval_set(
                context_failure_manifest_path=manifest,
                output_dir=output_dir,
                top_per_group=2,
                public_report_path=public_report,
            )
            output_manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.group_count, 5)
            self.assertEqual(result.unique_scenario_count, 4)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(result.scenario_ids_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(output_manifest["format"], CONTEXT_EVAL_SET_FORMAT)
            self.assertIn("signal_case", result.scenario_ids_path.read_text())

    def test_context_eval_set_cli_writes_run_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = _write_context_failure_manifest(root)
            output_dir = root / "eval_set"
            public_report = root / "reports" / "context_eval_set.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "context-eval-set",
                    "--context-failure-manifest",
                    str(manifest),
                    "--output-dir",
                    str(output_dir),
                    "--top-per-group",
                    "2",
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated 5 eval group", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "scenario_ids.txt").exists())
            self.assertTrue(public_report.exists())


def _write_context_failure_manifest(root: Path) -> Path:
    rows = {
        "signal": _row(
            scenario_id="signal_case",
            cv_fde=45.0,
            lane_delta=-8.0,
            signal_states=20,
            route_links=10,
            fallback_count=1,
        ),
        "signal_two": _row(
            scenario_id="signal_case_two",
            cv_fde=35.0,
            lane_delta=2.0,
            signal_states=8,
            route_links=4,
        ),
        "route": _row(
            scenario_id="route_case",
            cv_fde=30.0,
            lane_delta=4.0,
            signal_states=0,
            route_links=40,
        ),
        "regression": _row(
            scenario_id="regression_case",
            cv_fde=25.0,
            lane_delta=-14.0,
            signal_states=2,
            route_links=12,
            fallback_count=2,
        ),
    }
    payload = {
        "format": CONTEXT_FAILURE_STUDY_FORMAT,
        "ready": True,
        "source_count": 1,
        "scenario_count": 4,
        "aggregate": {
            "evaluated_target_count": 12,
            "constant_velocity_fde_m": 33.75,
            "constant_velocity_miss_rate": 0.75,
        },
        "hardest_context_failures": [
            rows["signal"],
            rows["route"],
            rows["regression"],
        ],
        "signal_context_failures": [rows["signal"], rows["signal_two"]],
        "route_context_failures": [rows["route"]],
        "lane_regressions_with_context": [rows["regression"]],
    }
    path = root / "context_failure_manifest.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _row(
    scenario_id: str,
    cv_fde: float,
    lane_delta: float,
    signal_states: int,
    route_links: int,
    fallback_count: int = 0,
) -> dict[str, object]:
    return {
        "source_input": "data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150",
        "source_name": "validation.tfrecord-00007-of-00150",
        "scenario_id": scenario_id,
        "score": 50.0,
        "evaluated_target_count": 3,
        "constant_velocity_fde_m": cv_fde,
        "constant_velocity_miss_rate": 1.0,
        "lane_aware_fde_m": cv_fde - lane_delta,
        "fde_improvement_m": lane_delta,
        "map_used_count": 2,
        "fallback_count": fallback_count,
        "map_feature_count": 120,
        "lane_count": 40,
        "signal_lane_state_count": signal_states,
        "signal_stop_state_count": signal_states // 2,
        "route_link_count": route_links,
        "entry_link_count": route_links // 3,
        "exit_link_count": route_links // 3,
        "neighbor_link_count": route_links // 3,
        "top_signal_state": "LANE_STATE_STOP (2)" if signal_states else "none",
    }


if __name__ == "__main__":
    unittest.main()
