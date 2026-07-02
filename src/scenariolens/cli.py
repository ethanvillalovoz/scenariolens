from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from scenariolens.baseline_compare import (
    STRICT_LANE_MATCH_THRESHOLD_M,
    json_baseline_ablation_report,
    json_baseline_comparison_report,
    markdown_baseline_ablation_report,
    markdown_baseline_comparison_report,
)
from scenariolens.baseline_compare_study import (
    BASELINE_COMPARISON_STUDY_INPUT_FORMATS,
    generate_baseline_comparison_study,
)
from scenariolens.baseline_debug import (
    BASELINE_DEBUG_INPUT_FORMATS,
    generate_baseline_debug_casebook,
)
from scenariolens.context_study import (
    CONTEXT_STUDY_INPUT_FORMATS,
    generate_context_study,
)
from scenariolens.context_failure_study import (
    CONTEXT_FAILURE_STUDY_INPUT_FORMATS,
    generate_context_failure_study,
)
from scenariolens.context_eval_set import generate_context_eval_set
from scenariolens.dashboard import (
    DEFAULT_LANE_SELECTION_MANIFEST,
    generate_dashboard_data,
)
from scenariolens.failure_study import (
    FAILURE_STUDY_INPUT_FORMATS,
    generate_failure_study,
)
from scenariolens.failure_stability import generate_failure_stability_study
from scenariolens.heading_replay_prototype import generate_heading_replay_prototype
from scenariolens.ingest.csv_tracks import save_track_csv_as_scenarios
from scenariolens.ingest.waymo_motion import (
    adapter_status,
    inspect_waymo_motion_slice,
    save_normalized_motion_csv_as_scenarios,
    save_waymo_motion_as_scenarios,
    waymo_motion_slice_ready,
)
from scenariolens.io import load_scenarios, save_scenarios
from scenariolens.lane_selection_study import (
    LANE_SELECTION_STUDY_INPUT_FORMATS,
    generate_lane_selection_study,
)
from scenariolens.lane_continuation import (
    LANE_CONTINUATION_STUDY_INPUT_FORMATS,
    generate_lane_continuation_prototype,
    generate_lane_continuation_study,
)
from scenariolens.lane_continuation_candidates import (
    generate_lane_continuation_candidate_plan,
)
from scenariolens.lane_continuation_branch_selection import (
    generate_lane_continuation_branch_selection,
)
from scenariolens.lane_continuation_branch_replay import (
    generate_lane_continuation_branch_replay,
)
from scenariolens.lane_continuation_diagnostics import (
    generate_lane_continuation_route_diagnostics,
)
from scenariolens.lane_continuation_replay import (
    LANE_CONTINUATION_REPLAY_INPUT_FORMATS,
    generate_lane_continuation_replay_prototype,
)
from scenariolens.map_match_audit import (
    DEFAULT_AUDIT_THRESHOLDS_M,
    generate_map_match_audit,
)
from scenariolens.portfolio import generate_portfolio_report
from scenariolens.report import json_report, markdown_report, ranked_scores
from scenariolens.replay_candidates import generate_replay_candidate_plan
from scenariolens.replay_prototype import generate_replay_prototype
from scenariolens.route_intent_audit import generate_route_intent_audit
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario
from scenariolens.slice_validation import validate_waymo_motion_slice
from scenariolens.visualize import scenario_svg
from scenariolens.waymo_readiness import (
    DEFAULT_WAYMO_MOTION_INPUT,
    inspect_waymo_motion_readiness,
)
from scenariolens.waymo_shards import generate_waymo_motion_shard_plan


def demo() -> int:
    print(json_report(synthetic_scenarios()))
    return 0


def _load_or_synthetic(input_path: str | None) -> tuple[Scenario, ...]:
    if input_path:
        return load_scenarios(input_path)
    return synthetic_scenarios()


def export_synthetic(output_path: str) -> int:
    save_scenarios(output_path, synthetic_scenarios())
    print(f"Exported {len(synthetic_scenarios())} scenario(s) to {output_path}")
    return 0


def ingest_csv(input_path: str, output_path: str) -> int:
    save_track_csv_as_scenarios(input_path, output_path)
    scenarios = load_scenarios(output_path)
    print(f"Ingested {len(scenarios)} scenario(s) from {input_path} to {output_path}")
    return 0


def waymo_motion_status() -> int:
    status = adapter_status()
    print(f"Adapter: {status.adapter_name}")
    print(f"Implemented: {status.implemented}")
    print(f"Optional package: {status.optional_package}")
    print(f"Optional package available: {status.optional_package_available}")
    print(f"Dataset: {status.dataset_url}")
    print(f"Challenges: {status.challenges_url}")
    print(status.message)
    return 0


def waymo_motion_preflight(input_path: str) -> int:
    report = inspect_waymo_motion_slice(input_path)
    print(f"Input: {report.input_path}")
    print(f"Exists: {report.exists}")
    print(f"Directory: {report.is_directory}")
    print(f"Files scanned: {report.file_count}")
    print(f"Supported files: {report.supported_file_count}")
    print(f"Unsupported files: {report.unsupported_file_count}")
    print(f"Total size: {_format_bytes(report.total_bytes)}")
    print(f"Optional package waymo_open_dataset: {report.optional_package_available}")
    print(f"Optional package tensorflow: {report.tensorflow_available}")
    print(f"Ready for ingestion: {waymo_motion_slice_ready(report)}")

    if report.supported_suffix_counts:
        print("Supported suffixes:")
        for suffix, count in report.supported_suffix_counts.items():
            print(f"  {suffix}: {count}")
    if report.unsupported_suffix_counts:
        print("Unsupported suffixes:")
        for suffix, count in report.unsupported_suffix_counts.items():
            print(f"  {suffix}: {count}")
    if report.sample_supported_files:
        print("Sample supported files:")
        for file_path in report.sample_supported_files:
            print(f"  {file_path}")
    if report.notes:
        print("Notes:")
        for note in report.notes:
            print(f"  - {note}")

    return 0 if waymo_motion_slice_ready(report) else 2


def waymo_motion_doctor(
    input_path: str,
    output_path: str | None,
    search_common_locations: bool,
) -> int:
    readiness = inspect_waymo_motion_readiness(
        input_path=input_path,
        search_common_locations=search_common_locations,
    )
    if output_path:
        Path(output_path).write_text(
            json.dumps(asdict(readiness), indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"Input: {readiness.input_path}")
    print(f"Ready for ingestion: {readiness.ready}")
    print(f"Files scanned: {readiness.preflight.file_count}")
    print(f"Supported files: {readiness.preflight.supported_file_count}")
    print(f"Total size: {_format_bytes(readiness.preflight.total_bytes)}")
    print(f"Tool gcloud: {readiness.tooling.gcloud_path or 'missing'}")
    print(f"Tool gsutil: {readiness.tooling.gsutil_path or 'missing'}")
    print(
        "Optional package waymo_open_dataset: "
        f"{readiness.tooling.waymo_open_dataset_available}"
    )
    print(f"Optional package tensorflow: {readiness.tooling.tensorflow_available}")

    if readiness.searched_roots:
        print("Searched common locations:")
        for root in readiness.searched_roots:
            print(f"  {root}")
    if readiness.candidate_files:
        print("Candidate files found outside input:")
        for candidate in readiness.candidate_files:
            print(f"  {candidate.path} ({_format_bytes(candidate.size_bytes)})")
    if readiness.preflight.notes:
        print("Preflight notes:")
        for note in readiness.preflight.notes:
            print(f"  - {note}")
    if readiness.next_actions:
        print("Next actions:")
        for action in readiness.next_actions:
            print(f"  - {action}")
    if output_path:
        print(f"Wrote readiness packet to {output_path}")

    return 0 if readiness.ready else 2


def waymo_motion_shard_plan_command(
    input_path: str,
    output_path: str,
    json_output_path: str | None,
    split: str,
    dataset_version: str,
    total_shards: int,
    next_count: int,
) -> int:
    try:
        result = generate_waymo_motion_shard_plan(
            input_path=input_path,
            output_path=output_path,
            json_output_path=json_output_path,
            split=split,
            dataset_version=dataset_version,
            total_shards=total_shards,
            next_count=next_count,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote Waymo shard expansion plan to {result.output_path}")
    if result.json_output_path is not None:
        print(f"Wrote Waymo shard expansion JSON to {result.json_output_path}")
    print(
        f"Found {result.local_shard_count} local shard(s); "
        f"recommended {result.recommended_download_count} download(s)."
    )
    return 0


def ingest_waymo_motion_command(
    input_path: str,
    output_path: str,
    max_scenarios: int | None,
    input_format: str,
) -> int:
    if input_format == "normalized-csv":
        save_normalized_motion_csv_as_scenarios(
            input_path=input_path,
            output_path=output_path,
            max_scenarios=max_scenarios,
        )
        scenarios = load_scenarios(output_path)
        print(
            f"Ingested {len(scenarios)} normalized Waymo Motion scenario(s) "
            f"from {input_path} to {output_path}"
        )
        return 0

    try:
        save_waymo_motion_as_scenarios(
            input_path=input_path,
            output_path=output_path,
            max_scenarios=max_scenarios,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    scenarios = load_scenarios(output_path)
    print(
        f"Ingested {len(scenarios)} native Waymo Motion scenario(s) "
        f"from {input_path} to {output_path}"
    )
    return 0


def validate_waymo_motion_command(
    input_path: str,
    output_dir: str,
    max_scenarios: int | None,
    top: int,
) -> int:
    try:
        result = validate_waymo_motion_slice(
            input_path=input_path,
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote validation manifest to {result.manifest_path}")
    print(f"Wrote validation summary to {result.summary_path}")
    if not result.ready:
        print("Slice is not ready for ingestion. See preflight.json for details.")
        return 2

    print(
        f"Validated {result.scenario_count} Waymo Motion scenario(s); "
        f"reported top {result.reported_count}."
    )
    if result.scenarios_path is not None:
        print(f"ScenarioLens JSON: {result.scenarios_path}")
    if result.report_path is not None:
        print(f"Ranked report: {result.report_path}")
    if result.case_study_path is not None:
        print(f"Case study: {result.case_study_path}")
    if result.assets_dir is not None:
        print(f"SVG gallery: {result.assets_dir}")
    return 0


def failure_study_command(
    input_path: str,
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    min_tag_count: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_failure_study(
            input_path=input_path,
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            min_tag_count=min_tag_count,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote failure-study manifest to {result.manifest_path}")
    print(f"Wrote failure-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Input is not ready for failure analysis. See manifest.json for details.")
        return 2
    print(f"Analyzed {result.scenario_count} scenario(s).")
    return 0


def failure_stability_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    window_size: int | None,
    top_tags: int,
    min_tag_slices: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_failure_stability_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            window_size=window_size,
            top_tags=top_tags,
            min_tag_slices=min_tag_slices,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote failure-stability manifest to {result.manifest_path}")
    print(f"Wrote failure-stability report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("One or more inputs are not ready. See manifest.json for details.")
        return 2
    print(
        f"Compared {result.slice_count} slice(s) "
        f"across {result.scenario_count} scenario(s)."
    )
    return 0


def _format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def portfolio_report(
    output_path: str,
    assets_dir: str,
    waymo_normalized_path: str,
    waymo_native_path: str,
    top_n: int,
) -> int:
    generate_portfolio_report(
        output_path=output_path,
        assets_dir=assets_dir,
        waymo_normalized_path=waymo_normalized_path,
        waymo_native_path=waymo_native_path,
        top_n=top_n,
    )
    print(f"Generated portfolio report at {output_path}")
    return 0


def dashboard_data(
    output_path: str,
    assets_dir: str,
    waymo_normalized_path: str,
    waymo_native_path: str,
    lane_selection_manifest_path: str | None,
    limit: int | None,
) -> int:
    generate_dashboard_data(
        output_path=output_path,
        assets_dir=assets_dir,
        waymo_normalized_path=waymo_normalized_path,
        waymo_native_path=waymo_native_path,
        lane_selection_manifest_path=lane_selection_manifest_path,
        limit=limit,
    )
    print(f"Generated dashboard data at {output_path}")
    return 0


def report(
    output_format: str,
    limit: int | None,
    output_path: str | None,
    input_path: str | None,
) -> int:
    scenarios = _load_or_synthetic(input_path)
    if output_format == "json":
        content = json_report(scenarios, limit=limit)
    else:
        content = markdown_report(scenarios, limit=limit)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


def baseline_compare(
    output_format: str,
    limit: int | None,
    output_path: str | None,
    input_path: str | None,
) -> int:
    scenarios = _load_or_synthetic(input_path)
    if output_format == "json":
        content = json_baseline_comparison_report(scenarios, limit=limit)
    else:
        content = markdown_baseline_comparison_report(scenarios, limit=limit)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


def baseline_ablation(
    output_format: str,
    output_path: str | None,
    input_path: str | None,
    strict_lane_threshold_m: float,
) -> int:
    scenarios = _load_or_synthetic(input_path)
    if output_format == "json":
        content = json_baseline_ablation_report(
            scenarios,
            strict_lane_match_threshold_m=strict_lane_threshold_m,
        )
    else:
        content = markdown_baseline_ablation_report(
            scenarios,
            strict_lane_match_threshold_m=strict_lane_threshold_m,
        )

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


def baseline_compare_study_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_baseline_comparison_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote baseline-compare-study manifest to {result.manifest_path}")
    print(f"Wrote baseline-compare-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("One or more inputs are not ready. See manifest.json for details.")
        return 2
    print(
        f"Compared {result.source_count} source(s) across "
        f"{result.scenario_count} scenario(s) and "
        f"{result.evaluated_target_count} evaluated target(s)."
    )
    return 0


def lane_selection_study_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_selection_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-selection-study manifest to {result.manifest_path}")
    print(f"Wrote lane-selection-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("One or more inputs are not ready. See manifest.json for details.")
        return 2
    print(
        f"Compared {result.source_count} source(s) across "
        f"{result.scenario_count} scenario(s) and "
        f"{result.evaluated_target_count} evaluated target(s)."
    )
    return 0


def baseline_debug_command(
    output_dir: str,
    input_path: str | None,
    scenario_ids: list[str] | None,
    input_format: str,
    max_scenarios: int | None,
    study_manifest: str | None,
    case_count: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_baseline_debug_casebook(
            output_dir=output_dir,
            input_path=input_path,
            scenario_ids=tuple(scenario_ids or ()),
            input_format=input_format,
            max_scenarios=max_scenarios,
            study_manifest_path=study_manifest,
            case_count=case_count,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote baseline-debug manifest to {result.manifest_path}")
    print(f"Wrote baseline-debug report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("One or more debug cases are not ready. See manifest.json for details.")
        return 2
    print(f"Generated {result.case_count} baseline-debug case(s).")
    return 0


def replay_candidates_command(
    debug_manifest: str,
    output_dir: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_replay_candidate_plan(
            debug_manifest_path=debug_manifest,
            output_dir=output_dir,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote replay-candidates manifest to {result.manifest_path}")
    print(f"Wrote replay-candidates report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Replay-candidate plan is not ready. See manifest.json for details.")
        return 2
    print(f"Generated {result.candidate_count} replay candidate(s).")
    return 0


def replay_prototype_command(
    candidate_manifest: str,
    output_dir: str,
    top: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_replay_prototype(
            candidate_manifest_path=candidate_manifest,
            output_dir=output_dir,
            top=top,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote replay-prototype manifest to {result.manifest_path}")
    print(f"Wrote replay-prototype report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Replay prototype is not ready. See manifest.json for details.")
        return 2
    print(
        f"Generated {result.case_count} replay case(s) across "
        f"{result.replay_track_count} target(s)."
    )
    return 0


def route_intent_audit_command(
    replay_manifest: str,
    output_dir: str,
    case_count: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_route_intent_audit(
            replay_manifest_path=replay_manifest,
            output_dir=output_dir,
            case_count=case_count,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote route-intent-audit manifest to {result.manifest_path}")
    print(f"Wrote route-intent-audit report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Route/intent audit is not ready. See manifest.json for details.")
        return 2
    print(
        f"Generated {result.case_count} route/intent audit case(s) across "
        f"{result.audited_track_count} track(s)."
    )
    return 0


def lane_continuation_prototype_command(
    audit_manifest: str,
    output_dir: str,
    case_count: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_prototype(
            audit_manifest_path=audit_manifest,
            output_dir=output_dir,
            case_count=case_count,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-prototype manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-prototype report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation prototype is not ready. See manifest.json for details.")
        return 2
    print(
        f"Generated {result.case_count} lane-continuation case(s) across "
        f"{result.evaluated_track_count} track(s)."
    )
    return 0


def lane_continuation_study_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-study manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("One or more inputs are not ready. See manifest.json for details.")
        return 2
    print(
        f"Scanned {result.source_count} source(s) across "
        f"{result.scenario_count} scenario(s) and "
        f"{result.candidate_track_count} lane-continuation candidate target(s)."
    )
    return 0


def lane_continuation_candidates_command(
    study_manifest: str,
    output_dir: str,
    top_per_bucket: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_candidate_plan(
            study_manifest_path=study_manifest,
            output_dir=output_dir,
            top_per_bucket=top_per_bucket,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-candidates manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-candidates report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation candidate plan is not ready. See manifest.json.")
        return 2
    print(
        f"Generated {result.candidate_count} lane-continuation candidate(s): "
        f"{result.replay_candidate_count} replay candidate(s), "
        f"{result.audit_candidate_count} topology audit candidate(s)."
    )
    return 0


def lane_continuation_replay_command(
    candidate_manifest: str,
    output_dir: str,
    top_per_bucket: int,
    input_format: str,
    max_scenarios_per_source: int | None,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_replay_prototype(
            candidate_manifest_path=candidate_manifest,
            output_dir=output_dir,
            top_per_bucket=top_per_bucket,
            input_format=input_format,
            max_scenarios_per_source=max_scenarios_per_source,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-replay manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-replay report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation replay prototype is not ready. See manifest.json.")
        return 2
    print(
        f"Generated {result.case_count} lane-continuation replay/audit case(s): "
        f"{result.replay_case_count} replay case(s), "
        f"{result.topology_case_count} topology probe(s)."
    )
    return 0


def lane_continuation_route_diagnostics_command(
    replay_manifest: str,
    output_dir: str,
    top: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_route_diagnostics(
            replay_manifest_path=replay_manifest,
            output_dir=output_dir,
            top=top,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-route-diagnostics manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-route-diagnostics report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation route diagnostics are not ready. See manifest.json.")
        return 2
    print(
        f"Generated {result.diagnostic_count} lane-continuation diagnostic(s): "
        f"{result.regression_count} regression diagnostic(s), "
        f"{result.topology_count} topology diagnostic(s)."
    )
    return 0


def lane_continuation_branch_selection_command(
    diagnostics_manifest: str,
    output_dir: str,
    top: int,
    max_hops: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_branch_selection(
            diagnostics_manifest_path=diagnostics_manifest,
            output_dir=output_dir,
            top=top,
            max_hops=max_hops,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-branch-selection manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-branch-selection report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation branch selection is not ready. See manifest.json.")
        return 2
    print(
        f"Generated {result.case_count} branch-selection diagnostic(s): "
        f"{result.branchable_count} branchable case(s), "
        f"{result.motion_context_improved_count} motion-context improvement(s), "
        f"{result.oracle_improved_count} oracle upper-bound improvement(s)."
    )
    return 0


def lane_continuation_branch_replay_command(
    branch_selection_manifest: str,
    output_dir: str,
    top: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_lane_continuation_branch_replay(
            branch_selection_manifest_path=branch_selection_manifest,
            output_dir=output_dir,
            top=top,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote lane-continuation-branch-replay manifest to {result.manifest_path}")
    print(f"Wrote lane-continuation-branch-replay report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Lane-continuation branch replay is not ready. See manifest.json.")
        return 2
    print(
        f"Generated {result.case_count} branch replay diagnostic(s): "
        f"{result.replayed_case_count} replayed case(s), "
        f"{result.stable_case_count} stable motion-context case(s), "
        f"{result.accepted_case_count} accepted branch case(s)."
    )
    return 0


def heading_replay_prototype_command(
    candidate_manifest: str,
    output_dir: str,
    top: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_heading_replay_prototype(
            candidate_manifest_path=candidate_manifest,
            output_dir=output_dir,
            top=top,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote heading-replay-prototype manifest to {result.manifest_path}")
    print(f"Wrote heading-replay-prototype report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print(
            "Heading replay prototype is not ready. See manifest.json for details."
        )
        return 2
    print(
        f"Generated {result.case_count} heading replay case(s) across "
        f"{result.replay_track_count} target(s)."
    )
    return 0


def map_match_audit_command(
    debug_manifest: str,
    output_dir: str,
    thresholds: str,
    case_count: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_map_match_audit(
            debug_manifest_path=debug_manifest,
            output_dir=output_dir,
            thresholds_m=_parse_thresholds(thresholds),
            case_count=case_count,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote map-match-audit manifest to {result.manifest_path}")
    print(f"Wrote map-match-audit report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Map-match audit is not ready. See manifest.json for details.")
        return 2
    print(f"Generated {result.case_count} map-match audit case(s).")
    return 0


def context_study_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_context_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote context-study manifest to {result.manifest_path}")
    print(f"Wrote context-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Context study is not ready. See manifest.json for details.")
        return 2
    print(
        f"Analyzed {result.scenario_count} scenario(s) across "
        f"{result.source_count} source(s)."
    )
    return 0


def context_failure_study_command(
    input_paths: list[str],
    output_dir: str,
    max_scenarios: int | None,
    top: int,
    input_format: str,
    public_report: str | None,
) -> int:
    try:
        result = generate_context_failure_study(
            input_paths=tuple(input_paths),
            output_dir=output_dir,
            max_scenarios=max_scenarios,
            top=top,
            input_format=input_format,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote context-failure-study manifest to {result.manifest_path}")
    print(f"Wrote context-failure-study report to {result.report_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Context-failure study is not ready. See manifest.json for details.")
        return 2
    print(
        f"Joined context and failure metrics for {result.scenario_count} "
        f"scenario(s) across {result.source_count} source(s)."
    )
    return 0


def context_eval_set_command(
    context_failure_manifest: str,
    output_dir: str,
    top_per_group: int,
    public_report: str | None,
) -> int:
    try:
        result = generate_context_eval_set(
            context_failure_manifest_path=context_failure_manifest,
            output_dir=output_dir,
            top_per_group=top_per_group,
            public_report_path=public_report,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Wrote context-eval-set manifest to {result.manifest_path}")
    print(f"Wrote context-eval-set report to {result.report_path}")
    print(f"Wrote context-eval-set scenario IDs to {result.scenario_ids_path}")
    if result.public_report_path is not None:
        print(f"Wrote public report copy to {result.public_report_path}")
    if not result.ready:
        print("Context eval set is not ready. See manifest.json for details.")
        return 2
    print(
        f"Generated {result.group_count} eval group(s) with "
        f"{result.unique_scenario_count} unique scenario(s)."
    )
    return 0


def _parse_thresholds(value: str) -> tuple[float, ...]:
    thresholds = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        thresholds.append(float(item))
    if not thresholds:
        raise ValueError("At least one threshold is required.")
    return tuple(thresholds)


def render(
    scenario_id: str | None,
    top: int | None,
    output_path: str | None,
    output_dir: str | None,
    input_path: str | None,
) -> int:
    scenarios = _load_or_synthetic(input_path)
    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}

    if top is not None:
        ranked_ids = [score.scenario_id for score in ranked_scores(scenarios)[:top]]
        selected = tuple(scenario_by_id[ranked_id] for ranked_id in ranked_ids)
        target_dir = Path(output_dir or "rendered")
        target_dir.mkdir(parents=True, exist_ok=True)
        for scenario in selected:
            svg = scenario_svg(scenario)
            (target_dir / f"{scenario.scenario_id}.svg").write_text(
                svg,
                encoding="utf-8",
            )
        print(f"Rendered {len(selected)} scenario(s) to {target_dir}")
        return 0

    selected_scenario = _select_scenario(scenarios, scenario_id)
    svg = scenario_svg(selected_scenario)
    if output_path:
        Path(output_path).write_text(svg, encoding="utf-8")
    else:
        print(svg, end="")
    return 0


def _select_scenario(
    scenarios: tuple[Scenario, ...],
    scenario_id: str | None,
) -> Scenario:
    if scenario_id is None:
        return scenarios[0]

    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario

    valid_ids = ", ".join(scenario.scenario_id for scenario in scenarios)
    raise SystemExit(f"Unknown scenario id: {scenario_id}. Valid ids: {valid_ids}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="scenariolens",
        description="Long-tail autonomous-driving scenario discovery utilities.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="Score built-in synthetic scenarios.")
    export_parser = subparsers.add_parser(
        "export-synthetic",
        help="Export built-in synthetic scenarios as ScenarioLens JSON.",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Scenario JSON path to write.",
    )
    ingest_csv_parser = subparsers.add_parser(
        "ingest-csv",
        help="Convert row-wise track CSV into ScenarioLens JSON.",
    )
    ingest_csv_parser.add_argument(
        "--input",
        required=True,
        help="Input CSV path with one row per agent state.",
    )
    ingest_csv_parser.add_argument(
        "--output",
        required=True,
        help="ScenarioLens JSON path to write.",
    )
    waymo_status_parser = subparsers.add_parser(
        "waymo-motion-status",
        help="Show readiness status for the optional Waymo Motion adapter.",
    )
    waymo_status_parser.set_defaults(command="waymo-motion-status")
    waymo_preflight_parser = subparsers.add_parser(
        "waymo-motion-preflight",
        help="Inspect a local Waymo Motion file or directory before ingestion.",
    )
    waymo_preflight_parser.add_argument(
        "--input",
        required=True,
        help="Local Waymo Motion file or directory to inspect.",
    )
    waymo_doctor_parser = subparsers.add_parser(
        "waymo-motion-doctor",
        help=(
            "Diagnose local Waymo Motion data, optional packages, cloud tooling, "
            "and likely downloaded files."
        ),
    )
    waymo_doctor_parser.add_argument(
        "--input",
        default=str(DEFAULT_WAYMO_MOTION_INPUT),
        help="Configured local Waymo Motion file or directory.",
    )
    waymo_doctor_parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON readiness packet to write.",
    )
    waymo_doctor_parser.add_argument(
        "--no-search-common-locations",
        action="store_true",
        help="Skip searching Downloads and Desktop for candidate raw files.",
    )
    waymo_shard_plan_parser = subparsers.add_parser(
        "waymo-motion-shard-plan",
        help="Generate a public-safe plan for expanding local Waymo Motion shards.",
    )
    waymo_shard_plan_parser.add_argument(
        "--input",
        default=str(DEFAULT_WAYMO_MOTION_INPUT),
        help="Local Waymo Motion shard file or directory.",
    )
    waymo_shard_plan_parser.add_argument(
        "--output",
        default="docs/reports/waymo_motion_shard_plan.md",
        help="Markdown output path for the shard expansion plan.",
    )
    waymo_shard_plan_parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON output path for the shard expansion plan.",
    )
    waymo_shard_plan_parser.add_argument(
        "--split",
        default="validation",
        help="Waymo Motion split name used in shard filenames.",
    )
    waymo_shard_plan_parser.add_argument(
        "--dataset-version",
        default="waymo_open_dataset_motion_v_1_3_1",
        help="Waymo Open Dataset Motion GCS bucket/version name.",
    )
    waymo_shard_plan_parser.add_argument(
        "--total-shards",
        type=int,
        default=150,
        help="Total number of shards in the split.",
    )
    waymo_shard_plan_parser.add_argument(
        "--next-count",
        type=int,
        default=3,
        help="Number of next missing shards to recommend.",
    )
    waymo_parser = subparsers.add_parser(
        "ingest-waymo-motion",
        help="Convert Waymo Motion records into ScenarioLens JSON.",
    )
    waymo_parser.add_argument(
        "--format",
        choices=("native", "normalized-csv"),
        default="native",
        help=(
            "Input representation. Native supports protobuf-shaped JSON "
            "without dependencies and binary inputs with optional packages."
        ),
    )
    waymo_parser.add_argument(
        "--input",
        required=True,
        help="Input Waymo Motion dataset file or directory.",
    )
    waymo_parser.add_argument(
        "--output",
        required=True,
        help="ScenarioLens JSON path to write.",
    )
    waymo_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Optional maximum number of scenarios to convert.",
    )
    waymo_validate_parser = subparsers.add_parser(
        "waymo-motion-validate",
        help=(
            "Run preflight, ingestion, report generation, and SVG rendering "
            "for a local Waymo Motion slice."
        ),
    )
    waymo_validate_parser.add_argument(
        "--input",
        required=True,
        help="Local Waymo Motion file or directory to validate.",
    )
    waymo_validate_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_motion_validation_run",
        help="Directory for validation outputs.",
    )
    waymo_validate_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum number of scenarios to ingest before scoring.",
    )
    waymo_validate_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top-ranked scenarios to report and render.",
    )
    failure_study_parser = subparsers.add_parser(
        "failure-study",
        help=(
            "Generate public-safe aggregate ADE/FDE and miss-rate analysis "
            "for a Waymo Motion or ScenarioLens JSON slice."
        ),
    )
    failure_study_parser.add_argument(
        "--input",
        required=True,
        help="Input Waymo Motion file/directory or ScenarioLens JSON file.",
    )
    failure_study_parser.add_argument(
        "--format",
        choices=FAILURE_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation. Native accepts Waymo Motion files.",
    )
    failure_study_parser.add_argument(
        "--output-dir",
        default="data/processed/failure_study",
        help="Directory for manifest.json and report.md.",
    )
    failure_study_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=100,
        help="Maximum number of scenarios to ingest before analysis.",
    )
    failure_study_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of hardest baseline-failure scenarios to report.",
    )
    failure_study_parser.add_argument(
        "--min-tag-count",
        type=int,
        default=1,
        help="Minimum scenarios required for a tag to appear in the tag table.",
    )
    failure_study_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe report copy.",
    )
    failure_stability_parser = subparsers.add_parser(
        "failure-study-stability",
        help=(
            "Compare public-safe ADE/FDE and miss-rate distributions across "
            "Waymo Motion shards, inputs, or scenario windows."
        ),
    )
    failure_stability_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help=(
            "Input Waymo Motion file/directory or ScenarioLens JSON file. "
            "Repeat this flag to compare multiple downloaded shards."
        ),
    )
    failure_stability_parser.add_argument(
        "--format",
        choices=FAILURE_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation. Native accepts Waymo Motion files.",
    )
    failure_stability_parser.add_argument(
        "--output-dir",
        default="data/processed/failure_stability",
        help="Directory for manifest.json and report.md.",
    )
    failure_stability_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=75,
        help="Maximum number of scenarios to ingest per input before analysis.",
    )
    failure_stability_parser.add_argument(
        "--window-size",
        type=int,
        default=25,
        help=(
            "Scenario count per comparison window. Use a value greater than "
            "max-scenarios to keep one slice per input."
        ),
    )
    failure_stability_parser.add_argument(
        "--top-tags",
        type=int,
        default=10,
        help="Number of tag stability rows to report.",
    )
    failure_stability_parser.add_argument(
        "--min-tag-slices",
        type=int,
        default=2,
        help="Minimum slices a tag must appear in to be included.",
    )
    failure_stability_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe report copy.",
    )
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a ranked scenario report.",
    )
    report_parser.add_argument(
        "--input",
        default=None,
        help="Optional ScenarioLens JSON file. Defaults to built-in synthetic scenarios.",
    )
    report_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report output format.",
    )
    report_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of ranked scenarios to include.",
    )
    report_parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write instead of printing to stdout.",
    )
    baseline_compare_parser = subparsers.add_parser(
        "baseline-compare",
        help="Compare constant-velocity and lane-aware prediction baselines.",
    )
    baseline_compare_parser.add_argument(
        "--input",
        default=None,
        help="Optional ScenarioLens JSON file. Defaults to built-in synthetic scenarios.",
    )
    baseline_compare_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report output format.",
    )
    baseline_compare_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of comparison rows to include.",
    )
    baseline_compare_parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write instead of printing to stdout.",
    )
    baseline_ablation_parser = subparsers.add_parser(
        "baseline-ablation",
        help=(
            "Run a no-auth ablation over constant-velocity and lane-aware "
            "prediction baseline variants."
        ),
    )
    baseline_ablation_parser.add_argument(
        "--input",
        default=None,
        help="Optional ScenarioLens JSON file. Defaults to built-in synthetic scenarios.",
    )
    baseline_ablation_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report output format.",
    )
    baseline_ablation_parser.add_argument(
        "--strict-lane-threshold",
        type=float,
        default=STRICT_LANE_MATCH_THRESHOLD_M,
        help="Lane-match threshold for the strict lane-aware variant.",
    )
    baseline_ablation_parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write instead of printing to stdout.",
    )
    baseline_compare_study_parser = subparsers.add_parser(
        "baseline-compare-study",
        help=(
            "Compare constant-velocity and lane-aware baselines across one or "
            "more Waymo Motion or ScenarioLens JSON inputs."
        ),
    )
    baseline_compare_study_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help=(
            "Input Waymo Motion file/directory or ScenarioLens JSON file. "
            "Repeat this flag to compare multiple downloaded shards."
        ),
    )
    baseline_compare_study_parser.add_argument(
        "--format",
        choices=BASELINE_COMPARISON_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation. Native accepts Waymo Motion files.",
    )
    baseline_compare_study_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_aware_baseline_cross_shard",
        help="Directory for manifest.json and report.md.",
    )
    baseline_compare_study_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum number of scenarios to ingest per input before analysis.",
    )
    baseline_compare_study_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of improvement/regression rows to report.",
    )
    baseline_compare_study_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe report copy.",
    )
    lane_selection_study_parser = subparsers.add_parser(
        "lane-selection-study",
        help=(
            "Compare nearest-lane and heading-aware lane-selection baselines "
            "across one or more inputs."
        ),
    )
    lane_selection_study_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help=(
            "Input Waymo Motion file/directory or ScenarioLens JSON file. "
            "Repeat this flag to compare multiple downloaded shards."
        ),
    )
    lane_selection_study_parser.add_argument(
        "--format",
        choices=LANE_SELECTION_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation. Native accepts Waymo Motion files.",
    )
    lane_selection_study_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_selection_study",
        help="Directory for manifest.json and report.md.",
    )
    lane_selection_study_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum number of scenarios to ingest per input before analysis.",
    )
    lane_selection_study_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of improvement/regression rows to report.",
    )
    lane_selection_study_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe report copy.",
    )
    baseline_debug_parser = subparsers.add_parser(
        "baseline-debug",
        help=(
            "Generate local SVG/debug artifacts for selected baseline or "
            "lane-selection cases."
        ),
    )
    baseline_debug_parser.add_argument(
        "--study-manifest",
        default=None,
        help=(
            "Optional baseline-compare-study or lane-selection-study manifest "
            "to auto-select improvement, regression, and fallback-heavy cases."
        ),
    )
    baseline_debug_parser.add_argument(
        "--input",
        default=None,
        help=(
            "Input Waymo Motion file/directory or ScenarioLens JSON file for "
            "direct debugging. Not required when --study-manifest is used."
        ),
    )
    baseline_debug_parser.add_argument(
        "--scenario",
        action="append",
        default=None,
        help=(
            "Scenario id to debug from --input. Repeat to render multiple "
            "cases. Defaults to the first loaded scenario."
        ),
    )
    baseline_debug_parser.add_argument(
        "--format",
        choices=BASELINE_DEBUG_INPUT_FORMATS,
        default="native",
        help="Input representation for direct --input mode.",
    )
    baseline_debug_parser.add_argument(
        "--output-dir",
        default="data/processed/baseline_debug_casebook",
        help="Ignored directory for manifest, report, and SVG debug artifacts.",
    )
    baseline_debug_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum scenarios to load per input before selecting cases.",
    )
    baseline_debug_parser.add_argument(
        "--case-count",
        type=int,
        default=3,
        help="Number of cases to select when using --study-manifest.",
    )
    baseline_debug_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe casebook copy.",
    )
    replay_candidates_parser = subparsers.add_parser(
        "replay-candidates",
        help=(
            "Turn a baseline-debug manifest into a public-safe Waymax/JAX "
            "replay candidate plan."
        ),
    )
    replay_candidates_parser.add_argument(
        "--debug-manifest",
        required=True,
        help="Manifest produced by scenariolens baseline-debug.",
    )
    replay_candidates_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_replay_candidates",
        help="Directory for replay candidate manifest.json and report.md.",
    )
    replay_candidates_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe replay plan copy.",
    )
    replay_prototype_parser = subparsers.add_parser(
        "replay-prototype",
        help=(
            "Run a laptop-safe open-loop replay and perturbation prototype "
            "for replay-ready candidates."
        ),
    )
    replay_prototype_parser.add_argument(
        "--candidate-manifest",
        required=True,
        help="Manifest produced by scenariolens replay-candidates.",
    )
    replay_prototype_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_replay_prototype",
        help="Directory for replay prototype manifest, report, and local artifacts.",
    )
    replay_prototype_parser.add_argument(
        "--top",
        type=int,
        default=2,
        help="Maximum replay-ready candidates to evaluate.",
    )
    replay_prototype_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe replay prototype copy.",
    )
    route_intent_parser = subparsers.add_parser(
        "route-intent-audit",
        help=(
            "Audit stable replay regressions for route, intent, lane-continuity, "
            "and heading-selection failure modes."
        ),
    )
    route_intent_parser.add_argument(
        "--replay-manifest",
        required=True,
        help="Manifest produced by scenariolens replay-prototype.",
    )
    route_intent_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_route_intent_audit",
        help="Directory for route/intent audit manifest, report, and local packets.",
    )
    route_intent_parser.add_argument(
        "--case-count",
        type=int,
        default=3,
        help="Maximum stable replay regression cases to audit.",
    )
    route_intent_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe route/intent audit copy.",
    )
    lane_continuation_parser = subparsers.add_parser(
        "lane-continuation-prototype",
        help=(
            "Prototype lane-link continuation for route/intent audit cases "
            "that were diagnosed as lane-continuity risks."
        ),
    )
    lane_continuation_parser.add_argument(
        "--audit-manifest",
        required=True,
        help="Manifest produced by scenariolens route-intent-audit.",
    )
    lane_continuation_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_prototype",
        help=(
            "Directory for lane-continuation prototype manifest, report, "
            "and local packets."
        ),
    )
    lane_continuation_parser.add_argument(
        "--case-count",
        type=int,
        default=3,
        help="Maximum lane-continuity audit cases to evaluate.",
    )
    lane_continuation_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe lane-continuation report copy.",
    )
    lane_continuation_study_parser = subparsers.add_parser(
        "lane-continuation-study",
        help=(
            "Scan scenario inputs for lane-end clamp candidates and compare "
            "nearest-lane vs linked-lane continuation."
        ),
    )
    lane_continuation_study_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input Waymo Motion file/directory or ScenarioLens JSON file. Repeat for shards.",
    )
    lane_continuation_study_parser.add_argument(
        "--format",
        choices=LANE_CONTINUATION_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation.",
    )
    lane_continuation_study_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_study",
        help="Directory for lane-continuation study manifest.json and report.md.",
    )
    lane_continuation_study_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum scenarios to load per input.",
    )
    lane_continuation_study_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of ranked lane-continuation rows to include.",
    )
    lane_continuation_study_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe lane-continuation study copy.",
    )
    lane_continuation_candidates_parser = subparsers.add_parser(
        "lane-continuation-candidates",
        help=(
            "Turn a lane-continuation study manifest into replay and topology "
            "audit candidate queues."
        ),
    )
    lane_continuation_candidates_parser.add_argument(
        "--study-manifest",
        required=True,
        help="Manifest produced by scenariolens lane-continuation-study.",
    )
    lane_continuation_candidates_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_candidates",
        help="Directory for candidate manifest.json and report.md.",
    )
    lane_continuation_candidates_parser.add_argument(
        "--top-per-bucket",
        type=int,
        default=5,
        help="Maximum improvement, regression, and topology rows to queue.",
    )
    lane_continuation_candidates_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe candidate plan copy.",
    )
    lane_continuation_replay_parser = subparsers.add_parser(
        "lane-continuation-replay-prototype",
        help=(
            "Execute queued lane-continuation replay controls, regression "
            "debug targets, and topology probes."
        ),
    )
    lane_continuation_replay_parser.add_argument(
        "--candidate-manifest",
        required=True,
        help="Manifest produced by scenariolens lane-continuation-candidates.",
    )
    lane_continuation_replay_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_replay_prototype",
        help=(
            "Directory for lane-continuation replay manifest, report, and "
            "local packets."
        ),
    )
    lane_continuation_replay_parser.add_argument(
        "--top-per-bucket",
        type=int,
        default=5,
        help="Maximum improvement, regression, and topology candidates to replay/probe.",
    )
    lane_continuation_replay_parser.add_argument(
        "--format",
        choices=LANE_CONTINUATION_REPLAY_INPUT_FORMATS,
        default="native",
        help="Input representation for candidate source paths.",
    )
    lane_continuation_replay_parser.add_argument(
        "--max-scenarios-per-source",
        type=int,
        default=25,
        help="Maximum scenarios to load from each candidate source.",
    )
    lane_continuation_replay_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe replay prototype copy.",
    )
    lane_continuation_route_diagnostics_parser = subparsers.add_parser(
        "lane-continuation-route-diagnostics",
        help=(
            "Classify replayed lane-continuation regressions and topology "
            "blockers into route-choice follow-up buckets."
        ),
    )
    lane_continuation_route_diagnostics_parser.add_argument(
        "--replay-manifest",
        required=True,
        help="Manifest produced by scenariolens lane-continuation-replay-prototype.",
    )
    lane_continuation_route_diagnostics_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_route_diagnostics",
        help="Directory for route/topology diagnostic manifest.json and report.md.",
    )
    lane_continuation_route_diagnostics_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum route/topology diagnostic rows to publish.",
    )
    lane_continuation_route_diagnostics_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe route/topology report copy.",
    )
    lane_continuation_branch_selection_parser = subparsers.add_parser(
        "lane-continuation-branch-selection",
        help=(
            "Enumerate parsed lane-link branch alternatives for continuation "
            "regression diagnostics."
        ),
    )
    lane_continuation_branch_selection_parser.add_argument(
        "--diagnostics-manifest",
        required=True,
        help="Manifest produced by scenariolens lane-continuation-route-diagnostics.",
    )
    lane_continuation_branch_selection_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_branch_selection",
        help="Directory for branch-selection manifest.json and report.md.",
    )
    lane_continuation_branch_selection_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Maximum regression diagnostics to branch-sweep.",
    )
    lane_continuation_branch_selection_parser.add_argument(
        "--max-hops",
        type=int,
        default=2,
        help="Maximum parsed lane-link hops to enumerate per branch.",
    )
    lane_continuation_branch_selection_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe branch-selection report copy.",
    )
    lane_continuation_branch_replay_parser = subparsers.add_parser(
        "lane-continuation-branch-replay",
        help=(
            "Replay motion-context branch choices under deterministic "
            "anchor perturbations."
        ),
    )
    lane_continuation_branch_replay_parser.add_argument(
        "--branch-selection-manifest",
        required=True,
        help="Manifest produced by scenariolens lane-continuation-branch-selection.",
    )
    lane_continuation_branch_replay_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_lane_continuation_branch_replay",
        help="Directory for branch-replay manifest.json and report.md.",
    )
    lane_continuation_branch_replay_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Maximum motion-context branch cases to replay.",
    )
    lane_continuation_branch_replay_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe branch-replay report copy.",
    )
    heading_replay_parser = subparsers.add_parser(
        "heading-replay-prototype",
        help=(
            "Run a laptop-safe nearest-lane vs heading-aware replay prototype "
            "for heading-ready candidates."
        ),
    )
    heading_replay_parser.add_argument(
        "--candidate-manifest",
        required=True,
        help="Heading-aware manifest produced by scenariolens replay-candidates.",
    )
    heading_replay_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_heading_aware_replay_prototype",
        help=(
            "Directory for heading replay prototype manifest, report, and "
            "local artifacts."
        ),
    )
    heading_replay_parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Maximum heading-ready candidates to evaluate.",
    )
    heading_replay_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe heading replay copy.",
    )
    map_match_audit_parser = subparsers.add_parser(
        "map-match-audit",
        help=(
            "Audit lane-aware fallback-heavy cases with a lane-match threshold "
            "sweep."
        ),
    )
    map_match_audit_parser.add_argument(
        "--debug-manifest",
        required=True,
        help="Manifest produced by scenariolens baseline-debug.",
    )
    map_match_audit_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_map_match_audit",
        help="Directory for map-match audit manifest, report, and local packets.",
    )
    map_match_audit_parser.add_argument(
        "--thresholds",
        default=",".join(str(value) for value in DEFAULT_AUDIT_THRESHOLDS_M),
        help="Comma-separated lane-match thresholds in meters.",
    )
    map_match_audit_parser.add_argument(
        "--case-count",
        type=int,
        default=3,
        help="Maximum fallback-heavy debug cases to audit.",
    )
    map_match_audit_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe map-match audit copy.",
    )
    context_study_parser = subparsers.add_parser(
        "context-study",
        help=(
            "Summarize public-safe map, traffic-signal, and lane-topology "
            "context from Waymo Motion slices."
        ),
    )
    context_study_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input Waymo Motion file/directory or ScenarioLens JSON file. Repeat for shards.",
    )
    context_study_parser.add_argument(
        "--format",
        choices=CONTEXT_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation.",
    )
    context_study_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_context_study",
        help="Directory for context-study manifest.json and report.md.",
    )
    context_study_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum scenarios to load per input.",
    )
    context_study_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of context-heavy scenarios to include in ranked tables.",
    )
    context_study_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe context-study copy.",
    )
    context_failure_parser = subparsers.add_parser(
        "context-failure-study",
        help=(
            "Join map/signal context summaries with baseline failure metrics "
            "for public-safe real-data diagnostics."
        ),
    )
    context_failure_parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input Waymo Motion file/directory or ScenarioLens JSON file. Repeat for shards.",
    )
    context_failure_parser.add_argument(
        "--format",
        choices=CONTEXT_FAILURE_STUDY_INPUT_FORMATS,
        default="native",
        help="Input representation.",
    )
    context_failure_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_context_failure_study",
        help="Directory for context-failure manifest.json and report.md.",
    )
    context_failure_parser.add_argument(
        "--max-scenarios",
        type=int,
        default=25,
        help="Maximum scenarios to load per input.",
    )
    context_failure_parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of ranked joined-diagnostic rows to include.",
    )
    context_failure_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe context-failure report copy.",
    )
    context_eval_parser = subparsers.add_parser(
        "context-eval-set",
        help=(
            "Turn a context-failure-study manifest into a curated public-safe "
            "evaluation set."
        ),
    )
    context_eval_parser.add_argument(
        "--context-failure-manifest",
        required=True,
        help="Manifest produced by scenariolens context-failure-study.",
    )
    context_eval_parser.add_argument(
        "--output-dir",
        default="data/processed/waymo_context_eval_set",
        help="Directory for eval-set manifest, report, and scenario_ids.txt.",
    )
    context_eval_parser.add_argument(
        "--top-per-group",
        type=int,
        default=5,
        help="Maximum ranked cases to keep in each eval group.",
    )
    context_eval_parser.add_argument(
        "--public-report",
        default=None,
        help="Optional Markdown path for a public-safe eval-set report copy.",
    )
    portfolio_parser = subparsers.add_parser(
        "portfolio-report",
        help="Generate the checked-in ScenarioLens portfolio report.",
    )
    portfolio_parser.add_argument(
        "--output",
        default="docs/reports/portfolio_report.md",
        help="Markdown report path to write.",
    )
    portfolio_parser.add_argument(
        "--assets-dir",
        default="docs/reports/assets",
        help="Directory for generated SVG assets.",
    )
    portfolio_parser.add_argument(
        "--waymo-normalized",
        default="docs/examples/waymo_motion_normalized.csv",
        help="Normalized Waymo Motion-shaped CSV fixture.",
    )
    portfolio_parser.add_argument(
        "--waymo-native",
        default="docs/examples/waymo_motion_native_sample.json",
        help="Native protobuf-shaped Waymo Motion JSON fixture.",
    )
    portfolio_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of top scenarios per section.",
    )
    dashboard_parser = subparsers.add_parser(
        "dashboard-data",
        help="Generate static JSON and SVG assets for the Scenario Explorer dashboard.",
    )
    dashboard_parser.add_argument(
        "--output",
        default="docs/demo/scenarios.json",
        help="Dashboard JSON path to write.",
    )
    dashboard_parser.add_argument(
        "--assets-dir",
        default="docs/demo/assets",
        help="Directory for dashboard SVG assets.",
    )
    dashboard_parser.add_argument(
        "--waymo-normalized",
        default="docs/examples/waymo_motion_normalized.csv",
        help="Normalized Waymo Motion-shaped CSV fixture.",
    )
    dashboard_parser.add_argument(
        "--waymo-native",
        default="docs/examples/waymo_motion_native_sample.json",
        help="Native protobuf-shaped Waymo Motion JSON fixture.",
    )
    dashboard_parser.add_argument(
        "--lane-selection-manifest",
        default=str(DEFAULT_LANE_SELECTION_MANIFEST),
        help=(
            "Optional lane-selection study manifest used to add public-safe "
            "case diagnostics to the dashboard payload."
        ),
    )
    dashboard_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of ranked scenarios to include.",
    )
    render_parser = subparsers.add_parser(
        "render",
        help="Render scenarios as SVG trajectory views.",
    )
    render_parser.add_argument(
        "--input",
        default=None,
        help="Optional ScenarioLens JSON file. Defaults to built-in synthetic scenarios.",
    )
    render_parser.add_argument(
        "--scenario",
        default=None,
        help="Scenario id to render. Defaults to the first synthetic scenario.",
    )
    render_parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Render the top N ranked scenarios into an output directory.",
    )
    render_parser.add_argument(
        "--output",
        default=None,
        help="Optional SVG path for single-scenario rendering.",
    )
    render_parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for --top rendering. Defaults to rendered/.",
    )
    args = parser.parse_args()

    if args.command == "demo":
        return demo()
    if args.command == "export-synthetic":
        return export_synthetic(output_path=args.output)
    if args.command == "ingest-csv":
        return ingest_csv(input_path=args.input, output_path=args.output)
    if args.command == "waymo-motion-status":
        return waymo_motion_status()
    if args.command == "waymo-motion-preflight":
        return waymo_motion_preflight(input_path=args.input)
    if args.command == "waymo-motion-doctor":
        return waymo_motion_doctor(
            input_path=args.input,
            output_path=args.output,
            search_common_locations=not args.no_search_common_locations,
        )
    if args.command == "waymo-motion-shard-plan":
        return waymo_motion_shard_plan_command(
            input_path=args.input,
            output_path=args.output,
            json_output_path=args.json_output,
            split=args.split,
            dataset_version=args.dataset_version,
            total_shards=args.total_shards,
            next_count=args.next_count,
        )
    if args.command == "ingest-waymo-motion":
        return ingest_waymo_motion_command(
            input_path=args.input,
            output_path=args.output,
            max_scenarios=args.max_scenarios,
            input_format=args.format,
        )
    if args.command == "waymo-motion-validate":
        return validate_waymo_motion_command(
            input_path=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
        )
    if args.command == "failure-study":
        return failure_study_command(
            input_path=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            min_tag_count=args.min_tag_count,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "failure-study-stability":
        return failure_stability_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            window_size=args.window_size,
            top_tags=args.top_tags,
            min_tag_slices=args.min_tag_slices,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "report":
        return report(
            output_format=args.format,
            limit=args.limit,
            output_path=args.output,
            input_path=args.input,
        )
    if args.command == "baseline-compare":
        return baseline_compare(
            output_format=args.format,
            limit=args.limit,
            output_path=args.output,
            input_path=args.input,
        )
    if args.command == "baseline-ablation":
        return baseline_ablation(
            output_format=args.format,
            output_path=args.output,
            input_path=args.input,
            strict_lane_threshold_m=args.strict_lane_threshold,
        )
    if args.command == "baseline-compare-study":
        return baseline_compare_study_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "lane-selection-study":
        return lane_selection_study_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "baseline-debug":
        return baseline_debug_command(
            output_dir=args.output_dir,
            input_path=args.input,
            scenario_ids=args.scenario,
            input_format=args.format,
            max_scenarios=args.max_scenarios,
            study_manifest=args.study_manifest,
            case_count=args.case_count,
            public_report=args.public_report,
        )
    if args.command == "replay-candidates":
        return replay_candidates_command(
            debug_manifest=args.debug_manifest,
            output_dir=args.output_dir,
            public_report=args.public_report,
        )
    if args.command == "replay-prototype":
        return replay_prototype_command(
            candidate_manifest=args.candidate_manifest,
            output_dir=args.output_dir,
            top=args.top,
            public_report=args.public_report,
        )
    if args.command == "route-intent-audit":
        return route_intent_audit_command(
            replay_manifest=args.replay_manifest,
            output_dir=args.output_dir,
            case_count=args.case_count,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-prototype":
        return lane_continuation_prototype_command(
            audit_manifest=args.audit_manifest,
            output_dir=args.output_dir,
            case_count=args.case_count,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-study":
        return lane_continuation_study_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-candidates":
        return lane_continuation_candidates_command(
            study_manifest=args.study_manifest,
            output_dir=args.output_dir,
            top_per_bucket=args.top_per_bucket,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-replay-prototype":
        return lane_continuation_replay_command(
            candidate_manifest=args.candidate_manifest,
            output_dir=args.output_dir,
            top_per_bucket=args.top_per_bucket,
            input_format=args.format,
            max_scenarios_per_source=args.max_scenarios_per_source,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-route-diagnostics":
        return lane_continuation_route_diagnostics_command(
            replay_manifest=args.replay_manifest,
            output_dir=args.output_dir,
            top=args.top,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-branch-selection":
        return lane_continuation_branch_selection_command(
            diagnostics_manifest=args.diagnostics_manifest,
            output_dir=args.output_dir,
            top=args.top,
            max_hops=args.max_hops,
            public_report=args.public_report,
        )
    if args.command == "lane-continuation-branch-replay":
        return lane_continuation_branch_replay_command(
            branch_selection_manifest=args.branch_selection_manifest,
            output_dir=args.output_dir,
            top=args.top,
            public_report=args.public_report,
        )
    if args.command == "heading-replay-prototype":
        return heading_replay_prototype_command(
            candidate_manifest=args.candidate_manifest,
            output_dir=args.output_dir,
            top=args.top,
            public_report=args.public_report,
        )
    if args.command == "map-match-audit":
        return map_match_audit_command(
            debug_manifest=args.debug_manifest,
            output_dir=args.output_dir,
            thresholds=args.thresholds,
            case_count=args.case_count,
            public_report=args.public_report,
        )
    if args.command == "context-study":
        return context_study_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "context-failure-study":
        return context_failure_study_command(
            input_paths=args.input,
            output_dir=args.output_dir,
            max_scenarios=args.max_scenarios,
            top=args.top,
            input_format=args.format,
            public_report=args.public_report,
        )
    if args.command == "context-eval-set":
        return context_eval_set_command(
            context_failure_manifest=args.context_failure_manifest,
            output_dir=args.output_dir,
            top_per_group=args.top_per_group,
            public_report=args.public_report,
        )
    if args.command == "portfolio-report":
        return portfolio_report(
            output_path=args.output,
            assets_dir=args.assets_dir,
            waymo_normalized_path=args.waymo_normalized,
            waymo_native_path=args.waymo_native,
            top_n=args.top,
        )
    if args.command == "dashboard-data":
        return dashboard_data(
            output_path=args.output,
            assets_dir=args.assets_dir,
            waymo_normalized_path=args.waymo_normalized,
            waymo_native_path=args.waymo_native,
            lane_selection_manifest_path=args.lane_selection_manifest,
            limit=args.limit,
        )
    if args.command == "render":
        return render(
            scenario_id=args.scenario,
            top=args.top,
            output_path=args.output,
            output_dir=args.output_dir,
            input_path=args.input,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
