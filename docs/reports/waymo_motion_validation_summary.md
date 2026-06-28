# Waymo Motion Validation Slice Summary

This note summarizes a local ScenarioLens run against one downloaded Waymo Open
Dataset Motion validation shard. Raw Waymo files and per-scenario derived
outputs are intentionally kept out of git.

## Source

- Dataset: Waymo Open Dataset Motion
- Version: `waymo_open_dataset_motion_v_1_3_1`
- Split: `uncompressed/scenario/validation`
- Local shard: `validation.tfrecord-00007-of-00150`
- Local raw path: `data/raw/waymo/motion/validation/`
- File size: 246,887,249 bytes
- Access path: official Waymo Open Dataset download flow

## Command

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

## Result

- Ready for ingestion: true
- Supported files: 1
- Supported format: `.tfrecord`
- Scenarios ingested: 25
- Top scenarios reported: 5
- Parser: dependency-free TFRecord reader plus lightweight Waymo Motion
  `Scenario` proto field extraction
- Case study: [Waymo Motion Real-Data Case Study](waymo_motion_case_study.md)
- Failure study: [Waymo Motion Real-Slice Failure Study](waymo_motion_failure_study.md)

## Aggregate Metrics

- Score range: 19.48 min / 41.06 median / 39.29 mean / 51.43 max
- Average raw agents: 59.40
- Average scored agents: 58.72
- Low-quality track rate: 1.14%
- Scenarios with VRUs: 19 of 25
- Prediction targets: 101
- Objects of interest: 18
- Scenarios with parsed map features: 25
- Baseline targets evaluated: 101
- Mean baseline ADE / FDE: 10.49 m / 27.55 m
- Max baseline FDE: 69.32 m
- Weighted baseline miss rate: 96.04%

| Rank | Scenario | Score | Main Reason |
| ---: | --- | ---: | --- |
| 1 | `7e969997e3e0b772` | 51.427 | contains 9 vulnerable road users |
| 2 | `706fecd25045c8d` | 51.325 | contains 7 vulnerable road users |
| 3 | `770fec53ec3e0395` | 50.890 | contains 4 vulnerable road users |
| 4 | `d30709cd60e60395` | 50.759 | contains 14 vulnerable road users |
| 5 | `67fff4d5bb3acf8d` | 50.543 | contains 9 vulnerable road users |

## Notes

- The run proves the local pipeline can ingest a real Waymo Motion TFRecord
  shard on an Apple Silicon laptop without TensorFlow or the Waymo Python
  package.
- ScenarioLens extracts the fields needed for current ranking and rendering:
  scenario id, timestamps, tracks, object types, states, SDC index, objects of
  interest, prediction targets, and coarse map/traffic-signal presence.
- The current metrics are screening features, not certified safety metrics.
  Ranking now uses a quality-filtered, ego-centered scoring context plus a
  calibrated constant-velocity baseline failure component, and reports raw
  agent counts separately from scored agent counts.
- Raw Waymo data, normalized ScenarioLens JSON from the shard, and generated
  SVGs remain ignored local artifacts unless licensing and publication choices
  are reviewed separately.
