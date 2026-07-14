from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.run_bundle import RUN_BUNDLE_FORMAT

RUN_VALIDATION_FORMAT = "scenariolens.run_validation.v1"
DEFAULT_MAX_DURATION_SECONDS = 15 * 60
DEFAULT_MAX_PEAK_MEMORY_GB = 8.0


@dataclass(frozen=True)
class RunValidationResult:
    """Artifacts produced by a deterministic run-bundle validation."""

    ready: bool
    run_count: int
    check_count: int
    passed_count: int
    analysis_digest: str | None
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_run_validation(
    run_manifest_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    max_peak_memory_gb: float = DEFAULT_MAX_PEAK_MEMORY_GB,
    public_report_path: str | Path | None = None,
) -> RunValidationResult:
    """Validate repeated run bundles for readiness, determinism, and budget."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None
    payload = run_validation_payload(
        run_manifest_paths=tuple(Path(path) for path in run_manifest_paths),
        output_dir=target,
        max_duration_seconds=max_duration_seconds,
        max_peak_memory_gb=max_peak_memory_gb,
    )
    report = run_validation_markdown(payload)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    checks = _required_list(payload, "checks")
    return RunValidationResult(
        ready=bool(payload["ready"]),
        run_count=int(payload["run_count"]),
        check_count=len(checks),
        passed_count=sum(bool(check["passed"]) for check in checks),
        analysis_digest=_optional_string(payload.get("analysis_digest")),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def run_validation_payload(
    run_manifest_paths: tuple[Path, ...],
    output_dir: Path,
    max_duration_seconds: float,
    max_peak_memory_gb: float,
) -> dict[str, object]:
    if len(run_manifest_paths) < 2:
        raise ValueError("At least two run manifests are required for validation.")
    if max_duration_seconds <= 0:
        raise ValueError("max-duration-seconds must be greater than zero.")
    if max_peak_memory_gb <= 0:
        raise ValueError("max-peak-memory-gb must be greater than zero.")

    runs = [
        _run_summary(path, index=index)
        for index, path in enumerate(run_manifest_paths, start=1)
    ]
    digests = [str(run["analysis_digest"]) for run in runs]
    input_fingerprints = [str(run["input_fingerprint"]) for run in runs]
    scenario_counts = [int(run["scenario_count"]) for run in runs]
    source_counts = [int(run["source_count"]) for run in runs]
    stage_fingerprints = [str(run["stage_fingerprint"]) for run in runs]
    durations = [float(run["duration_seconds"]) for run in runs]
    peak_values = [run.get("peak_rss_bytes") for run in runs]
    max_peak_memory_bytes = int(max_peak_memory_gb * 1000**3)

    checks = [
        _check(
            "run_readiness",
            "Every run and stage is ready",
            all(bool(run["ready"]) and bool(run["all_stages_ready"]) for run in runs),
            f"{sum(bool(run['ready']) for run in runs)}/{len(runs)} top-level runs ready.",
        ),
        _check(
            "analysis_digest",
            "Analysis digests match",
            len(set(digests)) == 1,
            f"Observed {len(set(digests))} unique digest(s).",
        ),
        _check(
            "input_identity",
            "Input fingerprints match",
            len(set(input_fingerprints)) == 1,
            f"Observed {len(set(input_fingerprints))} unique input fingerprint(s).",
        ),
        _check(
            "scenario_scope",
            "Source and scenario counts match",
            len(set(scenario_counts)) == 1 and len(set(source_counts)) == 1,
            f"Scenario counts: {scenario_counts}; source counts: {source_counts}.",
        ),
        _check(
            "stage_scope",
            "Stable stage outputs match",
            len(set(stage_fingerprints)) == 1,
            f"Observed {len(set(stage_fingerprints))} stable stage fingerprint(s).",
        ),
        _check(
            "duration_budget",
            "Every run meets the duration budget",
            all(duration <= max_duration_seconds for duration in durations),
            f"Maximum {max(durations):.3f} s; budget {max_duration_seconds:.3f} s.",
        ),
        _check(
            "memory_budget",
            "Every run reports and meets the peak-memory budget",
            all(
                value is not None and int(value) <= max_peak_memory_bytes
                for value in peak_values
            ),
            f"Maximum {_max_memory_text(peak_values)}; budget {max_peak_memory_gb:.2f} GB.",
        ),
    ]
    ready = all(bool(check["passed"]) for check in checks)
    return {
        "format": RUN_VALIDATION_FORMAT,
        "ready": ready,
        "output_dir": str(output_dir),
        "run_count": len(runs),
        "analysis_digest": digests[0] if len(set(digests)) == 1 else None,
        "input_fingerprint": (
            input_fingerprints[0]
            if len(set(input_fingerprints)) == 1
            else None
        ),
        "configuration": {
            "max_duration_seconds": max_duration_seconds,
            "max_peak_memory_gb": max_peak_memory_gb,
            "max_peak_memory_bytes": max_peak_memory_bytes,
        },
        "aggregate": {
            "source_count": source_counts[0] if len(set(source_counts)) == 1 else None,
            "scenario_count": (
                scenario_counts[0] if len(set(scenario_counts)) == 1 else None
            ),
            "minimum_duration_seconds": round(min(durations), 3),
            "maximum_duration_seconds": round(max(durations), 3),
            "duration_range_seconds": round(max(durations) - min(durations), 3),
            "maximum_peak_rss_bytes": _max_peak_bytes(peak_values),
        },
        "runs": runs,
        "checks": checks,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
        "scope_note": (
            "This validation compares generated ScenarioLens analysis bundles. "
            "It verifies deterministic aggregate evidence and laptop execution "
            "budgets, not closed-loop autonomy safety or Waymo benchmark status."
        ),
    }


def run_validation_markdown(payload: dict[str, object]) -> str:
    configuration = _required_mapping(payload, "configuration")
    aggregate = _required_mapping(payload, "aggregate")
    runs = _required_list(payload, "runs")
    checks = _required_list(payload, "checks")
    lines = [
        "# ScenarioLens Run Reproducibility Validation",
        "",
        "This generated report validates independent executions of the "
        "ScenarioLens one-command analysis bundle.",
        "",
        "## Summary",
        "",
        f"- Ready: {'yes' if payload.get('ready') else 'no'}",
        f"- Runs compared: {payload.get('run_count')}",
        f"- Sources per run: {aggregate.get('source_count')}",
        f"- Scenarios per run: {aggregate.get('scenario_count')}",
        f"- Analysis digest: `{payload.get('analysis_digest') or 'mismatch'}`",
        f"- Maximum duration: {float(aggregate.get('maximum_duration_seconds', 0.0)):.3f} seconds",
        f"- Maximum peak memory: {_bytes_text(aggregate.get('maximum_peak_rss_bytes'))}",
        f"- Duration budget: {float(configuration.get('max_duration_seconds', 0.0)):.3f} seconds",
        f"- Peak-memory budget: {float(configuration.get('max_peak_memory_gb', 0.0)):.2f} GB",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        assert isinstance(check, dict)
        lines.append(
            f"| {check.get('label')} | {'pass' if check.get('passed') else 'fail'} | "
            f"{check.get('detail')} |"
        )

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Run | Ready | Sources | Scenarios | Stages | Duration | Peak memory | Digest |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in runs:
        assert isinstance(run, dict)
        lines.append(
            f"| {run.get('run_index')} | {'yes' if run.get('ready') else 'no'} | "
            f"{run.get('source_count')} | {run.get('scenario_count')} | "
            f"{run.get('stage_count')} | {float(run.get('duration_seconds', 0.0)):.3f} s | "
            f"{_bytes_text(run.get('peak_rss_bytes'))} | "
            f"`{str(run.get('analysis_digest'))[:12]}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            f"- {payload.get('scope_note')}",
            "- Volatile timestamps, output paths, and timings are excluded from "
            "the analysis digest; input identities, configuration, stage formats, "
            "counts, and aggregate metrics are included.",
            "- Raw Waymo records and per-scenario trajectories remain local and "
            "are not embedded in this report.",
            "",
        ]
    )
    return "\n".join(lines)


def _run_summary(path: Path, index: int) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"ScenarioLens run manifest does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != RUN_BUNDLE_FORMAT:
        raise ValueError(
            f"Expected run manifest format {RUN_BUNDLE_FORMAT}: {path}"
        )
    inputs = _required_list(payload, "inputs")
    stages = _required_list(payload, "stages")
    return {
        "run_index": index,
        "run_name": path.parent.name,
        "ready": bool(payload.get("ready")),
        "all_stages_ready": all(
            isinstance(stage, dict) and bool(stage.get("ready")) for stage in stages
        ),
        "source_count": int(payload.get("source_count", 0)),
        "scenario_count": int(payload.get("scenario_count", 0)),
        "stage_count": int(payload.get("stage_count", 0)),
        "duration_seconds": float(payload.get("duration_seconds", 0.0)),
        "peak_rss_bytes": payload.get("peak_rss_bytes"),
        "analysis_digest": str(payload.get("analysis_digest", "")),
        "input_fingerprint": _fingerprint(inputs),
        "stage_fingerprint": _fingerprint(
            [
                {
                    "stage_id": stage.get("stage_id"),
                    "format": stage.get("format"),
                    "ready": stage.get("ready"),
                    "scenario_count": stage.get("scenario_count"),
                    "evaluated_count": stage.get("evaluated_count"),
                    "aggregate": stage.get("aggregate"),
                }
                for stage in stages
                if isinstance(stage, dict)
            ]
        ),
    }


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _check(check_id: str, label: str, passed: bool, detail: str) -> dict[str, object]:
    return {
        "check_id": check_id,
        "label": label,
        "passed": passed,
        "detail": detail,
    }


def _max_peak_bytes(values: list[object]) -> int | None:
    present = [int(value) for value in values if value is not None]
    return max(present) if present else None


def _max_memory_text(values: list[object]) -> str:
    return _bytes_text(_max_peak_bytes(values))


def _bytes_text(value: object) -> str:
    if value is None:
        return "not available"
    return f"{int(value) / 1000**3:.3f} GB"


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


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
