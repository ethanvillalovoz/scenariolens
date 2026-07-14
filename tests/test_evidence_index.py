import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.evidence_index import (
    DEFAULT_EVIDENCE_CATALOG,
    EVIDENCE_INDEX_FORMAT,
    evidence_index_markdown,
    evidence_index_payload,
    generate_evidence_index,
)


class EvidenceIndexTest(unittest.TestCase):
    def test_payload_verifies_catalog_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_catalog_files(Path(tmpdir))

            payload = evidence_index_payload(repo_root=root)

        self.assertEqual(payload["format"], EVIDENCE_INDEX_FORMAT)
        self.assertTrue(payload["ready"])
        aggregate = payload["aggregate"]
        self.assertEqual(aggregate["artifact_count"], len(DEFAULT_EVIDENCE_CATALOG))
        self.assertEqual(aggregate["missing_count"], 0)
        self.assertGreaterEqual(aggregate["stage_count"], 5)
        self.assertIn("selector_validation", aggregate["stage_counts"])

        artifact_ids = {artifact["id"] for artifact in payload["artifacts"]}
        self.assertIn("explorer_run_contract", artifact_ids)
        self.assertIn("terminal_selector_decision_atlas_200", artifact_ids)
        self.assertIn("selector_holdout_993", artifact_ids)
        self.assertIn("v1_run_validation", artifact_ids)
        self.assertIn("v1_release_check", artifact_ids)
        self.assertIn("ci_workflow", artifact_ids)

    def test_payload_marks_missing_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_catalog_files(Path(tmpdir))
            missing_path = root / DEFAULT_EVIDENCE_CATALOG[0].path
            missing_path.unlink()

            payload = evidence_index_payload(repo_root=root)

        self.assertFalse(payload["ready"])
        self.assertEqual(payload["aggregate"]["missing_count"], 1)
        self.assertEqual(payload["missing_artifacts"][0]["path"], DEFAULT_EVIDENCE_CATALOG[0].path)

    def test_markdown_summarizes_readiness_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = evidence_index_payload(repo_root=_write_catalog_files(Path(tmpdir)))

        markdown = evidence_index_markdown(payload)

        self.assertIn("ScenarioLens V1 Evidence Index", markdown)
        self.assertIn("Ready: yes", markdown)
        self.assertIn("Terminal Selector Decision Atlas", markdown)
        self.assertIn("993-Scenario Frozen Selector Holdout", markdown)
        self.assertIn("Full-Corpus Run Reproducibility", markdown)
        self.assertIn("V1 Clean-Package Release Check", markdown)
        self.assertIn("Public-Safety Boundary", markdown)

    def test_generator_writes_manifest_report_public_report_and_demo_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_catalog_files(Path(tmpdir) / "repo")
            output_dir = Path(tmpdir) / "evidence"
            public_report = root / "docs" / "reports" / "scenariolens_evidence_index.md"
            demo_json = root / "docs" / "demo" / "evidence_index.json"

            result = generate_evidence_index(
                output_dir=output_dir,
                public_report_path=public_report,
                demo_json_path=demo_json,
                repo_root=root,
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.missing_count, 0)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())
            self.assertTrue(demo_json.exists())
            demo_payload = json.loads(demo_json.read_text(encoding="utf-8"))
            self.assertEqual(demo_payload["format"], EVIDENCE_INDEX_FORMAT)

    def test_cli_writes_evidence_index_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _write_catalog_files(Path(tmpdir) / "repo")
            output_dir = Path(tmpdir) / "evidence"
            public_report = root / "docs" / "reports" / "scenariolens_evidence_index.md"
            demo_json = root / "docs" / "demo" / "evidence_index.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "evidence-index",
                    "--repo-root",
                    str(root),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                    "--demo-json",
                    str(demo_json),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Indexed", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue(public_report.exists())
            self.assertTrue(demo_json.exists())


def _write_catalog_files(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for item in DEFAULT_EVIDENCE_CATALOG:
        path = root / item.path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}\n", encoding="utf-8")
        elif path.suffix in {".yml", ".yaml"}:
            path.write_text("name: test\n", encoding="utf-8")
        else:
            path.write_text(f"# {item.title}\n", encoding="utf-8")
    return root
