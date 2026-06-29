# ScenarioLens Baseline Debug Casebook

This casebook explains selected constant-velocity vs lane-aware prediction outcomes. It is meant to turn the aggregate study into debuggable evidence: where maps help, where naive lane following regresses, and where the lane-aware baseline intentionally falls back.

## Scope

- Source: `data/processed/waymo_lane_aware_baseline_cross_shard/manifest.json`
- Input format: `native`
- Ready for analysis: True
- Cases selected: 3
- Raw Waymo files committed: no
- Raw trajectories, local SVG overlays, and per-case debug manifests committed: no

The public copy reports scenario IDs, metric summaries, fallback reasons, and interpretation only. Local SVGs and per-track debug manifests stay under ignored `data/processed/` paths.

## Selected Cases

| Case | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Largest improvement | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 3 | 55.051 m | 40.900 m | +14.151 m | 3 | 0 | `none` |
| Largest regression | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | 1 | 3.152 m | 144.514 m | -141.362 m | 1 | 0 | `none` |
| Fallback-heavy case | `validation.tfrecord-00010-of-00150` | `2f035a284480e981` | 8 | 31.995 m | 31.995 m | 0.000 m | 0 | 8 | `target_too_far_from_lane (8)` |

## Largest improvement: `b2b7c2ad7bcd134b`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`
- Why selected: Highest positive FDE improvement from the baseline comparison study.
- Constant-velocity FDE: 55.051 m
- Lane-aware FDE: 40.900 m
- FDE improvement: +14.151 m
- Map-used / fallback targets: 3 / 0

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `4357` | `vehicle` | 44.237 m | 47.331 m | -3.094 m | True | `none` | 0.134 m | 44.237 m | 47.331 m |
| `4365` | `vehicle` | 74.805 m | 46.831 m | +27.974 m | True | `none` | 0.288 m | 74.805 m | 46.831 m |
| `4364` | `vehicle` | 46.111 m | 28.539 m | +17.572 m | True | `none` | 0.815 m | 46.111 m | 28.539 m |

## Largest regression: `fc8c647623f81bb4`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`
- Why selected: Most negative FDE delta from the baseline comparison study.
- Constant-velocity FDE: 3.152 m
- Lane-aware FDE: 144.514 m
- FDE improvement: -141.362 m
- Map-used / fallback targets: 1 / 0

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `1466` | `vehicle` | 3.152 m | 144.514 m | -141.362 m | True | `none` | 0.031 m | 3.152 m | 144.514 m |

## Fallback-heavy case: `2f035a284480e981`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Why selected: Most lane-aware fallback-heavy scenario in the comparison study.
- Constant-velocity FDE: 31.995 m
- Lane-aware FDE: 31.995 m
- FDE improvement: 0.000 m
- Map-used / fallback targets: 0 / 8

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `722` | `vehicle` | 56.508 m | 56.508 m | 0.000 m | False | `target_too_far_from_lane` | 118.156 m | 56.508 m | 56.508 m |
| `715` | `vehicle` | 22.381 m | 22.381 m | 0.000 m | False | `target_too_far_from_lane` | 78.585 m | 22.381 m | 22.381 m |
| `726` | `vehicle` | 30.847 m | 30.847 m | 0.000 m | False | `target_too_far_from_lane` | 23.999 m | 30.847 m | 30.847 m |
| `717` | `vehicle` | 31.953 m | 31.953 m | 0.000 m | False | `target_too_far_from_lane` | 51.799 m | 31.953 m | 31.953 m |
| `721` | `vehicle` | 36.929 m | 36.929 m | 0.000 m | False | `target_too_far_from_lane` | 121.153 m | 36.929 m | 36.929 m |
| `724` | `vehicle` | 36.177 m | 36.177 m | 0.000 m | False | `target_too_far_from_lane` | 103.781 m | 36.177 m | 36.177 m |
| `731` | `vehicle` | 9.968 m | 9.968 m | 0.000 m | False | `target_too_far_from_lane` | 138.703 m | 9.968 m | 9.968 m |
| `732` | `vehicle` | 31.195 m | 31.195 m | 0.000 m | False | `target_too_far_from_lane` | 7.609 m | 31.195 m | 31.195 m |

## Interpretation

- The improvement case shows where map-conditioned motion can reduce a simple forecast error.
- The regression case is the useful warning: nearest-lane following can be wrong when lane choice, direction, or intent is ambiguous.
- The fallback-heavy case shows production-minded behavior for a diagnostic baseline: when inputs are not trustworthy, it records why and returns to the safer baseline.
- This is still an evaluation/debugging framework, not a production prediction model or Waymo benchmark claim.
