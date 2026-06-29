from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WAYMO_MOTION_VERSION = "waymo_open_dataset_motion_v_1_3_1"
DEFAULT_WAYMO_MOTION_SPLIT = "validation"
DEFAULT_WAYMO_MOTION_TOTAL_SHARDS = 150
DEFAULT_NEXT_SHARD_COUNT = 3

_SHARD_RE = re.compile(
    r"^(?P<split>[A-Za-z_]+)\.tfrecord-"
    r"(?P<index>\d{5})-of-(?P<total>\d{5})$"
)


@dataclass(frozen=True)
class WaymoShardPlanResult:
    """Files produced by a public-safe Waymo Motion shard expansion plan."""

    local_shard_count: int
    recommended_download_count: int
    output_path: Path
    json_output_path: Path | None


def generate_waymo_motion_shard_plan(
    input_path: str | Path,
    output_path: str | Path,
    json_output_path: str | Path | None = None,
    split: str = DEFAULT_WAYMO_MOTION_SPLIT,
    dataset_version: str = DEFAULT_WAYMO_MOTION_VERSION,
    total_shards: int = DEFAULT_WAYMO_MOTION_TOTAL_SHARDS,
    next_count: int = DEFAULT_NEXT_SHARD_COUNT,
) -> WaymoShardPlanResult:
    """Write a public-safe plan for expanding local Waymo Motion shard coverage."""

    payload = waymo_motion_shard_plan_payload(
        input_path=Path(input_path),
        split=split,
        dataset_version=dataset_version,
        total_shards=total_shards,
        next_count=next_count,
    )
    report = waymo_motion_shard_plan_markdown(payload)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")

    json_target = Path(json_output_path) if json_output_path else None
    if json_target is not None:
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return WaymoShardPlanResult(
        local_shard_count=int(payload["local_shard_count"]),
        recommended_download_count=int(payload["recommended_download_count"]),
        output_path=target,
        json_output_path=json_target,
    )


def waymo_motion_shard_plan_payload(
    input_path: Path,
    split: str,
    dataset_version: str,
    total_shards: int,
    next_count: int,
) -> dict[str, object]:
    """Return a deterministic, public-safe Waymo Motion shard plan."""

    if total_shards < 1:
        raise ValueError("total_shards must be at least 1.")
    if next_count < 0:
        raise ValueError("next_count must be non-negative.")

    local_shards = _local_shards(input_path=input_path, split=split)
    existing_indices = {int(row["index"]) for row in local_shards}
    next_indices = _next_missing_indices(
        existing_indices=existing_indices,
        total_shards=total_shards,
        next_count=next_count,
    )
    target_dir = input_path if input_path.is_dir() else input_path.parent
    recommended_downloads = [
        _download_row(
            index=index,
            split=split,
            dataset_version=dataset_version,
            total_shards=total_shards,
            target_dir=target_dir,
        )
        for index in next_indices
    ]
    stability_inputs = [
        str(row["path"]) for row in local_shards
    ] + [str(row["local_path"]) for row in recommended_downloads]

    return {
        "format": "scenariolens.waymo_motion_shard_plan.v1",
        "input_path": str(input_path),
        "input_exists": input_path.exists(),
        "split": split,
        "dataset_version": dataset_version,
        "total_shards": total_shards,
        "next_count": next_count,
        "local_shard_count": len(local_shards),
        "local_shards": local_shards,
        "local_coverage_percent": _coverage_percent(
            count=len(local_shards),
            total=total_shards,
        ),
        "recommended_download_count": len(recommended_downloads),
        "recommended_downloads": recommended_downloads,
        "download_commands": [
            str(row["gsutil_command"]) for row in recommended_downloads
        ],
        "cross_shard_stability_command": _stability_command(stability_inputs),
        "notes": _notes(input_path=input_path, local_shards=local_shards),
    }


def waymo_motion_shard_plan_markdown(payload: dict[str, object]) -> str:
    """Return Markdown for a Waymo Motion shard plan."""

    local_shards = _required_list(payload, "local_shards")
    downloads = _required_list(payload, "recommended_downloads")
    download_commands = _required_string_list(payload, "download_commands")
    stability_command = str(payload["cross_shard_stability_command"])
    notes = _required_string_list(payload, "notes")

    lines = [
        "# ScenarioLens Waymo Motion Shard Expansion Plan",
        "",
        "This report inventories local Waymo Motion validation shards and lists "
        "the next small downloads needed for an expanded cross-shard stability run. "
        "Raw Waymo files remain outside git.",
        "",
        "## Current Inventory",
        "",
        "| Field | Value |",
        "| --- | ---: |",
        f"| Input path | `{payload['input_path']}` |",
        f"| Input exists | {payload['input_exists']} |",
        f"| Split | `{payload['split']}` |",
        f"| Dataset version | `{payload['dataset_version']}` |",
        f"| Local shards | {payload['local_shard_count']} / {payload['total_shards']} |",
        f"| Local coverage | {_percent_text(payload['local_coverage_percent'])} |",
        "",
        "## Local Shards",
        "",
        "| Shard | Size | Path |",
        "| ---: | ---: | --- |",
    ]
    if local_shards:
        for row in local_shards:
            lines.append(
                f"| {row['index']} | {_bytes_text(row['size_bytes'])} | "
                f"`{row['path']}` |"
            )
    else:
        lines.append("| n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Recommended Next Downloads",
            "",
            "| Shard | GCS URI | Local Path |",
            "| ---: | --- | --- |",
        ]
    )
    if downloads:
        for row in downloads:
            lines.append(
                f"| {row['index']} | `{row['gcs_uri']}` | "
                f"`{row['local_path']}` |"
            )
    else:
        lines.append("| n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Download Commands",
            "",
            "```bash",
            *download_commands,
            "```",
            "",
            "If `gsutil` returns a 401, complete the official Waymo Open Dataset "
            "access flow and authenticate `gcloud` before rerunning the commands.",
            "",
            "## Cross-Shard Stability Command",
            "",
            "Run this after the recommended shard files exist locally:",
            "",
            "```bash",
            stability_command,
            "```",
            "",
            "## Notes",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in notes)
    return "\n".join(lines).rstrip() + "\n"


def _local_shards(input_path: Path, split: str) -> list[dict[str, object]]:
    paths: tuple[Path, ...]
    if input_path.is_dir():
        paths = tuple(sorted(path for path in input_path.iterdir() if path.is_file()))
    elif input_path.exists():
        paths = (input_path,)
    else:
        paths = ()

    rows: list[dict[str, object]] = []
    for path in paths:
        match = _SHARD_RE.match(path.name)
        if match is None or match.group("split") != split:
            continue
        rows.append(
            {
                "index": int(match.group("index")),
                "total": int(match.group("total")),
                "size_bytes": path.stat().st_size,
                "path": str(path),
            }
        )
    return sorted(rows, key=lambda row: int(row["index"]))


def _next_missing_indices(
    existing_indices: set[int],
    total_shards: int,
    next_count: int,
) -> tuple[int, ...]:
    if next_count == 0:
        return ()
    start = max(existing_indices) + 1 if existing_indices else 0
    indices: list[int] = []
    for candidate in range(start, total_shards):
        if candidate not in existing_indices:
            indices.append(candidate)
        if len(indices) >= next_count:
            break
    return tuple(indices)


def _download_row(
    index: int,
    split: str,
    dataset_version: str,
    total_shards: int,
    target_dir: Path,
) -> dict[str, object]:
    filename = _shard_filename(split=split, index=index, total_shards=total_shards)
    uri = (
        f"gs://{dataset_version}/uncompressed/scenario/"
        f"{split}/{filename}"
    )
    local_path = target_dir / filename
    return {
        "index": index,
        "gcs_uri": uri,
        "local_path": str(local_path),
        "gsutil_command": f"gsutil cp {uri} {target_dir}/",
    }


def _shard_filename(split: str, index: int, total_shards: int) -> str:
    return f"{split}.tfrecord-{index:05d}-of-{total_shards:05d}"


def _stability_command(input_paths: list[str]) -> str:
    lines = ["PYTHONPATH=src python3 -m scenariolens.cli failure-study-stability \\"]
    lines.extend(f"  --input {path} \\" for path in input_paths)
    lines.extend(
        [
            "  --output-dir data/processed/waymo_motion_failure_stability_cross_shard \\",
            "  --max-scenarios 25 \\",
            "  --window-size 25 \\",
            "  --top-tags 10 \\",
            "  --min-tag-slices 2 \\",
            "  --public-report docs/reports/waymo_motion_failure_stability_cross_shard.md",
        ]
    )
    return "\n".join(lines)


def _notes(input_path: Path, local_shards: list[dict[str, object]]) -> tuple[str, ...]:
    notes = [
        "This is a download and analysis plan, not a checked-in raw-data artifact.",
        "Use repeated `--input` paths for cross-shard stability so each shard is "
        "treated as its own comparison slice.",
    ]
    if not input_path.exists():
        notes.append("The input path does not exist yet.")
    if not local_shards:
        notes.append("No local shard filenames matched the expected Motion pattern.")
    return tuple(notes)


def _coverage_percent(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _required_list(mapping: dict[str, object], key: str) -> list[dict[str, object]]:
    value = mapping[key]
    if not isinstance(value, list):
        raise TypeError(f"waymo shard plan {key} must be a list")
    return value


def _required_string_list(mapping: dict[str, object], key: str) -> list[str]:
    value = mapping[key]
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"waymo shard plan {key} must be a list")
    return [str(item) for item in value]


def _percent_text(value: object) -> str:
    return f"{float(value) * 100:.2f}%"


def _bytes_text(value: object) -> str:
    size = float(value)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{int(value)} B"
