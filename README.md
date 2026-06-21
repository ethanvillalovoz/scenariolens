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

## First Milestone

The first milestone is a complete local prototype on synthetic and small curated
scenario records:

- define a scenario schema,
- compute risk/interaction features,
- rank scenarios,
- export a simple report,
- then replace synthetic inputs with a small Waymo Open Dataset slice.

See [docs/project_brief.md](docs/project_brief.md) and
[docs/roadmap.md](docs/roadmap.md).

## Local Commands

Run the starter demo without installing the package:

```bash
PYTHONPATH=src python3 -m scenariolens.cli demo
```

Run tests with only the Python standard library:

```bash
PYTHONPATH=src python3 -m unittest discover
```
