import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scenariolens.lane_continuation_terminal_neighborhood_casebook import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_candidate_validation import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT,
    generate_lane_continuation_terminal_neighborhood_selector_decision_atlas,
    lane_continuation_terminal_neighborhood_selector_decision_atlas_markdown,
    lane_continuation_terminal_neighborhood_selector_decision_atlas_payload,
)


class LaneContinuationTerminalNeighborhoodSelectorDecisionAtlasTest(unittest.TestCase):
    def test_payload_joins_casebook_cards_to_candidate_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            casebook = _write_casebook(root)
            candidate = _write_candidate_validation(root)

            payload = (
                lane_continuation_terminal_neighborhood_selector_decision_atlas_payload(
                    casebook_manifest_path=casebook,
                    candidate_validation_manifest_path=candidate,
                    output_dir=root / "atlas",
                    asset_base_path="cards",
                )
            )

        self.assertEqual(
            payload["format"],
            LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_DECISION_ATLAS_FORMAT,
        )
        aggregate = payload["aggregate"]
        self.assertEqual(aggregate["case_count"], 3)
        self.assertEqual(aggregate["candidate_match_count"], 3)
        self.assertEqual(aggregate["recovered_false_hold_count"], 1)
        self.assertEqual(aggregate["candidate_false_promote_count"], 0)
        self.assertEqual(aggregate["category_counts"]["candidate_recovery"], 1)
        self.assertEqual(aggregate["category_counts"]["negative_control"], 1)
        self.assertEqual(aggregate["category_counts"]["retained_hold"], 1)

        cases = payload["cases"]
        self.assertEqual(cases[0]["category"], "candidate_recovery")
        self.assertEqual(cases[0]["decision_label"], "Recovered false hold")
        self.assertEqual(cases[0]["asset_path"], "cards/card_01.svg")
        self.assertEqual(cases[1]["category"], "negative_control")
        self.assertEqual(cases[2]["category"], "retained_hold")

    def test_markdown_names_visual_decision_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = (
                lane_continuation_terminal_neighborhood_selector_decision_atlas_payload(
                    casebook_manifest_path=_write_casebook(root),
                    candidate_validation_manifest_path=_write_candidate_validation(root),
                    output_dir=root / "atlas",
                )
            )

        markdown = lane_continuation_terminal_neighborhood_selector_decision_atlas_markdown(
            payload
        )
        self.assertIn("Terminal Selector Decision Atlas", markdown)
        self.assertIn("Recovered false hold", markdown)
        self.assertIn("Negative control", markdown)
        self.assertIn("Retained hold", markdown)
        self.assertIn("![Case 01 selector diagnostic](assets/card_01.svg)", markdown)

    def test_generator_writes_manifest_report_public_report_and_demo_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "atlas"
            public_report = root / "reports" / "atlas.md"
            demo_json = root / "demo" / "selector_decisions.json"
            demo_assets = root / "demo" / "assets"

            result = generate_lane_continuation_terminal_neighborhood_selector_decision_atlas(
                casebook_manifest_path=_write_casebook(root),
                candidate_validation_manifest_path=_write_candidate_validation(root),
                output_dir=output_dir,
                public_report_path=public_report,
                demo_json_path=demo_json,
                demo_assets_dir=demo_assets,
            )

            self.assertTrue(result.ready)
            self.assertEqual(result.case_count, 3)
            self.assertEqual(result.visual_asset_count, 3)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue((output_dir / "assets" / "card_01.svg").exists())
            self.assertTrue(public_report.exists())
            self.assertTrue((public_report.parent / "assets" / "card_02.svg").exists())
            self.assertTrue(demo_json.exists())
            self.assertTrue((demo_assets / "card_03.svg").exists())

            demo_payload = json.loads(demo_json.read_text(encoding="utf-8"))
            self.assertEqual(demo_payload["cases"][0]["asset_path"], "assets/card_01.svg")

    def test_cli_writes_decision_atlas_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "atlas"
            public_report = root / "reports" / "atlas.md"
            demo_json = root / "demo" / "selector_decisions.json"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scenariolens.cli",
                    "lane-continuation-terminal-neighborhood-selector-decision-atlas",
                    "--casebook-manifest",
                    str(_write_casebook(root)),
                    "--candidate-validation-manifest",
                    str(_write_candidate_validation(root)),
                    "--output-dir",
                    str(output_dir),
                    "--public-report",
                    str(public_report),
                    "--demo-json",
                    str(demo_json),
                    "--demo-assets-dir",
                    str(root / "demo" / "assets"),
                ],
                check=True,
                env={"PYTHONPATH": "src"},
                capture_output=True,
                text=True,
            )

            self.assertIn("Generated terminal-neighborhood selector decision atlas", result.stdout)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "report.md").exists())
            self.assertTrue(public_report.exists())
            self.assertTrue(demo_json.exists())


def _write_casebook(root: Path) -> Path:
    casebook_dir = root / "casebook"
    assets_dir = casebook_dir / "assets"
    assets_dir.mkdir(parents=True)
    for index in range(1, 4):
        (assets_dir / f"card_{index:02d}.svg").write_text(
            f"<svg xmlns=\"http://www.w3.org/2000/svg\"><text>card {index}</text></svg>",
            encoding="utf-8",
        )
    manifest = casebook_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "format": LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_CASEBOOK_FORMAT,
                "ready": True,
                "source_scope": {"replay_case_count": 3},
                "aggregate": {
                    "case_count": 3,
                    "visual_asset_count": 3,
                    "replay_gate_accepted_count": 2,
                    "replay_gate_held_count": 1,
                },
                "cases": [
                    _casebook_case("Case 01", "candidate_case", "11", "card_01.svg", 30.0),
                    _casebook_case("Case 02", "negative_case", "22", "card_02.svg", -5.0),
                    _casebook_case("Case 03", "hold_case", "33", "card_03.svg", 8.0),
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _write_candidate_validation(root: Path) -> Path:
    manifest = root / "candidate.json"
    manifest.write_text(
        json.dumps(
            {
                "format": (
                    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CANDIDATE_VALIDATION_FORMAT
                ),
                "ready": True,
                "source_scope": {"validation_scope": {"validation_case_count": 3}},
                "candidate_policy": {"policy_label": "context_aware_heading_candidate"},
                "aggregate": {
                    "case_count": 3,
                    "replay_accepted_count": 2,
                    "replay_held_count": 1,
                    "transfer_match_count": 2,
                    "candidate_match_count": 3,
                    "match_delta": 1,
                    "candidate_false_promote_count": 0,
                    "candidate_false_hold_count": 1,
                    "recovered_false_hold_count": 1,
                    "preserved_negative_control_count": 1,
                    "retained_route_context_hold_count": 1,
                    "candidate_promote_count": 1,
                    "candidate_hold_count": 2,
                },
                "cases": [
                    _candidate_case(
                        "candidate_case",
                        "11",
                        accepted=True,
                        transfer_promotes=False,
                        candidate_promotes=True,
                        changed=True,
                        match="true_positive_recovery",
                        context="heading_relaxation_candidate",
                        gain=30.0,
                    ),
                    _candidate_case(
                        "negative_case",
                        "22",
                        accepted=False,
                        transfer_promotes=False,
                        candidate_promotes=False,
                        changed=False,
                        match="true_hold",
                        context="not_a_false_hold",
                        gain=-5.0,
                    ),
                    _candidate_case(
                        "hold_case",
                        "33",
                        accepted=True,
                        transfer_promotes=False,
                        candidate_promotes=False,
                        changed=False,
                        match="false_hold",
                        context="route_context_hold",
                        gain=8.0,
                    ),
                ],
                "recommendation": "Keep the default selector unchanged.",
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _casebook_case(
    label: str,
    scenario_id: str,
    track_id: str,
    asset_name: str,
    gain: float,
) -> dict[str, object]:
    return {
        "case_label": label,
        "asset_name": asset_name,
        "asset_path": f"assets/{asset_name}",
        "rank": 1,
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "validation.tfrecord-00000-of-00150",
        "selected_heading_alignment": 0.99,
        "alternate_heading_alignment": 0.88,
        "minimum_heading_alignment": 0.88,
        "alternate_lane_distance_m": 2.0,
        "route_extension_m": 42.0,
        "replay_gain_m": gain,
        "selector_hold_flags": [],
        "selector_checks": {"route_extension_gate": True},
        "case_read": "fixture case",
    }


def _candidate_case(
    scenario_id: str,
    track_id: str,
    accepted: bool,
    transfer_promotes: bool,
    candidate_promotes: bool,
    changed: bool,
    match: str,
    context: str,
    gain: float,
) -> dict[str, object]:
    return {
        "rank": 1,
        "validation_split": "novel",
        "scenario_id": scenario_id,
        "track_id": track_id,
        "source_name": "validation.tfrecord-00000-of-00150",
        "replay_gate_accepted": accepted,
        "replay_label": "accepted" if accepted else "held",
        "transfer_promotes": transfer_promotes,
        "candidate_promotes": candidate_promotes,
        "transfer_decision": (
            "promote_terminal_neighborhood_alternate"
            if transfer_promotes
            else "hold_for_terminal_neighborhood_context"
        ),
        "candidate_decision": (
            "promote_terminal_neighborhood_alternate"
            if candidate_promotes
            else "hold_for_terminal_neighborhood_context"
        ),
        "transfer_match_label": match,
        "candidate_match_label": match,
        "changed_by_candidate": changed,
        "route_context_classification": context,
        "context_labels": ["fixture_context"],
        "replay_gain_m": gain,
        "selected_heading_alignment": 0.99,
        "alternate_heading_alignment": 0.88,
        "route_extension_m": 42.0,
        "candidate_rationale": "fixture rationale",
        "next_validation_step": "fixture next step",
    }
