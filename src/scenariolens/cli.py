from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scenariolens.ingest.csv_tracks import save_track_csv_as_scenarios
from scenariolens.ingest.waymo_motion import adapter_status, ingest_waymo_motion
from scenariolens.io import load_scenarios, save_scenarios
from scenariolens.report import json_report, markdown_report, ranked_scores
from scenariolens.samples import synthetic_scenarios
from scenariolens.schema import Scenario
from scenariolens.visualize import scenario_svg


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


def ingest_waymo_motion_command(
    input_path: str,
    output_path: str,
    max_scenarios: int | None,
) -> int:
    try:
        ingest_waymo_motion(
            input_path=input_path,
            output_path=output_path,
            max_scenarios=max_scenarios,
        )
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
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
    waymo_parser = subparsers.add_parser(
        "ingest-waymo-motion",
        help="Planned optional Waymo Motion Dataset ingestion adapter.",
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
    if args.command == "ingest-waymo-motion":
        return ingest_waymo_motion_command(
            input_path=args.input,
            output_path=args.output,
            max_scenarios=args.max_scenarios,
        )
    if args.command == "report":
        return report(
            output_format=args.format,
            limit=args.limit,
            output_path=args.output,
            input_path=args.input,
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
