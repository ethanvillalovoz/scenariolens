from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scenariolens import cli
from scenariolens.selector_holdout import (
    FROZEN_SELECTOR_COMMIT,
    SELECTOR_HOLDOUT_STUDY_FORMAT,
    default_frozen_selector_policy_path,
    generate_selector_holdout_study,
)


class SelectorHoldoutStudyTest(unittest.TestCase):
    def test_generate_holdout_passes_disjoint_complete_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "fixture.json"
            input_path.write_text("[]\n", encoding="utf-8")
            payloads = _stage_payloads(scenario_index=51, decision_count=2)

            with _patched_pipeline(payloads):
                first = generate_selector_holdout_study(
                    input_paths=(input_path,),
                    output_dir=root / "first",
                    input_format="scenariolens-json",
                    scenario_offset=50,
                    expected_scenarios=2,
                    top=3,
                    minimum_selector_decisions=2,
                )
                second = generate_selector_holdout_study(
                    input_paths=(input_path,),
                    output_dir=root / "second",
                    input_format="scenariolens-json",
                    scenario_offset=50,
                    expected_scenarios=2,
                    top=3,
                    minimum_selector_decisions=2,
                )

            self.assertTrue(first.ready)
            self.assertEqual(first.selector_decision_count, 2)
            self.assertEqual(first.passed_check_count, first.check_count)
            self.assertEqual(first.analysis_digest, second.analysis_digest)
            manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], SELECTOR_HOLDOUT_STUDY_FORMAT)
            self.assertEqual(manifest["frozen_policy"]["frozen_at_commit"], FROZEN_SELECTOR_COMMIT)
            self.assertEqual(len(manifest["stages"]), 9)
            self.assertEqual(manifest["cohort"]["independent_shard_benchmark"], False)
            report = first.report_path.read_text(encoding="utf-8")
            self.assertIn("Release-gate status: PASS", report)
            self.assertIn("same-shard scenario-window validation", report)
            self.assertIn("No selector threshold is tuned here", report)
            self.assertIn("](stages/", report)

            public_report = root / "public.md"
            with _patched_pipeline(payloads):
                generate_selector_holdout_study(
                    input_paths=(input_path,),
                    output_dir=root / "public-run",
                    input_format="scenariolens-json",
                    scenario_offset=50,
                    expected_scenarios=2,
                    top=3,
                    minimum_selector_decisions=2,
                    public_report_path=public_report,
                )
            public_text = public_report.read_text(encoding="utf-8")
            self.assertNotIn("](stages/", public_text)
            self.assertIn("local run bundle", public_text)

    def test_holdout_fails_when_development_index_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "fixture.json"
            input_path.write_text("[]\n", encoding="utf-8")

            with _patched_pipeline(
                _stage_payloads(scenario_index=50, decision_count=2)
            ):
                result = generate_selector_holdout_study(
                    input_paths=(input_path,),
                    output_dir=root / "holdout",
                    input_format="scenariolens-json",
                    scenario_offset=50,
                    expected_scenarios=2,
                    top=3,
                    minimum_selector_decisions=2,
                )

            self.assertFalse(result.ready)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            check = _check(manifest, "scenario_window")
            self.assertFalse(check["passed"])
            self.assertEqual(check["observed"], 50)

    def test_holdout_fails_below_frozen_decision_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "fixture.json"
            input_path.write_text("[]\n", encoding="utf-8")

            with _patched_pipeline(
                _stage_payloads(scenario_index=51, decision_count=1)
            ):
                result = generate_selector_holdout_study(
                    input_paths=(input_path,),
                    output_dir=root / "holdout",
                    input_format="scenariolens-json",
                    scenario_offset=50,
                    expected_scenarios=2,
                    top=3,
                    minimum_selector_decisions=2,
                )

            self.assertFalse(result.ready)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            check = _check(manifest, "minimum_selector_decisions")
            self.assertEqual(check["observed"], 1)
            self.assertEqual(check["expected"], ">= 2")
            self.assertIn("do not retune", manifest["recommendation"])

    def test_packaged_frozen_policy_is_machine_readable(self) -> None:
        path = default_frozen_selector_policy_path()
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(path.exists())
        self.assertEqual(payload["frozen_at_commit"], FROZEN_SELECTOR_COMMIT)
        self.assertEqual(payload["recommended_policy"]["min_route_extension_m"], 40.0)
        self.assertEqual(len(payload["cases"]), 6)

    def test_cli_returns_nonzero_for_failed_release_gate(self) -> None:
        result = SimpleNamespace(
            ready=False,
            passed_check_count=7,
            check_count=8,
            scenario_count=993,
            selector_decision_count=28,
            manifest_path=Path("manifest.json"),
            report_path=Path("report.md"),
            public_report_path=None,
        )
        stdout = StringIO()
        argv = [
            "scenariolens",
            "selector-holdout-study",
            "--input",
            "fixture.json",
        ]
        with patch.object(cli, "generate_selector_holdout_study", return_value=result):
            with patch("sys.argv", argv), redirect_stdout(stdout):
                exit_code = cli.main()

        self.assertEqual(exit_code, 2)
        self.assertIn("7/8 checks passed", stdout.getvalue())


def _check(manifest: dict[str, object], check_id: str) -> dict[str, object]:
    return next(
        check
        for check in manifest["checks"]  # type: ignore[index]
        if isinstance(check, dict) and check["check_id"] == check_id
    )


def _stage_payloads(
    *,
    scenario_index: int,
    decision_count: int,
) -> dict[str, dict[str, object]]:
    tracks = [
        {
            "scenario_id": f"holdout-{index}",
            "track_id": str(index),
            "scenario_index": scenario_index + index - 1,
        }
        for index in range(1, decision_count + 1)
    ]
    decisions = [
        {
            "scenario_id": track["scenario_id"],
            "track_id": track["track_id"],
            "replay_label": "accepted",
            "transfer_decision": "promote_terminal_neighborhood_alternate",
            "candidate_decision": "promote_terminal_neighborhood_alternate",
            "candidate_match_label": "true_positive_recovery",
            "route_context_classification": "not_a_false_hold",
        }
        for track in tracks
    ]
    selector_aggregate = {
        "case_count": decision_count,
        "selector_replay_gate_match_count": decision_count,
        "selector_false_promote_count": 0,
        "selector_false_hold_count": 0,
        "selector_promote_count": decision_count,
        "selector_hold_count": 0,
    }
    candidate_aggregate = {
        "case_count": decision_count,
        "candidate_match_count": decision_count,
        "candidate_false_promote_count": 0,
        "candidate_false_hold_count": 0,
        "candidate_promote_count": decision_count,
        "candidate_hold_count": 0,
        "recovered_false_hold_count": 0,
    }
    base = {"ready": True}
    return {
        "generate_lane_continuation_study": {
            **base,
            "format": "study",
            "source_count": 1,
            "scenario_count": 2,
            "candidate_track_count": decision_count,
            "aggregate": {
                "evaluated_track_count": decision_count,
                "linked_lane_track_count": decision_count,
                "improved_over_nearest_count": decision_count,
                "regressed_vs_nearest_count": 0,
                "topology_gap_count": decision_count,
            },
            "cases": [
                {
                    "scenario_index": scenario_index,
                    "track_results": tracks,
                }
            ],
        },
        "generate_lane_continuation_candidate_plan": {
            **base,
            "format": "candidates",
            "aggregate": {"topology_audit_count": decision_count},
        },
        "generate_lane_continuation_replay_prototype": {
            **base,
            "format": "replay",
            "aggregate": {"case_count": decision_count},
        },
        "generate_lane_continuation_topology_gap_audit": {
            **base,
            "format": "topology",
            "aggregate": {"case_count": decision_count},
        },
        "generate_lane_continuation_terminal_neighborhood_audit": {
            **base,
            "format": "terminal",
            "aggregate": {
                "case_count": decision_count,
                "nearby_recovery_case_count": decision_count,
            },
        },
        "generate_lane_continuation_terminal_neighborhood_replay": {
            **base,
            "format": "terminal-replay",
            "selected_candidate_count": decision_count,
            "aggregate": {
                "accepted_case_count": decision_count,
                "held_case_count": 0,
            },
        },
        "generate_lane_continuation_terminal_neighborhood_selector_transfer": {
            **base,
            "format": "transfer",
            "validation_scope": {
                "validation_case_count": decision_count,
                "overlap_case_count": 0,
                "novel_case_count": decision_count,
            },
            "transfer_policy_result": {
                "aggregate": selector_aggregate,
                "cases": decisions,
            },
        },
        "generate_lane_continuation_terminal_neighborhood_selector_route_context_audit": {
            **base,
            "format": "route-context",
            "aggregate": {"heading_relaxation_candidate_count": 0},
        },
        "generate_lane_continuation_terminal_neighborhood_selector_candidate_validation": {
            **base,
            "format": "candidate-validation",
            "aggregate": candidate_aggregate,
            "cases": decisions,
        },
    }


def _patched_pipeline(payloads: dict[str, dict[str, object]]):
    patches = []
    for name, payload in payloads.items():
        patches.append(
            patch(
                f"scenariolens.selector_holdout.{name}",
                side_effect=_writer(payload),
            )
        )
    return _PatchStack(patches)


def _writer(payload: dict[str, object]):
    def write(*, output_dir: str | Path, **_: object) -> SimpleNamespace:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        manifest_path = target / "manifest.json"
        report_path = target / "report.md"
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        report_path.write_text("# Stage fixture\n", encoding="utf-8")
        return SimpleNamespace(manifest_path=manifest_path, report_path=report_path)

    return write


class _PatchStack:
    def __init__(self, patches: list[unittest.mock._patch]) -> None:  # type: ignore[name-defined]
        self.patches = patches

    def __enter__(self) -> "_PatchStack":
        for item in self.patches:
            item.start()
        return self

    def __exit__(self, *exc: object) -> None:
        for item in reversed(self.patches):
            item.stop()


if __name__ == "__main__":
    unittest.main()
