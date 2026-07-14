from __future__ import annotations

import json
import os
import re
import shutil
import sysconfig
from dataclasses import dataclass
from pathlib import Path

from scenariolens.dashboard import (
    DASHBOARD_FORMAT,
    DashboardScenarioSet,
    load_lane_selection_case_diagnostics,
    write_dashboard_data,
)
from scenariolens.ingest.waymo_motion import load_waymo_motion
from scenariolens.io import load_scenarios

EXPLORER_RUN_FORMAT = "scenariolens.explorer_run.v1"
EXPLORER_STATIC_FILES = ("index.html", "app.js", "styles.css")


@dataclass(frozen=True)
class ExplorerResult:
    """Artifacts produced for one run-local ScenarioLens Explorer."""

    ready: bool
    source_count: int
    scenario_count: int
    rendered_case_count: int
    scenario_ids: tuple[str, ...]
    explorer_dir: Path
    index_path: Path
    scenario_payload_path: Path
    run_payload_path: Path
    assets_dir: Path


def generate_run_explorer(
    input_paths: tuple[str | Path, ...],
    input_format: str,
    output_dir: str | Path,
    max_scenarios: int | None,
    limit: int,
    lane_selection_manifest_path: str | Path | None = None,
    static_dir: str | Path | None = None,
) -> ExplorerResult:
    """Generate ranked cases, trajectory assets, and static Explorer files."""

    if not input_paths:
        raise ValueError("At least one Explorer input is required.")
    if input_format not in {"native", "scenariolens-json"}:
        raise ValueError(f"Unsupported Explorer input format: {input_format}")
    if max_scenarios is not None and max_scenarios < 1:
        raise ValueError("max-scenarios must be at least 1 when provided.")
    if limit < 1:
        raise ValueError("Explorer case limit must be at least 1.")

    sources = tuple(Path(path) for path in input_paths)
    scenario_sets = tuple(
        _scenario_set(
            path=path,
            source_index=index,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )
        for index, path in enumerate(sources, start=1)
    )
    scenario_count = sum(len(item.scenarios) for item in scenario_sets)
    if scenario_count == 0:
        raise ValueError("Explorer inputs did not contain any scenarios.")

    target = Path(output_dir)
    explorer_dir = target / "explorer"
    assets_dir = target / "assets"
    explorer_dir.mkdir(parents=True, exist_ok=True)
    _copy_static_explorer(explorer_dir, static_dir=static_dir)

    diagnostics = load_lane_selection_case_diagnostics(
        lane_selection_manifest_path,
        report_path="../studies/lane_selection/report.md",
        debug_report_path="../studies/lane_selection/report.md",
    )
    scenario_payload_path = explorer_dir / "scenarios.json"
    payload = write_dashboard_data(
        scenario_sets=scenario_sets,
        output_path=scenario_payload_path,
        assets_dir=assets_dir,
        case_diagnostics=diagnostics,
        limit=min(limit, scenario_count),
    )
    scenario_ids = tuple(
        str(item["scenario_id"])
        for item in payload["scenarios"]
        if isinstance(item, dict) and "scenario_id" in item
    )
    run_payload_path = explorer_dir / "run.json"
    return ExplorerResult(
        ready=(
            payload.get("format") == DASHBOARD_FORMAT
            and len(scenario_ids) == int(payload.get("reported_count", 0))
            and all((assets_dir / f"{scenario_id}.svg").exists() for scenario_id in scenario_ids)
        ),
        source_count=len(sources),
        scenario_count=scenario_count,
        rendered_case_count=len(scenario_ids),
        scenario_ids=scenario_ids,
        explorer_dir=explorer_dir,
        index_path=explorer_dir / "index.html",
        scenario_payload_path=scenario_payload_path,
        run_payload_path=run_payload_path,
        assets_dir=assets_dir,
    )


def write_explorer_run_payload(
    run_manifest: dict[str, object],
    output_path: str | Path,
) -> dict[str, object]:
    """Write the public-safe run summary consumed by the static Explorer."""

    payload = explorer_run_payload(run_manifest)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def explorer_run_payload(run_manifest: dict[str, object]) -> dict[str, object]:
    """Convert a top-level run manifest into the Explorer run contract."""

    configuration = _mapping(run_manifest, "configuration")
    explorer = _mapping(run_manifest, "explorer")
    inputs = _list(run_manifest, "inputs")
    stages = _list(run_manifest, "stages")
    stage_rows = []
    reports = [
        {
            "report_id": "run",
            "label": "Run report",
            "description": "Top-level findings, provenance, and interpretation boundary.",
            "path": "../report.md",
        }
    ]
    for item in stages:
        if not isinstance(item, dict):
            continue
        report_path = "../" + str(item.get("report", ""))
        stage_rows.append(
            {
                "stage_id": item.get("stage_id"),
                "label": item.get("label"),
                "ready": bool(item.get("ready")),
                "scenario_count": item.get("scenario_count"),
                "evaluated_count": item.get("evaluated_count"),
                "duration_seconds": item.get("duration_seconds"),
                "aggregate": item.get("aggregate", {}),
                "report_path": report_path,
            }
        )
        reports.append(
            {
                "report_id": item.get("stage_id"),
                "label": item.get("label"),
                "description": _stage_description(str(item.get("stage_id", ""))),
                "path": report_path,
            }
        )

    return {
        "format": EXPLORER_RUN_FORMAT,
        "ready": bool(run_manifest.get("ready")),
        "mode": "local_run",
        "summary": {
            "scenariolens_version": run_manifest.get("scenariolens_version"),
            "source_count": run_manifest.get("source_count"),
            "scenario_count": run_manifest.get("scenario_count"),
            "rendered_case_count": explorer.get("reported_count"),
            "stage_count": run_manifest.get("stage_count"),
            "duration_seconds": run_manifest.get("duration_seconds"),
            "peak_rss_bytes": run_manifest.get("peak_rss_bytes"),
            "analysis_digest": run_manifest.get("analysis_digest"),
        },
        "configuration": {
            "input_format": configuration.get("input_format"),
            "max_scenarios_per_input": configuration.get("max_scenarios_per_input"),
            "top": configuration.get("top"),
        },
        "inputs": [
            {
                "source_index": item.get("source_index"),
                "source_name": item.get("source_name"),
                "size_bytes": item.get("size_bytes"),
                "sha256": item.get("sha256"),
            }
            for item in inputs
            if isinstance(item, dict)
        ],
        "stages": stage_rows,
        "reports": reports,
        "scope_note": run_manifest.get("scope_note"),
    }


def _scenario_set(
    path: Path,
    source_index: int,
    input_format: str,
    max_scenarios: int | None,
) -> DashboardScenarioSet:
    if input_format == "scenariolens-json":
        scenarios = load_scenarios(path)
        if max_scenarios is not None:
            scenarios = scenarios[:max_scenarios]
    else:
        scenarios = load_waymo_motion(path, max_scenarios=max_scenarios)
    slug = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_") or "source"
    return DashboardScenarioSet(
        dataset_id=f"source_{source_index}_{slug}",
        label=path.name,
        scenarios=tuple(scenarios),
    )


def _copy_static_explorer(
    output_dir: Path,
    static_dir: str | Path | None,
) -> None:
    source = _resolve_static_dir(static_dir)
    for name in EXPLORER_STATIC_FILES:
        shutil.copyfile(source / name, output_dir / name)


def _resolve_static_dir(static_dir: str | Path | None) -> Path:
    candidates: list[Path] = []
    if static_dir is not None:
        candidates.append(Path(static_dir))
    override = os.environ.get("SCENARIOLENS_EXPLORER_STATIC_DIR")
    if override:
        candidates.append(Path(override))
    candidates.extend(
        (
            Path(__file__).resolve().parents[2] / "docs" / "demo",
            Path(sysconfig.get_path("data")) / "share" / "scenariolens" / "explorer",
        )
    )
    for candidate in candidates:
        if all((candidate / name).is_file() for name in EXPLORER_STATIC_FILES):
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise RuntimeError(f"ScenarioLens Explorer static files were not found. Searched: {searched}")


def _mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping field: {key}")
    return value


def _list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}")
    return value


def _stage_description(stage_id: str) -> str:
    return {
        "baseline_comparison": "Constant-velocity and lane-aware baseline comparison.",
        "lane_selection": "Nearest-lane and heading-aware selector diagnostics.",
        "lane_continuation": "Linked-lane continuation improvements and regressions.",
    }.get(stage_id, "ScenarioLens analysis stage.")
