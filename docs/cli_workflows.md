# ScenarioLens CLI Workflows

This page collects the copy-paste workflows that make ScenarioLens feel like a
real framework instead of a one-off script.

## Install Locally

```bash
python -m pip install -e .
scenariolens --help
```

If your system Python is externally managed, create a virtualenv first:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover
```

## Synthetic Demo

```bash
scenariolens demo
scenariolens report --format markdown --limit 5
scenariolens render --top 3 --output-dir /tmp/scenariolens-gallery
```

## Waymo-Shaped Fixtures

```bash
scenariolens ingest-waymo-motion \
  --format native \
  --input docs/examples/waymo_motion_native_sample.json \
  --output /tmp/scenariolens-waymo-native.json

scenariolens report \
  --input /tmp/scenariolens-waymo-native.json \
  --format markdown \
  --limit 5
```

## Local Waymo Motion Slice

Raw Waymo files stay outside git under `data/raw/`.

```bash
scenariolens waymo-motion-doctor \
  --input data/raw/waymo/motion/validation \
  --output data/processed/waymo_motion_readiness.json

scenariolens waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

## Failure Study

```bash
scenariolens failure-study \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_failure_study \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_motion_failure_study.md
```

## Baseline Comparison

```bash
scenariolens baseline-compare \
  --format markdown \
  --limit 8 \
  --output docs/reports/lane_aware_baseline_study.md
```

This compares the default constant-velocity baseline against the lane-aware
baseline. Vehicles and cyclists use parsed lane polylines when map context is
available; pedestrians, missing maps, low-speed tracks, and distant lane matches
fall back to constant velocity.

## Stability Study

```bash
scenariolens failure-study-stability \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_failure_stability \
  --max-scenarios 75 \
  --window-size 25 \
  --top-tags 10 \
  --min-tag-slices 2 \
  --public-report docs/reports/waymo_motion_failure_stability.md
```

## Shard Expansion Plan

```bash
scenariolens waymo-motion-shard-plan \
  --input data/raw/waymo/motion/validation \
  --output docs/reports/waymo_motion_shard_plan.md \
  --json-output data/processed/waymo_motion_shard_plan.json \
  --next-count 3
```

## Dashboard Assets

```bash
scenariolens dashboard-data \
  --output docs/demo/scenarios.json \
  --assets-dir docs/demo/assets
```

Then preview:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000/demo/`.
