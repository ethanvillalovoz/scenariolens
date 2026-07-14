from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from scenariolens import __version__


RELEASE_CHECK_FORMAT = "scenariolens.release_check.v1"
DEFAULT_RELEASE_CHECK_TIMEOUT_SECONDS = 300.0
_PROBE_MARKER = "SCENARIOLENS_RELEASE_PROBE="


@dataclass(frozen=True)
class ReleaseCheckResult:
    """Artifacts produced by the clean-package v1 release check."""

    ready: bool
    check_count: int
    passed_count: int
    failed_count: int
    analysis_digest: str
    duration_seconds: float
    output_dir: Path
    manifest_path: Path
    report_path: Path
    public_report_path: Path | None
    wheel_path: Path | None


def generate_release_check(
    repo_root: str | Path,
    output_dir: str | Path,
    public_report_path: str | Path | None = None,
    timeout_seconds: float = DEFAULT_RELEASE_CHECK_TIMEOUT_SECONDS,
) -> ReleaseCheckResult:
    """Build, install, and exercise ScenarioLens from an isolated wheel."""

    if timeout_seconds <= 0:
        raise ValueError("release-check timeout must be positive.")
    requested_root = Path(repo_root).absolute()
    root = requested_root.resolve()
    if not (root / "pyproject.toml").is_file():
        raise FileNotFoundError(
            f"ScenarioLens repository root is missing pyproject.toml: {root}"
        )
    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    checks: list[dict[str, object]] = []
    evidence: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="scenariolens-release-check-") as tmpdir:
        workspace = Path(tmpdir).resolve()
        try:
            checks, evidence = _execute_release_checks(
                repo_root=root,
                output_dir=target,
                workspace=workspace,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            checks.append(
                _check(
                    "release_check_execution",
                    "Release-check orchestration",
                    False,
                    type(exc).__name__,
                    "all checks execute",
                    [
                        _sanitize_text(
                            str(exc),
                            root,
                            workspace,
                            additional_paths=(requested_root,),
                        )
                    ],
                )
            )

    passed_count = sum(bool(check["passed"]) for check in checks)
    check_count = len(checks)
    failed_count = check_count - passed_count
    ready = check_count > 0 and failed_count == 0
    stable_payload = {
        "format": RELEASE_CHECK_FORMAT,
        "scenariolens_version": __version__,
        "checks": [
            {
                "check_id": check["check_id"],
                "passed": check["passed"],
                "observed": check["observed"],
                "expected": check["expected"],
            }
            for check in checks
        ],
        "evidence": {
            "wheel_sha256": evidence.get("wheel_sha256"),
            "rebuild_wheel_sha256": evidence.get("rebuild_wheel_sha256"),
            "product_analysis_digest": evidence.get("product_analysis_digest"),
            "resume_analysis_digest": evidence.get("resume_analysis_digest"),
        },
    }
    analysis_digest = _canonical_digest(stable_payload)
    duration_seconds = round(perf_counter() - started, 3)
    wheel_name = evidence.get("wheel_name")
    wheel_path = (
        target / "dist" / str(wheel_name)
        if isinstance(wheel_name, str) and wheel_name
        else None
    )
    payload: dict[str, object] = {
        "format": RELEASE_CHECK_FORMAT,
        "ready": ready,
        "created_at_utc": _utc_now(),
        "scenariolens_version": __version__,
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "duration_seconds": duration_seconds,
        "analysis_digest": analysis_digest,
        "aggregate": {
            "check_count": check_count,
            "passed_count": passed_count,
            "failed_count": failed_count,
        },
        "checks": checks,
        "evidence": evidence,
        "outputs": {
            "manifest": "manifest.json",
            "report": "report.md",
            "wheel": f"dist/{wheel_name}" if wheel_name else None,
        },
        "scope_note": (
            "This packet validates packaging, the installed product loop, "
            "failure diagnostics, no-map fallback behavior, and resumable "
            "execution using synthetic public fixtures. It complements, but "
            "does not replace, the separate real Waymo full-corpus and frozen "
            "holdout reports. It is not a benchmark or safety certification."
        ),
    }
    manifest_path = target / "manifest.json"
    report_path = target / "report.md"
    copied_report_path = Path(public_report_path) if public_report_path else None
    _write_text_atomic(manifest_path, json.dumps(payload, indent=2) + "\n")
    report = release_check_markdown(payload)
    _write_text_atomic(report_path, report)
    if copied_report_path is not None:
        copied_report_path.parent.mkdir(parents=True, exist_ok=True)
        _write_text_atomic(copied_report_path, report)

    return ReleaseCheckResult(
        ready=ready,
        check_count=check_count,
        passed_count=passed_count,
        failed_count=failed_count,
        analysis_digest=analysis_digest,
        duration_seconds=duration_seconds,
        output_dir=target,
        manifest_path=manifest_path,
        report_path=report_path,
        public_report_path=copied_report_path,
        wheel_path=wheel_path,
    )


def release_check_markdown(payload: dict[str, object]) -> str:
    """Return a concise public-safe release validation report."""

    aggregate = _mapping(payload, "aggregate")
    evidence = _mapping(payload, "evidence")
    checks = _list(payload, "checks")
    lines = [
        "# ScenarioLens V1 Release Check",
        "",
        f"**Status: {'PASS' if payload.get('ready') else 'FAIL'}.**",
        "",
        "This packet builds ScenarioLens from the repository, installs the "
        "wheel into a clean virtual environment, and exercises the installed "
        "entrypoint from outside the checkout.",
        "",
        "It uses checked-in synthetic fixtures for packaging and failure-path "
        "validation. Real-data claims remain in the separate full-corpus and "
        "frozen selector holdout reports.",
        "",
        "## Summary",
        "",
        f"- ScenarioLens version: `{payload['scenariolens_version']}`",
        f"- Checks passed: {aggregate['passed_count']} / {aggregate['check_count']}",
        f"- Duration: {float(payload['duration_seconds']):.3f} s",
        f"- Release-check digest: `{payload['analysis_digest']}`",
        f"- Wheel: `{evidence.get('wheel_name', 'not built')}`",
        f"- Wheel SHA-256: `{evidence.get('wheel_sha256', 'not available')}`",
        f"- Product-run digest: `{evidence.get('product_analysis_digest', 'not available')}`",
        f"- Resume digest: `{evidence.get('resume_analysis_digest', 'not available')}`",
        "",
        "## Checks",
        "",
        "| Check | Result | Observed | Expected |",
        "| --- | --- | --- | --- |",
    ]
    for check in checks:
        assert isinstance(check, dict)
        lines.append(
            f"| {_table_text(check['label'])} | "
            f"{'pass' if check['passed'] else 'fail'} | "
            f"{_table_text(check['observed'])} | "
            f"{_table_text(check['expected'])} |"
        )
    lines.extend(["", "## Diagnostics", ""])
    for check in checks:
        assert isinstance(check, dict)
        lines.extend(
            [
                f"### {check['label']}",
                "",
                f"- Result: {'pass' if check['passed'] else 'fail'}",
            ]
        )
        for detail in check.get("details", []):
            lines.append(f"- {detail}")
        lines.append("")
    lines.extend(
        [
            "## Boundaries",
            "",
            "- The installed product run uses public synthetic scenarios.",
            "- The no-map check validates explicit constant-velocity fallback, "
            "not map-aware accuracy.",
            "- The interruption probe runs the actual installed nine-stage "
            "pipeline and injects one `KeyboardInterrupt` at the topology stage.",
            "- This packet does not publish or inspect raw Waymo records.",
            "- Passing this packet is necessary for v1 release readiness, but it "
            "does not establish production autonomy safety.",
            "",
        ]
    )
    return "\n".join(lines)


def _execute_release_checks(
    *,
    repo_root: Path,
    output_dir: Path,
    workspace: Path,
    timeout_seconds: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    checks: list[dict[str, object]] = []
    evidence: dict[str, object] = {}
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["SOURCE_DATE_EPOCH"] = "315532800"
    replacements = (
        (repo_root, "<repo>"),
        (workspace, "<temp>"),
        (Path(tempfile.gettempdir()).resolve(), "<system-temp>"),
    )

    dist_dir = output_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)
    build = _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(dist_dir),
            str(repo_root),
        ],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    wheels = sorted(dist_dir.glob("scenariolens-*.whl"))
    build_ready = build.returncode == 0 and len(wheels) == 1
    checks.append(
        _check(
            "wheel_build",
            "Wheel build",
            build_ready,
            f"exit {build.returncode}; {len(wheels)} wheel(s)",
            "exit 0; exactly 1 wheel",
            [_command_excerpt(build, replacements)],
        )
    )
    if not build_ready:
        return checks, evidence
    wheel_path = wheels[0]
    evidence.update(
        {
            "wheel_name": wheel_path.name,
            "wheel_size_bytes": wheel_path.stat().st_size,
            "wheel_sha256": _sha256_file(wheel_path),
            "source_date_epoch": environment["SOURCE_DATE_EPOCH"],
        }
    )

    rebuild_dir = workspace / "rebuild-dist"
    rebuild_dir.mkdir()
    rebuild = _run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(rebuild_dir),
            str(repo_root),
        ],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    rebuilt_wheels = sorted(rebuild_dir.glob("scenariolens-*.whl"))
    rebuilt_hash = (
        _sha256_file(rebuilt_wheels[0])
        if rebuild.returncode == 0 and len(rebuilt_wheels) == 1
        else None
    )
    evidence["rebuild_wheel_sha256"] = rebuilt_hash
    reproducible_wheel = (
        rebuilt_hash is not None
        and rebuilt_wheels[0].name == wheel_path.name
        and rebuilt_hash == evidence["wheel_sha256"]
    )
    checks.append(
        _check(
            "reproducible_wheel_build",
            "Reproducible wheel rebuild",
            reproducible_wheel,
            (
                f"exit {rebuild.returncode}; name match "
                f"{bool(rebuilt_wheels and rebuilt_wheels[0].name == wheel_path.name)}; "
                f"hash match {rebuilt_hash == evidence['wheel_sha256']}"
            ),
            "exit 0; wheel names and SHA-256 hashes match",
            [_command_excerpt(rebuild, replacements)],
        )
    )

    venv_dir = workspace / "venv"
    create_venv = _run_command(
        [sys.executable, "-m", "venv", str(venv_dir)],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    executable_suffix = ".exe" if os.name == "nt" else ""
    venv_python = scripts_dir / f"python{executable_suffix}"
    scenariolens = scripts_dir / f"scenariolens{executable_suffix}"
    install = (
        _run_command(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                str(wheel_path),
            ],
            cwd=workspace,
            environment=environment,
            timeout_seconds=timeout_seconds,
        )
        if create_venv.returncode == 0 and venv_python.is_file()
        else _failed_command("virtual environment creation failed")
    )
    install_ready = (
        create_venv.returncode == 0
        and install.returncode == 0
        and scenariolens.is_file()
    )
    checks.append(
        _check(
            "clean_install",
            "Clean wheel installation",
            install_ready,
            f"venv exit {create_venv.returncode}; install exit {install.returncode}",
            "both exit 0; console script present",
            [
                _command_excerpt(create_venv, replacements),
                _command_excerpt(install, replacements),
            ],
        )
    )
    if not install_ready:
        return checks, evidence

    import_probe = _run_command(
        [
            str(venv_python),
            "-c",
            (
                "import json, scenariolens; "
                "print(json.dumps({'version': scenariolens.__version__, "
                "'path': scenariolens.__file__}))"
            ),
        ],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    import_payload = _last_json_object(import_probe.stdout)
    import_path = Path(str(import_payload.get("path", ""))).resolve()
    import_ready = (
        import_probe.returncode == 0
        and import_payload.get("version") == __version__
        and not import_path.is_relative_to(repo_root)
    )
    evidence["installed_version"] = import_payload.get("version")
    checks.append(
        _check(
            "outside_checkout_import",
            "Installed import provenance",
            import_ready,
            (
                f"version {import_payload.get('version')}; "
                f"outside checkout {not import_path.is_relative_to(repo_root)}"
            ),
            f"version {__version__}; outside checkout true",
            [_command_excerpt(import_probe, replacements)],
        )
    )

    help_result = _run_command(
        [str(scenariolens), "--help"],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    help_ready = (
        help_result.returncode == 0
        and "ScenarioLens" in help_result.stdout
        and "selector-holdout-study" in help_result.stdout
    )
    checks.append(
        _check(
            "console_entrypoint",
            "Installed console entrypoint",
            help_ready,
            f"exit {help_result.returncode}; command list present {help_ready}",
            "exit 0; ScenarioLens commands listed",
            [_command_excerpt(help_result, replacements)],
        )
    )

    fixture_path = workspace / "synthetic.json"
    export_result = _run_command(
        [str(scenariolens), "export-synthetic", "--output", str(fixture_path)],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    fixture_ready = export_result.returncode == 0 and fixture_path.is_file()
    checks.append(
        _check(
            "fixture_export",
            "Installed synthetic fixture export",
            fixture_ready,
            f"exit {export_result.returncode}; file present {fixture_path.is_file()}",
            "exit 0; fixture present",
            [_command_excerpt(export_result, replacements)],
        )
    )
    if not fixture_ready:
        return checks, evidence

    product_dir = workspace / "product-run"
    product_result = _run_command(
        [
            str(scenariolens),
            "run",
            "--input",
            str(fixture_path),
            "--format",
            "scenariolens-json",
            "--output",
            str(product_dir),
            "--max-scenarios",
            "11",
            "--top",
            "4",
        ],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    product_manifest = _read_json_object(product_dir / "manifest.json")
    product_ready = (
        product_result.returncode == 0
        and product_manifest.get("ready") is True
        and product_manifest.get("scenario_count") == 11
        and product_manifest.get("stage_count") == 3
    )
    evidence["product_analysis_digest"] = product_manifest.get("analysis_digest")
    checks.append(
        _check(
            "installed_product_run",
            "Installed one-command product run",
            product_ready,
            (
                f"exit {product_result.returncode}; ready "
                f"{product_manifest.get('ready')}; scenarios "
                f"{product_manifest.get('scenario_count')}"
            ),
            "exit 0; ready true; 11 scenarios; 3 stages",
            [_command_excerpt(product_result, replacements)],
        )
    )
    required_artifacts = (
        product_dir / "manifest.json",
        product_dir / "report.md",
        product_dir / "explorer" / "index.html",
        product_dir / "explorer" / "run.json",
        product_dir / "explorer" / "scenarios.json",
        product_dir / "studies" / "baseline_comparison" / "manifest.json",
        product_dir / "studies" / "lane_selection" / "manifest.json",
        product_dir / "studies" / "lane_continuation" / "manifest.json",
    )
    artifact_count = sum(path.is_file() for path in required_artifacts)
    checks.append(
        _check(
            "run_bundle_contract",
            "Installed run-bundle contract",
            artifact_count == len(required_artifacts),
            f"{artifact_count}/{len(required_artifacts)} required artifacts",
            f"{len(required_artifacts)}/{len(required_artifacts)} required artifacts",
            [
                "Missing: "
                + ", ".join(
                    path.relative_to(product_dir).as_posix()
                    for path in required_artifacts
                    if not path.is_file()
                )
                if artifact_count != len(required_artifacts)
                else "All top-level, study, and Explorer artifacts are present."
            ],
        )
    )
    baseline_manifest = _read_json_object(
        product_dir / "studies" / "baseline_comparison" / "manifest.json"
    )
    fallback_reasons = baseline_manifest.get("fallback_reasons", {})
    no_map_count = (
        int(fallback_reasons.get("no_lane_map_features", 0))
        if isinstance(fallback_reasons, dict)
        else 0
    )
    no_map_ready = product_ready and no_map_count > 0
    checks.append(
        _check(
            "missing_map_fallback",
            "Missing map-context fallback",
            no_map_ready,
            f"run ready {product_ready}; no-map fallbacks {no_map_count}",
            "run ready true; no-map fallbacks > 0",
            [
                "Targets without lane geometry retained the documented "
                "constant-velocity fallback."
            ],
        )
    )

    _append_expected_failure_checks(
        checks=checks,
        scenariolens=scenariolens,
        workspace=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
        replacements=replacements,
    )

    resume_root = workspace / "resume-probe"
    resume_probe = _run_command(
        [
            str(venv_python),
            "-c",
            _RESUME_PROBE_SCRIPT,
            str(fixture_path),
            str(resume_root),
        ],
        cwd=workspace,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    probe = _marked_json_object(resume_probe.stdout, _PROBE_MARKER)
    interrupted_ready = (
        resume_probe.returncode == 0
        and probe.get("interrupted_status") == "interrupted"
        and probe.get("interrupted_stage_count") == 3
        and probe.get("interrupted_active_stage") == "topology_gap_audit"
        and probe.get("failure_type") == "KeyboardInterrupt"
    )
    checks.append(
        _check(
            "interrupted_output_state",
            "Interrupted output diagnostics",
            interrupted_ready,
            (
                f"exit {resume_probe.returncode}; status "
                f"{probe.get('interrupted_status')}; completed "
                f"{probe.get('interrupted_stage_count')}"
            ),
            "exit 0; interrupted; 3 completed stages",
            [_command_excerpt(resume_probe, replacements)],
        )
    )
    resume_ready = (
        resume_probe.returncode == 0
        and probe.get("final_status") == "complete"
        and probe.get("reused_stage_count") == 3
        and probe.get("executed_stage_count") == 6
        and probe.get("digest_match") is True
        and probe.get("stage_count") == 9
    )
    evidence["resume_analysis_digest"] = probe.get("analysis_digest")
    evidence["resume_reused_stage_count"] = probe.get("reused_stage_count")
    evidence["resume_executed_stage_count"] = probe.get("executed_stage_count")
    checks.append(
        _check(
            "resumed_output_equivalence",
            "Verified interruption resume",
            resume_ready,
            (
                f"status {probe.get('final_status')}; reused "
                f"{probe.get('reused_stage_count')}; executed "
                f"{probe.get('executed_stage_count')}; digest match "
                f"{probe.get('digest_match')}"
            ),
            "complete; 3 reused; 6 executed; digest match true",
            [_command_excerpt(resume_probe, replacements)],
        )
    )
    return checks, evidence


def _append_expected_failure_checks(
    *,
    checks: list[dict[str, object]],
    scenariolens: Path,
    workspace: Path,
    environment: dict[str, str],
    timeout_seconds: float,
    replacements: tuple[tuple[Path, str], ...],
) -> None:
    missing_path = workspace / "missing.tfrecord"
    unsupported_path = workspace / "unsupported.txt"
    unsupported_path.write_text("unsupported\n", encoding="utf-8")
    truncated_path = workspace / "truncated.tfrecord"
    truncated_path.write_bytes(b"\x01\x02")
    cases = (
        (
            "empty_input_failure",
            "Empty input rejection",
            [str(scenariolens), "run", "--output", str(workspace / "empty")],
            "the following arguments are required: --input",
        ),
        (
            "missing_input_failure",
            "Missing input rejection",
            [
                str(scenariolens),
                "run",
                "--input",
                str(missing_path),
                "--output",
                str(workspace / "missing-output"),
            ],
            "ScenarioLens run input does not exist",
        ),
        (
            "unsupported_input_failure",
            "Unsupported input rejection",
            [
                str(scenariolens),
                "run",
                "--input",
                str(unsupported_path),
                "--output",
                str(workspace / "unsupported-output"),
            ],
            "Unsupported Waymo Motion input suffix",
        ),
        (
            "truncated_tfrecord_failure",
            "Truncated TFRecord rejection",
            [
                str(scenariolens),
                "run",
                "--input",
                str(truncated_path),
                "--output",
                str(workspace / "truncated-output"),
            ],
            "truncated TFRecord header at record 0",
        ),
    )
    for check_id, label, command, marker in cases:
        result = _run_command(
            command,
            cwd=workspace,
            environment=environment,
            timeout_seconds=timeout_seconds,
        )
        combined = f"{result.stdout}\n{result.stderr}"
        passed = result.returncode == 2 and marker in combined
        checks.append(
            _check(
                check_id,
                label,
                passed,
                f"exit {result.returncode}; diagnostic present {marker in combined}",
                "exit 2; expected diagnostic present",
                [_command_excerpt(result, replacements)],
            )
        )


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def _failed_command(message: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode=1, stdout="", stderr=message)


def _check(
    check_id: str,
    label: str,
    passed: bool,
    observed: object,
    expected: object,
    details: list[str],
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "label": label,
        "passed": passed,
        "observed": observed,
        "expected": expected,
        "details": details,
    }


def _command_excerpt(
    result: subprocess.CompletedProcess[str],
    replacements: tuple[tuple[Path, str], ...],
) -> str:
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    if not output:
        return "No command output."
    for path, replacement in replacements:
        output = output.replace(str(path), replacement)
    compact = " / ".join(line.strip() for line in output.splitlines() if line.strip())
    if len(compact) > 800:
        compact = f"...{compact[-797:]}"
    compact = compact.replace("`", "'")
    return f"Command output: `{compact}`"


def _sanitize_text(
    value: str,
    repo_root: Path,
    workspace: Path,
    additional_paths: tuple[Path, ...] = (),
) -> str:
    replacements = (
        *((path, "<repo>") for path in additional_paths),
        (repo_root, "<repo>"),
        (workspace, "<temp>"),
    )
    for path, replacement in replacements:
        value = value.replace(str(path), replacement)
    return value


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _last_json_object(value: str) -> dict[str, object]:
    for line in reversed(value.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _marked_json_object(value: str, marker: str) -> dict[str, object]:
    for line in reversed(value.splitlines()):
        if not line.startswith(marker):
            continue
        try:
            payload = json.loads(line[len(marker) :])
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


def _mapping(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object field: {key}.")
    return value


def _list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list field: {key}.")
    return value


def _canonical_digest(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text_atomic(path: Path, value: str) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(value, encoding="utf-8")
    temporary_path.replace(path)


def _table_text(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


_RESUME_PROBE_SCRIPT = r'''
import json
import sys
from pathlib import Path
from unittest.mock import patch

from scenariolens.selector_holdout import generate_selector_holdout_study

fixture = Path(sys.argv[1])
root = Path(sys.argv[2])
interrupted_dir = root / "interrupted"
common = {
    "input_paths": (fixture,),
    "input_format": "scenariolens-json",
    "scenario_offset": 0,
    "max_scenarios": 11,
    "expected_scenarios": 11,
    "top": 20,
    "minimum_selector_decisions": 1,
}

try:
    with patch(
        "scenariolens.selector_holdout.generate_lane_continuation_topology_gap_audit",
        side_effect=KeyboardInterrupt("release-check fault injection"),
    ):
        generate_selector_holdout_study(output_dir=interrupted_dir, **common)
except KeyboardInterrupt:
    pass

interrupted_state = json.loads((interrupted_dir / "state.json").read_text())
uninterrupted = generate_selector_holdout_study(
    output_dir=root / "uninterrupted",
    **common,
)
resumed = generate_selector_holdout_study(
    output_dir=interrupted_dir,
    resume=True,
    **common,
)
final_state = json.loads(resumed.state_path.read_text())
payload = {
    "interrupted_status": interrupted_state.get("status"),
    "interrupted_stage_count": len(interrupted_state.get("stages", [])),
    "interrupted_active_stage": interrupted_state.get("active_stage"),
    "failure_type": interrupted_state.get("failures", [{}])[-1].get("error_type"),
    "final_status": final_state.get("status"),
    "stage_count": len(final_state.get("stages", [])),
    "reused_stage_count": resumed.reused_stage_count,
    "executed_stage_count": resumed.executed_stage_count,
    "digest_match": resumed.analysis_digest == uninterrupted.analysis_digest,
    "analysis_digest": resumed.analysis_digest,
}
print("SCENARIOLENS_RELEASE_PROBE=" + json.dumps(payload, sort_keys=True))
'''
