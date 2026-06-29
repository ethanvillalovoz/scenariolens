from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    failure_study_payload,
    load_failure_study_input,
)
from scenariolens.report import ranked_scores
from scenariolens.schema import Scenario

FAILURE_STABILITY_FORMAT = "scenariolens.failure_stability.v1"


@dataclass(frozen=True)
class FailureStabilityResult:
    """Files produced by a public-safe failure distribution stability study."""

    ready: bool
    scenario_count: int
    slice_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_failure_stability_study(
    input_paths: tuple[str | Path, ...],
    output_dir: str | Path,
    max_scenarios: int | None = 75,
    window_size: int | None = 25,
    top_tags: int = 10,
    min_tag_slices: int = 2,
    input_format: str = "native",
    public_report_path: str | Path | None = None,
) -> FailureStabilityResult:
    """Compare baseline failure distributions across inputs or windows."""

    if not input_paths:
        raise ValueError("At least one input path is required for stability analysis.")
    if input_format not in FAILURE_STUDY_INPUT_FORMATS:
        raise ValueError(
            "Unsupported failure-study input format: "
            f"{input_format}. Expected one of: {', '.join(FAILURE_STUDY_INPUT_FORMATS)}"
        )
    if window_size is not None and window_size < 1:
        raise ValueError("window_size must be at least 1 when provided.")
    if top_tags < 1:
        raise ValueError("top_tags must be at least 1.")
    if min_tag_slices < 1:
        raise ValueError("min_tag_slices must be at least 1.")

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = failure_stability_payload(
        input_paths=tuple(Path(path) for path in input_paths),
        output_dir=target,
        input_format=input_format,
        max_scenarios=max_scenarios,
        window_size=window_size,
        top_tags=top_tags,
        min_tag_slices=min_tag_slices,
    )
    report = failure_stability_markdown(payload)

    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    return FailureStabilityResult(
        ready=bool(payload["ready"]),
        scenario_count=int(payload["scenario_count"]),
        slice_count=int(payload["slice_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def failure_stability_payload(
    input_paths: tuple[Path, ...],
    output_dir: Path,
    input_format: str,
    max_scenarios: int | None,
    window_size: int | None,
    top_tags: int,
    min_tag_slices: int,
) -> dict[str, object]:
    """Return a deterministic public-safe stability-study manifest."""

    sources: list[dict[str, object]] = []
    slice_payloads: list[dict[str, object]] = []
    slice_summaries: list[dict[str, object]] = []
    ready = True

    for input_index, source in enumerate(input_paths, start=1):
        input_ready, preflight, scenarios = load_failure_study_input(
            source=source,
            input_format=input_format,
            max_scenarios=max_scenarios,
        )
        if not input_ready:
            ready = False
            sources.append(
                {
                    "input_path": str(source),
                    "ready": False,
                    "scenario_count": 0,
                    "preflight": preflight or {},
                    "slices": [],
                }
            )
            continue

        windows = _scenario_windows(
            scenarios=scenarios,
            input_path=source,
            input_index=input_index,
            window_size=window_size,
        )
        source_slice_names: list[str] = []
        for window in windows:
            scores = ranked_scores(window.scenarios)
            study_payload = failure_study_payload(
                input_path=Path(f"{source}#{window.name}"),
                output_dir=output_dir / "slices" / window.name,
                input_format=input_format,
                max_scenarios=len(window.scenarios),
                top=1,
                min_tag_count=1,
                ready=True,
                preflight=preflight,
                scores=scores,
            )
            slice_payloads.append(study_payload)
            summary = _slice_summary(
                study_payload=study_payload,
                source=source,
                window=window,
            )
            slice_summaries.append(summary)
            source_slice_names.append(window.name)

        sources.append(
            {
                "input_path": str(source),
                "ready": True,
                "scenario_count": len(scenarios),
                "preflight": preflight or {},
                "slices": source_slice_names,
            }
        )

    tag_stability = _tag_stability(
        slice_payloads=slice_payloads,
        slice_summaries=slice_summaries,
        min_tag_slices=min_tag_slices,
        top_tags=top_tags,
    )
    stability = _stability_summary(slice_summaries, tag_stability)
    return {
        "format": FAILURE_STABILITY_FORMAT,
        "input_paths": [str(path) for path in input_paths],
        "output_dir": str(output_dir),
        "input_format": input_format,
        "max_scenarios_per_input": max_scenarios,
        "window_size": window_size,
        "top_tags": top_tags,
        "min_tag_slices": min_tag_slices,
        "ready": ready,
        "source_count": len(input_paths),
        "slice_count": len(slice_summaries),
        "scenario_count": sum(int(row["scenario_count"]) for row in slice_summaries),
        "evaluated_target_total": sum(
            int(row["evaluated_target_total"]) for row in slice_summaries
        ),
        "comparison_mode": _comparison_mode(
            source_count=len(input_paths),
            slice_count=len(slice_summaries),
        ),
        "sources": sources,
        "stability": stability,
        "slice_summaries": slice_summaries,
        "tag_stability": tag_stability,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
        },
    }


def failure_stability_markdown(payload: dict[str, object]) -> str:
    """Return Markdown report from a stability-study payload."""

    stability = _required_mapping(payload, "stability")
    slice_summaries = _required_list(payload, "slice_summaries")
    tag_stability = _required_list(payload, "tag_stability")

    lines = [
        "# ScenarioLens Failure Distribution Stability Study",
        "",
        "This report compares public-safe aggregate baseline-failure statistics "
        "across real-data slices. Raw Waymo files and per-scenario derived "
        "outputs remain outside git.",
        "",
        "## Run Scope",
        "",
        f"- Inputs: {', '.join(f'`{path}`' for path in payload['input_paths'])}",
        f"- Input format: `{payload['input_format']}`",
        f"- Comparison mode: {payload['comparison_mode']}",
        f"- Ready for analysis: {payload['ready']}",
        f"- Slices compared: {payload['slice_count']}",
        f"- Scenarios analyzed: {payload['scenario_count']}",
        f"- Evaluated baseline targets: {payload['evaluated_target_total']}",
        f"- Max scenarios per input: {payload['max_scenarios_per_input']}",
        f"- Window size: {payload['window_size']}",
        "- Raw scenario data committed: no",
        "",
        "## Executive Findings",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Mean FDE min / max / range | {_range_text(stability, 'fde')} |",
        f"| Miss-rate min / max / range | {_percent_range_text(stability, 'miss_rate')} |",
        f"| Highest mean-FDE slice | {_slice_name_text(stability, 'highest_fde_slice')} |",
        f"| Lowest mean-FDE slice | {_slice_name_text(stability, 'lowest_fde_slice')} |",
        f"| Most variable tag | {_most_variable_tag_text(tag_stability)} |",
        "",
    ]

    if not payload["ready"]:
        lines.extend(
            [
                "## Next Action",
                "",
                "Fix the failing input path or use an ingestable ScenarioLens JSON "
                "file, then rerun `failure-study-stability`.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "## Slice Distribution",
            "",
            "| Slice | Scenarios | Targets | Mean ADE | Mean FDE | "
            "Miss Rate | Top FDE Tag | Hardest Scenario |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in slice_summaries:
        lines.append(
            f"| `{row['name']}` | {row['scenario_count']} | "
            f"{row['evaluated_target_total']} | {_meter_text(row['mean_ade_m'])} | "
            f"{_meter_text(row['mean_fde_m'])} | "
            f"{_percent_text(row['weighted_miss_rate'])} | "
            f"{_tag_text(row['top_tag'])} | {_scenario_text(row)} |"
        )

    lines.extend(
        [
            "",
            "## Tag Stability",
            "",
            "| Tag | Slices | Scenarios | Targets | Mean FDE | "
            "FDE Range | Miss-Rate Range | Highest FDE Slice |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    if tag_stability:
        for row in tag_stability:
            lines.append(
                f"| `{row['tag']}` | {row['slice_count']} | "
                f"{row['scenario_count']} | {row['evaluated_target_total']} | "
                f"{_meter_text(row['mean_fde_m'])} | "
                f"{_meter_text(row['fde_range_m'])} | "
                f"{_percent_text(row['miss_rate_range'])} | "
                f"`{row['highest_fde_slice']}` |"
            )
    else:
        lines.append("| n/a | 0 | 0 | 0 | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Hardest Slice Representatives",
            "",
            "| Slice | Scenario | FDE | Miss Rate | Tags |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in slice_summaries:
        lines.append(
            f"| `{row['name']}` | {_scenario_text(row)} | "
            f"{_optional_meter_text(row['hardest_fde_m'])} | "
            f"{_optional_percent_text(row['hardest_miss_rate'])} | "
            f"{_tags_text(row['hardest_tags'])} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a distribution screen, not a benchmark claim.",
            "- Large FDE range across slices means the constant-velocity baseline "
            "fails unevenly across sampled scenario families.",
            _analysis_scope_note(payload),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _analysis_scope_note(payload: dict[str, object]) -> str:
    if int(payload["source_count"]) > 1:
        return (
            "- This run uses repeated `--input` values, so each downloaded shard "
            "is treated as its own cross-input comparison slice."
        )
    return (
        "- With one local shard, the current report compares contiguous "
        "scenario windows; with more downloaded shards, rerun the same "
        "command with multiple `--input` values for true cross-shard "
        "stability."
    )


@dataclass(frozen=True)
class _ScenarioWindow:
    name: str
    source_input: str
    window_index: int
    start_index: int
    end_index: int
    scenarios: tuple[Scenario, ...]


def _scenario_windows(
    scenarios: tuple[Scenario, ...],
    input_path: Path,
    input_index: int,
    window_size: int | None,
) -> tuple[_ScenarioWindow, ...]:
    if not scenarios:
        return ()
    if window_size is None or window_size >= len(scenarios):
        return (
            _ScenarioWindow(
                name=f"input_{input_index:02d}",
                source_input=str(input_path),
                window_index=1,
                start_index=1,
                end_index=len(scenarios),
                scenarios=scenarios,
            ),
        )

    windows: list[_ScenarioWindow] = []
    for window_index, start in enumerate(range(0, len(scenarios), window_size), start=1):
        end = min(start + window_size, len(scenarios))
        windows.append(
            _ScenarioWindow(
                name=(
                    f"input_{input_index:02d}_"
                    f"window_{start + 1:03d}_{end:03d}"
                ),
                source_input=str(input_path),
                window_index=window_index,
                start_index=start + 1,
                end_index=end,
                scenarios=scenarios[start:end],
            )
        )
    return tuple(windows)


def _slice_summary(
    study_payload: dict[str, object],
    source: Path,
    window: _ScenarioWindow,
) -> dict[str, object]:
    aggregate = _required_mapping(study_payload, "aggregate")
    baseline = _required_mapping(aggregate, "baseline")
    score_summary = _required_mapping(aggregate, "score")
    tag_failures = _required_list(study_payload, "tag_failures")
    hardest = _required_list(study_payload, "hardest_scenarios")
    top_tag = tag_failures[0] if tag_failures else {}
    hardest_row = hardest[0] if hardest else {}
    return {
        "name": window.name,
        "source_input": str(source),
        "window_index": window.window_index,
        "scenario_start_index": window.start_index,
        "scenario_end_index": window.end_index,
        "scenario_count": study_payload["scenario_count"],
        "evaluated_target_total": baseline["evaluated_target_total"],
        "mean_interaction_score": score_summary["mean"],
        "mean_ade_m": baseline["mean_ade_m"],
        "mean_fde_m": baseline["mean_fde_m"],
        "max_fde_m": baseline["max_fde_m"],
        "weighted_miss_rate": baseline["weighted_miss_rate"],
        "top_tag": top_tag.get("tag"),
        "top_tag_mean_fde_m": top_tag.get("mean_fde_m"),
        "hardest_scenario_id": hardest_row.get("scenario_id"),
        "hardest_fde_m": hardest_row.get("baseline_fde_m"),
        "hardest_miss_rate": hardest_row.get("baseline_miss_rate"),
        "hardest_tags": hardest_row.get("tags", []),
    }


def _tag_stability(
    slice_payloads: list[dict[str, object]],
    slice_summaries: list[dict[str, object]],
    min_tag_slices: int,
    top_tags: int,
) -> list[dict[str, object]]:
    by_tag: dict[str, list[tuple[dict[str, object], dict[str, object]]]] = {}
    for study_payload, slice_summary in zip(slice_payloads, slice_summaries):
        for row in _required_list(study_payload, "tag_failures"):
            tag = str(row["tag"])
            by_tag.setdefault(tag, []).append((slice_summary, row))

    rows: list[dict[str, object]] = []
    for tag, group in by_tag.items():
        if len(group) < min_tag_slices:
            continue
        fde_values = tuple(float(row["mean_fde_m"]) for _, row in group)
        miss_values = tuple(float(row["weighted_miss_rate"]) for _, row in group)
        highest_slice, _ = max(group, key=lambda item: float(item[1]["mean_fde_m"]))
        rows.append(
            {
                "tag": tag,
                "slice_count": len(group),
                "scenario_count": sum(int(row["scenario_count"]) for _, row in group),
                "evaluated_target_total": sum(
                    int(row["evaluated_target_total"]) for _, row in group
                ),
                "mean_fde_m": round(_mean(fde_values), 3),
                "min_fde_m": round(min(fde_values), 3),
                "max_fde_m": round(max(fde_values), 3),
                "fde_range_m": round(max(fde_values) - min(fde_values), 3),
                "mean_miss_rate": round(_mean(miss_values), 4),
                "miss_rate_range": round(max(miss_values) - min(miss_values), 4),
                "highest_fde_slice": highest_slice["name"],
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            -float(row["fde_range_m"]),
            -float(row["mean_fde_m"]),
            str(row["tag"]),
        ),
    )[:top_tags]


def _stability_summary(
    slice_summaries: list[dict[str, object]],
    tag_stability: list[dict[str, object]],
) -> dict[str, object]:
    scored = tuple(
        row for row in slice_summaries if int(row["evaluated_target_total"]) > 0
    )
    fde_values = tuple(float(row["mean_fde_m"]) for row in scored)
    miss_values = tuple(float(row["weighted_miss_rate"]) for row in scored)
    highest_fde = max(scored, key=lambda row: float(row["mean_fde_m"]), default=None)
    lowest_fde = min(scored, key=lambda row: float(row["mean_fde_m"]), default=None)
    return {
        "comparison_ready": len(scored) >= 2,
        "fde_min_m": round(min(fde_values), 3) if fde_values else None,
        "fde_max_m": round(max(fde_values), 3) if fde_values else None,
        "fde_range_m": (
            round(max(fde_values) - min(fde_values), 3) if fde_values else None
        ),
        "miss_rate_min": round(min(miss_values), 4) if miss_values else None,
        "miss_rate_max": round(max(miss_values), 4) if miss_values else None,
        "miss_rate_range": (
            round(max(miss_values) - min(miss_values), 4) if miss_values else None
        ),
        "highest_fde_slice": None if highest_fde is None else highest_fde["name"],
        "lowest_fde_slice": None if lowest_fde is None else lowest_fde["name"],
        "most_variable_tag": None if not tag_stability else tag_stability[0]["tag"],
    }


def _comparison_mode(source_count: int, slice_count: int) -> str:
    if source_count > 1 and slice_count > source_count:
        return "cross-input windowed comparison"
    if source_count > 1:
        return "cross-input comparison"
    if slice_count > 1:
        return "single-input windowed comparison"
    return "single-input summary"


def _required_mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping[key]
    if not isinstance(value, dict):
        raise TypeError(f"failure stability {key} must be a dictionary")
    return value


def _required_list(mapping: dict[str, object], key: str) -> list[dict[str, object]]:
    value = mapping[key]
    if not isinstance(value, list):
        raise TypeError(f"failure stability {key} must be a list")
    return value


def _range_text(summary: dict[str, object], prefix: str) -> str:
    min_value = summary.get(f"{prefix}_min_m")
    max_value = summary.get(f"{prefix}_max_m")
    range_value = summary.get(f"{prefix}_range_m")
    if min_value is None or max_value is None or range_value is None:
        return "n/a"
    return (
        f"{_float_text(min_value)} m / {_float_text(max_value)} m / "
        f"{_float_text(range_value)} m"
    )


def _percent_range_text(summary: dict[str, object], prefix: str) -> str:
    min_value = summary.get(f"{prefix}_min")
    max_value = summary.get(f"{prefix}_max")
    range_value = summary.get(f"{prefix}_range")
    if min_value is None or max_value is None or range_value is None:
        return "n/a"
    return (
        f"{_percent_text(min_value)} / {_percent_text(max_value)} / "
        f"{_percent_text(range_value)}"
    )


def _slice_name_text(summary: dict[str, object], key: str) -> str:
    value = summary.get(key)
    return "n/a" if value is None else f"`{value}`"


def _most_variable_tag_text(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "n/a"
    row = rows[0]
    return f"`{row['tag']}` ({_meter_text(row['fde_range_m'])} FDE range)"


def _scenario_text(row: dict[str, object]) -> str:
    scenario_id = row.get("hardest_scenario_id")
    return "n/a" if scenario_id is None else f"`{scenario_id}`"


def _tag_text(value: object) -> str:
    return "n/a" if value is None else f"`{value}`"


def _tags_text(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "n/a"
    return ", ".join(f"`{tag}`" for tag in value)


def _meter_text(value: object) -> str:
    return f"{float(value):.2f} m"


def _optional_meter_text(value: object) -> str:
    if value is None:
        return "n/a"
    return _meter_text(value)


def _percent_text(value: object) -> str:
    return f"{float(value) * 100:.2f}%"


def _optional_percent_text(value: object) -> str:
    if value is None:
        return "n/a"
    return _percent_text(value)


def _float_text(value: object) -> str:
    return f"{float(value):.2f}"


def _mean(values: tuple[float, ...]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
