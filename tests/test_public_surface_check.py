import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.public_surface_check import (
    PUBLIC_SURFACE_CHECK_FORMAT,
    generate_public_surface_check,
    public_surface_check_markdown,
    public_surface_check_payload,
)


class PublicSurfaceCheckTest(unittest.TestCase):
    def test_payload_passes_for_complete_public_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_public_surface_repo(Path(tmpdir))

            payload = public_surface_check_payload(repo_root=root)

        self.assertEqual(payload["format"], PUBLIC_SURFACE_CHECK_FORMAT)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["aggregate"]["failed_count"], 0)
        check_ids = {check["id"] for check in payload["checks"]}
        self.assertIn("local_link_integrity", check_ids)
        self.assertIn("raw_data_boundary", check_ids)
        self.assertIn("ci_surface", check_ids)

    def test_payload_fails_for_broken_local_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_public_surface_repo(Path(tmpdir))
            (root / "README.md").write_text(
                "[missing](docs/reports/missing.md)\n",
                encoding="utf-8",
            )

            payload = public_surface_check_payload(repo_root=root)

        self.assertFalse(payload["ready"])
        failures = {failure["id"] for failure in payload["failures"]}
        self.assertIn("local_link_integrity", failures)

    def test_payload_fails_for_raw_tfrecord_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_public_surface_repo(Path(tmpdir))
            raw = root / "data" / "raw" / "waymo" / "motion" / "validation.tfrecord-00000-of-00150"
            raw.parent.mkdir(parents=True)
            raw.write_text("raw placeholder", encoding="utf-8")

            payload = public_surface_check_payload(repo_root=root)

        self.assertFalse(payload["ready"])
        failures = {failure["id"] for failure in payload["failures"]}
        self.assertIn("raw_data_boundary", failures)

    def test_markdown_names_public_safety_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = public_surface_check_payload(
                repo_root=_write_public_surface_repo(Path(tmpdir))
            )

        markdown = public_surface_check_markdown(payload)

        self.assertIn("ScenarioLens Public Surface Check", markdown)
        self.assertIn("Ready: yes", markdown)
        self.assertIn("Public-Safety Boundary", markdown)

    def test_generator_writes_manifest_report_and_public_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_public_surface_repo(Path(tmpdir) / "repo")
            output_dir = Path(tmpdir) / "surface"
            public_report = root / "docs" / "reports" / "scenariolens_public_surface_check.md"

            result = generate_public_surface_check(
                output_dir=output_dir,
                public_report_path=public_report,
                repo_root=root,
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.failed_count, 0)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())

    def test_cli_writes_public_surface_check_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_public_surface_repo(Path(tmpdir) / "repo")
            output_dir = Path(tmpdir) / "surface"
            public_report = root / "docs" / "reports" / "scenariolens_public_surface_check.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "public-surface-check",
                    "--repo-root",
                    str(root),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Ran", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue(public_report.exists())


def _write_public_surface_repo(root: Path) -> Path:
    (root / "docs" / "demo" / "assets").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "reports").mkdir(parents=True, exist_ok=True)
    (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "raw" / ".gitkeep").write_text("", encoding="utf-8")

    (root / "README.md").write_text(
        "\n".join(
            [
                "# ScenarioLens",
                "[demo](docs/demo/index.html)",
                "[evidence](docs/reports/scenariolens_evidence_index.md)",
                "[license](LICENSE)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "docs" / "data_provenance.md").write_text(
        "Raw Waymo files stay outside git.\n",
        encoding="utf-8",
    )
    (root / "docs" / "demo" / "index.html").write_text(
        """
        <html>
          <head><link href="styles.css" rel="stylesheet"></head>
          <body>
            <a href="../reports/scenariolens_evidence_index.md">Evidence index</a>
            <a href="../reports/scenariolens_public_surface_check.md">Surface check</a>
            <script src="app.js"></script>
          </body>
        </html>
        """,
        encoding="utf-8",
    )
    (root / "docs" / "demo" / "README.md").write_text(
        "[provenance](../data_provenance.md)\n",
        encoding="utf-8",
    )
    (root / "docs" / "demo" / "styles.css").write_text("body{}\n", encoding="utf-8")
    (root / "docs" / "demo" / "app.js").write_text("console.log('ok');\n", encoding="utf-8")
    (root / "docs" / "demo" / "assets" / "scenario.svg").write_text(
        "<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>\n",
        encoding="utf-8",
    )
    (root / "docs" / "demo" / "assets" / "selector.svg").write_text(
        "<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>\n",
        encoding="utf-8",
    )
    _write_json(
        root / "docs" / "demo" / "scenarios.json",
        {
            "format": "scenariolens.dashboard.v1",
            "scenario_count": 1,
            "scenarios": [{"scenario_id": "s1", "asset_path": "assets/scenario.svg"}],
        },
    )
    _write_json(
        root / "docs" / "demo" / "run.json",
        {
            "format": "scenariolens.explorer_run.v1",
            "ready": True,
            "summary": {"scenario_count": 1},
            "stages": [],
            "reports": [],
        },
    )
    _write_json(
        root / "docs" / "demo" / "selector_decisions.json",
        {
            "format": (
                "scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas.v1"
            ),
            "ready": True,
            "aggregate": {"case_count": 1},
            "cases": [{"case_label": "Case 01", "asset_path": "assets/selector.svg"}],
        },
    )
    _write_json(
        root / "docs" / "demo" / "evidence_index.json",
        {
            "format": "scenariolens.evidence_index.v1",
            "ready": True,
            "aggregate": {
                "artifact_count": 16,
                "missing_count": 0,
                "required_count": 16,
            },
            "artifacts": [],
        },
    )
    (root / "docs" / "reports" / "scenariolens_evidence_index.md").write_text(
        "\n".join(
            [
                "# Evidence",
                "This is not a Waymo benchmark.",
                "Raw Waymo TFRecords stay outside git.",
                "The default selector remains unchanged.",
                "[demo](../demo/index.html)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "docs" / "reports" / "scenariolens_public_surface_check.md").write_text(
        "# Surface check\n",
        encoding="utf-8",
    )
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "\n".join(
            [
                "python -m unittest discover",
                "node --check docs/demo/app.js",
                "python -m json.tool docs/demo/run.json",
                "python -m json.tool docs/demo/evidence_index.json",
                "npm run test:browser",
                "scenariolens run",
                "scenariolens run-verify",
                "scenariolens release-check",
                "scenariolens evidence-index",
                "scenariolens public-surface-check",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
