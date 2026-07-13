from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable

from scenariolens import __version__
from scenariolens.baseline_compare_study import (
    BASELINE_COMPARISON_STUDY_INPUT_FORMATS,
    generate_baseline_comparison_study,
)
from scenariolens.ingest.waymo_motion import is_native_motion_file
from scenariolens.lane_continuation import generate_lane_continuation_study
from scenariolens.lane_selection_study import generate_lane_selection_study

try:
    import resource
except ImportError:  # pragma: no cover - resource is available on CI and macOS.
    resource = None  # type: ignore[assignment]

RUN_BUNDLE_FORMAT = "scenariolens.run.v1"
RUN_BUNDLE_INPUT_FORMATS = BASELINE_COMPARISON_STUDY_INPUT_FORMATS


@dataclass(frozen=True)
class RunBundleResult:
    """Top-level artifacts produced by one ScenarioLens analysis run."""

    ready: bool
    source_count: int
    scenario_count: int
    stage_count: int
    analysis_digest: str
    duration_seconds: float
    peak_rss_bytes: int | None
    output_dir: Path
    manifest_path: Path
    report_path: Path


@dataclass(frozen=True)
class _StageDefinition:
    stage_id: str
    label: str
    generator: Callable[..., object]


_STAGES = (
    _StageDefinition(
        stage_id="baseline_comparison",
        label="Constant-velocity vs lane-aware baseline",
        generator=generate_baseline_comparison_study,
    ),
    _StageDefinition(
        stage_id="lane_selection",
        label="Nearest-lane vs heading-aware lane selection",
        generator=generate_lane_selection_study,
    ),
    _StageDefinition(
        stage_id="lane_continuation",
        label="Linked-lane continuation diagnostic",
        generator=generate_lane_continuation_study,
    ),
)


def generate_run_bundle(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 10,
    input_format: str = "native",
    hash_inputs: bool = True,
) -> RunBundleResult:
    """Run the core ScenarioLens studies and write one reproducible bundle."""

    _validate_options(
        input_paths=input_paths,
        max_scenarios=max_scenarios,
        top=top,
        input_format=input_format,
    )
    sources = resolve_run_inputs(input_paths, input_format=input_format)
    target = Path(output_dir)
    studies_dir = target / "studies"
    target.mkdir(parents=True, exist_ok=True)
    studies_dir.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    input_provenance = [
        _input_provenance(path, index=index, hash_input=hash_inputs)
        for index, path in enumerate(sources, start=1)
    ]
    stages: list[dict[str, object]] = []

    for definition in _STAGES:
        stage_dir = studies_dir / definition.stage_id
        stage_started = perf_counter()
        result = definition.generator(
            input_paths=sources,
            output_dir=stage_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
        )
        duration_seconds = perf_counter() - stage_started
        manifest_path = Path(getattr(result, "manifest_path"))
        report_path = Path(getattr(result, "report_path"))
        stage_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        stages.append(
            _stage_summary(
                definition=definition,
                payload=stage_payload,
                duration_seconds=duration_seconds,
                manifest_path=manifest_path,
                report_path=report_path,
                output_dir=target,
            )
        )

    scenario_counts = {
        int(stage["scenario_count"])
        for stage in stages
        if stage.get("scenario_count") is not None
    }
    warnings = []
    if len(scenario_counts) > 1:
        warnings.append(
            "Study scenario counts differ; inspect stage manifests before using this run."
        )
    scenario_count = max(scenario_counts, default=0)
    ready = all(bool(stage["ready"]) for stage in stages) and not warnings
    stable_payload = _stable_analysis_payload(
        input_format=input_format,
        max_scenarios=max_scenarios,
        top=top,
        inputs=input_provenance,
        stages=stages,
    )
    analysis_digest = hashlib.sha256(
        json.dumps(
            stable_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    duration_seconds = perf_counter() - started
    peak_rss_bytes = _peak_rss_bytes()
    payload: dict[str, object] = {
        "format": RUN_BUNDLE_FORMAT,
        "ready": ready,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scenariolens_version": __version__,
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "configuration": {
            "input_format": input_format,
            "max_scenarios_per_input": max_scenarios,
            "top": top,
            "hash_inputs": hash_inputs,
        },
        "source_count": len(sources),
        "scenario_count": scenario_count,
        "stage_count": len(stages),
        "duration_seconds": round(duration_seconds, 3),
        "peak_rss_bytes": peak_rss_bytes,
        "analysis_digest": analysis_digest,
        "inputs": input_provenance,
        "stages": stages,
        "warnings": warnings,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "studies": "studies/",
        },
        "scope_note": (
            "This run is a local scenario-mining and baseline diagnostic. It is "
            "not a Waymo benchmark, not closed-loop safety validation, and not "
            "a production prediction model."
        ),
    }
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(run_bundle_markdown(payload), encoding="utf-8")

    return RunBundleResult(
        ready=ready,
        source_count=len(sources),
        scenario_count=scenario_count,
        stage_count=len(stages),
        analysis_digest=analysis_digest,
        duration_seconds=round(duration_seconds, 3),
        peak_rss_bytes=peak_rss_bytes,
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
    )


def resolve_run_inputs(
    input_paths: tuple[str | Path, ...],
    input_format: str,
) -> tuple[Path, ...]:
    """Expand native directories into stable, de-duplicated input files."""

    resolved: list[Path] = []
    seen: set[Path] = set()
    for value in input_paths:
        path = Path(value)
        if not path.exists():
            raise FileNotFoundError(f"ScenarioLens run input does not exist: {path}")
        candidates: tuple[Path, ...]
        if path.is_dir():
            if input_format != "native":
                raise ValueError(
                    "ScenarioLens JSON run inputs must be files, not directories: "
                    f"{path}"
                )
            candidates = tuple(
                sorted(
                    candidate
                    for candidate in path.rglob("*")
                    if candidate.is_file() and is_native_motion_file(candidate)
                )
            )
            if not candidates:
                raise ValueError(f"No supported Waymo Motion files found under {path}.")
        else:
            candidates = (path,)

        for candidate in candidates:
            identity = candidate.resolve()
            if identity in seen:
                continue
            seen.add(identity)
            resolved.append(candidate)

    if not resolved:
        raise ValueError("At least one ScenarioLens run input is required.")
    return tuple(resolved)


def run_bundle_markdown(payload: dict[str, object]) -> str:
    """Return a concise human-readable summary of a run bundle."""

    configuration = _required_mapping(payload, "configuration")
    inputs = _required_list(payload, "inputs")
    stages = _required_list(payload, "stages")
    lines = [
        "# ScenarioLens Run Report",
        "",
        "This report is the top-level summary for one reproducible ScenarioLens "
        "analysis bundle.",
        "",
        "## Run Summary",
        "",
        f"- Ready: {'yes' if payload.get('ready') else 'no'}",
        f"- ScenarioLens version: `{payload.get('scenariolens_version')}`",
        f"- Sources: {payload.get('source_count')}",
        f"- Scenarios: {payload.get('scenario_count')}",
        f"- Stages: {payload.get('stage_count')}",
        f"- Duration: {float(payload.get('duration_seconds', 0.0)):.3f} seconds",
        f"- Peak process memory: {_optional_bytes(payload.get('peak_rss_bytes'))}",
        f"- Analysis digest: `{payload.get('analysis_digest')}`",
        f"- Input format: `{configuration.get('input_format')}`",
        f"- Maximum scenarios per input: {configuration.get('max_scenarios_per_input')}",
        "",
        "## Input Provenance",
        "",
        "| Source | Size | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    for item in inputs:
        assert isinstance(item, dict)
        digest = item.get("sha256") or "not computed"
        lines.append(
            f"| `{item.get('source_name')}` | {_format_bytes(int(item.get('size_bytes', 0)))} | "
            f"`{digest}` |"
        )

    lines.extend(
        [
            "",
            "## Stage Summary",
            "",
            "| Stage | Status | Scenarios | Evaluated rows | Duration | Artifacts |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for item in stages:
        assert isinstance(item, dict)
        status = "ready" if item.get("ready") else "not ready"
        lines.append(
            f"| {item.get('label')} | {status} | {item.get('scenario_count')} | "
            f"{item.get('evaluated_count')} | "
            f"{float(item.get('duration_seconds', 0.0)):.3f} s | "
            f"[manifest]({item.get('manifest')}) / [report]({item.get('report')}) |"
        )

    stage_lookup = {
        str(item.get("stage_id")): item
        for item in stages
        if isinstance(item, dict)
    }
    lines.extend(_baseline_findings(stage_lookup.get("baseline_comparison")))
    lines.extend(_lane_selection_findings(stage_lookup.get("lane_selection")))
    lines.extend(_lane_continuation_findings(stage_lookup.get("lane_continuation")))
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            f"- {payload.get('scope_note')}",
            "- Positive and negative baseline deltas are both retained because "
            "regressions are diagnostic evidence, not failed project outcomes.",
            "- Raw Waymo records remain local and are not copied into this bundle.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_options(
    input_paths: tuple[str | Path, ...],
    max_scenarios: int | None,
    top: int,
    input_format: str,
) -> None:
    if not input_paths:
        raise ValueError("At least one ScenarioLens run input is required.")
    if input_format not in RUN_BUNDLE_INPUT_FORMATS:
        raise ValueError(
            f"Unsupported ScenarioLens run input format: {input_format}. "
            f"Expected one of: {', '.join(RUN_BUNDLE_INPUT_FORMATS)}"
        )
    if max_scenarios is not None and max_scenarios < 1:
        raise ValueError("max-scenarios must be at least 1 when provided.")
    if top < 1:
        raise ValueError("top must be at least 1.")


def _input_provenance(path: Path, index: int, hash_input: bool) -> dict[str, object]:
    return {
        "source_index": index,
        "source_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path) if hash_input else None,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stage_summary(
    definition: _StageDefinition,
    payload: dict[str, object],
    duration_seconds: float,
    manifest_path: Path,
    report_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    aggregate = _required_mapping(payload, "aggregate")
    evaluated_count = aggregate.get(
        "evaluated_target_count",
        aggregate.get("evaluated_track_count", 0),
    )
    return {
        "stage_id": definition.stage_id,
        "label": definition.label,
        "format": payload.get("format"),
        "ready": bool(payload.get("ready")),
        "scenario_count": int(payload.get("scenario_count", 0)),
        "evaluated_count": int(evaluated_count or 0),
        "duration_seconds": round(duration_seconds, 3),
        "manifest": manifest_path.relative_to(output_dir).as_posix(),
        "report": report_path.relative_to(output_dir).as_posix(),
        "aggregate": aggregate,
    }


def _stable_analysis_payload(
    input_format: str,
    max_scenarios: int | None,
    top: int,
    inputs: list[dict[str, object]],
    stages: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "format": RUN_BUNDLE_FORMAT,
        "scenariolens_version": __version__,
        "configuration": {
            "input_format": input_format,
            "max_scenarios_per_input": max_scenarios,
            "top": top,
        },
        "inputs": [
            {
                "source_index": item["source_index"],
                "source_name": item["source_name"],
                "size_bytes": item["size_bytes"],
                "sha256": item["sha256"],
            }
            for item in inputs
        ],
        "stages": [
            {
                "stage_id": stage["stage_id"],
                "format": stage["format"],
                "ready": stage["ready"],
                "scenario_count": stage["scenario_count"],
                "evaluated_count": stage["evaluated_count"],
                "aggregate": stage["aggregate"],
            }
            for stage in stages
        ],
    }


def _baseline_findings(stage: dict[str, object] | None) -> list[str]:
    if stage is None:
        return []
    aggregate = _required_mapping(stage, "aggregate")
    return [
        "",
        "## Baseline Comparison",
        "",
        f"- Constant-velocity mean FDE: {_meters(aggregate.get('constant_velocity_fde_m'))}",
        f"- Lane-aware mean FDE: {_meters(aggregate.get('lane_aware_fde_m'))}",
        f"- Lane-aware FDE improvement: {_signed_meters(aggregate.get('fde_improvement_m'))}",
        f"- Map-used targets: {aggregate.get('map_used_count', 0)}",
        f"- Fallback targets: {aggregate.get('fallback_count', 0)}",
    ]


def _lane_selection_findings(stage: dict[str, object] | None) -> list[str]:
    if stage is None:
        return []
    aggregate = _required_mapping(stage, "aggregate")
    return [
        "",
        "## Heading-Aware Lane Selection",
        "",
        f"- Nearest-lane mean FDE: {_meters(aggregate.get('nearest_lane_fde_m'))}",
        f"- Heading-aware mean FDE: {_meters(aggregate.get('heading_lane_fde_m'))}",
        "- Heading-aware improvement over nearest lane: "
        f"{_signed_meters(aggregate.get('heading_vs_nearest_fde_improvement_m'))}",
    ]


def _lane_continuation_findings(stage: dict[str, object] | None) -> list[str]:
    if stage is None:
        return []
    aggregate = _required_mapping(stage, "aggregate")
    return [
        "",
        "## Lane Continuation",
        "",
        f"- Evaluated continuation targets: {aggregate.get('evaluated_track_count', 0)}",
        f"- Improvements over nearest lane: {aggregate.get('improved_over_nearest_count', 0)}",
        f"- Regressions versus nearest lane: {aggregate.get('regressed_vs_nearest_count', 0)}",
        f"- Topology gaps: {aggregate.get('topology_gap_count', 0)}",
        "- Mean lane-link improvement over nearest lane: "
        f"{_signed_meters(aggregate.get('mean_lane_link_improvement_m'))}",
    ]


def _required_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping field: {key}")
    return value


def _required_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}")
    return value


def _meters(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f} m"


def _signed_meters(value: object) -> str:
    if value is None:
        return "n/a"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.3f} m"


def _format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(value)
    for unit in units:
        if amount < 1000 or unit == units[-1]:
            if unit == "B":
                return f"{int(amount)} {unit}"
            return f"{amount:.2f} {unit}"
        amount /= 1000
    return f"{value} B"


def _optional_bytes(value: object) -> str:
    if value is None:
        return "not available"
    return _format_bytes(int(value))


def _peak_rss_bytes() -> int | None:
    if resource is None:
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    return peak
