from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

PUBLIC_SURFACE_CHECK_FORMAT = "scenariolens.public_surface_check.v1"


@dataclass(frozen=True)
class PublicSurfaceCheckResult:
    """Files produced by a public-surface check run."""

    ready: bool
    check_count: int
    passed_count: int
    failed_count: int
    warning_count: int
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None


def generate_public_surface_check(
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
    repo_root: str | Path = ".",
) -> PublicSurfaceCheckResult:
    """Generate a CI-safe public surface readiness packet."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None

    payload = public_surface_check_payload(repo_root=repo_root)
    report = public_surface_check_markdown(payload)
    _write_json(manifest_path, payload)
    report_path.write_text(report, encoding="utf-8")

    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        copied_report_path.write_text(report, encoding="utf-8")

    aggregate = payload["aggregate"]
    return PublicSurfaceCheckResult(
        ready=bool(payload["ready"]),
        check_count=int(aggregate["check_count"]),
        passed_count=int(aggregate["passed_count"]),
        failed_count=int(aggregate["failed_count"]),
        warning_count=int(aggregate["warning_count"]),
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
    )


def public_surface_check_payload(repo_root: str | Path = ".") -> dict[str, object]:
    """Return public-surface readiness checks for the current repository."""

    root = Path(repo_root)
    checks = [
        _evidence_index_check(root),
        _demo_payload_contract_check(root),
        _link_integrity_check(root),
        _demo_asset_check(root),
        _raw_data_boundary_check(root),
        _ci_surface_check(root),
        _public_safety_language_check(root),
    ]
    failed = [check for check in checks if check["status"] == "fail"]
    warning_count = sum(len(check["warnings"]) for check in checks)
    return {
        "format": PUBLIC_SURFACE_CHECK_FORMAT,
        "ready": len(failed) == 0,
        "generated_by": "scenariolens public-surface-check",
        "scope_note": (
            "This check verifies public repository surfaces only: checked-in "
            "docs, demo payloads, report links, public-safe data boundaries, "
            "and CI smoke commands. It does not require raw Waymo shards and "
            "does not claim benchmark completeness."
        ),
        "aggregate": {
            "check_count": len(checks),
            "passed_count": sum(1 for check in checks if check["status"] == "pass"),
            "failed_count": len(failed),
            "warning_count": warning_count,
            "checked_files_count": sum(len(check["files"]) for check in checks),
        },
        "checks": checks,
        "failures": [
            {
                "id": check["id"],
                "title": check["title"],
                "details": check["details"],
            }
            for check in failed
        ],
    }


def public_surface_check_markdown(payload: dict[str, object]) -> str:
    """Return a public-safe Markdown readiness report."""

    aggregate = _required_mapping(payload, "aggregate")
    checks = _required_list(payload, "checks")
    lines = [
        "# ScenarioLens Public Surface Check",
        "",
        "This generated report is the v1 release-readiness gate for the public "
        "ScenarioLens surface. It verifies that the demo payloads, report links, "
        "public evidence index, raw-data boundary, and CI smoke commands are "
        "internally consistent without requiring local Waymo shards.",
        "",
        "It is intentionally scoped to repository health. It is not a Waymo "
        "benchmark claim, not a production autonomy validation, and not a "
        "closed-loop simulation result.",
        "",
        "## Summary",
        "",
        f"- Ready: {'yes' if payload['ready'] else 'no'}",
        f"- Checks passed: {aggregate['passed_count']} / {aggregate['check_count']}",
        f"- Failed checks: {aggregate['failed_count']}",
        f"- Warnings: {aggregate['warning_count']}",
        f"- Files checked: {aggregate['checked_files_count']}",
        "",
        "## Checks",
        "",
        "| Check | Status | Summary |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(
            f"| {check['title']} | {check['status']} | {check['summary']} |"
        )

    lines.extend(["", "## Details", ""])
    for check in checks:
        lines.extend(
            [
                f"### {check['title']}",
                "",
                f"- Status: {check['status']}",
                f"- Files: {', '.join(f'`{path}`' for path in check['files']) or 'n/a'}",
                f"- Summary: {check['summary']}",
            ]
        )
        for detail in check["details"]:
            lines.append(f"- {detail}")
        for warning in check["warnings"]:
            lines.append(f"- Warning: {warning}")
        lines.append("")

    lines.extend(
        [
            "## Public-Safety Boundary",
            "",
            "- The check reads checked-in derived reports and demo payloads only.",
            "- Raw Waymo TFRecords, local replay packets, and per-case debug artifacts stay outside git.",
            "- External links are counted but not fetched, so CI remains deterministic and offline-safe.",
            "",
        ]
    )
    return "\n".join(lines)


def _evidence_index_check(root: Path) -> dict[str, object]:
    path = root / "docs/demo/evidence_index.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _check(
            "evidence_index",
            "Evidence index readiness",
            "fail",
            [path],
            f"Unable to parse evidence index: {exc}",
            [str(exc)],
        )

    aggregate = payload.get("aggregate", {})
    missing = int(aggregate.get("missing_count", -1))
    ready = payload.get("format") == "scenariolens.evidence_index.v1" and bool(payload.get("ready")) and missing == 0
    details = [
        f"Format: `{payload.get('format')}`",
        f"Ready flag: {payload.get('ready')}",
        f"Artifact count: {aggregate.get('artifact_count')}",
        f"Missing required artifacts: {missing}",
    ]
    return _check(
        "evidence_index",
        "Evidence index readiness",
        "pass" if ready else "fail",
        [path],
        "Evidence index is ready with no missing required artifacts."
        if ready
        else "Evidence index is missing required artifacts or has an unexpected format.",
        details,
    )


def _demo_payload_contract_check(root: Path) -> dict[str, object]:
    expected = {
        root / "docs/demo/scenarios.json": "scenariolens.dashboard.v1",
        root / "docs/demo/selector_decisions.json": (
            "scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas.v1"
        ),
        root / "docs/demo/evidence_index.json": "scenariolens.evidence_index.v1",
    }
    details: list[str] = []
    failures: list[str] = []
    for path, expected_format in expected.items():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"`{_display_path(root, path)}` failed to parse: {exc}")
            continue
        actual = payload.get("format")
        if actual != expected_format:
            failures.append(
                f"`{_display_path(root, path)}` format `{actual}` != `{expected_format}`"
            )
        details.append(f"`{_display_path(root, path)}` format `{actual}`")

    return _check(
        "demo_payload_contracts",
        "Demo payload contracts",
        "fail" if failures else "pass",
        expected.keys(),
        "Static demo JSON payloads parse and expose expected format versions."
        if not failures
        else "One or more static demo payloads failed contract checks.",
        details + failures,
    )


def _link_integrity_check(root: Path) -> dict[str, object]:
    files = [
        root / "README.md",
        root / "docs/demo/index.html",
        root / "docs/demo/README.md",
        root / "docs/reports/scenariolens_evidence_index.md",
        root / "docs/reports/scenariolens_public_surface_check.md",
    ]
    local_links = 0
    external_links = 0
    missing: list[str] = []
    details: list[str] = []
    checked_files = [path for path in files if path.exists()]

    for path in checked_files:
        links = _extract_links(path)
        details.append(f"`{_display_path(root, path)}` links scanned: {len(links)}")
        for link in links:
            if _is_external_link(link):
                external_links += 1
                continue
            target = _resolve_local_link(path, link)
            if target is None:
                continue
            local_links += 1
            if not target.exists():
                missing.append(
                    f"`{_display_path(root, path)}` -> `{link}` resolves to missing `{_display_path(root, target)}`"
                )

    details.append(f"Local links checked: {local_links}")
    details.append(f"External links skipped: {external_links}")
    details.extend(missing)
    return _check(
        "local_link_integrity",
        "Local link integrity",
        "fail" if missing else "pass",
        checked_files,
        "All checked local links resolve to files in the repository."
        if not missing
        else "One or more checked local links are broken.",
        details,
        warnings=[] if len(checked_files) == len(files) else ["Some optional surface files are not present yet."],
    )


def _demo_asset_check(root: Path) -> dict[str, object]:
    files = [root / "docs/demo/scenarios.json", root / "docs/demo/selector_decisions.json"]
    details: list[str] = []
    missing: list[str] = []
    asset_count = 0

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        base = path.parent
        records = payload.get("scenarios", []) if path.name == "scenarios.json" else payload.get("cases", [])
        for record in records:
            if not isinstance(record, dict):
                continue
            asset_path = record.get("asset_path")
            if not isinstance(asset_path, str) or not asset_path:
                continue
            asset_count += 1
            resolved = base / asset_path
            if not resolved.exists():
                missing.append(
                    f"`{_display_path(root, path)}` references missing asset `{asset_path}`"
                )
    details.append(f"Referenced demo assets checked: {asset_count}")
    details.extend(missing)
    return _check(
        "demo_asset_integrity",
        "Demo asset integrity",
        "fail" if missing else "pass",
        files,
        "All checked SVG assets referenced by demo JSON exist."
        if not missing
        else "One or more demo JSON asset references are missing.",
        details,
    )


def _raw_data_boundary_check(root: Path) -> dict[str, object]:
    tracked = _tracked_files(root)
    raw_paths = [
        path
        for path in tracked
        if (
            path.startswith("data/raw/")
            and Path(path).name not in {".gitkeep", ".gitignore", "README.md"}
        )
        or path.endswith(".tfrecord")
        or ".tfrecord-" in path
    ]
    details = [
        f"Tracked files inspected: {len(tracked)}",
        f"Tracked raw Waymo/TFRecord-like files: {len(raw_paths)}",
    ]
    details.extend(f"`{path}`" for path in raw_paths[:20])
    return _check(
        "raw_data_boundary",
        "Raw-data boundary",
        "fail" if raw_paths else "pass",
        [root / ".gitignore", root / "docs/data_provenance.md"],
        "No raw Waymo or TFRecord-like files are tracked."
        if not raw_paths
        else "Raw Waymo or TFRecord-like files appear to be tracked.",
        details,
    )


def _ci_surface_check(root: Path) -> dict[str, object]:
    path = root / ".github/workflows/ci.yml"
    text = path.read_text(encoding="utf-8")
    required = [
        "python -m unittest discover",
        "node --check docs/demo/app.js",
        "python -m json.tool docs/demo/evidence_index.json",
        "scenariolens run",
        "scenariolens run-verify",
        "scenariolens evidence-index",
        "scenariolens public-surface-check",
    ]
    missing = [item for item in required if item not in text]
    details = [f"`{item}` present: {item not in missing}" for item in required]
    return _check(
        "ci_surface",
        "CI surface",
        "fail" if missing else "pass",
        [path],
        "CI covers unit tests, deterministic run integration, static demo syntax, evidence JSON, and public-surface checks."
        if not missing
        else "CI is missing one or more required integration or public-surface commands.",
        details,
    )


def _public_safety_language_check(root: Path) -> dict[str, object]:
    required = {
        root / "docs/reports/scenariolens_evidence_index.md": [
            "not a Waymo benchmark",
            "Raw Waymo TFRecords",
            "default selector remains unchanged",
        ],
        root / "docs/data_provenance.md": [
            "Raw Waymo",
            "outside git",
        ],
    }
    missing: list[str] = []
    details: list[str] = []
    for path, phrases in required.items():
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            present = phrase.lower() in text.lower()
            details.append(f"`{_display_path(root, path)}` contains `{phrase}`: {present}")
            if not present:
                missing.append(f"`{_display_path(root, path)}` missing `{phrase}`")
    return _check(
        "public_safety_language",
        "Public-safety language",
        "fail" if missing else "pass",
        required.keys(),
        "Core provenance/evidence docs state the non-benchmark and raw-data boundaries."
        if not missing
        else "Core public-safety language is missing.",
        details + missing,
    )


def _check(
    identifier: str,
    title: str,
    status: str,
    files: object,
    summary: str,
    details: list[str],
    warnings: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": identifier,
        "title": title,
        "status": status,
        "summary": summary,
        "files": [_display_path(Path("."), Path(path)) for path in files],
        "details": details,
        "warnings": warnings or [],
    }


def _extract_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".html", ".htm"}:
        parser = _LinkParser()
        parser.feed(text)
        return parser.links
    return _markdown_links(text)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


def _markdown_links(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^\)]+)\)", text)
        if match.group(1).strip()
    ]


def _is_external_link(link: str) -> bool:
    parsed = urlparse(link)
    return parsed.scheme in {"http", "https", "mailto"}


def _resolve_local_link(source: Path, link: str) -> Path | None:
    target_text = link.split("#", 1)[0]
    if not target_text or target_text.startswith("#"):
        return None
    if target_text.startswith("data:"):
        return None
    return (source.parent / target_text).resolve()


def _tracked_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]
    return [line for line in result.stdout.splitlines() if line]


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _required_mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at {key}.")
    return value


def _required_list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Expected list of mappings at {key}.")
    return value
