# ScenarioLens Heading-Aware Lane Selection Study

This report compares the existing nearest-lane baseline with a heading-aware lane-selection variant. The variant keeps the same constant-velocity fallback discipline, but when multiple lane polylines are close to a target it prefers a lane whose tangent aligns with the target's anchor velocity.

It is intentionally scoped: this is an ablation beside the default baseline, not a production map matcher, not a Waymo benchmark claim, and not a change to ScenarioLens' default scoring baseline.

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

| Metric | Constant velocity | Nearest lane | Heading-aware lane |
| --- | ---: | ---: | ---: |
| Mean FDE | 25.564 m | 31.067 m | 30.578 m |
| Miss rate | 94.0% | 93.8% | 93.8% |
| Map used | n/a | 137 | 132 |
| Fallbacks | n/a | 281 | 286 |

| Delta | Value |
| --- | ---: |
| Heading FDE improvement vs nearest lane | +0.489 m |
| Heading FDE improvement vs constant velocity | -5.014 m |

## Per-Source Summary

| Source | Scenarios | Targets | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Heading map used | Heading fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 25 | 101 | 26.663 m | 34.139 m | 34.116 m | +0.023 m | 36 | 65 |
| `validation.tfrecord-00008-of-00150` | 25 | 94 | 25.238 m | 30.666 m | 29.820 m | +0.846 m | 27 | 67 |
| `validation.tfrecord-00009-of-00150` | 25 | 107 | 21.204 m | 25.070 m | 24.719 m | +0.351 m | 31 | 76 |
| `validation.tfrecord-00010-of-00150` | 25 | 116 | 28.893 m | 34.247 m | 33.515 m | +0.732 m | 38 | 78 |

## Heading-Aware Fallback Reasons

- `target_too_far_from_lane`: 210
- `non_vehicle_or_cyclist_target`: 41
- `low_or_invalid_anchor_speed`: 27
- `lane_heading_misaligned`: 5
- `no_lane_map_features`: 3

## Largest Heading-Aware Improvements

| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 8 | 48.599 m | 36.443 m | +12.156 m | 3 | 5 | `target_too_far_from_lane (3)` |
| 2 | `validation.tfrecord-00008-of-00150` | `7912ee9523cb6fd` | 4 | 41.547 m | 33.623 m | +7.924 m | 2 | 2 | `lane_heading_misaligned (1)` |
| 3 | `validation.tfrecord-00007-of-00150` | `46c1c1fbe5ef29d1` | 6 | 41.729 m | 36.241 m | +5.488 m | 3 | 3 | `target_too_far_from_lane (2)` |
| 4 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | 5 | 53.824 m | 48.816 m | +5.008 m | 4 | 1 | `target_too_far_from_lane (1)` |
| 5 | `validation.tfrecord-00009-of-00150` | `e5d86b1e27302416` | 7 | 41.630 m | 38.503 m | +3.127 m | 4 | 3 | `lane_heading_misaligned (1)` |
| 6 | `validation.tfrecord-00008-of-00150` | `685a1cbb71a2c433` | 4 | 22.363 m | 19.491 m | +2.872 m | 2 | 2 | `non_vehicle_or_cyclist_target (2)` |
| 7 | `validation.tfrecord-00009-of-00150` | `3a2a03200cd1663e` | 4 | 48.198 m | 45.476 m | +2.722 m | 3 | 1 | `target_too_far_from_lane (1)` |
| 8 | `validation.tfrecord-00008-of-00150` | `792b88608157b8b9` | 4 | 22.635 m | 20.424 m | +2.211 m | 1 | 3 | `low_or_invalid_anchor_speed (2)` |
| 9 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 3 | 40.900 m | 39.258 m | +1.642 m | 3 | 0 | `none` |
| 10 | `validation.tfrecord-00008-of-00150` | `44dadb51fdafb58b` | 3 | 9.471 m | 8.647 m | +0.824 m | 0 | 3 | `target_too_far_from_lane (2)` |

## Largest Heading-Aware Regressions

Negative deltas mean the heading-aware selector had higher FDE than the nearest-lane selector. Those rows are useful diagnostics for map coverage, lane direction, and intent assumptions.

| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00007-of-00150` | `706fecd25045c8d` | 7 | 31.232 m | 35.605 m | -4.373 m | 4 | 3 | `target_too_far_from_lane (2)` |
| 2 | `validation.tfrecord-00010-of-00150` | `63eca292d17e9a3a` | 4 | 47.850 m | 50.847 m | -2.997 m | 2 | 2 | `low_or_invalid_anchor_speed (2)` |
| 3 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | 8 | 46.650 m | 46.754 m | -0.104 m | 4 | 4 | `target_too_far_from_lane (4)` |
| 4 | `validation.tfrecord-00009-of-00150` | `48b920063c9f98cc` | 4 | 27.985 m | 28.020 m | -0.035 m | 3 | 1 | `non_vehicle_or_cyclist_target (1)` |
| 5 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | 8 | 45.671 m | 45.671 m | 0.000 m | 6 | 2 | `low_or_invalid_anchor_speed (1)` |
| 6 | `validation.tfrecord-00010-of-00150` | `ddaf259a043c2688` | 8 | 35.867 m | 35.867 m | 0.000 m | 6 | 2 | `non_vehicle_or_cyclist_target (2)` |
| 7 | `validation.tfrecord-00010-of-00150` | `fa73256456e9e406` | 7 | 30.243 m | 30.243 m | 0.000 m | 6 | 1 | `non_vehicle_or_cyclist_target (1)` |
| 8 | `validation.tfrecord-00007-of-00150` | `d963287c8360ac9d` | 7 | 43.971 m | 43.971 m | 0.000 m | 5 | 2 | `target_too_far_from_lane (2)` |
| 9 | `validation.tfrecord-00007-of-00150` | `35767b81d9f68385` | 5 | 22.211 m | 22.211 m | 0.000 m | 4 | 1 | `target_too_far_from_lane (1)` |
| 10 | `validation.tfrecord-00009-of-00150` | `381e4a50092e3e58` | 8 | 22.559 m | 22.559 m | 0.000 m | 4 | 4 | `non_vehicle_or_cyclist_target (2)` |

## Heading-Fallback Heavy Scenarios

| Rank | Source | Scenario | Targets | Nearest FDE | Heading FDE | Delta | Heading map used | Heading fallbacks | Top heading fallback |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00010-of-00150` | `2f035a284480e981` | 8 | 31.995 m | 31.995 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (8)` |
| 2 | `validation.tfrecord-00009-of-00150` | `6bdc7f92afefff73` | 8 | 14.348 m | 14.348 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (8)` |
| 3 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | 8 | 18.817 m | 18.817 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (8)` |
| 4 | `validation.tfrecord-00008-of-00150` | `ed1dc559821784f8` | 8 | 20.197 m | 20.197 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (7)` |
| 5 | `validation.tfrecord-00008-of-00150` | `4cc3cc262460ff87` | 8 | 22.874 m | 22.874 m | 0.000 m | 1 | 7 | `target_too_far_from_lane (5)` |
| 6 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | 8 | 25.149 m | 25.149 m | 0.000 m | 1 | 7 | `target_too_far_from_lane (3)` |
| 7 | `validation.tfrecord-00008-of-00150` | `6bfab54b46fe8f78` | 7 | 46.271 m | 46.271 m | 0.000 m | 0 | 7 | `target_too_far_from_lane (6)` |
| 8 | `validation.tfrecord-00007-of-00150` | `d30709cd60e60395` | 7 | 25.307 m | 25.307 m | 0.000 m | 0 | 7 | `target_too_far_from_lane (6)` |
| 9 | `validation.tfrecord-00008-of-00150` | `3a63a018b28ad4ef` | 7 | 21.064 m | 21.064 m | 0.000 m | 1 | 6 | `low_or_invalid_anchor_speed (2)` |
| 10 | `validation.tfrecord-00009-of-00150` | `d896f49c65abbda` | 6 | 18.879 m | 18.879 m | 0.000 m | 0 | 6 | `target_too_far_from_lane (5)` |

## Interpretation

- Heading-aware lane selection reduced mean FDE relative to the nearest-lane selector, but it still trails constant velocity overall in this run.
- Heading-aware selection can reduce bad nearest-lane matches, but it can also choose to fall back more often when nearby lanes are poorly aligned.
- The default ScenarioLens scorer remains constant velocity; this study is evidence for the next map-matching iteration, not a certified prediction model.
- Public rows are aggregate and scenario-id level only; raw Waymo files and per-scenario derived packets stay out of git.
