# Contributing To ScenarioLens

ScenarioLens is a lightweight autonomy scenario evaluation framework. The best
contributions make the tool more reproducible, public-safe, and useful for
scenario mining, baseline failure analysis, or visualization.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover
node --check docs/demo/app.js
```

Preview the static explorer:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/demo/`.

## Contribution Areas

- Dataset adapters for public motion-scenario formats.
- Interpretable scenario metrics and baseline evaluators.
- Public-safe reports that avoid committing raw dataset records.
- Static dashboard improvements backed by deterministic JSON/SVG assets.
- Documentation, examples, and release polish.

## Data And Safety Rules

- Do not commit raw Waymo Open Dataset files.
- Do not commit generated per-scenario outputs from gated datasets unless the
  license and terms allow it.
- Public reports should use aggregate statistics, scenario IDs, and reproducible
  commands rather than raw tracks.
- Avoid claims that ScenarioLens is a production AV stack, a Waymo internal
  tool, or a benchmark on the full Waymo dataset.

## Pull Request Checklist

- Run `PYTHONPATH=src python -m unittest discover`.
- Run `node --check docs/demo/app.js` when dashboard code changes.
- Run `git diff --check`.
- Update docs when CLI commands, report formats, or public workflows change.
- Include screenshots when changing the explorer UI.

## Development Style

Keep the core package dependency-light. Prefer deterministic fixtures, explicit
schemas, and small public-safe artifacts over opaque demos that require private
data or heavyweight setup.
