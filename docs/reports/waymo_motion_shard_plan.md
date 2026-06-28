# ScenarioLens Waymo Motion Shard Expansion Plan

This report inventories local Waymo Motion validation shards and lists the next small downloads needed for a true cross-shard stability run. Raw Waymo files remain outside git.

## Current Inventory

| Field | Value |
| --- | ---: |
| Input path | `data/raw/waymo/motion/validation` |
| Input exists | True |
| Split | `validation` |
| Dataset version | `waymo_open_dataset_motion_v_1_3_1` |
| Local shards | 1 / 150 |
| Local coverage | 0.67% |

## Local Shards

| Shard | Size | Path |
| ---: | ---: | --- |
| 7 | 235.45 MB | `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150` |

## Recommended Next Downloads

| Shard | GCS URI | Local Path |
| ---: | --- | --- |
| 8 | `gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00008-of-00150` | `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150` |
| 9 | `gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00009-of-00150` | `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150` |
| 10 | `gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00010-of-00150` | `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150` |

## Download Commands

```bash
gsutil cp gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00008-of-00150 data/raw/waymo/motion/validation/
gsutil cp gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00009-of-00150 data/raw/waymo/motion/validation/
gsutil cp gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/scenario/validation/validation.tfrecord-00010-of-00150 data/raw/waymo/motion/validation/
```

If `gsutil` returns a 401, complete the official Waymo Open Dataset access flow and authenticate `gcloud` before rerunning the commands.

## Auth Gate Status

Checked on 2026-06-28:

- `gcloud auth list` reported no credentialed accounts.
- `gsutil ls` for shard `00008` returned a 401 anonymous-caller error.
- Cross-shard downloads remain gated; the v0.2.0 release proceeds with the
  checked-in 75-scenario windowed study and the lane-aware baseline comparison.

## Cross-Shard Stability Command

Run this after the recommended shard files exist locally:

```bash
PYTHONPATH=src python3 -m scenariolens.cli failure-study-stability \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --output-dir data/processed/waymo_motion_failure_stability_cross_shard \
  --max-scenarios 25 \
  --window-size 25 \
  --top-tags 10 \
  --min-tag-slices 2 \
  --public-report docs/reports/waymo_motion_failure_stability_cross_shard.md
```

## Notes

- This is a download and analysis plan, not a checked-in raw-data artifact.
- Use repeated `--input` paths for cross-shard stability so each shard is treated as its own comparison slice.
