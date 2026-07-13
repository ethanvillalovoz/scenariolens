from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.dashboard import DASHBOARD_FORMAT
from scenariolens.explorer import (
    EXPLORER_RUN_FORMAT,
    explorer_run_payload,
    generate_run_explorer,
    write_explorer_run_payload,
)
from scenariolens.io import save_scenarios
from scenariolens.samples import synthetic_scenarios


class ExplorerTest(unittest.TestCase):
    def test_generate_run_explorer_writes_ranked_cases_and_static_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            save_scenarios(input_path, synthetic_scenarios())

            result = generate_run_explorer(
                input_paths=(input_path,),
                input_format="scenariolens-json",
                output_dir=root / "run",
                max_scenarios=5,
                limit=3,
            )
            payload = json.loads(
                result.scenario_payload_path.read_text(encoding="utf-8")
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.source_count, 1)
            self.assertEqual(result.scenario_count, 5)
            self.assertEqual(result.rendered_case_count, 3)
            self.assertEqual(payload["format"], DASHBOARD_FORMAT)
            self.assertEqual(payload["reported_count"], 3)
            self.assertTrue(result.index_path.exists())
            self.assertTrue((result.explorer_dir / "app.js").exists())
            self.assertTrue((result.explorer_dir / "styles.css").exists())
            for scenario_id in result.scenario_ids:
                self.assertTrue((result.assets_dir / f"{scenario_id}.svg").exists())

    def test_generate_run_explorer_replaces_stale_svg_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "synthetic.json"
            output_dir = root / "run"
            assets_dir = output_dir / "assets"
            assets_dir.mkdir(parents=True)
            (assets_dir / "stale.svg").write_text("stale", encoding="utf-8")
            save_scenarios(input_path, synthetic_scenarios())

            generate_run_explorer(
                input_paths=(input_path,),
                input_format="scenariolens-json",
                output_dir=output_dir,
                max_scenarios=2,
                limit=1,
            )

            self.assertFalse((assets_dir / "stale.svg").exists())

    def test_explorer_run_payload_keeps_only_portable_input_provenance(self) -> None:
        manifest = _run_manifest()

        payload = explorer_run_payload(manifest)

        self.assertEqual(payload["format"], EXPLORER_RUN_FORMAT)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["summary"]["scenario_count"], 5)
        self.assertEqual(payload["summary"]["rendered_case_count"], 3)
        self.assertEqual(payload["inputs"][0]["source_name"], "synthetic.json")
        self.assertNotIn("input_path", payload["inputs"][0])
        self.assertEqual(
            payload["stages"][0]["report_path"],
            "../studies/baseline_comparison/report.md",
        )
        self.assertEqual(payload["reports"][0]["path"], "../report.md")

    def test_write_explorer_run_payload_writes_json_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "explorer" / "run.json"

            payload = write_explorer_run_payload(_run_manifest(), output_path)
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload, written)
        self.assertEqual(written["format"], EXPLORER_RUN_FORMAT)


def _run_manifest() -> dict[str, object]:
    return {
        "format": "scenariolens.run.v1",
        "ready": True,
        "scenariolens_version": "0.2.0",
        "source_count": 1,
        "scenario_count": 5,
        "stage_count": 1,
        "duration_seconds": 1.25,
        "peak_rss_bytes": 1024,
        "analysis_digest": "a" * 64,
        "configuration": {
            "input_format": "scenariolens-json",
            "max_scenarios_per_input": 5,
            "top": 3,
        },
        "inputs": [
            {
                "source_index": 1,
                "source_name": "synthetic.json",
                "input_path": "/private/synthetic.json",
                "size_bytes": 100,
                "sha256": "b" * 64,
            }
        ],
        "stages": [
            {
                "stage_id": "baseline_comparison",
                "label": "Baseline comparison",
                "ready": True,
                "scenario_count": 5,
                "evaluated_count": 8,
                "duration_seconds": 0.5,
                "aggregate": {"constant_velocity_fde_m": 2.0},
                "report": "studies/baseline_comparison/report.md",
            }
        ],
        "explorer": {
            "format": DASHBOARD_FORMAT,
            "ready": True,
            "scenario_count": 5,
            "reported_count": 3,
            "scenario_ids": ["one", "two", "three"],
        },
        "scope_note": "diagnostic only",
    }


if __name__ == "__main__":
    unittest.main()
