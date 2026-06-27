from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from scenariolens.ingest.waymo_motion import (
    WAYMO_OPEN_DATASET_URL,
    WaymoMotionSliceReport,
    inspect_waymo_motion_slice,
    native_motion_format_label,
    waymo_motion_slice_ready,
)

DEFAULT_WAYMO_MOTION_INPUT = Path("data/raw/waymo/motion/validation")


@dataclass(frozen=True)
class WaymoMotionCandidateFile:
    """Potential raw Waymo Motion file found outside the configured input path."""

    path: str
    suffix: str
    size_bytes: int


@dataclass(frozen=True)
class WaymoMotionTooling:
    """Local tools and optional Python packages used by native Motion ingestion."""

    gcloud_path: str | None
    gsutil_path: str | None
    waymo_open_dataset_available: bool
    tensorflow_available: bool


@dataclass(frozen=True)
class WaymoMotionReadiness:
    """End-to-end readiness snapshot for a local Waymo Motion slice."""

    input_path: str
    ready: bool
    preflight: WaymoMotionSliceReport
    tooling: WaymoMotionTooling
    searched_roots: tuple[str, ...]
    candidate_files: tuple[WaymoMotionCandidateFile, ...]
    next_actions: tuple[str, ...]


def inspect_waymo_motion_readiness(
    input_path: str | Path = DEFAULT_WAYMO_MOTION_INPUT,
    *,
    search_common_locations: bool = True,
    candidate_roots: tuple[str | Path, ...] | None = None,
    max_depth: int = 3,
    max_candidates: int = 8,
) -> WaymoMotionReadiness:
    """Inspect local data, optional packages, cloud tooling, and likely downloads."""

    source = Path(input_path)
    preflight = inspect_waymo_motion_slice(source)
    tooling = WaymoMotionTooling(
        gcloud_path=shutil.which("gcloud"),
        gsutil_path=shutil.which("gsutil"),
        waymo_open_dataset_available=preflight.optional_package_available,
        tensorflow_available=preflight.tensorflow_available,
    )

    ready = waymo_motion_slice_ready(preflight)
    roots = () if ready else _candidate_roots(candidate_roots, search_common_locations)
    candidates = (
        ()
        if ready
        else _find_candidate_files(
            roots=roots,
            input_path=source,
            max_depth=max_depth,
            max_candidates=max_candidates,
        )
    )

    return WaymoMotionReadiness(
        input_path=str(source),
        ready=ready,
        preflight=preflight,
        tooling=tooling,
        searched_roots=tuple(str(root) for root in roots),
        candidate_files=candidates,
        next_actions=_next_actions(
            source=source,
            preflight=preflight,
            ready=ready,
            tooling=tooling,
            candidates=candidates,
        ),
    )


def _candidate_roots(
    candidate_roots: tuple[str | Path, ...] | None,
    search_common_locations: bool,
) -> tuple[Path, ...]:
    if candidate_roots is not None:
        return tuple(Path(root) for root in candidate_roots)
    if not search_common_locations:
        return ()
    home = Path.home()
    return tuple(
        root
        for root in (
            home / "Downloads",
            home / "Desktop",
        )
        if root.exists()
    )


def _find_candidate_files(
    roots: tuple[Path, ...],
    input_path: Path,
    max_depth: int,
    max_candidates: int,
) -> tuple[WaymoMotionCandidateFile, ...]:
    candidates: list[WaymoMotionCandidateFile] = []
    resolved_input = input_path.resolve() if input_path.exists() else None

    for root in roots:
        if not root.exists():
            continue
        for file_path in _walk_files(root, max_depth=max_depth):
            format_label = native_motion_format_label(file_path)
            if format_label is None:
                continue
            if resolved_input is not None and _is_under(file_path, resolved_input):
                continue
            candidates.append(
                WaymoMotionCandidateFile(
                    path=str(file_path),
                    suffix=format_label,
                    size_bytes=file_path.stat().st_size,
                )
            )
            if len(candidates) >= max_candidates:
                return tuple(candidates)
    return tuple(candidates)


def _walk_files(root: Path, max_depth: int) -> tuple[Path, ...]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        try:
            depth = len(current.relative_to(root).parts)
        except ValueError:
            depth = 0
        if depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith(".")]
        files.extend(current / filename for filename in filenames)
    return tuple(sorted(files))


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def _next_actions(
    source: Path,
    preflight: WaymoMotionSliceReport,
    ready: bool,
    tooling: WaymoMotionTooling,
    candidates: tuple[WaymoMotionCandidateFile, ...],
) -> tuple[str, ...]:
    if ready:
        return (
            "Run `waymo-motion-validate` against this input path to generate "
            "the ScenarioLens JSON, ranked report, and SVG gallery.",
        )

    actions: list[str] = []
    if not preflight.exists:
        actions.append(f"Create `{source}` or pass `--input` to the folder you downloaded.")

    if preflight.supported_file_count == 0:
        if candidates:
            actions.append(
                "Copy or move one candidate file into the configured input folder: "
                f"`{candidates[0].path}`."
            )
        else:
            actions.append(
                "Download one Waymo Motion validation shard from "
                f"{WAYMO_OPEN_DATASET_URL} into `{source}`."
            )

    if not tooling.gcloud_path and not tooling.gsutil_path:
        actions.append(
            "Install Google Cloud SDK only if you want command-line `gs://` downloads; "
            "manual browser downloads also work."
        )

    if not actions:
        actions.append("Inspect the preflight notes, fix the input path, and rerun doctor.")
    return tuple(actions)
