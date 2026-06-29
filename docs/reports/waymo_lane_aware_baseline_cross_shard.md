# ScenarioLens Real Waymo Lane-Aware Baseline Study

This report compares the default constant-velocity prediction baseline against ScenarioLens' lightweight lane-aware baseline over public-safe aggregate scenario slices. Raw Waymo files and per-scenario derived outputs remain outside git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Ready for analysis: True
- Sources compared: 4
- Scenarios analyzed: 100
- Evaluated prediction targets: 418
- Max scenarios per input: 25
- Raw scenario data committed: no

## Executive Findings

| Metric | Constant velocity | Lane-aware | Delta / Count |
| --- | ---: | ---: | ---: |
| Mean ADE | 9.415 m | 12.305 m | n/a |
| Mean FDE | 25.564 m | 31.067 m | -5.503 m |
| Miss rate | 94.0% | 93.8% | n/a |
| Target handling | n/a | n/a | 137 map-used / 281 fallback |

## Per-Source Summary

| Source | Scenarios | Targets | CV FDE | Lane FDE | FDE delta | CV miss | Lane miss | Map used | Fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 25 | 101 | 26.663 m | 34.139 m | -7.476 m | 96.0% | 96.0% | 36 | 65 |
| `validation.tfrecord-00008-of-00150` | 25 | 94 | 25.238 m | 30.666 m | -5.428 m | 94.7% | 94.7% | 29 | 65 |
| `validation.tfrecord-00009-of-00150` | 25 | 107 | 21.204 m | 25.070 m | -3.866 m | 94.4% | 93.5% | 32 | 75 |
| `validation.tfrecord-00010-of-00150` | 25 | 116 | 28.893 m | 34.247 m | -5.354 m | 91.4% | 91.4% | 40 | 76 |

## Fallback Reasons

- `target_too_far_from_lane`: 210
- `non_vehicle_or_cyclist_target`: 41
- `low_or_invalid_anchor_speed`: 27
- `no_lane_map_features`: 3

## Largest Lane-Aware Improvements

| Rank | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback reason |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 3 | 55.051 m | 40.900 m | +14.151 m | 3 | 0 | `none` |
| 2 | `validation.tfrecord-00007-of-00150` | `2a3333bf80e243c6` | 1 | 40.106 m | 28.529 m | +11.577 m | 1 | 0 | `none` |
| 3 | `validation.tfrecord-00009-of-00150` | `260785192cf6c991` | 7 | 31.218 m | 20.614 m | +10.604 m | 2 | 5 | `target_too_far_from_lane (5)` |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 2 | 57.623 m | 51.031 m | +6.592 m | 2 | 0 | `none` |
| 5 | `validation.tfrecord-00007-of-00150` | `c38351406efe25f7` | 7 | 24.130 m | 17.661 m | +6.469 m | 3 | 4 | `low_or_invalid_anchor_speed (2)` |
| 6 | `validation.tfrecord-00009-of-00150` | `9d8102fede02a0` | 2 | 16.468 m | 10.869 m | +5.599 m | 1 | 1 | `non_vehicle_or_cyclist_target (1)` |
| 7 | `validation.tfrecord-00009-of-00150` | `960befeb46843095` | 6 | 13.824 m | 9.858 m | +3.966 m | 3 | 3 | `target_too_far_from_lane (2)` |
| 8 | `validation.tfrecord-00008-of-00150` | `52970d613186713a` | 1 | 39.854 m | 36.067 m | +3.787 m | 1 | 0 | `none` |
| 9 | `validation.tfrecord-00010-of-00150` | `f669c226f3292cf7` | 3 | 8.225 m | 6.102 m | +2.123 m | 1 | 2 | `non_vehicle_or_cyclist_target (2)` |
| 10 | `validation.tfrecord-00010-of-00150` | `72cc84f24cc08d18` | 7 | 18.768 m | 17.036 m | +1.732 m | 3 | 4 | `target_too_far_from_lane (3)` |

## Largest Lane-Aware Regressions

Negative deltas mean the naive lane-following baseline had higher FDE than constant velocity. Those rows are useful diagnostics for map matching, lane direction, and behavior assumptions.

| Rank | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback reason |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | 1 | 3.152 m | 144.514 m | -141.362 m | 1 | 0 | `none` |
| 2 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | 2 | 7.576 m | 141.108 m | -133.532 m | 2 | 0 | `none` |
| 3 | `validation.tfrecord-00008-of-00150` | `ef4c5d0e40fdea48` | 1 | 46.688 m | 110.266 m | -63.578 m | 1 | 0 | `none` |
| 4 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 3 | 22.523 m | 65.007 m | -42.484 m | 2 | 1 | `low_or_invalid_anchor_speed (1)` |
| 5 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | 8 | 11.285 m | 45.671 m | -34.386 m | 6 | 2 | `low_or_invalid_anchor_speed (1)` |
| 6 | `validation.tfrecord-00009-of-00150` | `f2f8b5f3501ae33a` | 2 | 32.950 m | 64.437 m | -31.487 m | 1 | 1 | `target_too_far_from_lane (1)` |
| 7 | `validation.tfrecord-00009-of-00150` | `3a2a03200cd1663e` | 4 | 25.233 m | 48.198 m | -22.965 m | 3 | 1 | `target_too_far_from_lane (1)` |
| 8 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 8 | 27.509 m | 48.599 m | -21.090 m | 5 | 3 | `target_too_far_from_lane (3)` |
| 9 | `validation.tfrecord-00007-of-00150` | `46c1c1fbe5ef29d1` | 6 | 20.759 m | 41.729 m | -20.970 m | 3 | 3 | `target_too_far_from_lane (2)` |
| 10 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | 4 | 33.797 m | 53.772 m | -19.975 m | 3 | 1 | `target_too_far_from_lane (1)` |

## Interpretation

- The lane-aware mean FDE is higher in this run, which is useful: it exposes cases where nearest-lane following is too naive.
- Lane-aware is intentionally conservative: pedestrians, missing maps, low-speed targets, and distant lane matches fall back to constant velocity.
- A regression is not a project failure. It marks a scenario where the simple lane-following assumption needs richer map, agent intent, or replay context.
- This is a scenario-triage diagnostic, not a Waymo benchmark claim or production prediction model.
