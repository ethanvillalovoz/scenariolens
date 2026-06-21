# ScenarioLens

ScenarioLens is a local-first autonomous-driving project for discovering, tagging,
and evaluating long-tail driving scenarios.

The project is designed as a Waymo-targeted portfolio artifact: it demonstrates
interest in autonomous driving while staying realistic on a laptop-scale setup.
Instead of trying to build a full self-driving stack, ScenarioLens focuses on a
problem that appears across perception, prediction, planning, simulation, and
safety evaluation:

> Which rare driving scenarios deserve targeted evaluation before an autonomous
> driving system is trusted in a new operating domain?

## Project Thesis

Autonomous driving systems do not only need high average performance. They need
evidence that they behave well in rare, interactive, safety-relevant situations:
occlusions, unprotected turns, cyclists, pedestrians, blocked lanes, unusual
merges, and other long-tail cases.

ScenarioLens will build a small but polished pipeline that can:

1. Ingest curated autonomous-driving scenario data.
2. Compute lightweight interaction and risk features.
3. Tag scenarios by ODD-relevant attributes.
4. Rank scenarios for evaluation value.
5. Present the results in a searchable demo/dashboard.

## Hardware-Conscious Scope

This repo is intentionally scoped for an Apple Silicon laptop with 32 GB RAM and
1 TB storage.

- Work from curated slices, not full raw datasets.
- Store raw dataset files outside git.
- Prefer metadata indexes over repeatedly scanning large files.
- Begin with motion/scenario data before heavy image/LiDAR workloads.
- Make cloud/GPU usage optional, not required for the core demo.

## Initial Repo Layout

```text
docs/                 Project brief, data strategy, and roadmap
src/scenariolens/     Lightweight Python package
tests/                Unit tests for metrics and tagging logic
data/                 Local data mount points, ignored by git
notebooks/            Experiments and exploratory analysis
```

## Current Milestone

The first milestone is a complete local prototype on synthetic and small curated
scenario records. The current prototype can:

- define a compact scenario schema,
- compute lightweight risk/interaction features,
- normalize and infer scenario taxonomy tags,
- rank 10 synthetic scenarios by evaluation value,
- save/load ScenarioLens scenario JSON,
- export Markdown or JSON reports,
- render 2D SVG trajectory views,
- run without external dependencies.

See [docs/project_brief.md](docs/project_brief.md) and
[docs/roadmap.md](docs/roadmap.md).

## Portfolio Report

For a quick project overview, see the generated
[ScenarioLens Portfolio Report](docs/reports/portfolio_report.md). It summarizes
the ranking pipeline, top synthetic scenarios, normalized Waymo-shaped fixture
results, limitations, and next work.

## Example Gallery

The current top-ranked synthetic scenarios are checked in under
[docs/examples/top_scenarios](docs/examples/top_scenarios).

![Dense intersection VRU scenario](docs/examples/top_scenarios/synthetic_dense_intersection_vru.svg)

![Occluded pedestrian scenario](docs/examples/top_scenarios/synthetic_occluded_pedestrian.svg)

![Unprotected left turn scenario](docs/examples/top_scenarios/synthetic_unprotected_left_turn.svg)

## Local Commands

Run the starter demo without installing the package:

```bash
PYTHONPATH=src python3 -m scenariolens.cli demo
```

Generate a ranked Markdown report:

```bash
PYTHONPATH=src python3 -m scenariolens.cli report --format markdown --limit 5
```

Generate a machine-readable JSON report:

```bash
PYTHONPATH=src python3 -m scenariolens.cli report --format json --limit 5
```

Export the synthetic corpus as ScenarioLens JSON:

```bash
PYTHONPATH=src python3 -m scenariolens.cli export-synthetic --output data/processed/synthetic_scenarios.json
```

Run a report from a scenario JSON file:

```bash
PYTHONPATH=src python3 -m scenariolens.cli report \
  --input data/processed/synthetic_scenarios.json \
  --format markdown \
  --limit 5
```

Ingest a small row-wise CSV fixture:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-csv \
  --input data/raw/example_tracks.csv \
  --output data/processed/example_scenarios.json
```

Ingest the checked-in Waymo Motion-shaped normalized fixture:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format normalized-csv \
  --input docs/examples/waymo_motion_normalized.csv \
  --output data/processed/waymo_motion_normalized.json
```

Render one scenario as SVG:

```bash
PYTHONPATH=src python3 -m scenariolens.cli render \
  --scenario synthetic_occluded_pedestrian \
  --output /tmp/synthetic_occluded_pedestrian.svg
```

Render a top-ranked scenario gallery:

```bash
PYTHONPATH=src python3 -m scenariolens.cli render --top 3 --output-dir /tmp/scenariolens-gallery
```

Regenerate the checked-in portfolio report:

```bash
PYTHONPATH=src python3 -m scenariolens.cli portfolio-report \
  --output docs/reports/portfolio_report.md \
  --assets-dir docs/reports/assets \
  --top 3
```

Run tests with only the Python standard library:

```bash
PYTHONPATH=src python3 -m unittest discover
```

## Scenario Categories

The first taxonomy covers high-signal autonomy-evaluation cases:

- vulnerable road users,
- pedestrian crossings,
- cyclist interactions,
- merge conflicts,
- unprotected turns,
- blocked lanes,
- stopped vehicles,
- hard braking,
- close interactions,
- dense multi-agent scenes,
- low-interaction baselines.

See [docs/scenario_taxonomy.md](docs/scenario_taxonomy.md).

## Data Format

ScenarioLens JSON is documented in [docs/data_format.md](docs/data_format.md).
Dataset ingestion is documented in [docs/ingestion.md](docs/ingestion.md).
