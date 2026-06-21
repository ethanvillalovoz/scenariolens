from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

WAYMO_OPEN_DATASET_URL = "https://waymo.com/open/"
WAYMO_OPEN_CHALLENGES_URL = "https://waymo.com/open/challenges/"
OPTIONAL_PACKAGE = "waymo_open_dataset"


@dataclass(frozen=True)
class WaymoMotionAdapterStatus:
    """Current readiness state for the optional Waymo Motion adapter."""

    adapter_name: str
    implemented: bool
    optional_package: str
    optional_package_available: bool
    dataset_url: str
    challenges_url: str
    message: str


def adapter_status() -> WaymoMotionAdapterStatus:
    package_available = find_spec(OPTIONAL_PACKAGE) is not None
    return WaymoMotionAdapterStatus(
        adapter_name="waymo_motion",
        implemented=False,
        optional_package=OPTIONAL_PACKAGE,
        optional_package_available=package_available,
        dataset_url=WAYMO_OPEN_DATASET_URL,
        challenges_url=WAYMO_OPEN_CHALLENGES_URL,
        message=(
            "Waymo Motion ingestion is a planned optional adapter. Use "
            "`ingest-csv` or ScenarioLens JSON until the Waymo parser is added."
        ),
    )


def ingest_waymo_motion(
    input_path: str | Path,
    output_path: str | Path,
    max_scenarios: int | None = None,
) -> None:
    """Placeholder for future Waymo Motion Dataset conversion.

    The real implementation should convert a tiny Motion Dataset slice into
    ScenarioLens JSON without making Waymo dependencies mandatory for the core
    package.
    """

    status = adapter_status()
    raise NotImplementedError(
        f"{status.message} Requested input={input_path}, output={output_path}, "
        f"max_scenarios={max_scenarios}."
    )

