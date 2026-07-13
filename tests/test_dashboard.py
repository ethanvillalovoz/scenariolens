import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.dashboard import (
    CASE_DIAGNOSTICS_FORMAT,
    DASHBOARD_FORMAT,
    DashboardScenarioSet,
    dashboard_payload,
    generate_dashboard_data,
    load_lane_selection_case_diagnostics,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT,
)
from scenariolens.samples import synthetic_scenarios


class DashboardDataTest(unittest.TestCase):
    def test_checked_in_static_demo_files_are_present(self) -> None:
        docs_root = Path("docs")
        root = Path("docs/demo")
        landing = (docs_root / "index.html").read_text(encoding="utf-8")
        html = (root / "index.html").read_text(encoding="utf-8")
        payload = json.loads((root / "scenarios.json").read_text(encoding="utf-8"))
        run_payload = json.loads((root / "run.json").read_text(encoding="utf-8"))
        selector_atlas = json.loads(
            (root / "selector_decisions.json").read_text(encoding="utf-8")
        )

        self.assertIn('url=demo/', landing)
        self.assertTrue((docs_root / ".nojekyll").exists())
        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js"', html)
        self.assertIn('id="heroScenarioCount"', html)
        self.assertIn('id="heroMaxFde"', html)
        self.assertIn('id="stageSummary"', html)
        self.assertIn('id="reportLinks"', html)
        self.assertIn('id="baselineCard"', html)
        self.assertIn('id="diagnosticRows"', html)
        self.assertIn('id="selectorAtlasCards"', html)
        self.assertIn('./run.json', html)
        self.assertIn(
            '../reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md',
            html,
        )
        self.assertTrue((docs_root / "data_provenance.md").exists())
        self.assertTrue((docs_root / "reports" / "waymo_motion_failure_stability.md").exists())
        self.assertTrue((docs_root / "reports" / "waymo_motion_shard_plan.md").exists())
        self.assertTrue((root / "assets" / "scenariolens-explorer.png").exists())
        self.assertEqual(payload["format"], DASHBOARD_FORMAT)
        self.assertEqual(run_payload["format"], "scenariolens.explorer_run.v1")
        self.assertTrue(run_payload["ready"])
        self.assertEqual(run_payload["summary"]["scenario_count"], 1193)
        self.assertEqual(len(run_payload["stages"]), 3)
        self.assertIn("case_diagnostics", payload)
        self.assertEqual(
            payload["case_diagnostics"]["format"],
            CASE_DIAGNOSTICS_FORMAT,
        )
        self.assertEqual(
            selector_atlas["format"],
            LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT,
        )
        self.assertEqual(selector_atlas["aggregate"]["case_count"], 7)
        self.assertEqual(selector_atlas["aggregate"]["candidate_match_count"], 6)
        self.assertEqual(selector_atlas["aggregate"]["candidate_false_promote_count"], 0)
        self.assertEqual(
            selector_atlas["aggregate"]["category_counts"]["candidate_recovery"],
            1,
        )
        for item in payload["scenarios"]:
            self.assertTrue((root / item["svg_path"]).exists())
        for item in selector_atlas["cases"]:
            self.assertTrue((root / item["asset_path"]).exists())

    def test_dashboard_payload_contains_stable_contract_fields(self) -> None:
        scenarios = synthetic_scenarios()[:2]
        payload = dashboard_payload(
            scenario_sets=(
                DashboardScenarioSet(
                    dataset_id="synthetic_test",
                    label="Synthetic test",
                    scenarios=scenarios,
                ),
            ),
            asset_prefix=Path("assets"),
        )

        self.assertEqual(payload["format"], DASHBOARD_FORMAT)
        self.assertEqual(payload["scenario_count"], 2)
        self.assertEqual(payload["reported_count"], 2)
        self.assertEqual(payload["datasets"][0]["dataset_id"], "synthetic_test")
        self.assertIn("tags", payload["filters"])
        self.assertIn("component_names", payload["filters"])

        first = payload["scenarios"][0]
        self.assertIn("rank", first)
        self.assertIn("scenario_id", first)
        self.assertIn("dataset_id", first)
        self.assertIn("svg_path", first)
        self.assertIn("reasons", first)
        self.assertIn("score", first)
        self.assertIn("metrics", first)
        self.assertIn("tracks", first)
        self.assertTrue(first["svg_path"].startswith("assets/"))
        self.assertIn("components", first["score"])
        self.assertIn("agent_count", first["metrics"])
        self.assertIn("scoring_agent_count", first["metrics"])
        self.assertIn("excluded_track_count", first["metrics"])
        self.assertIn("sdc_track_present", first["metrics"])
        self.assertIn("baseline_fde_m", first["metrics"])
        self.assertIn("baseline_failure", first["score"]["components"])
        self.assertIn("lane_aware_fde_m", first["metrics"])
        self.assertIn("baseline_fde_improvement_m", first["metrics"])
        self.assertIn("lane_aware_map_used_count", first["metrics"])
        self.assertIn("lane_aware_fallback_reasons", first["metrics"])

    def test_dashboard_payload_can_include_case_diagnostics(self) -> None:
        diagnostics = {
            "format": CASE_DIAGNOSTICS_FORMAT,
            "groups": [],
        }
        payload = dashboard_payload(
            scenario_sets=(
                DashboardScenarioSet(
                    dataset_id="synthetic_test",
                    label="Synthetic test",
                    scenarios=synthetic_scenarios()[:1],
                ),
            ),
            asset_prefix=Path("assets"),
            case_diagnostics=diagnostics,
        )

        self.assertEqual(payload["case_diagnostics"], diagnostics)

    def test_load_lane_selection_case_diagnostics_is_public_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "format": "scenariolens.lane_selection_study.v1",
                        "source_count": 1,
                        "scenario_count": 2,
                        "aggregate": {
                            "evaluated_target_count": 4,
                            "constant_velocity_fde_m": 12.0,
                            "nearest_lane_fde_m": 11.0,
                            "heading_lane_fde_m": 9.0,
                            "heading_vs_nearest_fde_improvement_m": 2.0,
                            "heading_vs_constant_velocity_fde_improvement_m": 3.0,
                        },
                        "heading_fallback_reasons": {
                            "target_too_far_from_lane": 3,
                            "lane_heading_misaligned": 1,
                        },
                        "sources": [
                            {
                                "input_path": "data/raw/private.tfrecord",
                                "source_name": "validation.tfrecord-00008-of-00150",
                                "ready": True,
                                "scenario_count": 2,
                                "evaluated_target_count": 4,
                                "constant_velocity_fde_m": 12.0,
                                "nearest_lane_fde_m": 11.0,
                                "heading_lane_fde_m": 9.0,
                            }
                        ],
                        "top_heading_improvements": [
                            _diagnostic_case("improved_case", 2.0)
                        ],
                        "top_heading_regressions": [
                            _diagnostic_case("regressed_case", -1.0)
                        ],
                        "top_heading_fallbacks": [
                            _diagnostic_case("fallback_case", 0.0)
                        ],
                        "scope_note": "diagnostic only",
                    }
                ),
                encoding="utf-8",
            )

            diagnostics = load_lane_selection_case_diagnostics(manifest)

        self.assertIsNotNone(diagnostics)
        assert diagnostics is not None
        self.assertEqual(diagnostics["format"], CASE_DIAGNOSTICS_FORMAT)
        self.assertEqual(diagnostics["scenario_count"], 2)
        self.assertEqual(diagnostics["summary"]["heading_lane_fde_m"], 9.0)
        self.assertEqual(
            diagnostics["debug_report_path"],
            "../reports/waymo_heading_aware_debug_casebook.md",
        )
        self.assertEqual(diagnostics["fallback_reasons"][0]["reason"], "target_too_far_from_lane")
        self.assertEqual(len(diagnostics["groups"]), 3)
        first_case = diagnostics["groups"][0]["cases"][0]
        self.assertEqual(first_case["scenario_id"], "improved_case")
        self.assertNotIn("source_input", first_case)
        self.assertNotIn("input_path", diagnostics["sources"][0])

    def test_load_lane_selection_case_diagnostics_ignores_missing_manifest(self) -> None:
        self.assertIsNone(load_lane_selection_case_diagnostics("missing-manifest.json"))

    def test_generate_dashboard_data_writes_json_and_svg_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "demo" / "scenarios.json"
            assets = root / "demo" / "assets"

            generate_dashboard_data(
                output_path=output,
                assets_dir=assets,
                lane_selection_manifest_path=None,
                limit=3,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(payload["format"], DASHBOARD_FORMAT)
            self.assertEqual(payload["reported_count"], 3)
            self.assertEqual(len(payload["scenarios"]), 3)
            for item in payload["scenarios"]:
                self.assertTrue((root / "demo" / item["svg_path"]).exists())

    def test_generate_dashboard_data_supports_external_assets_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "demo" / "scenarios.json"
            assets = root / "shared_assets"

            generate_dashboard_data(
                output_path=output,
                assets_dir=assets,
                lane_selection_manifest_path=None,
                limit=1,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            item = payload["scenarios"][0]

            self.assertTrue(item["svg_path"].startswith("../shared_assets/"))
            self.assertTrue((root / "demo" / item["svg_path"]).exists())

    def test_dashboard_payload_rejects_duplicate_scenario_ids(self) -> None:
        scenario = synthetic_scenarios()[0]

        with self.assertRaises(ValueError):
            dashboard_payload(
                scenario_sets=(
                    DashboardScenarioSet(
                        dataset_id="first",
                        label="First",
                        scenarios=(scenario,),
                    ),
                    DashboardScenarioSet(
                        dataset_id="second",
                        label="Second",
                        scenarios=(scenario,),
                    ),
                ),
                asset_prefix=Path("assets"),
            )


def _diagnostic_case(scenario_id: str, improvement: float) -> dict[str, object]:
    return {
        "source_input": "data/raw/private.tfrecord",
        "source_name": "validation.tfrecord-00008-of-00150",
        "source_index": 1,
        "scenario_index": 2,
        "scenario_id": scenario_id,
        "evaluated_target_count": 4,
        "constant_velocity_fde_m": 12.0,
        "nearest_lane_fde_m": 11.0,
        "heading_lane_fde_m": 9.0,
        "heading_vs_nearest_fde_improvement_m": improvement,
        "heading_vs_constant_velocity_fde_improvement_m": 3.0,
        "nearest_map_used_count": 2,
        "nearest_fallback_count": 2,
        "heading_map_used_count": 3,
        "heading_fallback_count": 1,
        "top_heading_fallback_reason": "target_too_far_from_lane (1)",
    }


if __name__ == "__main__":
    unittest.main()
