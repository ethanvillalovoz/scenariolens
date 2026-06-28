"""Check that key local documentation files exist.

Run from the repo root:
    python scripts/check_links.py

Exits with status 0 if all checked files are present, 1 otherwise.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Local files that must exist for the public docs surface to be intact.
REQUIRED_FILES = [
    "README.md",
    "docs/demo/index.html",
    "docs/project_strategy.md",
    *[str(p.relative_to(REPO_ROOT)) for p in sorted((REPO_ROOT / "docs/reports").glob("*.md"))],
]


def main() -> int:
    missing = []
    for rel in REQUIRED_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            missing.append(rel)

    if missing:
        print("ERROR: the following required documentation files are missing:")
        for f in missing:
            print(f"  - {f}")
        return 1

    print(f"OK: all {len(REQUIRED_FILES)} required documentation files present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
