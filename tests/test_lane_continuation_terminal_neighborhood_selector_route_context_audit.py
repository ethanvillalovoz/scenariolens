import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_route_context_audit import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_route_context_audit,
    lane_continuation_terminal_neighborhood_selector_route_context_audit_markdown,
    lane_continuation_terminal_neighborhood_selector_route_context_audit_payload,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
)


class LaneContinuationTerminalNeighborhoodSelectorRouteContextAuditTest(
    unittest.TestCase
):
    def test_payload_joins_false_holds_to_route_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            payload = (
                lane_continuation_terminal_neighborhood_selector_route_context_audit_payload(
                    selector_transfer_manifest_path=_write_transfer_manifest(root),
                    terminal_neighborhood_replay_manifest_path=_write_replay_manifest(
                        root
                    ),
                    output_dir=root / "audit",
                    diagnostic_heading_gate=0.70,
                )
            )

            self.assertEqual(
                payload["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT,
            )
            self.assertTrue(payload["ready"])
            aggregate = payload["aggregate"]
            self.assertEqual(aggregate["transfer_case_count"], 5)
            self.assertEqual(aggregate["false_hold_count"], 2)
            self.assertEqual(aggregate["joined_false_hold_count"], 2)
            self.assertEqual(aggregate["stable_recovery_count"], 2)
            self.assertEqual(aggregate["no_exit_to_linked_chain_count"], 2)
            self.assertEqual(aggregate["heading_relaxation_candidate_count"], 1)
            self.assertEqual(aggregate["route_context_hold_count"], 1)
            self.assertEqual(aggregate["mean_selected_terminal_deficit_m"], 18.67)
            self.assertEqual(aggregate["mean_route_extension_m"], 63.511)
            self.assertEqual(aggregate["mean_replay_gain_m"], 32.505)

            cases = payload["cases"]
            self.assertEqual(
                cases[0]["classification"], "heading_relaxation_candidate"
            )
            self.assertIn("within_diagnostic_heading_gate", cases[0]["context_labels"])
            self.assertEqual(cases[1]["classification"], "route_context_hold")
            self.assertIn("selected_heading_disagreement", cases[1]["context_labels"])
            self.assertIn("Keep the default selector unchanged", payload["recommendation"])

    def test_markdown_names_context_findings_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = (
                lane_continuation_terminal_neighborhood_selector_route_context_audit_payload(
                    selector_transfer_manifest_path=_write_transfer_manifest(root),
                    terminal_neighborhood_replay_manifest_path=_write_replay_manifest(
                        root
                    ),
                    output_dir=root / "audit",
                )
            )

            markdown = (
                lane_continuation_terminal_neighborhood_selector_route_context_audit_markdown(
                    payload
                )
            )

            self.assertIn("Selector Route/Context Audit", markdown)
            self.assertIn("heading_relaxation_candidate", markdown)
            self.assertIn("route_context_hold", markdown)
            self.assertIn("selected terminal deficit", markdown)
            self.assertIn("Raw map geometry published: no", markdown)
            self.assertIn("not a route planner", markdown)

    def test_zero_false_holds_is_a_ready_noop_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            transfer_path = _write_transfer_manifest(root)
            transfer = json.loads(transfer_path.read_text(encoding="utf-8"))
            transfer_result = transfer["transfer_policy_result"]
            transfer_result["cases"] = [transfer_result["cases"][0]]
            transfer_result["aggregate"]["case_count"] = 1
            transfer_result["aggregate"]["selector_false_hold_count"] = 0
            transfer["validation_scope"]["validation_case_count"] = 1
            transfer_path.write_text(
                json.dumps(transfer, indent=2) + "\n",
                encoding="utf-8",
            )

            payload = (
                lane_continuation_terminal_neighborhood_selector_route_context_audit_payload(
                    selector_transfer_manifest_path=transfer_path,
                    terminal_neighborhood_replay_manifest_path=_write_replay_manifest(
                        root
                    ),
                    output_dir=root / "audit",
                )
            )

            self.assertTrue(payload["ready"])
            self.assertEqual(payload["aggregate"]["false_hold_count"], 0)
            self.assertEqual(payload["cases"], [])

    def test_generate_route_context_audit_writes_manifest_and_public_report(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "audit"
            public_report = root / "reports" / "selector_route_context_audit.md"

            result = (
                generate_lane_continuation_terminal_neighborhood_selector_route_context_audit(
                    selector_transfer_manifest_path=_write_transfer_manifest(root),
                    terminal_neighborhood_replay_manifest_path=_write_replay_manifest(
                        root
                    ),
                    output_dir=output_dir,
                    public_report_path=public_report,
                )
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(result.ready)
            self.assertEqual(result.false_hold_count, 2)
            self.assertEqual(result.joined_false_hold_count, 2)
            self.assertEqual(result.heading_relaxation_candidate_count, 1)
            self.assertEqual(result.route_context_hold_count, 1)
            self.assertTrue(result.report_path.exists())
            self.assertTrue(public_report.exists())
            self.assertEqual(
                manifest["format"],
                LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_ROUTE_CONTEXT_AUDIT_FORMAT,
            )

    def test_terminal_neighborhood_selector_route_context_audit_cli_writes_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "audit"
            public_report = root / "reports" / "selector_route_context_audit.md"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-route-context-audit",
                    "--selector-transfer-manifest",
                    str(_write_transfer_manifest(root)),
                    "--terminal-neighborhood-replay-manifest",
                    str(_write_replay_manifest(root)),
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
                "Generated terminal-neighborhood selector route/context audit",
                result.stdout,
            )
            self.assertIn("2 false hold", result.stdout)
            self.assertIn("1 heading-relaxation", result.stdout)
            self.assertIn("1 route/context hold", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())


def _write_transfer_manifest(root: Path) -> Path:
    manifest = root / "selector_transfer_manifest.json"
    cases = [
        _transfer_case(
            rank=31,
            split="overlap_with_calibration",
            scenario_id="accepted_long_extension",
            track_id="1061",
            accepted=True,
            match_label="true_positive_recovery",
            promotes=True,
            selected_heading=1.0,
            alternate_heading=1.0,
            route_extension=228.779,
            gain=125.481,
            hold_flags=[],
        ),
        _transfer_case(
            rank=34,
            split="overlap_with_calibration",
            scenario_id="held_low_heading",
            track_id="3178",
            accepted=False,
            match_label="true_hold",
            promotes=False,
            selected_heading=0.690,
            alternate_heading=0.690,
            route_extension=72.451,
            gain=-15.163,
            hold_flags=["selected_heading_below_gate", "alternate_heading_below_gate"],
        ),
        _transfer_case(
            rank=35,
            split="novel_case",
            scenario_id="accepted_borderline_heading",
            track_id="987",
            accepted=True,
            match_label="false_hold",
            promotes=False,
            selected_heading=0.997,
            alternate_heading=0.886,
            route_extension=56.882,
            gain=26.119,
            hold_flags=["alternate_heading_below_gate"],
        ),
        _transfer_case(
            rank=36,
            split="novel_case",
            scenario_id="held_route_negative",
            track_id="116",
            accepted=False,
            match_label="true_hold",
            promotes=False,
            selected_heading=0.823,
            alternate_heading=0.823,
            route_extension=32.514,
            gain=-16.230,
            hold_flags=["alternate_heading_below_gate", "route_extension_below_gate"],
        ),
        _transfer_case(
            rank=42,
            split="novel_case",
            scenario_id="accepted_severe_heading",
            track_id="88",
            accepted=True,
            match_label="false_hold",
            promotes=False,
            selected_heading=0.122,
            alternate_heading=0.741,
            route_extension=70.140,
            gain=38.890,
            hold_flags=["selected_heading_below_gate", "alternate_heading_below_gate"],
        ),
    ]
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_TRANSFER_FORMAT,
                "ready": True,
                "training_scope": {"training_case_count": 4},
                "validation_scope": {
                    "validation_case_count": 5,
                    "overlap_case_count": 2,
                    "novel_case_count": 3,
                    "replay_gate_accepted_count": 3,
                    "replay_gate_held_count": 2,
                    "perturbation_trial_count": 20,
                },
                "transfer_policy_result": {
                    "policy": {
                        "max_alternate_distance_m": 5.0,
                        "min_heading_alignment": 0.95,
                        "min_route_extension_m": 40.0,
                        "require_chain_extension": True,
                    },
                    "aggregate": {
                        "case_count": 5,
                        "selector_false_promote_count": 0,
                        "selector_false_hold_count": 2,
                    },
                    "cases": cases,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_replay_manifest(root: Path) -> Path:
    manifest = root / "terminal_replay_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_REPLAY_FORMAT,
                "ready": True,
                "aggregate": {
                    "case_count": 2,
                    "accepted_case_count": 2,
                    "held_case_count": 0,
                    "perturbation_trial_count": 8,
                },
                "cases": [
                    _replay_case(
                        rank=35,
                        scenario_id="accepted_borderline_heading",
                        track_id="987",
                        source_name="validation.tfrecord-00009-of-00150",
                        selected_remaining=32.851,
                        alternate_remaining=89.733,
                        selected_base=32.851,
                        alternate_base=7.678,
                        horizon=57.799,
                        selected_fde=62.626,
                        alternate_fde=36.507,
                        selected_ade=21.291,
                        alternate_ade=14.237,
                        gain=26.119,
                        min_gain=20.34,
                    ),
                    _replay_case(
                        rank=42,
                        scenario_id="accepted_severe_heading",
                        track_id="88",
                        source_name="validation.tfrecord-00008-of-00150",
                        selected_remaining=24.718,
                        alternate_remaining=94.858,
                        selected_base=24.718,
                        alternate_base=11.027,
                        horizon=37.110,
                        selected_fde=48.172,
                        alternate_fde=9.282,
                        selected_ade=26.032,
                        alternate_ade=5.916,
                        gain=38.890,
                        min_gain=35.260,
                    ),
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _transfer_case(
    rank: int,
    split: str,
    scenario_id: str,
    track_id: str,
    accepted: bool,
    match_label: str,
    promotes: bool,
    selected_heading: float,
    alternate_heading: float,
    route_extension: float,
    gain: float,
    hold_flags: list[str],
) -> dict[str, object]:
    return {
        "rank": rank,
        "validation_split": split,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "validation.tfrecord-00008-of-00150",
        "ready": True,
        "selected_feature_id": "223",
        "alternate_feature_id": "237",
        "selected_route_remaining_m": 24.718,
        "alternate_route_remaining_m": 94.858,
        "route_extension_m": route_extension,
        "alternate_lane_distance_m": 2.07,
        "selected_heading_alignment": selected_heading,
        "alternate_heading_alignment": alternate_heading,
        "minimum_heading_alignment": min(selected_heading, alternate_heading),
        "chain_extended": True,
        "replay_gate_accepted": accepted,
        "selector_promotes": promotes,
        "selector_gate_match_label": match_label,
        "replay_gain_m": gain,
        "selector_hold_flags": hold_flags,
        "selector_checks": {
            "alternate_distance_ok": True,
            "selected_heading_ok": selected_heading >= 0.95,
            "alternate_heading_ok": alternate_heading >= 0.95,
            "route_extension_ok": route_extension >= 40.0,
            "chain_extension_ok": True,
        },
    }


def _replay_case(
    rank: int,
    scenario_id: str,
    track_id: str,
    source_name: str,
    selected_remaining: float,
    alternate_remaining: float,
    selected_base: float,
    alternate_base: float,
    horizon: float,
    selected_fde: float,
    alternate_fde: float,
    selected_ade: float,
    alternate_ade: float,
    gain: float,
    min_gain: float,
) -> dict[str, object]:
    return {
        "rank": rank,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": source_name,
        "ready": True,
        "selected_feature_id": "223",
        "alternate_feature_id": "237",
        "selected_route_status": "no_exit_lanes",
        "alternate_route_status": "linked_lane_chain",
        "selected_route_remaining_m": selected_remaining,
        "alternate_route_remaining_m": alternate_remaining,
        "selected_base_remaining_m": selected_base,
        "alternate_base_remaining_m": alternate_base,
        "horizon_travel_m": horizon,
        "selected_fde_m": selected_fde,
        "alternate_fde_m": alternate_fde,
        "selected_ade_m": selected_ade,
        "alternate_ade_m": alternate_ade,
        "nominal_gain_m": gain,
        "perturbation_stability": {
            "label": "stable_recovery",
            "valid_trial_count": 4,
            "chain_preserving_trial_count": 4,
            "stable_gain_trial_count": 4,
            "min_gain_m": min_gain,
        },
    }
