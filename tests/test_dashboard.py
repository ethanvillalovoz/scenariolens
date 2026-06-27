import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.dashboard import (
    DASHBOARD_FORMAT,
    DashboardScenarioSet,
    dashboard_payload,
    generate_dashboard_data,
)
from scenariolens.samples import synthetic_scenarios


class DashboardDataTest(unittest.TestCase):
    def test_checked_in_static_demo_files_are_present(self) -> None:
        docs_root = Path("docs")
        root = Path("docs/demo")
        landing = (docs_root / "index.html").read_text(encoding="utf-8")
        html = (root / "index.html").read_text(encoding="utf-8")
        payload = json.loads((root / "scenarios.json").read_text(encoding="utf-8"))

        self.assertIn('url=demo/', landing)
        self.assertTrue((docs_root / ".nojekyll").exists())
        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js"', html)
        self.assertTrue((root / "assets" / "scenariolens-explorer.png").exists())
        self.assertEqual(payload["format"], DASHBOARD_FORMAT)
        for item in payload["scenarios"]:
            self.assertTrue((root / item["svg_path"]).exists())

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

    def test_generate_dashboard_data_writes_json_and_svg_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "demo" / "scenarios.json"
            assets = root / "demo" / "assets"

            generate_dashboard_data(
                output_path=output,
                assets_dir=assets,
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


if __name__ == "__main__":
    unittest.main()
