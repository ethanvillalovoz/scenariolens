from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from scenariolens.metrics import score_scenario
from scenariolens.samples import synthetic_scenarios


def demo() -> int:
    scores = sorted(
        (score_scenario(scenario) for scenario in synthetic_scenarios()),
        key=lambda item: item.interaction_score,
        reverse=True,
    )
    print(json.dumps([asdict(score) for score in scores], indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="scenariolens",
        description="Long-tail autonomous-driving scenario discovery utilities.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="Score built-in synthetic scenarios.")
    args = parser.parse_args()

    if args.command == "demo":
        return demo()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

