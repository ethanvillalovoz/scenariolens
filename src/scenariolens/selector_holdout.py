from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable

from scenariolens import __version__
from scenariolens.lane_continuation import (
    LANE_CONTINUATION_STUDY_INPUT_FORMATS,
    generate_lane_continuation_study,
)
from scenariolens.lane_continuation_candidates import (
    generate_lane_continuation_candidate_plan,
)
from scenariolens.lane_continuation_replay import (
    generate_lane_continuation_replay_prototype,
)
from scenariolens.lane_continuation_terminal_neighborhood_audit import (
    generate_lane_continuation_terminal_neighborhood_audit,
)
from scenariolens.lane_continuation_terminal_neighborhood_replay import (
    DEFAULT_MIN_STABLE_GAIN_M,
    generate_lane_continuation_terminal_neighborhood_replay,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_candidate_validation import (
    generate_lane_continuation_terminal_neighborhood_selector_candidate_validation,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_calibration import (
    LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_route_context_audit import (
    generate_lane_continuation_terminal_neighborhood_selector_route_context_audit,
)
from scenariolens.lane_continuation_terminal_neighborhood_selector_transfer import (
    generate_lane_continuation_terminal_neighborhood_selector_transfer,
)
from scenariolens.lane_continuation_topology_gap_audit import (
    generate_lane_continuation_topology_gap_audit,
)
from scenariolens.run_bundle import resolve_run_inputs

try:
    import resource
except ImportError:  # pragma: no cover - available on CI and macOS.
    resource = None  # type: ignore[assignment]


SELECTOR_HOLDOUT_STUDY_FORMAT = "scenariolens.selector_holdout_study.v1"
SELECTOR_HOLDOUT_INPUT_FORMATS = LANE_CONTINUATION_STUDY_INPUT_FORMATS
FROZEN_SELECTOR_COMMIT = "ba0b37e"
FROZEN_MAX_ALTERNATE_DISTANCE_M = 5.0
FROZEN_MIN_HEADING_ALIGNMENT = 0.95
FROZEN_MIN_ROUTE_EXTENSION_M = 40.0
FROZEN_DIAGNOSTIC_HEADING_GATE = 0.70
DEFAULT_SCENARIO_OFFSET = 50
DEFAULT_EXPECTED_SCENARIOS = 993
DEFAULT_TOP = 150
MINIMUM_SELECTOR_DECISIONS = 30


@dataclass(frozen=True)
class SelectorHoldoutStudyResult:
    """Top-level artifacts produced by frozen selector holdout validation."""

    ready: bool
    source_count: int
    scenario_count: int
    selector_decision_count: int
    passed_check_count: int
    check_count: int
    analysis_digest: str
    duration_seconds: float
    peak_rss_bytes: int | None
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


@dataclass(frozen=True)
class _Stage:
    stage_id: str
    label: str
    generator: Callable[..., object]


def default_frozen_selector_policy_path() -> Path:
    """Return the packaged, public-safe selector policy frozen before holdout."""

    return Path(__file__).with_name("data") / "terminal_selector_policy_v1.json"


def generate_selector_holdout_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    input_format: str = "native",
    scenario_offset: int = DEFAULT_SCENARIO_OFFSET,
    max_scenarios: int | None = None,
    expected_scenarios: int | None = DEFAULT_EXPECTED_SCENARIOS,
    top: int = DEFAULT_TOP,
    minimum_selector_decisions: int = MINIMUM_SELECTOR_DECISIONS,
    calibration_manifest_path: str | Path | None = None,
    public_report_path: str | Path | None = None,
) -> SelectorHoldoutStudyResult:
    """Run the frozen terminal selector on a disjoint scenario window."""

    _validate_options(
        input_paths=input_paths,
        input_format=input_format,
        scenario_offset=scenario_offset,
        max_scenarios=max_scenarios,
        expected_scenarios=expected_scenarios,
        top=top,
        minimum_selector_decisions=minimum_selector_decisions,
    )
    sources = resolve_run_inputs(input_paths, input_format=input_format)
    calibration_path = Path(
        calibration_manifest_path or default_frozen_selector_policy_path()
    )
    calibration = _load_frozen_calibration(calibration_path)
    target = Path(output_dir)
    stages_dir = target / "stages"
    target.mkdir(parents=True, exist_ok=True)
    stages_dir.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    input_provenance = [
        _file_provenance(path, index=index)
        for index, path in enumerate(sources, start=1)
    ]
    calibration_provenance = _file_provenance(calibration_path, index=1)
    calibration_provenance["frozen_at_commit"] = FROZEN_SELECTOR_COMMIT
    calibration_provenance["policy"] = _frozen_policy(calibration)
    stages: list[dict[str, object]] = []

    study_result, study = _execute_stage(
        stage=_Stage(
            "continuation_study",
            "Holdout lane-continuation study",
            generate_lane_continuation_study,
        ),
        output_dir=stages_dir / "01_continuation_study",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "input_paths": sources,
            "max_scenarios": max_scenarios,
            "scenario_offset": scenario_offset,
            "top": top,
            "input_format": input_format,
        },
    )
    candidate_result, candidates = _execute_stage(
        stage=_Stage(
            "candidate_plan",
            "Replay and topology candidate plan",
            generate_lane_continuation_candidate_plan,
        ),
        output_dir=stages_dir / "02_candidate_plan",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "study_manifest_path": study_result.manifest_path,
            "top_per_bucket": top,
        },
    )
    replay_result, replay = _execute_stage(
        stage=_Stage(
            "replay_prototype",
            "Deterministic continuation replay",
            generate_lane_continuation_replay_prototype,
        ),
        output_dir=stages_dir / "03_replay_prototype",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "candidate_manifest_path": candidate_result.manifest_path,
            "top_per_bucket": top,
            "input_format": input_format,
            "max_scenarios_per_source": None,
        },
    )
    topology_result, topology = _execute_stage(
        stage=_Stage(
            "topology_gap_audit",
            "Topology gap audit",
            generate_lane_continuation_topology_gap_audit,
        ),
        output_dir=stages_dir / "04_topology_gap_audit",
        bundle_dir=target,
        stages=stages,
        kwargs={"replay_manifest_path": replay_result.manifest_path},
    )
    terminal_result, terminal = _execute_stage(
        stage=_Stage(
            "terminal_neighborhood_audit",
            "Terminal-neighborhood alternatives",
            generate_lane_continuation_terminal_neighborhood_audit,
        ),
        output_dir=stages_dir / "05_terminal_neighborhood_audit",
        bundle_dir=target,
        stages=stages,
        kwargs={"topology_manifest_path": topology_result.manifest_path},
    )
    terminal_replay_result, terminal_replay = _execute_stage(
        stage=_Stage(
            "terminal_neighborhood_replay",
            "Terminal-neighborhood perturbation replay",
            generate_lane_continuation_terminal_neighborhood_replay,
        ),
        output_dir=stages_dir / "06_terminal_neighborhood_replay",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "terminal_neighborhood_manifest_path": terminal_result.manifest_path,
            "top": top,
            "minimum_stable_gain_m": DEFAULT_MIN_STABLE_GAIN_M,
        },
    )
    transfer_result, transfer = _execute_stage(
        stage=_Stage(
            "selector_transfer",
            "Frozen selector transfer",
            generate_lane_continuation_terminal_neighborhood_selector_transfer,
        ),
        output_dir=stages_dir / "07_selector_transfer",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "selector_calibration_manifest_path": calibration_path,
            "terminal_neighborhood_replay_manifest_path": (
                terminal_replay_result.manifest_path
            ),
            "policy_source": "recommended",
        },
    )
    context_result, route_context = _execute_stage(
        stage=_Stage(
            "route_context_audit",
            "Frozen false-hold route/context audit",
            generate_lane_continuation_terminal_neighborhood_selector_route_context_audit,
        ),
        output_dir=stages_dir / "08_route_context_audit",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "selector_transfer_manifest_path": transfer_result.manifest_path,
            "terminal_neighborhood_replay_manifest_path": (
                terminal_replay_result.manifest_path
            ),
            "diagnostic_heading_gate": FROZEN_DIAGNOSTIC_HEADING_GATE,
        },
    )
    _, candidate_validation = _execute_stage(
        stage=_Stage(
            "candidate_validation",
            "Frozen context-aware candidate validation",
            generate_lane_continuation_terminal_neighborhood_selector_candidate_validation,
        ),
        output_dir=stages_dir / "09_candidate_validation",
        bundle_dir=target,
        stages=stages,
        kwargs={
            "selector_transfer_manifest_path": transfer_result.manifest_path,
            "selector_route_context_manifest_path": context_result.manifest_path,
        },
    )

    aggregate = _holdout_aggregate(
        study=study,
        candidates=candidates,
        replay=replay,
        topology=topology,
        terminal=terminal,
        terminal_replay=terminal_replay,
        transfer=transfer,
        route_context=route_context,
        candidate_validation=candidate_validation,
    )
    checks = _holdout_checks(
        stages=stages,
        study=study,
        transfer=transfer,
        candidate_validation=candidate_validation,
        aggregate=aggregate,
        scenario_offset=scenario_offset,
        expected_scenarios=expected_scenarios,
        minimum_selector_decisions=minimum_selector_decisions,
    )
    ready = all(bool(check["passed"]) for check in checks)
    stable_payload = {
        "format": SELECTOR_HOLDOUT_STUDY_FORMAT,
        "configuration": {
            "input_format": input_format,
            "scenario_offset_per_input": scenario_offset,
            "max_scenarios_per_input": max_scenarios,
            "expected_scenarios": expected_scenarios,
            "top": top,
            "minimum_selector_decisions": minimum_selector_decisions,
        },
        "inputs": [
            {
                "index": item["index"],
                "name": item["name"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
            }
            for item in input_provenance
        ],
        "calibration_sha256": calibration_provenance["sha256"],
        "frozen_at_commit": FROZEN_SELECTOR_COMMIT,
        "aggregate": aggregate,
        "checks": [
            {
                "check_id": check["check_id"],
                "passed": check["passed"],
                "observed": check["observed"],
                "expected": check["expected"],
            }
            for check in checks
        ],
        "candidate_decisions": _stable_candidate_decisions(candidate_validation),
    }
    analysis_digest = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    duration_seconds = round(perf_counter() - started, 3)
    peak_rss_bytes = _peak_rss_bytes()
    passed_check_count = sum(bool(check["passed"]) for check in checks)
    payload: dict[str, object] = {
        "format": SELECTOR_HOLDOUT_STUDY_FORMAT,
        "ready": ready,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenariolens_version": __version__,
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "configuration": stable_payload["configuration"],
        "cohort": {
            "label": "same_shard_scenario_window_holdout",
            "development_window": f"scenarios 1-{scenario_offset} per input",
            "holdout_window": f"scenarios {scenario_offset + 1}+ per input",
            "independent_shard_benchmark": False,
        },
        "source_count": len(sources),
        "scenario_count": aggregate["scenario_count"],
        "selector_decision_count": aggregate["selector_decision_count"],
        "duration_seconds": duration_seconds,
        "peak_rss_bytes": peak_rss_bytes,
        "analysis_digest": analysis_digest,
        "inputs": input_provenance,
        "frozen_policy": calibration_provenance,
        "stages": stages,
        "aggregate": aggregate,
        "checks": checks,
        "passed_check_count": passed_check_count,
        "check_count": len(checks),
        "recommendation": _recommendation(
            ready=ready,
            aggregate=aggregate,
            minimum_selector_decisions=minimum_selector_decisions,
        ),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "stages": "stages/",
        },
        "scope_note": (
            "This is a same-shard scenario-window holdout of a policy frozen "
            "before evaluation. It is not an independent-shard benchmark, a "
            "Waymo benchmark submission, closed-loop validation, or a "
            "production autonomy policy. Raw Waymo records remain local."
        ),
    }
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report = selector_holdout_markdown(payload, include_local_stage_links=True)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(
            selector_holdout_markdown(
                payload,
                include_local_stage_links=False,
            ),
            encoding="utf-8",
        )

    return SelectorHoldoutStudyResult(
        ready=ready,
        source_count=len(sources),
        scenario_count=int(aggregate["scenario_count"]),
        selector_decision_count=int(aggregate["selector_decision_count"]),
        passed_check_count=passed_check_count,
        check_count=len(checks),
        analysis_digest=analysis_digest,
        duration_seconds=duration_seconds,
        peak_rss_bytes=peak_rss_bytes,
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def selector_holdout_markdown(
    payload: dict[str, object],
    include_local_stage_links: bool = True,
) -> str:
    """Return the public-safe frozen selector holdout report."""

    aggregate = _mapping(payload, "aggregate")
    configuration = _mapping(payload, "configuration")
    policy_provenance = _mapping(payload, "frozen_policy")
    policy = _mapping(policy_provenance, "policy")
    checks = _list(payload, "checks")
    stages = _list(payload, "stages")
    inputs = _list(payload, "inputs")
    status = "PASS" if payload.get("ready") else "NOT READY"
    lines = [
        "# ScenarioLens Frozen Selector Holdout",
        "",
        f"**Release-gate status: {status}.**",
        "",
        "This report evaluates the terminal-neighborhood selector candidate on "
        "a scenario window that was excluded from policy calibration. The policy "
        f"was frozen at commit `{policy_provenance['frozen_at_commit']}` before "
        "this holdout run. No selector threshold is tuned here.",
        "",
        "This is same-shard scenario-window validation, not an independent-shard "
        "benchmark. It is useful evidence of out-of-window transfer, but it does "
        "not establish production autonomy safety or Waymo benchmark performance.",
        "",
        "## Cohort And Policy",
        "",
        f"- Sources: {payload['source_count']}",
        f"- Holdout scenarios evaluated: {payload['scenario_count']}",
        f"- Excluded prefix per source: {configuration['scenario_offset_per_input']}",
        f"- Expected holdout scenarios: {configuration['expected_scenarios']}",
        f"- Frozen maximum alternate distance: {float(policy['max_alternate_distance_m']):.3f} m",
        f"- Frozen minimum heading alignment: {float(policy['min_heading_alignment']):.3f}",
        f"- Frozen minimum route extension: {float(policy['min_route_extension_m']):.3f} m",
        f"- Frozen diagnostic heading gate: {FROZEN_DIAGNOSTIC_HEADING_GATE:.3f}",
        f"- Analysis digest: `{payload['analysis_digest']}`",
        f"- Runtime: {float(payload['duration_seconds']):.3f} s",
        f"- Peak process memory: {_memory_text(payload.get('peak_rss_bytes'))}",
        "- Raw Waymo records committed: no",
        "",
        "## Release Gates",
        "",
        "| Check | Result | Observed | Expected |",
        "| --- | --- | ---: | ---: |",
    ]
    for check in checks:
        assert isinstance(check, dict)
        lines.append(
            f"| {check['label']} | {'pass' if check['passed'] else 'fail'} | "
            f"{check['observed']} | {check['expected']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Funnel",
            "",
            "| Stage | Count |",
            "| --- | ---: |",
            f"| Candidate targets | {aggregate['candidate_track_count']} |",
            f"| Topology gaps | {aggregate['topology_gap_count']} |",
            f"| Topology cases audited | {aggregate['topology_case_count']} |",
            f"| Terminal-neighborhood cases | {aggregate['terminal_case_count']} |",
            f"| Nearby recovery candidates | {aggregate['nearby_recovery_count']} |",
            f"| Perturbation-replayed selector decisions | {aggregate['selector_decision_count']} |",
            f"| Replay-accepted recoveries | {aggregate['replay_accepted_count']} |",
            f"| Replay-held controls | {aggregate['replay_held_count']} |",
            "",
            "## Selector Outcomes",
            "",
            "| Metric | Frozen transfer policy | Context-aware candidate |",
            "| --- | ---: | ---: |",
            f"| Replay-label matches | {aggregate['transfer_match_count']} | {aggregate['candidate_match_count']} |",
            f"| False promotions | {aggregate['transfer_false_promote_count']} | {aggregate['candidate_false_promote_count']} |",
            f"| False holds | {aggregate['transfer_false_hold_count']} | {aggregate['candidate_false_hold_count']} |",
            f"| Promotions | {aggregate['transfer_promote_count']} | {aggregate['candidate_promote_count']} |",
            f"| Holds | {aggregate['transfer_hold_count']} | {aggregate['candidate_hold_count']} |",
            f"| False holds recovered by frozen context rule | n/a | {aggregate['recovered_false_hold_count']} |",
            "",
            "The replay labels come from deterministic nominal and perturbation "
            "tests. They are validation labels for this bounded diagnostic, not "
            "ground-truth driving-policy labels.",
            "",
            "## Stage Artifacts",
            "",
            "| Stage | Ready | Duration | Report |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for stage in stages:
        assert isinstance(stage, dict)
        report_cell = (
            f"[{stage['stage_id']}]({stage['report']})"
            if include_local_stage_links
            else "local run bundle"
        )
        lines.append(
            f"| {stage['label']} | {stage['ready']} | "
            f"{float(stage['duration_seconds']):.3f} s | "
            f"{report_cell} |"
        )
    lines.extend(
        [
            "",
            "## Input Provenance",
            "",
            "| Source | Bytes | SHA-256 |",
            "| --- | ---: | --- |",
        ]
    )
    for item in inputs:
        assert isinstance(item, dict)
        lines.append(
            f"| `{item['name']}` | {item['size_bytes']} | `{str(item['sha256'])[:16]}...` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation And Uncertainty",
            "",
            f"{payload['recommendation']}",
            "",
            "- Passing this packet means the evaluation is complete and "
            "leakage/coverage gates passed; it does not automatically mean the "
            "candidate should replace the default selector.",
            "- The cohort shares shards with development data, so geographic and "
            "collection correlations may remain.",
            "- The selector only sees terminal-neighborhood cases surfaced by the "
            "preceding lane-continuation diagnostic; it is not evaluated on every "
            "possible autonomy failure mode.",
            "- A stronger post-v1 result would preserve this frozen policy and "
            "repeat the packet on untouched shards.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _execute_stage(
    stage: _Stage,
    output_dir: Path,
    bundle_dir: Path,
    stages: list[dict[str, object]],
    kwargs: dict[str, object],
) -> tuple[object, dict[str, object]]:
    started = perf_counter()
    result = stage.generator(output_dir=output_dir, **kwargs)
    duration_seconds = round(perf_counter() - started, 3)
    manifest_path = Path(getattr(result, "manifest_path"))
    report_path = Path(getattr(result, "report_path"))
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    stages.append(
        {
            "stage_id": stage.stage_id,
            "label": stage.label,
            "format": payload.get("format"),
            "ready": bool(payload.get("ready")),
            "duration_seconds": duration_seconds,
            "manifest": manifest_path.relative_to(bundle_dir).as_posix(),
            "report": report_path.relative_to(bundle_dir).as_posix(),
        }
    )
    return result, payload


def _holdout_aggregate(
    *,
    study: dict[str, object],
    candidates: dict[str, object],
    replay: dict[str, object],
    topology: dict[str, object],
    terminal: dict[str, object],
    terminal_replay: dict[str, object],
    transfer: dict[str, object],
    route_context: dict[str, object],
    candidate_validation: dict[str, object],
) -> dict[str, object]:
    study_aggregate = _mapping(study, "aggregate")
    candidate_aggregate = _mapping(candidates, "aggregate")
    replay_aggregate = _mapping(replay, "aggregate")
    topology_aggregate = _mapping(topology, "aggregate")
    terminal_aggregate = _mapping(terminal, "aggregate")
    terminal_replay_aggregate = _mapping(terminal_replay, "aggregate")
    transfer_result = _mapping(transfer, "transfer_policy_result")
    transfer_aggregate = _mapping(transfer_result, "aggregate")
    context_aggregate = _mapping(route_context, "aggregate")
    candidate_aggregate_final = _mapping(candidate_validation, "aggregate")
    return {
        "scenario_count": _integer(study.get("scenario_count")),
        "candidate_track_count": _integer(study.get("candidate_track_count")),
        "evaluated_track_count": _integer(study_aggregate.get("evaluated_track_count")),
        "linked_lane_track_count": _integer(study_aggregate.get("linked_lane_track_count")),
        "improved_over_nearest_count": _integer(study_aggregate.get("improved_over_nearest_count")),
        "regressed_vs_nearest_count": _integer(study_aggregate.get("regressed_vs_nearest_count")),
        "topology_gap_count": _integer(study_aggregate.get("topology_gap_count")),
        "queued_topology_count": _integer(candidate_aggregate.get("topology_audit_count")),
        "replay_case_count": _integer(replay_aggregate.get("case_count")),
        "topology_case_count": _integer(topology_aggregate.get("case_count")),
        "terminal_case_count": _integer(terminal_aggregate.get("case_count")),
        "nearby_recovery_count": _integer(terminal_aggregate.get("nearby_recovery_case_count")),
        "terminal_replay_selected_count": _integer(terminal_replay.get("selected_candidate_count")),
        "selector_decision_count": _integer(transfer_aggregate.get("case_count")),
        "replay_accepted_count": _integer(terminal_replay_aggregate.get("accepted_case_count")),
        "replay_held_count": _integer(terminal_replay_aggregate.get("held_case_count")),
        "transfer_match_count": _integer(transfer_aggregate.get("selector_replay_gate_match_count")),
        "transfer_false_promote_count": _integer(transfer_aggregate.get("selector_false_promote_count")),
        "transfer_false_hold_count": _integer(transfer_aggregate.get("selector_false_hold_count")),
        "transfer_promote_count": _integer(transfer_aggregate.get("selector_promote_count")),
        "transfer_hold_count": _integer(transfer_aggregate.get("selector_hold_count")),
        "route_context_heading_candidate_count": _integer(context_aggregate.get("heading_relaxation_candidate_count")),
        "candidate_match_count": _integer(candidate_aggregate_final.get("candidate_match_count")),
        "candidate_false_promote_count": _integer(candidate_aggregate_final.get("candidate_false_promote_count")),
        "candidate_false_hold_count": _integer(candidate_aggregate_final.get("candidate_false_hold_count")),
        "candidate_promote_count": _integer(candidate_aggregate_final.get("candidate_promote_count")),
        "candidate_hold_count": _integer(candidate_aggregate_final.get("candidate_hold_count")),
        "recovered_false_hold_count": _integer(candidate_aggregate_final.get("recovered_false_hold_count")),
    }


def _holdout_checks(
    *,
    stages: list[dict[str, object]],
    study: dict[str, object],
    transfer: dict[str, object],
    candidate_validation: dict[str, object],
    aggregate: dict[str, object],
    scenario_offset: int,
    expected_scenarios: int | None,
    minimum_selector_decisions: int,
) -> list[dict[str, object]]:
    study_indices = _study_scenario_indices(study)
    holdout_keys = _study_track_keys(study)
    candidate_keys = {
        (str(case.get("scenario_id")), str(case.get("track_id")))
        for case in _list(candidate_validation, "cases")
        if isinstance(case, dict)
    }
    validation_scope = _mapping(transfer, "validation_scope")
    scenario_count = _integer(aggregate.get("scenario_count"))
    topology_count = _integer(aggregate.get("topology_gap_count"))
    queued_topology = _integer(aggregate.get("queued_topology_count"))
    recoveries = _integer(aggregate.get("nearby_recovery_count"))
    replayed_recoveries = _integer(aggregate.get("terminal_replay_selected_count"))
    decisions = _integer(aggregate.get("selector_decision_count"))
    return [
        _check(
            "stage_readiness",
            "All pipeline stages ready",
            all(bool(stage.get("ready")) for stage in stages),
            sum(bool(stage.get("ready")) for stage in stages),
            len(stages),
        ),
        _check(
            "scenario_count",
            "Expected holdout scenarios evaluated",
            expected_scenarios is None or scenario_count == expected_scenarios,
            scenario_count,
            expected_scenarios if expected_scenarios is not None else "recorded only",
        ),
        _check(
            "scenario_window",
            "No development-window scenario indices",
            bool(study_indices) and min(study_indices) > scenario_offset,
            min(study_indices) if study_indices else "none",
            f"> {scenario_offset}",
        ),
        _check(
            "candidate_provenance",
            "Selector decisions trace to holdout tracks",
            bool(candidate_keys) and candidate_keys.issubset(holdout_keys),
            len(candidate_keys & holdout_keys),
            len(candidate_keys),
        ),
        _check(
            "calibration_overlap",
            "No selector cases overlap calibration",
            _integer(validation_scope.get("overlap_case_count")) == 0,
            _integer(validation_scope.get("overlap_case_count")),
            0,
        ),
        _check(
            "topology_queue_coverage",
            "All surfaced topology gaps queued",
            topology_count == queued_topology,
            queued_topology,
            topology_count,
        ),
        _check(
            "terminal_replay_coverage",
            "All nearby recoveries replayed",
            recoveries == replayed_recoveries,
            replayed_recoveries,
            recoveries,
        ),
        _check(
            "minimum_selector_decisions",
            "Minimum selector decisions reached",
            decisions >= minimum_selector_decisions,
            decisions,
            f">= {minimum_selector_decisions}",
        ),
    ]


def _check(
    check_id: str,
    label: str,
    passed: bool,
    observed: object,
    expected: object,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "label": label,
        "passed": passed,
        "observed": observed,
        "expected": expected,
    }


def _study_scenario_indices(study: dict[str, object]) -> list[int]:
    indices: list[int] = []
    for case in _list(study, "cases"):
        if not isinstance(case, dict):
            continue
        value = case.get("scenario_index")
        if isinstance(value, int):
            indices.append(value)
        for track in case.get("track_results", []):
            if isinstance(track, dict) and isinstance(track.get("scenario_index"), int):
                indices.append(int(track["scenario_index"]))
    return indices


def _study_track_keys(study: dict[str, object]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for case in _list(study, "cases"):
        if not isinstance(case, dict):
            continue
        for track in case.get("track_results", []):
            if isinstance(track, dict):
                keys.add((str(track.get("scenario_id")), str(track.get("track_id"))))
    return keys


def _stable_candidate_decisions(
    candidate_validation: dict[str, object],
) -> list[dict[str, object]]:
    decisions = []
    for case in _list(candidate_validation, "cases"):
        if not isinstance(case, dict):
            continue
        decisions.append(
            {
                "scenario_id": case.get("scenario_id"),
                "track_id": case.get("track_id"),
                "replay_label": case.get("replay_label"),
                "transfer_decision": case.get("transfer_decision"),
                "candidate_decision": case.get("candidate_decision"),
                "candidate_match_label": case.get("candidate_match_label"),
                "route_context_classification": case.get(
                    "route_context_classification"
                ),
            }
        )
    return sorted(
        decisions,
        key=lambda item: (str(item["scenario_id"]), str(item["track_id"])),
    )


def _load_frozen_calibration(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Frozen selector policy does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != (
        LANE_CONTINUATION_TERMINAL_NEIGHBORHOOD_SELECTOR_CALIBRATION_FORMAT
    ):
        raise ValueError("Frozen selector policy has an unsupported format.")
    if not payload.get("ready"):
        raise ValueError("Frozen selector policy is not marked ready.")
    policy = _mapping(payload, "recommended_policy")
    expected = {
        "max_alternate_distance_m": FROZEN_MAX_ALTERNATE_DISTANCE_M,
        "min_heading_alignment": FROZEN_MIN_HEADING_ALIGNMENT,
        "min_route_extension_m": FROZEN_MIN_ROUTE_EXTENSION_M,
    }
    for key, value in expected.items():
        if float(policy.get(key, -1.0)) != value:
            raise ValueError(
                f"Frozen selector policy field {key} must remain {value}."
            )
    if not _list(payload, "cases"):
        raise ValueError("Frozen selector policy must retain development case identities.")
    return payload


def _frozen_policy(calibration: dict[str, object]) -> dict[str, object]:
    policy = _mapping(calibration, "recommended_policy")
    return {
        "max_alternate_distance_m": policy["max_alternate_distance_m"],
        "min_heading_alignment": policy["min_heading_alignment"],
        "min_route_extension_m": policy["min_route_extension_m"],
        "require_chain_extension": True,
        "diagnostic_heading_gate": FROZEN_DIAGNOSTIC_HEADING_GATE,
    }


def _file_provenance(path: Path, index: int) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "index": index,
        "path": str(path),
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def _recommendation(
    *,
    ready: bool,
    aggregate: dict[str, object],
    minimum_selector_decisions: int,
) -> str:
    decisions = _integer(aggregate.get("selector_decision_count"))
    false_promotes = _integer(aggregate.get("candidate_false_promote_count"))
    false_holds = _integer(aggregate.get("candidate_false_hold_count"))
    if decisions < minimum_selector_decisions:
        return (
            f"The holdout produced {decisions} selector decisions, below the "
            f"frozen {minimum_selector_decisions}-decision evidence gate. Preserve "
            "the policy and add untouched shards; do not retune on this cohort."
        )
    if not ready:
        return (
            "At least one provenance, coverage, or stage-readiness gate failed. "
            "Treat this packet as incomplete and fix the evaluation path without "
            "changing the frozen policy."
        )
    if false_promotes:
        return (
            f"The context-aware candidate created {false_promotes} false "
            "promotion(s) against the perturbation-replay labels. Keep the "
            "default selector unchanged and inspect these holdout failures; do "
            "not tune against this validation cohort."
        )
    if false_holds:
        return (
            f"The evaluation packet is complete with zero false promotions, but "
            f"{false_holds} false hold(s) remain. Keep the candidate diagnostic "
            "and preserve this cohort as validation evidence rather than tuning "
            "against it."
        )
    return (
        "The evaluation packet is complete and the frozen context-aware candidate "
        "matches every perturbation-replay label in this bounded holdout with zero "
        "false promotions. Keep the claim scoped to this same-shard window and "
        "seek untouched-shard replication before changing a production policy."
    )


def _validate_options(
    *,
    input_paths: tuple[str | Path, ...],
    input_format: str,
    scenario_offset: int,
    max_scenarios: int | None,
    expected_scenarios: int | None,
    top: int,
    minimum_selector_decisions: int,
) -> None:
    if not input_paths:
        raise ValueError("At least one input is required for selector holdout study.")
    if input_format not in SELECTOR_HOLDOUT_INPUT_FORMATS:
        raise ValueError(
            "Unsupported selector-holdout input format: "
            f"{input_format}. Expected one of: "
            f"{', '.join(SELECTOR_HOLDOUT_INPUT_FORMATS)}"
        )
    if scenario_offset < 0:
        raise ValueError("scenario-offset must be non-negative.")
    if max_scenarios is not None and max_scenarios < 1:
        raise ValueError("max-scenarios must be at least 1 when provided.")
    if expected_scenarios is not None and expected_scenarios < 1:
        raise ValueError("expected-scenarios must be at least 1 when provided.")
    if top < 1:
        raise ValueError("top must be at least 1.")
    if minimum_selector_decisions < 1:
        raise ValueError("minimum-selector-decisions must be at least 1.")


def _mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object field: {key}.")
    return value


def _list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}.")
    return value


def _integer(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _peak_rss_bytes() -> int | None:
    if resource is None:
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == "Darwin":
        return peak
    return peak * 1024


def _memory_text(value: object) -> str:
    if not isinstance(value, int):
        return "not available"
    return f"{value / (1024 ** 3):.3f} GB"
