# ScenarioLens Failure Distribution Stability Study

This report compares public-safe aggregate baseline-failure statistics across real-data slices. Raw Waymo files and per-scenario derived outputs remain outside git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Comparison mode: cross-input comparison
- Ready for analysis: True
- Slices compared: 4
- Scenarios analyzed: 100
- Evaluated baseline targets: 418
- Max scenarios per input: 25
- Window size: 25
- Raw scenario data committed: no

## Executive Findings

| Metric | Value |
| --- | ---: |
| Mean FDE min / max / range | 21.20 m / 28.89 m / 7.69 m |
| Miss-rate min / max / range | 91.38% / 96.04% / 4.66% |
| Highest mean-FDE slice | `input_04` |
| Lowest mean-FDE slice | `input_03` |
| Most variable tag | `cyclist_interaction` (14.48 m FDE range) |

## Slice Distribution

| Slice | Scenarios | Targets | Mean ADE | Mean FDE | Miss Rate | Top FDE Tag | Hardest Scenario |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `input_01` | 25 | 101 | 10.17 m | 26.66 m | 96.04% | `objects_of_interest` | `5c8f9e7af4b0248a` |
| `input_02` | 25 | 94 | 9.20 m | 25.24 m | 94.68% | `dense_multi_agent` | `8d4ff03a0b364739` |
| `input_03` | 25 | 107 | 7.81 m | 21.20 m | 94.39% | `objects_of_interest` | `b2b7c2ad7bcd134b` |
| `input_04` | 25 | 116 | 10.87 m | 28.89 m | 91.38% | `dense_multi_agent` | `7c8b1da44fecf0ba` |

## Tag Stability

| Tag | Slices | Scenarios | Targets | Mean FDE | FDE Range | Miss-Rate Range | Highest FDE Slice |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `cyclist_interaction` | 4 | 21 | 102 | 17.84 m | 14.48 m | 26.13% | `input_02` |
| `objects_of_interest` | 4 | 33 | 164 | 25.97 m | 10.14 m | 11.51% | `input_01` |
| `map_context` | 4 | 100 | 418 | 25.50 m | 7.69 m | 4.66% | `input_04` |
| `tracks_to_predict` | 4 | 100 | 418 | 25.50 m | 7.69 m | 4.66% | `input_04` |
| `traffic_signal_context` | 4 | 100 | 418 | 25.50 m | 7.69 m | 4.66% | `input_04` |
| `dense_multi_agent` | 4 | 99 | 417 | 25.47 m | 7.69 m | 4.62% | `input_04` |
| `vulnerable_road_user` | 4 | 80 | 356 | 24.02 m | 4.84 m | 6.04% | `input_04` |

## Hardest Slice Representatives

| Slice | Scenario | FDE | Miss Rate | Tags |
| --- | --- | ---: | ---: | --- |
| `input_01` | `5c8f9e7af4b0248a` | 69.32 m | 100.00% | `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` |
| `input_02` | `8d4ff03a0b364739` | 59.53 m | 100.00% | `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` |
| `input_03` | `b2b7c2ad7bcd134b` | 55.05 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` |
| `input_04` | `7c8b1da44fecf0ba` | 63.74 m | 100.00% | `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` |

## Interpretation

- This is a distribution screen, not a benchmark claim.
- Large FDE range across slices means the constant-velocity baseline fails unevenly across sampled scenario families.
- This run uses repeated `--input` values, so each downloaded shard is treated as its own cross-input comparison slice.
