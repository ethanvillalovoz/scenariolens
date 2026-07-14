from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scenariolens.cli import release_check_command
from scenariolens.release_check import (
    RELEASE_CHECK_FORMAT,
    ReleaseCheckResult,
    generate_release_check,
)


class ReleaseCheckTest(unittest.TestCase):
    def test_generator_writes_reproducible_passing_packet(self) -> None:
        checks = [
            _check("wheel_build", True),
            _check("installed_product_run", True),
        ]
        evidence = {
            "wheel_name": "scenariolens-1.0.1-py3-none-any.whl",
            "wheel_sha256": "a" * 64,
            "rebuild_wheel_sha256": "a" * 64,
            "product_analysis_digest": "b" * 64,
            "resume_analysis_digest": "c" * 64,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_root(Path(tmpdir) / "repo")
            public_report = root / "docs" / "reports" / "release_check.md"
            with patch(
                "scenariolens.release_check._execute_release_checks",
                return_value=(checks, evidence),
            ):
                first = generate_release_check(
                    repo_root=root,
                    output_dir=Path(tmpdir) / "first",
                    public_report_path=public_report,
                )
                second = generate_release_check(
                    repo_root=root,
                    output_dir=Path(tmpdir) / "second",
                )

            self.assertTrue(first.ready)
            self.assertEqual(first.check_count, 2)
            self.assertEqual(first.passed_count, 2)
            self.assertEqual(first.analysis_digest, second.analysis_digest)
            payload = json.loads(first.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["format"], RELEASE_CHECK_FORMAT)
            self.assertEqual(payload["aggregate"]["failed_count"], 0)
            self.assertEqual(payload["evidence"]["wheel_sha256"], "a" * 64)
            self.assertTrue(first.report_path.is_file())
            self.assertTrue(public_report.is_file())
            report = public_report.read_text(encoding="utf-8")
            self.assertIn("**Status: PASS.**", report)
            self.assertIn("Installed Product Run", report)

    def test_generator_marks_failed_check_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_root(Path(tmpdir) / "repo")
            with patch(
                "scenariolens.release_check._execute_release_checks",
                return_value=([_check("clean_install", False)], {}),
            ):
                result = generate_release_check(
                    repo_root=root,
                    output_dir=Path(tmpdir) / "output",
                )

            self.assertFalse(result.ready)
            self.assertEqual(result.failed_count, 1)
            self.assertIn(
                "**Status: FAIL.**",
                result.report_path.read_text(encoding="utf-8"),
            )

    def test_generator_records_sanitized_orchestration_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_root(Path(tmpdir) / "private-repo")
            with patch(
                "scenariolens.release_check._execute_release_checks",
                side_effect=RuntimeError(f"cannot build {root}"),
            ):
                result = generate_release_check(
                    repo_root=root,
                    output_dir=Path(tmpdir) / "output",
                )

            self.assertFalse(result.ready)
            manifest = result.manifest_path.read_text(encoding="utf-8")
            self.assertNotIn(str(root), manifest)
            self.assertIn("cannot build <repo>", manifest)

    def test_generator_rejects_invalid_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_root(Path(tmpdir) / "repo")
            with self.assertRaisesRegex(ValueError, "timeout must be positive"):
                generate_release_check(
                    repo_root=root,
                    output_dir=Path(tmpdir) / "output",
                    timeout_seconds=0,
                )

    def test_generator_resolves_relative_output_before_changing_cwd(self) -> None:
        checks = [_check("wheel_build", True)]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _repo_root(Path(tmpdir) / "repo")
            previous_cwd = Path.cwd()
            os.chdir(tmpdir)
            try:
                with patch(
                    "scenariolens.release_check._execute_release_checks",
                    return_value=(checks, {}),
                ) as execute:
                    result = generate_release_check(
                        repo_root=root,
                        output_dir="relative-output",
                    )
            finally:
                os.chdir(previous_cwd)

            expected = (Path(tmpdir) / "relative-output").resolve()
            self.assertEqual(result.output_dir, expected)
            self.assertEqual(execute.call_args.kwargs["output_dir"], expected)
            self.assertTrue((expected / "manifest.json").is_file())

    def test_cli_returns_nonzero_when_release_packet_fails(self) -> None:
        failed = ReleaseCheckResult(
            ready=False,
            check_count=15,
            passed_count=14,
            failed_count=1,
            analysis_digest="d" * 64,
            duration_seconds=1.0,
            output_dir=Path("output"),
            manifest_path=Path("output/manifest.json"),
            report_path=Path("output/report.md"),
            public_report_path=None,
            wheel_path=None,
        )

        output = StringIO()
        with (
            patch("scenariolens.cli.generate_release_check", return_value=failed),
            redirect_stdout(output),
        ):
            return_code = release_check_command(
                repo_root=".",
                output_dir="output",
                public_report=None,
                timeout_seconds=30.0,
            )

        self.assertEqual(return_code, 2)
        self.assertIn("Release check failed: 14/15", output.getvalue())


def _check(check_id: str, passed: bool) -> dict[str, object]:
    return {
        "check_id": check_id,
        "label": check_id.replace("_", " ").title(),
        "passed": passed,
        "observed": "observed",
        "expected": "expected",
        "details": ["diagnostic"],
    }


def _repo_root(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / "pyproject.toml").write_text(
        "[build-system]\nrequires = ['setuptools>=68']\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    unittest.main()
