from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    inspect_waymo_motion_slice,
    load_waymo_motion,
    waymo_motion_slice_ready,
)
from scenariolens.io import save_scenarios
from scenariolens.report import markdown_report, ranked_scores, score_reasons
from scenariolens.visualize import scenario_svg

VALIDATION_FORMAT = "scenariolens.waymo_motion_validation.v1"


@dataclass(frozen=True)
class WaymoMotionValidationResult:
    """Files produced by a local Waymo Motion validation run."""

    ready: bool
    scenario_count: int
    reported_count: int
    output_dir: Path
    preflight_path: Path
    manifest_path: Path
    summary_path: Path
    scenarios_path: Path | None
    report_path: Path | None
    assets_dir: Path | None


def validate_waymo_motion_slice(
    input_path: str | Path,
    output_dir: str | Path,
    max_scenarios: int | None = 25,
    top: int = 5,
) -> WaymoMotionValidationResult:
    """Preflight, ingest, score, report, and render a local Waymo Motion slice."""

    source = Path(input_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    preflight = inspect_waymo_motion_slice(source)
    preflight_path = target / "preflight.json"
    _write_json(preflight_path, asdict(preflight))

    if not waymo_motion_slice_ready(preflight):
        manifest = _manifest(
            input_path=source,
            output_dir=target,
            max_scenarios=max_scenarios,
            top=top,
            ready=False,
            preflight=preflight,
            scenarios=(),
            outputs={"preflight": preflight_path.name},
        )
        manifest_path = target / "manifest.json"
        summary_path = target / "README.md"
        _write_json(manifest_path, manifest)
        summary_path.write_text(_summary_markdown(manifest), encoding="utf-8")
        return WaymoMotionValidationResult(
            ready=False,
            scenario_count=0,
            reported_count=0,
            output_dir=target,
            preflight_path=preflight_path,
            manifest_path=manifest_path,
            summary_path=summary_path,
            scenarios_path=None,
            report_path=None,
            assets_dir=None,
        )

    scenarios = load_waymo_motion(source, max_scenarios=max_scenarios)
    scenarios_path = target / "scenarios.json"
    report_path = target / "report.md"
    assets_dir = target / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    save_scenarios(scenarios_path, scenarios)
    report_path.write_text(markdown_report(scenarios, limit=top), encoding="utf-8")

    top_scores = ranked_scores(scenarios)[:top]
    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    for score in top_scores:
        scenario = scenario_by_id[score.scenario_id]
        (assets_dir / f"{score.scenario_id}.svg").write_text(
            scenario_svg(scenario),
            encoding="utf-8",
        )

    manifest = _manifest(
        input_path=source,
        output_dir=target,
        max_scenarios=max_scenarios,
        top=top,
        ready=True,
        preflight=preflight,
        scenarios=scenarios,
        outputs={
            "preflight": preflight_path.name,
            "scenarios": scenarios_path.name,
            "report": report_path.name,
            "assets_dir": assets_dir.name,
        },
    )
    manifest_path = target / "manifest.json"
    summary_path = target / "README.md"
    _write_json(manifest_path, manifest)
    summary_path.write_text(_summary_markdown(manifest), encoding="utf-8")

    return WaymoMotionValidationResult(
        ready=True,
        scenario_count=len(scenarios),
        reported_count=len(top_scores),
        output_dir=target,
        preflight_path=preflight_path,
        manifest_path=manifest_path,
        summary_path=summary_path,
        scenarios_path=scenarios_path,
        report_path=report_path,
        assets_dir=assets_dir,
    )


def _manifest(
    input_path: Path,
    output_dir: Path,
    max_scenarios: int | None,
    top: int,
    ready: bool,
    preflight,
    scenarios,
    outputs: dict[str, str],
) -> dict[str, object]:
    scores = ranked_scores(tuple(scenarios))[:top] if scenarios else ()
    return {
        "format": VALIDATION_FORMAT,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "max_scenarios": max_scenarios,
        "top": top,
        "ready": ready,
        "scenario_count": len(scenarios),
        "reported_count": len(scores),
        "preflight": asdict(preflight),
        "outputs": outputs,
        "top_scenarios": [
            {
                "rank": rank,
                "scenario_id": score.scenario_id,
                "score": round(score.interaction_score, 3),
                "tags": list(score.tags),
                "reasons": list(score_reasons(score)),
            }
            for rank, score in enumerate(scores, start=1)
        ],
    }


def _summary_markdown(manifest: dict[str, object]) -> str:
    preflight = manifest["preflight"]
    if not isinstance(preflight, dict):
        raise TypeError("manifest preflight must be a dictionary")
    outputs = manifest["outputs"]
    if not isinstance(outputs, dict):
        raise TypeError("manifest outputs must be a dictionary")
    top_scenarios = manifest["top_scenarios"]
    if not isinstance(top_scenarios, list):
        raise TypeError("manifest top_scenarios must be a list")

    lines = [
        "# Waymo Motion Slice Validation",
        "",
        f"- Input: `{manifest['input_path']}`",
        f"- Ready for ingestion: {manifest['ready']}",
        f"- Files scanned: {preflight['file_count']}",
        f"- Supported files: {preflight['supported_file_count']}",
        f"- Scenario count: {manifest['scenario_count']}",
        f"- Reported top scenarios: {manifest['reported_count']}",
        "",
        "## Outputs",
        "",
    ]
    for label, path in outputs.items():
        lines.append(f"- {label}: `{path}`")

    notes = preflight.get("notes", ())
    if notes:
        lines.extend(["", "## Preflight Notes", ""])
        for note in notes:
            lines.append(f"- {note}")

    if top_scenarios:
        lines.extend(["", "## Top Scenarios", ""])
        lines.extend(["| Rank | Scenario | Score | Why |", "| ---: | --- | ---: | --- |"])
        for scenario in top_scenarios:
            reasons = scenario.get("reasons", [])
            reason = reasons[0] if reasons else "included for review"
            lines.append(
                f"| {scenario['rank']} | `{scenario['scenario_id']}` | "
                f"{scenario['score']:.3f} | {reason} |"
            )
    else:
        lines.extend(
            [
                "",
                "## Next Action",
                "",
                "Fix the input path or optional dependencies, then rerun the validation command.",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
