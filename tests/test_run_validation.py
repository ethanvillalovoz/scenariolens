from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import save_scenarios
from scenariolens.run_bundle import generate_run_bundle
from scenariolens.run_validation import (
    RUN_VALIDATION_FORMAT,
    generate_run_validation,
)
from scenariolens.samples import synthetic_scenarios


class RunValidationTest(unittest.TestCase):
    def test_generate_run_validation_accepts_matching_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first, second = _matching_runs(root)

            result = generate_run_validation(
                run_manifest_paths=(first.manifest_path, second.manifest_path),
                output_dir=root / "validation",
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.run_count, 2)
            self.assertEqual(result.check_count, 7)
            self.assertEqual(result.passed_count, 7)
            self.assertEqual(result.analysis_digest, first.analysis_digest)
            payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], RUN_VALIDATION_FORMAT)
            self.assertEqual(payload["aggregate"]["scenario_count"], 11)
            self.assertGreater(payload["aggregate"]["maximum_peak_rss_bytes"], 0)
            report = result.report_path.read_text(encoding="utf-8")
            self.assertIn("Run Reproducibility Validation", report)
            self.assertIn("7", str(result.passed_count))
            self.assertIn("not closed-loop autonomy safety", report)

    def test_generate_run_validation_rejects_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first, second = _matching_runs(root)
            payload = json.loads(second.manifest_path.read_text(encoding="utf-8"))
            payload["analysis_digest"] = "0" * 64
            second.manifest_path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

            result = generate_run_validation(
                run_manifest_paths=(first.manifest_path, second.manifest_path),
                output_dir=root / "validation",
            )

            self.assertFalse(result.ready)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            digest_check = next(
                check
                for check in manifest["checks"]
                if check["check_id"] == "analysis_digest"
            )
            self.assertFalse(digest_check["passed"])

    def test_generate_run_validation_enforces_duration_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first, second = _matching_runs(root)

            result = generate_run_validation(
                run_manifest_paths=(first.manifest_path, second.manifest_path),
                output_dir=root / "validation",
                max_duration_seconds=0.000001,
            )

            self.assertFalse(result.ready)
            self.assertEqual(result.passed_count, 6)

    def test_run_verify_cli_writes_validation_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first, second = _matching_runs(root)
            output_dir = root / "validation"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "run-verify",
                    "--manifest",
                    str(first.manifest_path),
                    "--manifest",
                    str(second.manifest_path),
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Run validation ready", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())


def _matching_runs(root: Path):
    input_path = root / "synthetic.json"
    save_scenarios(input_path, synthetic_scenarios())
    first = generate_run_bundle(
        input_paths=(input_path,),
        output_dir=root / "run_01",
        max_scenarios=11,
        top=4,
        input_format="scenariolens-json",
    )
    second = generate_run_bundle(
        input_paths=(input_path,),
        output_dir=root / "run_02",
        max_scenarios=11,
        top=4,
        input_format="scenariolens-json",
    )
    return first, second


if __name__ == "__main__":
    unittest.main()
