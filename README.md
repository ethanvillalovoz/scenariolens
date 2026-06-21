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
- export Markdown or JSON reports,
- run without external dependencies.

See [docs/project_brief.md](docs/project_brief.md) and
[docs/roadmap.md](docs/roadmap.md).

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
