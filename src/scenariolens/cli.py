from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from scenariolens.dashboard import generate_dashboard_data
from scenariolens.ingest.csv_tracks import save_track_csv_as_scenarios
from scenariolens.ingest.waymo_motion import (
    adapter_status,
    inspect_waymo_motion_slice,
    save_normalized_motion_csv_as_scenarios,
    save_waymo_motion_as_scenarios,
    waymo_motion_slice_ready,
)
from scenariolens.io import load_scenarios, save_scenarios
from scenariolens.portfolio import generate_portfolio_report
from scenariolens.report import json_report, markdown_report, ranked_scores
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario
from scenariolens.slice_validation import validate_waymo_motion_slice
from scenariolens.visualize import scenario_svg
from scenariolens.waymo_readiness import (
    DEFAULT_WAYMO_MOTION_INPUT,
    inspect_waymo_motion_readiness,
)


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
    if result.assets_dir is not None:
        print(f"SVG gallery: {result.assets_dir}")
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
    limit: int | None,
) -> int:
    generate_dashboard_data(
        output_path=output_path,
        assets_dir=assets_dir,
        waymo_normalized_path=waymo_normalized_path,
        waymo_native_path=waymo_native_path,
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
    if args.command == "report":
        return report(
            output_format=args.format,
            limit=args.limit,
            output_path=args.output,
            input_path=args.input,
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
