import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_selector_candidate_validation import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_candidate_validation,
    lane_continuation_terminal_neighborhood_selector_candidate_validation_markdown,
    lane_continuation_terminal_neighborhood_selector_candidate_validation_payload,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_route_context_audit import (
    generate_lane_continuation_terminal_neighborhood_selector_route_context_audit,
)
from tests.test_lane_continuation_terminal_neighborhood_selector_route_context_audit import (
    _write_replay_manifest,
    _write_transfer_manifest,
)


class LaneContinuationTerminalNeighborhoodSelectorCandidateValidationTest(
    unittest.TestCase
):
    def test_payload_recovers_heading_candidate_and_preserves_negatives(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            transfer_manifest = _write_transfer_manifest(root)
            route_context_manifest = _write_route_context_manifest(
                root, transfer_manifest
            )

            payload = (
                lane_continuation_terminal_neighborhood_selector_candidate_validation_payload(
                    selector_transfer_manifest_path=transfer_manifest,
                    selector_route_context_manifest_path=route_context_manifest,
                    output_dir=root / "candidate",
                )
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["case_count"], 5)
            self.assertEqual(aggregate["replay_accepted_count"], 3)
            self.assertEqual(aggregate["replay_held_count"], 2)
            self.assertEqual(aggregate["transfer_match_count"], 3)
            self.assertEqual(aggregate["candidate_match_count"], 4)
            self.assertEqual(aggregate["match_delta"], 1)
            self.assertEqual(aggregate["candidate_false_promote_count"], 0)
            self.assertEqual(aggregate["candidate_false_hold_count"], 1)
            self.assertEqual(aggregate["recovered_false_hold_count"], 1)
            self.assertEqual(aggregate["preserved_negative_control_count"], 2)
            self.assertEqual(aggregate["retained_route_context_hold_count"], 1)

            changed_cases = [
                case for case in payload["cases"] if case["changed_by_candidate"]
            ]
            self.assertEqual(len(changed_cases), 1)
            self.assertEqual(
                changed_cases[0]["route_context_classification"],
                "heading_relaxation_candidate",
            )
            self.assertIn("default selector unchanged", payload["recommendation"])

    def test_markdown_names_candidate_policy_and_negative_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            transfer_manifest = _write_transfer_manifest(root)
            route_context_manifest = _write_route_context_manifest(
                root, transfer_manifest
            )
            payload = (
                lane_continuation_terminal_neighborhood_selector_candidate_validation_payload(
                    selector_transfer_manifest_path=transfer_manifest,
                    selector_route_context_manifest_path=route_context_manifest,
                    output_dir=root / "candidate",
                )
            )

            markdown = (
                lane_continuation_terminal_neighborhood_selector_candidate_validation_markdown(
                    payload
                )
            )

            self.assertIn("Selector Candidate Validation", markdown)
            self.assertIn("context_aware_heading_candidate", markdown)
            self.assertIn("Recovered Cases", markdown)
            self.assertIn("Negative Controls", markdown)
            self.assertIn("Raw map geometry published: no", markdown)
            self.assertIn("not a default selector change", markdown)

    def test_generate_candidate_validation_writes_manifest_and_public_report(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            transfer_manifest = _write_transfer_manifest(root)
            route_context_manifest = _write_route_context_manifest(
                root, transfer_manifest
            )
            output_dir = root / "candidate"
            public_report = root / "reports" / "candidate_validation.md"

            result = (
                generate_lane_continuation_terminal_neighborhood_selector_candidate_validation(
                    selector_transfer_manifest_path=transfer_manifest,
                    selector_route_context_manifest_path=route_context_manifest,
                    output_dir=output_dir,
                    public_report_path=public_report,
                )
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 5)
            self.assertEqual(result.candidate_match_count, 4)
            self.assertEqual(result.candidate_false_promote_count, 0)
            self.assertEqual(result.candidate_false_hold_count, 1)
            self.assertEqual(result.recovered_false_hold_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT,
            )

    def test_terminal_neighborhood_selector_candidate_validation_cli_writes_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            transfer_manifest = _write_transfer_manifest(root)
            route_context_manifest = _write_route_context_manifest(
                root, transfer_manifest
            )
            output_dir = root / "candidate"
            public_report = root / "reports" / "candidate_validation.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-candidate-validation",
                    "--selector-transfer-manifest",
                    str(transfer_manifest),
                    "--selector-route-context-manifest",
                    str(route_context_manifest),
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

            self.assertIn(
                "Generated terminal-neighborhood selector candidate validation",
                result.stdout,
            )
            self.assertIn("4 candidate match", result.stdout)
            self.assertIn("0 false promote", result.stdout)
            self.assertIn("1 false hold", result.stdout)
            self.assertIn("1 recovered false hold", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_route_context_manifest(root: Path, transfer_manifest: Path) -> Path:
    result = generate_lane_continuation_terminal_neighborhood_selector_route_context_audit(
        selector_transfer_manifest_path=transfer_manifest,
        terminal_neighborhood_replay_manifest_path=_write_replay_manifest(root),
        output_dir=root / "route_context",
    )
    return result.manifest_path
