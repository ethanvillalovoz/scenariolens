# ScenarioLens Heading-Aware Debug Casebook

This casebook explains selected nearest-lane vs heading-aware lane-selection outcomes. It turns the aggregate heading-aware study into debuggable evidence: where heading alignment helps, where it regresses, and where the matcher intentionally falls back.

## Scope

- Source: `data/processed/waymo_lane_selection_study/manifest.json`
- Input format: `native`
- Ready for analysis: True
- Cases selected: 6
- Raw Waymo files committed: no
- Raw trajectories, local SVG overlays, and per-case debug manifests committed: no

The public copy reports scenario IDs, metric summaries, fallback reasons, and interpretation only. Local SVG overlays and per-track debug manifests stay under ignored `data/processed/` paths.

## Selected Cases

| Case | Source | Scenario | Targets | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Heading map used | Heading fallbacks | Top heading fallback |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Largest heading improvement | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 8 | 27.509 m | 48.599 m | 36.443 m | +12.156 m | 3 | 5 | `target_too_far_from_lane (3)` |
| Largest heading regression | `validation.tfrecord-00007-of-00150` | `706fecd25045c8d` | 7 | 32.547 m | 31.232 m | 35.605 m | -4.373 m | 4 | 3 | `target_too_far_from_lane (2)` |
| Heading fallback-heavy case | `validation.tfrecord-00010-of-00150` | `2f035a284480e981` | 8 | 31.995 m | 31.995 m | 31.995 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (8)` |
| Additional heading improvement | `validation.tfrecord-00008-of-00150` | `7912ee9523cb6fd` | 4 | 26.353 m | 41.547 m | 33.623 m | +7.924 m | 2 | 2 | `lane_heading_misaligned (1)` |
| Additional heading improvement | `validation.tfrecord-00007-of-00150` | `46c1c1fbe5ef29d1` | 6 | 20.759 m | 41.729 m | 36.241 m | +5.488 m | 3 | 3 | `target_too_far_from_lane (2)` |
| Additional heading improvement | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | 5 | 50.124 m | 53.824 m | 48.816 m | +5.008 m | 4 | 1 | `target_too_far_from_lane (1)` |

## Largest heading improvement: `d30e6448f14e4c75`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Why selected: Highest positive FDE improvement from heading-aware lane selection versus nearest-lane selection.
- Constant-velocity FDE: 27.509 m
- Nearest-lane FDE: 48.599 m
- Heading-aware FDE: 36.443 m
- Heading improvement vs nearest lane: +12.156 m
- Heading improvement vs constant velocity: -8.934 m
- Heading map-used / fallback targets: 3 / 5

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `201` | `vehicle` | 12.224 m | 61.338 m | 12.224 m | +49.114 m | `none` | `lane_heading_misaligned` | 0.897 m | `lane_heading_misaligned` |
| `205` | `vehicle` | 24.908 m | 24.908 m | 24.908 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 24.345 m | `target_too_far_from_lane` |
| `195` | `vehicle` | 13.915 m | 62.053 m | 13.915 m | +48.138 m | `none` | `lane_heading_misaligned` | 2.451 m | `lane_heading_misaligned` |
| `150` | `vehicle` | 42.804 m | 28.584 m | 28.584 m | 0.000 m | `none` | `none` | 0.016 m | `lane_matched` |
| `149` | `vehicle` | 35.931 m | 35.931 m | 35.931 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 15.655 m | `target_too_far_from_lane` |
| `155` | `vehicle` | 32.745 m | 83.171 m | 83.171 m | 0.000 m | `none` | `none` | 0.341 m | `lane_matched` |
| `164` | `vehicle` | 30.705 m | 65.970 m | 65.970 m | 0.000 m | `none` | `none` | 0.520 m | `lane_matched` |
| `148` | `vehicle` | 26.838 m | 26.838 m | 26.838 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 12.285 m | `target_too_far_from_lane` |

## Largest heading regression: `706fecd25045c8d`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`
- Why selected: Most negative FDE delta from heading-aware lane selection versus nearest-lane selection.
- Constant-velocity FDE: 32.547 m
- Nearest-lane FDE: 31.232 m
- Heading-aware FDE: 35.605 m
- Heading improvement vs nearest lane: -4.373 m
- Heading improvement vs constant velocity: -3.058 m
- Heading map-used / fallback targets: 4 / 3

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `1079` | `pedestrian` | 6.498 m | 6.498 m | 6.498 m | 0.000 m | `non_vehicle_or_cyclist_target` | `non_vehicle_or_cyclist_target` | n/a | `non_vehicle_or_cyclist_target` |
| `714` | `vehicle` | 60.406 m | 54.351 m | 84.959 m | -30.608 m | `none` | `none` | 0.260 m | `lane_matched` |
| `708` | `vehicle` | 29.903 m | 19.639 m | 19.639 m | 0.000 m | `none` | `none` | 2.163 m | `lane_matched` |
| `752` | `vehicle` | 31.210 m | 31.210 m | 31.210 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 6.124 m | `target_too_far_from_lane` |
| `746` | `vehicle` | 37.353 m | 52.350 m | 52.350 m | 0.000 m | `none` | `none` | 0.023 m | `lane_matched` |
| `738` | `vehicle` | 52.906 m | 45.026 m | 45.026 m | 0.000 m | `none` | `none` | 3.406 m | `lane_matched` |
| `710` | `vehicle` | 9.550 m | 9.550 m | 9.550 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 4.699 m | `target_too_far_from_lane` |

## Heading fallback-heavy case: `2f035a284480e981`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Why selected: Most heading-aware fallback-heavy scenario in the lane-selection study.
- Constant-velocity FDE: 31.995 m
- Nearest-lane FDE: 31.995 m
- Heading-aware FDE: 31.995 m
- Heading improvement vs nearest lane: 0.000 m
- Heading improvement vs constant velocity: 0.000 m
- Heading map-used / fallback targets: 0 / 8

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `722` | `vehicle` | 56.508 m | 56.508 m | 56.508 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 118.156 m | `target_too_far_from_lane` |
| `715` | `vehicle` | 22.381 m | 22.381 m | 22.381 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 78.585 m | `target_too_far_from_lane` |
| `726` | `vehicle` | 30.847 m | 30.847 m | 30.847 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 23.999 m | `target_too_far_from_lane` |
| `717` | `vehicle` | 31.953 m | 31.953 m | 31.953 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 51.799 m | `target_too_far_from_lane` |
| `721` | `vehicle` | 36.929 m | 36.929 m | 36.929 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 121.153 m | `target_too_far_from_lane` |
| `724` | `vehicle` | 36.177 m | 36.177 m | 36.177 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 103.781 m | `target_too_far_from_lane` |
| `731` | `vehicle` | 9.968 m | 9.968 m | 9.968 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 138.703 m | `target_too_far_from_lane` |
| `732` | `vehicle` | 31.195 m | 31.195 m | 31.195 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 7.609 m | `target_too_far_from_lane` |

## Additional heading improvement: `7912ee9523cb6fd`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`
- Why selected: Additional selected row from `top_heading_improvements`.
- Constant-velocity FDE: 26.353 m
- Nearest-lane FDE: 41.547 m
- Heading-aware FDE: 33.623 m
- Heading improvement vs nearest lane: +7.924 m
- Heading improvement vs constant velocity: -7.270 m
- Heading map-used / fallback targets: 2 / 2

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `1840` | `cyclist` | 8.875 m | 40.574 m | 8.875 m | +31.699 m | `none` | `lane_heading_misaligned` | 0.470 m | `lane_heading_misaligned` |
| `946` | `vehicle` | 36.226 m | 33.418 m | 33.418 m | 0.000 m | `none` | `none` | 2.542 m | `lane_matched` |
| `944` | `vehicle` | 38.011 m | 69.897 m | 69.897 m | 0.000 m | `none` | `none` | 0.050 m | `lane_matched` |
| `947` | `vehicle` | 22.301 m | 22.301 m | 22.301 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 3.764 m | `target_too_far_from_lane` |

## Additional heading improvement: `46c1c1fbe5ef29d1`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`
- Why selected: Additional selected row from `top_heading_improvements`.
- Constant-velocity FDE: 20.759 m
- Nearest-lane FDE: 41.729 m
- Heading-aware FDE: 36.241 m
- Heading improvement vs nearest lane: +5.488 m
- Heading improvement vs constant velocity: -15.482 m
- Heading map-used / fallback targets: 3 / 3

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `236` | `vehicle` | 5.826 m | 5.826 m | 5.826 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 5.332 m | `target_too_far_from_lane` |
| `244` | `vehicle` | 33.565 m | 33.565 m | 33.565 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 6.386 m | `target_too_far_from_lane` |
| `246` | `vehicle` | 40.145 m | 29.077 m | 11.848 m | +17.229 m | `none` | `none` | 1.834 m | `lane_matched` |
| `245` | `vehicle` | 6.930 m | 53.530 m | 53.530 m | 0.000 m | `none` | `none` | 0.152 m | `lane_matched` |
| `249` | `vehicle` | 18.945 m | 109.232 m | 93.531 m | +15.701 m | `none` | `none` | 0.038 m | `lane_matched` |
| `218` | `vehicle` | 19.144 m | 19.144 m | 19.144 m | 0.000 m | `low_or_invalid_anchor_speed` | `low_or_invalid_anchor_speed` | 1.059 m | `low_or_invalid_anchor_speed` |

## Additional heading improvement: `e3f6a29b59e42c1`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`
- Why selected: Additional selected row from `top_heading_improvements`.
- Constant-velocity FDE: 50.124 m
- Nearest-lane FDE: 53.824 m
- Heading-aware FDE: 48.816 m
- Heading improvement vs nearest lane: +5.008 m
- Heading improvement vs constant velocity: +1.308 m
- Heading map-used / fallback targets: 4 / 1

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest fallback | Heading fallback | Nearest lane distance | Heading match |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| `752` | `vehicle` | 54.431 m | 104.956 m | 79.918 m | +25.038 m | `none` | `none` | 0.598 m | `lane_matched` |
| `745` | `vehicle` | 64.254 m | 48.339 m | 48.339 m | 0.000 m | `none` | `none` | 0.389 m | `lane_matched` |
| `741` | `vehicle` | 58.947 m | 15.869 m | 15.869 m | 0.000 m | `none` | `none` | 0.140 m | `lane_matched` |
| `749` | `vehicle` | 48.516 m | 48.516 m | 48.516 m | 0.000 m | `target_too_far_from_lane` | `target_too_far_from_lane` | 5.394 m | `target_too_far_from_lane` |
| `755` | `vehicle` | 24.473 m | 51.438 m | 51.438 m | 0.000 m | `none` | `none` | 0.357 m | `lane_matched` |

## Interpretation

- The improvement case shows where heading alignment can avoid a worse nearest-lane hypothesis.
- The regression case is the useful warning: heading alignment can still be wrong when intent, lane direction, or parsed map context is ambiguous.
- The fallback-heavy case shows the matcher recording why it declines map-following and returns to the fallback forecast.
- This remains a diagnostic ablation, not a production map matcher, production prediction model, or Waymo benchmark claim.
