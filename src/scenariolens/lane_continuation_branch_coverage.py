from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.lane_continuation_branch_replay import (
    LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
)
from scenariolens.lane_continuation_branch_selection import (
    LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
    _optional_float,
    _required_list,
    _required_mapping,
    _write_json,
)
from scenariolens.lane_continuation_candidates import (
    LANE_CONTINUATION_CANDIDATES_FORMAT,
)
from scenariolens.lane_continuation_diagnostics import (
    LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
)
from scenariolens.lane_continuation_replay import LANE_CONTINUATION_REPLAY_FORMAT
from scenariolens.lane_continuation_route_context_guard import (
    LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
)

LANE_CONTINUATION_BRANCH_COVERAGE_FORMAT = (
    "scenariolens.lane_continuation_branch_coverage.v1"
)


@dataclass(frozen=True)
class LaneContinuationBranchCoverageResult:
    """Files produced by a lane-continuation branch coverage audit."""

    ready: bool
    candidate_count: int
    branchable_case_count: int
    topology_blocker_count: int
    expansion_queue_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_lane_continuation_branch_coverage(
    candidate_manifest_path: str | Path,
    replay_manifest_path: str | Path,
    diagnostics_manifest_path: str | Path,
    branch_selection_manifest_path: str | Path,
    output_dir: str | Path,
    branch_replay_manifest_path: str | Path | None = None,
    route_context_guard_manifest_path: str | Path | None = None,
    public_report_path: str | Path | None = None,
) -> LaneContinuationBranchCoverageResult:
    """Generate a public-safe funnel audit for branch-selection coverage."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = lane_continuation_branch_coverage_payload(
        candidate_manifest_path=Path(candidate_manifest_path),
        replay_manifest_path=Path(replay_manifest_path),
        diagnostics_manifest_path=Path(diagnostics_manifest_path),
        branch_selection_manifest_path=Path(branch_selection_manifest_path),
        output_dir=target,
        branch_replay_manifest_path=(
            Path(branch_replay_manifest_path) if branch_replay_manifest_path else None
        ),
        route_context_guard_manifest_path=(
            Path(route_context_guard_manifest_path)
            if route_context_guard_manifest_path
            else None
        ),
    )
    report = lane_continuation_branch_coverage_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = _required_mapping(payload, "aggregate")
    return LaneContinuationBranchCoverageResult(
        ready=bool(payload["ready"]),
        candidate_count=int(aggregate["candidate_count"]),
        branchable_case_count=int(aggregate["branchable_case_count"]),
        topology_blocker_count=int(aggregate["topology_blocker_count"]),
        expansion_queue_count=len(_required_list(payload, "expansion_queue")),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def lane_continuation_branch_coverage_payload(
    candidate_manifest_path: Path,
    replay_manifest_path: Path,
    diagnostics_manifest_path: Path,
    branch_selection_manifest_path: Path,
    output_dir: Path,
    branch_replay_manifest_path: Path | None = None,
    route_context_guard_manifest_path: Path | None = None,
) -> dict[str, object]:
    """Return a branch-selection coverage funnel from public-safe manifests."""

    candidates = _load_manifest(
        candidate_manifest_path,
        expected_format=LANE_CONTINUATION_CANDIDATES_FORMAT,
        label="lane-continuation candidate",
    )
    replay = _load_manifest(
        replay_manifest_path,
        expected_format=LANE_CONTINUATION_REPLAY_FORMAT,
        label="lane-continuation replay",
    )
    diagnostics = _load_manifest(
        diagnostics_manifest_path,
        expected_format=LANE_CONTINUATION_DIAGNOSTICS_FORMAT,
        label="lane-continuation route-diagnostics",
    )
    branch_selection = _load_manifest(
        branch_selection_manifest_path,
        expected_format=LANE_CONTINUATION_BRANCH_SELECTION_FORMAT,
        label="lane-continuation branch-selection",
    )
    branch_replay = (
        _load_manifest(
            branch_replay_manifest_path,
            expected_format=LANE_CONTINUATION_BRANCH_REPLAY_FORMAT,
            label="lane-continuation branch-replay",
        )
        if branch_replay_manifest_path is not None
        else None
    )
    route_guard = (
        _load_manifest(
            route_context_guard_manifest_path,
            expected_format=LANE_CONTINUATION_ROUTE_CONTEXT_GUARD_FORMAT,
            label="lane-continuation route-context guard",
        )
        if route_context_guard_manifest_path is not None
        else None
    )

    candidate_rows = [
        row for row in _required_list(candidates, "candidates") if isinstance(row, dict)
    ]
    replay_rows = [
        row for row in _required_list(replay, "cases") if isinstance(row, dict)
    ]
    diagnostic_rows = [
        row
        for row in _required_list(diagnostics, "diagnostics")
        if isinstance(row, dict)
    ]
    branch_rows = [
        row
        for row in _required_list(branch_selection, "cases")
        if isinstance(row, dict)
    ]
    branch_replay_rows = (
        [
            row
            for row in _required_list(branch_replay, "cases")
            if isinstance(row, dict)
        ]
        if branch_replay is not None
        else []
    )
    route_guard_rows = (
        [row for row in _required_list(route_guard, "cases") if isinstance(row, dict)]
        if route_guard is not None
        else []
    )

    aggregate = _aggregate(
        candidates=candidates,
        candidate_rows=candidate_rows,
        replay=replay,
        replay_rows=replay_rows,
        diagnostics=diagnostics,
        diagnostic_rows=diagnostic_rows,
        branch_selection=branch_selection,
        branch_rows=branch_rows,
        branch_replay_rows=branch_replay_rows,
        route_guard_rows=route_guard_rows,
    )
    funnel = _funnel(aggregate)
    bottlenecks = _bottlenecks(
        candidate_rows=candidate_rows,
        diagnostic_rows=diagnostic_rows,
        branch_rows=branch_rows,
        route_guard_rows=route_guard_rows,
        aggregate=aggregate,
    )
    expansion_queue = _expansion_queue(
        candidate_rows=candidate_rows,
        diagnostic_rows=diagnostic_rows,
        branch_rows=branch_rows,
        route_guard_rows=route_guard_rows,
    )
    return {
        "format": LANE_CONTINUATION_BRANCH_COVERAGE_FORMAT,
        "candidate_manifest": str(candidate_manifest_path),
        "candidate_format": candidates.get("format"),
        "replay_manifest": str(replay_manifest_path),
        "replay_format": replay.get("format"),
        "diagnostics_manifest": str(diagnostics_manifest_path),
        "diagnostics_format": diagnostics.get("format"),
        "branch_selection_manifest": str(branch_selection_manifest_path),
        "branch_selection_format": branch_selection.get("format"),
        "branch_replay_manifest": (
            str(branch_replay_manifest_path) if branch_replay_manifest_path else None
        ),
        "branch_replay_format": branch_replay.get("format") if branch_replay else None,
        "route_context_guard_manifest": (
            str(route_context_guard_manifest_path)
            if route_context_guard_manifest_path
            else None
        ),
        "route_context_guard_format": (
            route_guard.get("format") if route_guard else None
        ),
        "output_dir": str(output_dir),
        "ready": (
            bool(candidates.get("ready"))
            and bool(replay.get("ready"))
            and bool(diagnostics.get("ready"))
            and bool(branch_selection.get("ready"))
            and (branch_replay is None or bool(branch_replay.get("ready")))
            and (route_guard is None or bool(route_guard.get("ready")))
        ),
        "aggregate": aggregate,
        "funnel": funnel,
        "bottlenecks": bottlenecks,
        "expansion_queue": expansion_queue,
        "per_source": _per_source(candidate_rows, branch_rows, route_guard_rows),
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "The branch coverage audit is a public-safe funnel over existing "
            "ScenarioLens summary manifests. It does not read raw Waymo files, "
            "does not claim benchmark coverage, and does not replace branch "
            "selection, branch replay, or route-context guard decisions."
        ),
    }


def lane_continuation_branch_coverage_markdown(payload: dict[str, object]) -> str:
    """Return public-safe Markdown for the branch coverage audit."""

    aggregate = _required_mapping(payload, "aggregate")
    funnel = _required_list(payload, "funnel")
    bottlenecks = _required_list(payload, "bottlenecks")
    expansion_queue = _required_list(payload, "expansion_queue")
    per_source = _required_list(payload, "per_source")

    lines = [
        "# ScenarioLens Branch Coverage Audit",
        "",
        "This audit connects the lane-continuation candidate queue, replay "
        "prototype, route diagnostics, branch selection, branch replay, and "
        "route-context guard into one evidence funnel. Its job is to make the "
        "current bottleneck explicit: only a small subset of continuation "
        "failures is branchable today, so the next v1.0 work should expand "
        "topology/parser coverage and route-context guard coverage before "
        "claiming broader selector readiness.",
        "",
        "It is intentionally public-safe. It reads summary manifests only, "
        "publishes counts and scenario identifiers, and is not a Waymo "
        "benchmark claim.",
        "",
        "## Scope",
        "",
        f"- Candidate manifest: `{payload['candidate_manifest']}`",
        f"- Replay manifest: `{payload['replay_manifest']}`",
        f"- Diagnostics manifest: `{payload['diagnostics_manifest']}`",
        f"- Branch-selection manifest: `{payload['branch_selection_manifest']}`",
        f"- Branch-replay manifest: `{payload['branch_replay_manifest']}`",
        f"- Route-context guard manifest: `{payload['route_context_guard_manifest']}`",
        f"- Ready: {payload['ready']}",
        "- Raw scenario data committed: no",
        "- Local replay packets committed: no",
        "",
        "## Coverage Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Continuation candidates | {aggregate['candidate_count']} |",
        f"| Replay-ready candidates | {aggregate['replay_candidate_count']} |",
        f"| Regression-debug candidates | {aggregate['regression_debug_candidate_count']} |",
        f"| Topology-audit candidates | {aggregate['topology_audit_candidate_count']} |",
        f"| Route diagnostics | {aggregate['route_diagnostic_count']} |",
        f"| Branch-selection cases | {aggregate['branch_selection_case_count']} |",
        f"| Branchable cases | {aggregate['branchable_case_count']} |",
        f"| Single-chain cases | {aggregate['single_chain_case_count']} |",
        f"| Motion-context branch improvements | {aggregate['motion_context_improved_case_count']} |",
        f"| Branch-replay cases | {aggregate['branch_replay_case_count']} |",
        f"| Route-guard promotions | {aggregate['route_guard_promote_count']} |",
        f"| Route-guard holds | {aggregate['route_guard_hold_count']} |",
        f"| Topology blockers | {aggregate['topology_blocker_count']} |",
        f"| Expansion queue items | {aggregate['expansion_queue_count']} |",
        f"| Branchable coverage of candidates | {_percent_text(aggregate['branchable_candidate_rate'])} |",
        f"| Branchable coverage of branch-selection cases | {_percent_text(aggregate['branchable_selection_rate'])} |",
        f"| Route-guard promotion coverage of candidates | {_percent_text(aggregate['guard_promotion_candidate_rate'])} |",
        "",
        "## Funnel",
        "",
        "| Stage | Count | Conversion | What it proves | Next action |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for stage in funnel:
        assert isinstance(stage, dict)
        lines.append(
            "| "
            f"{stage['label']} | "
            f"{stage['count']} | "
            f"{_percent_text(stage.get('conversion_from_previous'))} | "
            f"{stage['evidence']} | "
            f"{stage['next_action']} |"
        )

    lines.extend(
        [
            "",
            "## Bottlenecks",
            "",
            "| Bottleneck | Count | Evidence | Expansion move |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in bottlenecks:
        assert isinstance(row, dict)
        lines.append(
            "| "
            f"`{row['label']}` | "
            f"{row['count']} | "
            f"{row['evidence']} | "
            f"{row['next_action']} |"
        )

    lines.extend(
        [
            "",
            "## Expansion Queue",
            "",
            "| Rank | Type | Scenario | Track | Source | Why it matters | First next action |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not expansion_queue:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
    for item in expansion_queue:
        assert isinstance(item, dict)
        lines.append(
            "| "
            f"{item['rank']} | "
            f"`{item['queue_type']}` | "
            f"`{item['scenario_id']}` | "
            f"`{item['track_id']}` | "
            f"`{item['source_name']}` | "
            f"{item['why_it_matters']} | "
            f"{item['first_next_action']} |"
        )

    lines.extend(
        [
            "",
            "## Source Coverage",
            "",
            "| Source | Candidates | Branch-selection cases | Branchable | Guard promotions | Guard holds |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source in per_source:
        assert isinstance(source, dict)
        lines.append(
            "| "
            f"`{source['source_name']}` | "
            f"{source['candidate_count']} | "
            f"{source['branch_selection_case_count']} | "
            f"{source['branchable_case_count']} | "
            f"{source['route_guard_promote_count']} | "
            f"{source['route_guard_hold_count']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The current branch selector is real but narrow: it promotes evidence "
            "only where parsed topology exposes multiple continuations.",
            "- Single-chain cases are useful negative evidence. They show that "
            "route-choice scoring cannot help until topology coverage, selected "
            "lane choice, or search depth exposes alternatives.",
            "- Topology-audit cases are the highest-leverage expansion path "
            "because they turn missing or terminal lane links into measurable "
            "parser/map-coverage work.",
            "- Route-context holds stay held. The audit records them as "
            "follow-up work instead of quietly counting them as selector wins.",
            "- This is not a benchmark or production rollout claim; it is a "
            "framework coverage audit for deciding what evidence to collect next.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _load_manifest(path: Path, expected_format: str, label: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != expected_format:
        raise ValueError(
            f"Expected a {label} manifest with format {expected_format}."
        )
    return payload


def _aggregate(
    candidates: dict[str, object],
    candidate_rows: list[dict[str, object]],
    replay: dict[str, object],
    replay_rows: list[dict[str, object]],
    diagnostics: dict[str, object],
    diagnostic_rows: list[dict[str, object]],
    branch_selection: dict[str, object],
    branch_rows: list[dict[str, object]],
    branch_replay_rows: list[dict[str, object]],
    route_guard_rows: list[dict[str, object]],
) -> dict[str, object]:
    candidate_count = len(candidate_rows)
    replay_candidate_count = _count_bucket(
        candidate_rows,
        {"improvement_replay_control", "regression_replay_debug"},
    )
    regression_candidate_count = _count_bucket(candidate_rows, {"regression_replay_debug"})
    topology_candidate_count = _count_bucket(candidate_rows, {"topology_audit"})
    branchable_count = sum(bool(row.get("branchable")) for row in branch_rows)
    single_chain_count = sum(
        str(row.get("verdict")) == "single_chain_no_branch_choice"
        for row in branch_rows
    )
    motion_context_improved_count = sum(
        str(row.get("verdict")) == "motion_context_selector_improves"
        for row in branch_rows
    )
    guard_promote_count = sum(
        str(row.get("guard_label")) == "promote_motion_context_candidate"
        for row in route_guard_rows
    )
    guard_hold_count = sum(
        str(row.get("guard_label")) == "hold_for_route_context_evidence"
        for row in route_guard_rows
    )
    topology_blocker_count = sum(
        str(row.get("bucket")) == "topology_audit" for row in diagnostic_rows
    )
    if not topology_blocker_count:
        topology_blocker_count = topology_candidate_count
    branch_selection_count = len(branch_rows)
    expansion_queue_count = single_chain_count + topology_blocker_count + guard_hold_count
    return {
        "candidate_count": candidate_count,
        "replay_candidate_count": replay_candidate_count,
        "improvement_control_candidate_count": _count_bucket(
            candidate_rows,
            {"improvement_replay_control"},
        ),
        "regression_debug_candidate_count": regression_candidate_count,
        "topology_audit_candidate_count": topology_candidate_count,
        "replay_selected_candidate_count": _optional_int(
            replay.get("selected_candidate_count")
        )
        or len(replay_rows),
        "replayed_case_count": _optional_int(
            _required_mapping(replay, "aggregate").get("replayed_case_count")
        )
        or 0,
        "route_diagnostic_count": len(diagnostic_rows),
        "regression_diagnostic_count": sum(
            str(row.get("bucket")) == "regression_replay_debug"
            for row in diagnostic_rows
        ),
        "topology_diagnostic_count": topology_blocker_count,
        "branch_selection_case_count": branch_selection_count,
        "branchable_case_count": branchable_count,
        "single_chain_case_count": single_chain_count,
        "motion_context_improved_case_count": motion_context_improved_count,
        "oracle_improved_case_count": sum(
            (_optional_float(row.get("oracle_recoverable_fde_m")) or 0.0) > 0.0
            for row in branch_rows
        ),
        "branch_replay_case_count": len(branch_replay_rows),
        "route_guard_case_count": len(route_guard_rows),
        "route_guard_promote_count": guard_promote_count,
        "route_guard_hold_count": guard_hold_count,
        "topology_blocker_count": topology_blocker_count,
        "expansion_queue_count": expansion_queue_count,
        "branchable_candidate_rate": _rate(branchable_count, candidate_count),
        "branchable_selection_rate": _rate(branchable_count, branch_selection_count),
        "guard_promotion_candidate_rate": _rate(guard_promote_count, candidate_count),
        "source_candidate_count": len(
            {str(row.get("source_name", "")) for row in candidate_rows}
        ),
        "branch_selection_ready": bool(branch_selection.get("ready")),
        "candidate_top_per_bucket": candidates.get("top_per_bucket"),
        "diagnostics_top": diagnostics.get("top"),
    }


def _funnel(aggregate: dict[str, object]) -> list[dict[str, object]]:
    stages = [
        {
            "label": "Continuation candidates",
            "count": int(aggregate["candidate_count"]),
            "evidence": "ScenarioLens found continuation cases worth replay or topology audit.",
            "next_action": "Keep this as the broad local queue for v1.0 expansion.",
        },
        {
            "label": "Replay/probe selected queue",
            "count": int(aggregate["replay_selected_candidate_count"]),
            "evidence": "Candidates selected for replay controls, regression replay, or topology probes.",
            "next_action": "Broaden top-per-bucket when raw-data budget allows.",
        },
        {
            "label": "Replayed cases",
            "count": int(aggregate["replayed_case_count"]),
            "evidence": "Improvement controls and regression-debug targets were replayed.",
            "next_action": "Keep topology probes separate from replay evidence.",
        },
        {
            "label": "Route diagnostics",
            "count": int(aggregate["route_diagnostic_count"]),
            "evidence": "Replayed regressions and topology blockers have named failure labels.",
            "next_action": "Use labels to separate route-choice work from parser/topology work.",
            "reset_conversion": True,
        },
        {
            "label": "Branch-selection cases",
            "count": int(aggregate["branch_selection_case_count"]),
            "evidence": "Regression diagnostics were reloaded and branch-swept.",
            "next_action": "Increase alternatives by improving topology parsing and search depth.",
        },
        {
            "label": "Branchable cases",
            "count": int(aggregate["branchable_case_count"]),
            "evidence": "Parsed map topology exposed multiple continuations.",
            "next_action": "Use these as selector/guard evidence, not as whole-dataset coverage.",
        },
        {
            "label": "Motion-context improvements",
            "count": int(aggregate["motion_context_improved_case_count"]),
            "evidence": "A non-oracle branch selector improved FDE on branchable cases.",
            "next_action": "Replay and guard these before changing selector defaults.",
        },
        {
            "label": "Route-guard promotions",
            "count": int(aggregate["route_guard_promote_count"]),
            "evidence": "Strict route-context guard accepted a branch for broader evaluation.",
            "next_action": "Treat this as the positive control for expanding the queue.",
        },
    ]
    rows: list[dict[str, object]] = []
    previous: int | None = None
    for stage in stages:
        count = int(stage["count"])
        rows.append(
            {
                "label": stage["label"],
                "count": count,
                "conversion_from_previous": (
                    None
                    if previous is None or bool(stage.get("reset_conversion"))
                    else _rate(count, previous)
                ),
                "evidence": stage["evidence"],
                "next_action": stage["next_action"],
            }
        )
        previous = count
    return rows


def _bottlenecks(
    candidate_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
    branch_rows: list[dict[str, object]],
    route_guard_rows: list[dict[str, object]],
    aggregate: dict[str, object],
) -> list[dict[str, object]]:
    topology_labels = _label_counts(
        [
            str(row.get("diagnosis_label", row.get("readiness", "unknown")))
            for row in diagnostic_rows
            if str(row.get("bucket")) == "topology_audit"
        ]
    )
    single_chain = [
        row
        for row in branch_rows
        if str(row.get("verdict")) == "single_chain_no_branch_choice"
    ]
    guard_holds = [
        row
        for row in route_guard_rows
        if str(row.get("guard_label")) == "hold_for_route_context_evidence"
    ]
    regression_candidates = [
        row
        for row in candidate_rows
        if str(row.get("bucket")) == "regression_replay_debug"
    ]
    return [
        {
            "label": "topology_parser_gap",
            "count": int(aggregate["topology_blocker_count"]),
            "evidence": _counts_text(topology_labels)
            or "Topology-audit candidates still lack usable linked-lane chains.",
            "next_action": (
                "Audit missing linked features, terminal lanes, and parser feature "
                "caps before expanding branch replay."
            ),
        },
        {
            "label": "single_chain_no_branch_choice",
            "count": len(single_chain),
            "evidence": _scenario_text(single_chain),
            "next_action": (
                "Expose alternate continuations through deeper topology search, "
                "better selected-lane choice, or richer lane-link parsing."
            ),
        },
        {
            "label": "route_context_margin_hold",
            "count": len(guard_holds),
            "evidence": _scenario_text(guard_holds),
            "next_action": (
                "Add endpoint-alignment, downstream topology, traffic-control, "
                "and speed-limit context before selector rollout."
            ),
        },
        {
            "label": "narrow_regression_branch_queue",
            "count": len(regression_candidates),
            "evidence": (
                f"{len(regression_candidates)} regression-debug candidates feed "
                "the current branch-selection stage."
            ),
            "next_action": (
                "After topology blockers shrink, raise top-per-bucket and rerun "
                "continuation replay, route diagnostics, branch selection, replay, "
                "and guard reports."
            ),
        },
    ]


def _expansion_queue(
    candidate_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
    branch_rows: list[dict[str, object]],
    route_guard_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    guard_holds = [
        row
        for row in route_guard_rows
        if str(row.get("guard_label")) == "hold_for_route_context_evidence"
    ]
    for row in guard_holds:
        items.append(
            _queue_item(
                queue_type="route_context_margin",
                row=row,
                why_it_matters=str(
                    row.get(
                        "guard_reason",
                        "A nominal branch gain needs stronger route-context evidence.",
                    )
                ),
                first_next_action=str(
                    row.get(
                        "first_next_action",
                        "Add richer route-context guard features before rollout.",
                    )
                ),
            )
        )

    single_chain = [
        row
        for row in branch_rows
        if str(row.get("verdict")) == "single_chain_no_branch_choice"
    ]
    for row in single_chain:
        items.append(
            _queue_item(
                queue_type="single_chain_branch_expansion",
                row=row,
                why_it_matters=str(
                    row.get(
                        "why_it_matters",
                        "Branch scoring cannot help until the map exposes alternatives.",
                    )
                ),
                first_next_action=_first_action(
                    row,
                    "Expose alternate continuations before rerunning branch selection.",
                ),
            )
        )

    diagnostic_by_key = {
        (str(row.get("scenario_id")), str(row.get("track_id"))): row
        for row in diagnostic_rows
    }
    for row in candidate_rows:
        if str(row.get("bucket")) != "topology_audit":
            continue
        diagnostic = diagnostic_by_key.get(
            (str(row.get("scenario_id")), str(row.get("track_id")))
        )
        source = diagnostic if diagnostic is not None else row
        items.append(
            _queue_item(
                queue_type="topology_parser_gap",
                row=source,
                why_it_matters=str(
                    source.get(
                        "why_it_matters",
                        "Topology coverage blocks branch replay for this target.",
                    )
                ),
                first_next_action=_first_action(
                    source,
                    "Audit parsed entry/exit links and rerun continuation diagnostics.",
                ),
            )
        )

    items = sorted(
        items,
        key=lambda item: (
            _queue_priority(str(item["queue_type"])),
            int(item.get("source_rank", 9999)),
            str(item.get("scenario_id", "")),
            str(item.get("track_id", "")),
        ),
    )
    for index, item in enumerate(items, start=1):
        item["rank"] = index
    return items


def _queue_item(
    queue_type: str,
    row: dict[str, object],
    why_it_matters: str,
    first_next_action: str,
) -> dict[str, object]:
    return {
        "rank": 0,
        "source_rank": int(row.get("rank", 9999) or 9999),
        "queue_type": queue_type,
        "scenario_id": str(row.get("scenario_id", "")),
        "track_id": str(row.get("track_id", "")),
        "source_name": str(row.get("source_name", "")),
        "why_it_matters": why_it_matters,
        "first_next_action": first_next_action,
    }


def _per_source(
    candidate_rows: list[dict[str, object]],
    branch_rows: list[dict[str, object]],
    route_guard_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    sources = sorted(
        {
            str(row.get("source_name", "unknown"))
            for row in [*candidate_rows, *branch_rows, *route_guard_rows]
            if str(row.get("source_name", ""))
        }
    )
    rows: list[dict[str, object]] = []
    for source in sources:
        rows.append(
            {
                "source_name": source,
                "candidate_count": sum(
                    str(row.get("source_name")) == source for row in candidate_rows
                ),
                "branch_selection_case_count": sum(
                    str(row.get("source_name")) == source for row in branch_rows
                ),
                "branchable_case_count": sum(
                    str(row.get("source_name")) == source
                    and bool(row.get("branchable"))
                    for row in branch_rows
                ),
                "route_guard_promote_count": sum(
                    str(row.get("source_name")) == source
                    and str(row.get("guard_label"))
                    == "promote_motion_context_candidate"
                    for row in route_guard_rows
                ),
                "route_guard_hold_count": sum(
                    str(row.get("source_name")) == source
                    and str(row.get("guard_label"))
                    == "hold_for_route_context_evidence"
                    for row in route_guard_rows
                ),
            }
        )
    return rows


def _count_bucket(rows: list[dict[str, object]], buckets: set[str]) -> int:
    return sum(str(row.get("bucket")) in buckets for row in rows)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _optional_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _percent_text(value: object) -> str:
    number = _optional_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.1f}%"


def _label_counts(labels: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return counts


def _counts_text(counts: dict[str, int]) -> str:
    if not counts:
        return ""
    return ", ".join(f"{label}: {count}" for label, count in sorted(counts.items()))


def _scenario_text(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "None in the current manifest."
    examples = [
        f"{row.get('scenario_id')} / track {row.get('track_id')}"
        for row in rows[:3]
    ]
    suffix = "" if len(rows) <= 3 else f", plus {len(rows) - 3} more"
    return ", ".join(examples) + suffix


def _first_action(row: dict[str, object], fallback: str) -> str:
    actions = row.get("next_actions")
    if isinstance(actions, list) and actions:
        return str(actions[0])
    return fallback


def _queue_priority(queue_type: str) -> int:
    priorities = {
        "route_context_margin": 0,
        "single_chain_branch_expansion": 1,
        "topology_parser_gap": 2,
    }
    return priorities.get(queue_type, 99)
