from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

EVIDENCE_INDEX_FORMAT = "scenariolens.evidence_index.v1"


@dataclass(frozen=True)
class EvidenceMetric:
    """Small public-safe metric displayed on an evidence card."""

    label: str
    value: str


@dataclass(frozen=True)
class EvidenceCatalogItem:
    """A curated public artifact that belongs in the v1 evidence spine."""

    identifier: str
    title: str
    stage: str
    stage_label: str
    proof_type: str
    scope: str
    path: str
    command: str
    data_status: str
    why_it_matters: str
    limitation: str
    metrics: tuple[EvidenceMetric, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class EvidenceIndexResult:
    """Files produced by an evidence-index generation run."""

    ready: bool
    artifact_count: int
    present_count: int
    missing_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None
    demo_json_path: Path | None


DEFAULT_EVIDENCE_CATALOG: tuple[EvidenceCatalogItem, ...] = (
    EvidenceCatalogItem(
        identifier="live_explorer",
        title="Static Scenario Explorer",
        stage="product_surface",
        stage_label="Product surface",
        proof_type="interactive demo",
        scope="14 public demo scenarios plus real-data evidence links",
        path="docs/demo/index.html",
        command="scenariolens dashboard-data --output docs/demo/scenarios.json",
        data_status="public fixtures plus aggregate/derived real-data links",
        why_it_matters=(
            "Gives a reviewer a zero-install first look at ranking, filtering, "
            "trajectory previews, failure cards, and selector diagnostics."
        ),
        limitation="The explorer is static and does not expose raw Waymo data.",
        metrics=(
            EvidenceMetric("Explorer scenarios", "14"),
            EvidenceMetric("Live route", "GitHub Pages/portfolio friendly"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="data_provenance",
        title="Data Provenance Boundary",
        stage="data_boundary",
        stage_label="Data boundary",
        proof_type="provenance",
        scope="Public-safe data handling and raw-data exclusion policy",
        path="docs/data_provenance.md",
        command="documented local Waymo Motion workflow",
        data_status="raw Waymo files ignored; public artifacts are derived",
        why_it_matters=(
            "Makes the project credible without implying private-data access or "
            "publishing restricted raw records."
        ),
        limitation="External users need their own Waymo Open Dataset access.",
        metrics=(EvidenceMetric("Raw TFRecords in git", "0"),),
    ),
    EvidenceCatalogItem(
        identifier="failure_stability_cross_shard",
        title="Cross-Shard Failure Stability",
        stage="scenario_mining",
        stage_label="Scenario mining",
        proof_type="real-data aggregate study",
        scope="100 scenarios across 4 local Waymo Motion validation shards",
        path="docs/reports/waymo_motion_failure_stability_cross_shard.md",
        command="scenariolens failure-study-stability --input ...",
        data_status="aggregate public report from local validation shards",
        why_it_matters=(
            "Shows that the ranking and baseline-failure workflow runs beyond "
            "one toy fixture or hand-picked scene."
        ),
        limitation="This is a local diagnostic slice, not a Waymo benchmark.",
        metrics=(
            EvidenceMetric("Scenarios", "100"),
            EvidenceMetric("Validation shards", "4"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="context_failure_study",
        title="Context-Joined Failure Study",
        stage="scenario_mining",
        stage_label="Scenario mining",
        proof_type="context diagnostic",
        scope="Map, route, signal, and failure metrics over the 100-scenario slice",
        path="docs/reports/waymo_context_failure_study_cross_shard.md",
        command="scenariolens context-failure-study --input ...",
        data_status="public scenario IDs and aggregate context counts",
        why_it_matters=(
            "Connects scenario mining to map/signal context so failures are "
            "actionable, not just high numeric scores."
        ),
        limitation="Context fields are derived from the lightweight parser boundary.",
        metrics=(EvidenceMetric("Scenarios", "100"),),
    ),
    EvidenceCatalogItem(
        identifier="lane_aware_baseline",
        title="Lane-Aware Baseline Diagnostic",
        stage="baseline_models",
        stage_label="Baseline models",
        proof_type="baseline comparison",
        scope="Constant-velocity vs lane-aware estimates on 100 real scenarios",
        path="docs/reports/waymo_lane_aware_baseline_cross_shard.md",
        command="scenariolens baseline-compare-study --input ...",
        data_status="aggregate public report with wins and regressions",
        why_it_matters=(
            "Demonstrates honest model evaluation: the map-aware baseline helps "
            "some cases and regresses others."
        ),
        limitation="The lane-aware baseline is diagnostic, not a production predictor.",
        metrics=(
            EvidenceMetric("Scenarios", "100"),
            EvidenceMetric("Published regressions", "yes"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="heading_lane_selection",
        title="Heading-Aware Lane Selection Study",
        stage="baseline_models",
        stage_label="Baseline models",
        proof_type="map-matching ablation",
        scope="418 evaluated prediction targets from the 100-scenario slice",
        path="docs/reports/waymo_heading_aware_lane_selection_study.md",
        command="scenariolens lane-selection-study --input ...",
        data_status="aggregate target-level comparison",
        why_it_matters=(
            "Turns a failed naive map baseline into a specific matcher ablation "
            "with measured improvement over nearest-lane selection."
        ),
        limitation="Heading-aware selection still trails constant velocity overall.",
        metrics=(
            EvidenceMetric("Evaluated targets", "418"),
            EvidenceMetric("FDE vs nearest lane", "+0.489 m improvement"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="heading_replay_prototype",
        title="Heading-Aware Replay Prototype",
        stage="replay_bridge",
        stage_label="Replay bridge",
        proof_type="open-loop replay",
        scope="Selected heading-aware cases with deterministic perturbations",
        path="docs/reports/waymo_heading_aware_replay_prototype.md",
        command="scenariolens heading-replay-prototype --candidate-manifest ...",
        data_status="public-safe replay summary; local packets ignored",
        why_it_matters=(
            "Shows the path from mined cases to replay-style validation while "
            "staying laptop-safe."
        ),
        limitation="Open-loop diagnostic only; no closed-loop Waymax/JAX claim.",
        metrics=(EvidenceMetric("Perturbation mode", "deterministic"),),
    ),
    EvidenceCatalogItem(
        identifier="lane_continuation_200",
        title="200-Scenario Lane-Continuation Study",
        stage="lane_continuation",
        stage_label="Lane continuation",
        proof_type="real-data map diagnostic",
        scope="451 lane-continuation targets across four local validation shards",
        path="docs/reports/waymo_lane_continuation_study_200.md",
        command="scenariolens lane-continuation-study --input ...",
        data_status="aggregate public report from local shards",
        why_it_matters=(
            "Scales the lane-continuation diagnosis from isolated examples to a "
            "larger real-data target set."
        ),
        limitation="Still bounded to four local validation shards.",
        metrics=(
            EvidenceMetric("Scenarios", "200"),
            EvidenceMetric("Continuation targets", "451"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="lane_continuation_replay_200",
        title="200-Scenario Continuation Replay",
        stage="lane_continuation",
        stage_label="Lane continuation",
        proof_type="open-loop replay",
        scope="Replay/probe queue derived from the 200-scenario continuation study",
        path="docs/reports/waymo_lane_continuation_replay_prototype_200.md",
        command="scenariolens lane-continuation-replay-prototype --candidate-manifest ...",
        data_status="public-safe replay summary; local trajectories ignored",
        why_it_matters=(
            "Checks whether continuation candidates survive bounded replay and "
            "topology probes."
        ),
        limitation="Open-loop rollouts only, with local per-case artifacts ignored.",
        metrics=(
            EvidenceMetric("Queued cases", "45"),
            EvidenceMetric("Raw trajectories committed", "0"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="terminal_selector_calibration_200",
        title="200-Scenario Terminal Selector Calibration",
        stage="selector_validation",
        stage_label="Selector validation",
        proof_type="policy calibration",
        scope="Zero-false-promotion gate sweep over terminal-neighborhood cases",
        path="docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md",
        command="scenariolens lane-continuation-terminal-neighborhood-selector-calibration ...",
        data_status="derived candidate labels and aggregate counts",
        why_it_matters=(
            "Makes selector promotion conservative and measurable instead of "
            "silently changing behavior."
        ),
        limitation="The selected gate is provisional and queue-bounded.",
        metrics=(
            EvidenceMetric("False promotions", "0"),
            EvidenceMetric("Default selector changed", "no"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="terminal_selector_transfer_200",
        title="Terminal Selector Transfer Validation",
        stage="selector_validation",
        stage_label="Selector validation",
        proof_type="transfer validation",
        scope="7-case validation queue, including 4 novel transfer cases",
        path="docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md",
        command="scenariolens lane-continuation-terminal-neighborhood-selector-transfer ...",
        data_status="derived replay labels and selector outcomes",
        why_it_matters=(
            "Tests whether the selector gate transfers beyond the calibration "
            "queue without false promotions."
        ),
        limitation="The transfer queue is intentionally small and diagnostic.",
        metrics=(
            EvidenceMetric("Validation cases", "7"),
            EvidenceMetric("Novel cases", "4"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="terminal_selector_candidate_validation_200",
        title="Context-Aware Selector Candidate Validation",
        stage="selector_validation",
        stage_label="Selector validation",
        proof_type="candidate validation",
        scope="Candidate policy joined to transfer and route/context audits",
        path="docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md",
        command="scenariolens lane-continuation-terminal-neighborhood-selector-candidate-validation ...",
        data_status="public-safe candidate labels and rationale",
        why_it_matters=(
            "Shows one narrow improvement path: recover a false hold while "
            "preserving negative controls."
        ),
        limitation="The default selector remains unchanged pending broader validation.",
        metrics=(
            EvidenceMetric("Agreement", "6/7"),
            EvidenceMetric("False promotions", "0"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="terminal_selector_decision_atlas_200",
        title="Terminal Selector Decision Atlas",
        stage="selector_validation",
        stage_label="Selector validation",
        proof_type="visual decision atlas",
        scope="7 derived selector cards joined to candidate-validation labels",
        path="docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md",
        command="scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas ...",
        data_status="SVG decision cards plus public-safe JSON payload",
        why_it_matters=(
            "Turns the selector validation into visual evidence a reviewer can "
            "inspect quickly."
        ),
        limitation="No raw Waymo trajectories or map geometry are published.",
        metrics=(
            EvidenceMetric("Visual cards", "7"),
            EvidenceMetric("Candidate agreement", "6/7"),
        ),
    ),
    EvidenceCatalogItem(
        identifier="selector_demo_payload",
        title="Selector Atlas Demo Payload",
        stage="product_surface",
        stage_label="Product surface",
        proof_type="static data contract",
        scope="Public-safe selector decision cards loaded by the static Explorer",
        path="docs/demo/selector_decisions.json",
        command="scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas --demo-json ...",
        data_status="derived public JSON, no raw trajectories",
        why_it_matters=(
            "Keeps the Explorer a thin presentation layer over generated, "
            "tested artifacts."
        ),
        limitation="The payload mirrors selected public report fields only.",
        metrics=(EvidenceMetric("Cards", "7"),),
    ),
    EvidenceCatalogItem(
        identifier="ci_workflow",
        title="CI Validation Workflow",
        stage="release_readiness",
        stage_label="Release readiness",
        proof_type="automation",
        scope="Unit tests plus CLI smoke workflows on every push",
        path=".github/workflows/ci.yml",
        command="python -m unittest discover; CLI smoke commands",
        data_status="CI-safe fixtures only",
        why_it_matters=(
            "Shows the framework is maintained as software, not just a set of "
            "static reports."
        ),
        limitation="Live Waymo shards remain local and are not required in CI.",
        metrics=(EvidenceMetric("CI raw Waymo dependency", "none"),),
    ),
    EvidenceCatalogItem(
        identifier="public_surface_check",
        title="Public Surface Check",
        stage="release_readiness",
        stage_label="Release readiness",
        proof_type="readiness gate",
        scope="Offline check for public links, payload contracts, raw-data boundary, and CI smoke coverage",
        path="docs/reports/scenariolens_public_surface_check.md",
        command="scenariolens public-surface-check --repo-root .",
        data_status="CI-safe repository metadata and derived public artifacts only",
        why_it_matters=(
            "Turns the public repo surface into a testable release gate instead "
            "of relying on manual README/demo inspection."
        ),
        limitation="External links are counted but not fetched to keep CI deterministic.",
        metrics=(
            EvidenceMetric("Offline checks", "7"),
            EvidenceMetric("Raw-data guard", "yes"),
        ),
    ),
)


def generate_evidence_index(
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
    demo_json_path: str | Path | None = None,
    repo_root: str | Path = ".",
) -> EvidenceIndexResult:
    """Generate a manifest/report that indexes ScenarioLens public evidence."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None
    copied_demo_path = Path(demo_json_path) if demo_json_path else None

    payload = evidence_index_payload(repo_root=repo_root)
    report = evidence_index_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")

    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")
    if copied_demo_path is not None:
        copied_demo_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(copied_demo_path, payload)

    aggregate = payload["aggregate"]
    return EvidenceIndexResult(
        ready=bool(payload["ready"]),
        artifact_count=int(aggregate["artifact_count"]),
        present_count=int(aggregate["present_count"]),
        missing_count=int(aggregate["missing_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
        demo_json_path=copied_demo_path,
    )


def evidence_index_payload(
    repo_root: str | Path = ".",
    catalog: tuple[EvidenceCatalogItem, ...] = DEFAULT_EVIDENCE_CATALOG,
) -> dict[str, object]:
    """Return a public-safe index of current ScenarioLens evidence artifacts."""

    root = Path(repo_root)
    artifacts = [_artifact_payload(root, item) for item in catalog]
    stage_order = _stage_order(catalog)
    stages = [
        _stage_payload(stage=stage, artifacts=artifacts, catalog=catalog)
        for stage in stage_order
    ]
    required = [artifact for artifact in artifacts if artifact["required"]]
    missing = [artifact for artifact in required if not artifact["present"]]
    proof_type_counts = _counts(str(artifact["proof_type"]) for artifact in artifacts)
    stage_counts = _counts(str(artifact["stage"]) for artifact in artifacts)
    present_count = sum(1 for artifact in artifacts if artifact["present"])
    public_safe_count = len(artifacts)
    local_real_data_count = sum(
        1
        for artifact in artifacts
        if _artifact_mentions_real_data(artifact)
    )

    return {
        "format": EVIDENCE_INDEX_FORMAT,
        "ready": len(missing) == 0,
        "generated_by": "scenariolens evidence-index",
        "scope_note": (
            "This evidence index is generated from a curated public artifact "
            "catalog and verifies that required reports, payloads, and CI files "
            "exist in the repository. It is a recruiter-facing map of evidence, "
            "not a Waymo benchmark claim."
        ),
        "aggregate": {
            "artifact_count": len(artifacts),
            "present_count": present_count,
            "missing_count": len(missing),
            "required_count": len(required),
            "stage_count": len(stages),
            "proof_type_counts": proof_type_counts,
            "stage_counts": stage_counts,
            "public_safe_artifact_count": public_safe_count,
            "local_real_data_artifact_count": local_real_data_count,
        },
        "stages": stages,
        "artifacts": artifacts,
        "missing_artifacts": [
            {
                "id": artifact["id"],
                "title": artifact["title"],
                "path": artifact["path"],
            }
            for artifact in missing
        ],
    }


def evidence_index_markdown(payload: dict[str, object]) -> str:
    """Return a Markdown evidence index from a payload."""

    aggregate = _mapping(payload, "aggregate")
    artifacts = _list(payload, "artifacts")
    stages = _list(payload, "stages")
    missing = _list(payload, "missing_artifacts")

    lines = [
        "# ScenarioLens V1 Evidence Index",
        "",
        "This generated index is the public evidence spine for ScenarioLens. It "
        "collects the product demo, data boundary, real-data diagnostics, replay "
        "bridges, selector validation reports, and CI surface that make the repo "
        "reviewable without publishing raw Waymo records.",
        "",
        "It is intentionally honest: this is a scenario-mining and evaluation "
        "framework, not a production autonomy stack, not a closed-loop simulator, "
        "and not a Waymo benchmark submission.",
        "",
        "## Readiness",
        "",
        f"- Ready: {'yes' if payload['ready'] else 'no'}",
        f"- Required artifacts present: {aggregate['present_count']} / {aggregate['required_count']}",
        f"- Missing required artifacts: {aggregate['missing_count']}",
        f"- Evidence stages: {aggregate['stage_count']}",
        f"- Public-safe artifacts indexed: {aggregate['public_safe_artifact_count']}",
        f"- Local real-data/Waymo-derived artifacts indexed: {aggregate['local_real_data_artifact_count']}",
        "",
        "## Stage Summary",
        "",
        "| Stage | Present | Artifacts | Why it matters |",
        "| --- | ---: | ---: | --- |",
    ]
    for stage in stages:
        lines.append(
            "| {label} | {present} | {count} | {summary} |".format(
                label=stage["label"],
                present=stage["present_count"],
                count=stage["artifact_count"],
                summary=stage["summary"],
            )
        )

    lines.extend(
        [
            "",
            "## Evidence Artifacts",
            "",
            "| Artifact | Stage | Scope | Key metrics | Present |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for artifact in artifacts:
        metrics = "; ".join(
            f"{metric['label']}: {metric['value']}"
            for metric in _list_value(artifact.get("metrics"))
        )
        metric_text = metrics or "n/a"
        lines.append(
            "| [{title}]({link}) | {stage} | {scope} | {metrics} | {present} |".format(
                title=artifact["title"],
                link=artifact["link_path"],
                stage=artifact["stage_label"],
                scope=artifact["scope"],
                metrics=metric_text,
                present="yes" if artifact["present"] else "no",
            )
        )

    lines.extend(["", "## Artifact Notes", ""])
    for artifact in artifacts:
        lines.extend(
            [
                f"### {artifact['title']}",
                "",
                f"- Path: `{artifact['path']}`",
                f"- Proof type: {artifact['proof_type']}",
                f"- Command: `{artifact['command']}`",
                f"- Data status: {artifact['data_status']}",
                f"- Why it matters: {artifact['why_it_matters']}",
                f"- Limitation: {artifact['limitation']}",
                "",
            ]
        )

    if missing:
        lines.extend(["## Missing Required Artifacts", ""])
        for artifact in missing:
            lines.append(f"- `{artifact['path']}` ({artifact['title']})")
        lines.append("")

    lines.extend(
        [
            "## Public-Safety Boundary",
            "",
            "- Raw Waymo TFRecords and per-case local replay/debug packets remain outside git.",
            "- Public reports use aggregate counts, scenario IDs, derived SVG cards, and documented limitations.",
            "- The selector evidence is diagnostic; the default selector remains unchanged until broader validation.",
            "- This index verifies repository artifacts, not local raw-data availability.",
            "",
        ]
    )
    return "\n".join(lines)


def _artifact_payload(root: Path, item: EvidenceCatalogItem) -> dict[str, object]:
    path = Path(item.path)
    absolute_path = root / path
    present = absolute_path.exists()
    metrics = [
        {"label": metric.label, "value": metric.value}
        for metric in item.metrics
    ]
    return {
        "id": item.identifier,
        "title": item.title,
        "stage": item.stage,
        "stage_label": item.stage_label,
        "proof_type": item.proof_type,
        "scope": item.scope,
        "path": item.path,
        "link_path": _public_report_link(item.path),
        "present": present,
        "required": item.required,
        "size_bytes": absolute_path.stat().st_size if present and absolute_path.is_file() else 0,
        "command": item.command,
        "data_status": item.data_status,
        "why_it_matters": item.why_it_matters,
        "limitation": item.limitation,
        "metrics": metrics,
    }


def _stage_order(catalog: tuple[EvidenceCatalogItem, ...]) -> list[str]:
    ordered: list[str] = []
    for item in catalog:
        if item.stage not in ordered:
            ordered.append(item.stage)
    return ordered


def _artifact_mentions_real_data(artifact: dict[str, object]) -> bool:
    text = " ".join(
        str(artifact[key])
        for key in ("path", "proof_type", "scope", "data_status")
    ).lower()
    return any(
        term in text
        for term in (
            "waymo",
            "real-data",
            "real scenario",
            "validation shard",
            "local shard",
            "prediction target",
            "continuation target",
            "validation queue",
        )
    )


def _public_report_link(path: str) -> str:
    if path.startswith("docs/reports/"):
        return path.removeprefix("docs/reports/")
    if path.startswith("docs/"):
        return "../" + path.removeprefix("docs/")
    return "../../" + path


def _stage_payload(
    stage: str,
    artifacts: list[dict[str, object]],
    catalog: tuple[EvidenceCatalogItem, ...],
) -> dict[str, object]:
    stage_artifacts = [
        artifact for artifact in artifacts if artifact["stage"] == stage
    ]
    first = next(item for item in catalog if item.stage == stage)
    return {
        "stage": stage,
        "label": first.stage_label,
        "artifact_count": len(stage_artifacts),
        "present_count": sum(1 for artifact in stage_artifacts if artifact["present"]),
        "artifact_ids": [artifact["id"] for artifact in stage_artifacts],
        "summary": _STAGE_SUMMARIES.get(stage, "Public evidence artifacts."),
    }


def _counts(values: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at {key}.")
    return value


def _list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload.get(key)
    return _list_value(value)


def _list_value(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("Expected list value.")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("Expected list of mappings.")
    return value


_STAGE_SUMMARIES = {
    "product_surface": "Makes the repo understandable quickly through static public artifacts.",
    "data_boundary": "Documents what data is trusted, derived, local, and excluded from git.",
    "scenario_mining": "Shows ScenarioLens can rank and explain real motion scenarios.",
    "baseline_models": "Compares lightweight prediction baselines with honest wins and regressions.",
    "replay_bridge": "Connects mined cases to laptop-safe open-loop replay diagnostics.",
    "lane_continuation": "Audits map-link and lane-continuation failure modes at larger scale.",
    "selector_validation": "Validates conservative selector gates before changing default behavior.",
    "release_readiness": "Keeps the public repo tested and contribution-ready.",
}
