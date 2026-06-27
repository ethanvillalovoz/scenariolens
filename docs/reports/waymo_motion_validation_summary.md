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

| Rank | Scenario | Score | Main Reason |
| ---: | --- | ---: | --- |
| 1 | `a651202aa8e79d45` | 69.920 | contains 22 vulnerable road users |
| 2 | `5f5660d70a6f14f6` | 59.105 | contains 16 vulnerable road users |
| 3 | `d30709cd60e60395` | 54.781 | contains 14 vulnerable road users |
| 4 | `7e969997e3e0b772` | 47.730 | contains 9 vulnerable road users |
| 5 | `67fff4d5bb3acf8d` | 45.501 | contains 9 vulnerable road users |

## Notes

- The run proves the local pipeline can ingest a real Waymo Motion TFRecord
  shard on an Apple Silicon laptop without TensorFlow or the Waymo Python
  package.
- ScenarioLens extracts the fields needed for current ranking and rendering:
  scenario id, timestamps, tracks, object types, states, SDC index, objects of
  interest, prediction targets, and coarse map/traffic-signal presence.
- The current metrics are screening features, not certified safety metrics.
- Raw Waymo data, normalized ScenarioLens JSON from the shard, and generated
  SVGs remain ignored local artifacts unless licensing and publication choices
  are reviewed separately.
