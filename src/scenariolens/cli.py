from __future__ import annotations

import argparse
from pathlib import Path

from scenariolens.report import json_report, markdown_report
from scenariolens.samples import synthetic_scenarios


def demo() -> int:
    print(json_report(synthetic_scenarios()))
    return 0


def report(output_format: str, limit: int | None, output_path: str | None) -> int:
    scenarios = synthetic_scenarios()
    if output_format == "json":
        content = json_report(scenarios, limit=limit)
    else:
        content = markdown_report(scenarios, limit=limit)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="scenariolens",
        description="Long-tail autonomous-driving scenario discovery utilities.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="Score built-in synthetic scenarios.")
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a ranked scenario report from built-in synthetic scenarios.",
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
    args = parser.parse_args()

    if args.command == "demo":
        return demo()
    if args.command == "report":
        return report(
            output_format=args.format,
            limit=args.limit,
            output_path=args.output,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
