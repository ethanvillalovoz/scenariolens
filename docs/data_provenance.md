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

## No-Auth Technical Proof

When authenticated Waymo shard downloads are unavailable, ScenarioLens still
has a reproducible local technical path:

```bash
PYTHONPATH=src python3 -m scenariolens.cli baseline-ablation \
  --format markdown \
  --output docs/reports/baseline_ablation_study.md
```

The ablation compares constant velocity, default lane-aware matching, and a
stricter lane-aware matcher over the checked-in fixture corpus. It is not a
dataset-scale claim; it is a no-auth proof that the framework can compare
baseline assumptions, summarize map-use/fallback behavior, and publish a
public-safe report while gated downloads remain blocked.

## Real Dataset Path

ScenarioLens has a local workflow for a downloaded public Waymo Motion slice:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

This command writes a preflight summary, normalized ScenarioLens JSON, a ranked
Markdown report, a rendered SVG gallery, and a machine-readable manifest.

Raw downloaded dataset files are intentionally ignored by git. Keep them under
`data/raw/` and follow the official dataset access terms.

A local smoke run has been completed on one Waymo Motion v1.3.1 validation
shard. The summary is checked in at
[`docs/reports/waymo_motion_validation_summary.md`](reports/waymo_motion_validation_summary.md);
the aggregate case study is checked in at
[`docs/reports/waymo_motion_case_study.md`](reports/waymo_motion_case_study.md);
the raw shard, normalized scenario JSON, and generated SVG gallery remain local
ignored artifacts.

A follow-up cross-shard stability run has also been completed over four local
validation shards (`00007` through `00010`), covering 100 real scenarios and
418 evaluated baseline targets. The public-safe aggregate report is checked in
at
[`docs/reports/waymo_motion_failure_stability_cross_shard.md`](reports/waymo_motion_failure_stability_cross_shard.md).
The raw TFRecord files and per-scenario derived outputs remain ignored local
artifacts.

The same four-shard slice now has a lane-aware baseline diagnostic comparing
constant-velocity and lightweight map-following forecasts over 418 evaluated
prediction targets. The report is checked in at
[`docs/reports/waymo_lane_aware_baseline_cross_shard.md`](reports/waymo_lane_aware_baseline_cross_shard.md).
It publishes both improvements and regressions: in this run, the naive
lane-aware baseline improved several individual scenarios but regressed overall,
which is useful evidence for the next replay or richer-map baseline step.

## Interpretation Rules

- Checked-in metrics demonstrate the ScenarioLens pipeline, not Waymo benchmark
  performance.
- Synthetic scenarios are useful for testing expected long-tail patterns before
  spending time on large downloads.
- Waymo-shaped fixtures prove field mapping and ingestion behavior, not dataset
  scale.
- The checked-in validation and stability reports document small local
  real-data runs, not full Waymo benchmark submissions.
