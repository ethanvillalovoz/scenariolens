# Data Provenance

ScenarioLens is intentionally honest about what is checked into git and what is
expected to live only on a developer machine.

## Current Public Demo Data

| Dataset in demo | Files | What it is | What it is not |
| --- | --- | --- | --- |
| Synthetic scenarios | `src/scenariolens/samples.py` | Hand-authored scenario records that exercise ranking, taxonomy, metrics, reports, and rendering. | Not recorded driving data and not a Waymo validation shard. |
| Native Waymo Motion JSON mini-slice | `docs/examples/waymo_motion_native_sample.json` | A tiny protobuf-shaped JSON fixture that mirrors key public Waymo Motion `Scenario` fields such as timestamps, SDC track index, tracks, states, object types, valid flags, velocities, objects of interest, and tracks to predict. | Not a downloaded Waymo Open Dataset file. |
| Normalized Waymo-shaped CSV fixture | `docs/examples/waymo_motion_normalized.csv` | A tiny row-wise fixture shaped like an extracted Motion slice so the CSV ingestion boundary can be tested without optional dependencies. | Not raw Waymo data and not benchmark evidence. |

The static explorer at `docs/demo/` is generated from these small fixtures so
the repository remains lightweight, reviewable, and safe to clone.

## Real Dataset Path

ScenarioLens has a local workflow for a downloaded public Waymo Motion slice:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-preflight \
  --input data/raw/waymo/motion/validation
```

Then, after optional Waymo/TensorFlow dependencies are available:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format native \
  --input data/raw/waymo/motion/validation \
  --output data/processed/waymo_motion_validation_sample.json \
  --max-scenarios 25
```

Raw downloaded dataset files are intentionally ignored by git. Keep them under
`data/raw/` and follow the official dataset access terms.

## Interpretation Rules

- Checked-in metrics demonstrate the ScenarioLens pipeline, not Waymo benchmark
  performance.
- Synthetic scenarios are useful for testing expected long-tail patterns before
  spending time on large downloads.
- Waymo-shaped fixtures prove field mapping and ingestion behavior, not dataset
  scale.
- The next production milestone is to run the same ranking/report/render path on
  a small downloaded Waymo Motion validation slice and document the slice size,
  commands, and output summary.

