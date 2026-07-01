# ScenarioLens Context Eval Debug Casebook

This casebook turns the context evaluation set into debuggable evidence: selected scenario IDs are reloaded locally, scored through constant-velocity and lane-aware baselines, and summarized with public-safe metrics while raw Waymo records and local overlays stay ignored.

## Scope

- Source: `data/processed/waymo_context_eval_set/manifest.json`
- Input format: `native`
- Ready for analysis: True
- Cases selected: 5
- Raw Waymo files committed: no
- Raw trajectories, local SVG overlays, and per-case debug manifests committed: no

The public copy reports scenario IDs, metric summaries, fallback reasons, and interpretation only. Local SVGs and per-track debug manifests stay under ignored `data/processed/` paths.

## Selected Cases

| Case | Source | Scenario | Targets | CV FDE | Lane FDE | FDE delta | Map used | Fallbacks | Top fallback |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Context eval seed 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 4 | 69.320 m | 69.320 m | 0.000 m | 0 | 4 | `target_too_far_from_lane (4)` |
| Context eval seed 2 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 8 | 46.985 m | 45.303 m | +1.682 m | 3 | 5 | `target_too_far_from_lane (5)` |
| Context eval seed 3 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 3 | 48.806 m | 48.806 m | 0.000 m | 0 | 3 | `target_too_far_from_lane (3)` |
| Context eval seed 4 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 4 | 50.184 m | 50.184 m | 0.000 m | 0 | 4 | `target_too_far_from_lane (4)` |
| Context eval seed 5 | `validation.tfrecord-00008-of-00150` | `ef4c5d0e40fdea48` | 1 | 46.688 m | 110.266 m | -63.578 m | 1 | 0 | `none` |

## Context eval seed 1: `5c8f9e7af4b0248a`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`
- Why selected: Selected from the context evaluation set; groups: Context-rich failures, Signal-context failures, Route/topology failures, Fallback-stress cases.
- Constant-velocity FDE: 69.320 m
- Lane-aware FDE: 69.320 m
- FDE improvement: 0.000 m
- Map-used / fallback targets: 0 / 4

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `1532` | `vehicle` | 101.652 m | 101.652 m | 0.000 m | False | `target_too_far_from_lane` | 28.668 m | 101.652 m | 101.652 m |
| `2351` | `vehicle` | 45.455 m | 45.455 m | 0.000 m | False | `target_too_far_from_lane` | 33.055 m | 45.455 m | 45.455 m |
| `1531` | `vehicle` | 78.121 m | 78.121 m | 0.000 m | False | `target_too_far_from_lane` | 28.339 m | 78.121 m | 78.121 m |
| `1533` | `vehicle` | 52.053 m | 52.053 m | 0.000 m | False | `target_too_far_from_lane` | 23.603 m | 52.053 m | 52.053 m |

## Context eval seed 2: `7fc449ae179c29ac`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`
- Why selected: Selected from the context evaluation set; groups: Fallback-stress cases.
- Constant-velocity FDE: 46.985 m
- Lane-aware FDE: 45.303 m
- FDE improvement: +1.682 m
- Map-used / fallback targets: 3 / 5

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `1238` | `vehicle` | 45.440 m | 21.410 m | +24.030 m | True | `none` | 0.311 m | 45.440 m | 21.410 m |
| `1239` | `vehicle` | 42.521 m | 30.540 m | +11.981 m | True | `none` | 0.996 m | 42.521 m | 30.540 m |
| `1230` | `vehicle` | 64.155 m | 86.709 m | -22.554 m | True | `none` | 1.774 m | 64.155 m | 86.709 m |
| `1221` | `vehicle` | 60.743 m | 60.743 m | 0.000 m | False | `target_too_far_from_lane` | 7.214 m | 60.743 m | 60.743 m |
| `1220` | `vehicle` | 50.094 m | 50.094 m | 0.000 m | False | `target_too_far_from_lane` | 8.482 m | 50.094 m | 50.094 m |
| `1256` | `vehicle` | 36.073 m | 36.073 m | 0.000 m | False | `target_too_far_from_lane` | 33.663 m | 36.073 m | 36.073 m |
| `1225` | `vehicle` | 51.355 m | 51.355 m | 0.000 m | False | `target_too_far_from_lane` | 3.516 m | 51.355 m | 51.355 m |
| `1233` | `vehicle` | 25.496 m | 25.496 m | 0.000 m | False | `target_too_far_from_lane` | 8.831 m | 25.496 m | 25.496 m |

## Context eval seed 3: `1f18831dfad32caa`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Why selected: Selected from the context evaluation set; groups: Fallback-stress cases.
- Constant-velocity FDE: 48.806 m
- Lane-aware FDE: 48.806 m
- FDE improvement: 0.000 m
- Map-used / fallback targets: 0 / 3

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `1612` | `vehicle` | 49.212 m | 49.212 m | 0.000 m | False | `target_too_far_from_lane` | 11.681 m | 49.212 m | 49.212 m |
| `1623` | `vehicle` | 42.504 m | 42.504 m | 0.000 m | False | `target_too_far_from_lane` | 26.611 m | 42.504 m | 42.504 m |
| `1603` | `vehicle` | 54.701 m | 54.701 m | 0.000 m | False | `target_too_far_from_lane` | 25.407 m | 54.701 m | 54.701 m |

## Context eval seed 4: `479404468f0a7548`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`
- Why selected: Selected from the context evaluation set; groups: Fallback-stress cases.
- Constant-velocity FDE: 50.184 m
- Lane-aware FDE: 50.184 m
- FDE improvement: 0.000 m
- Map-used / fallback targets: 0 / 4

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `511` | `vehicle` | 60.868 m | 60.868 m | 0.000 m | False | `target_too_far_from_lane` | 248.778 m | 60.868 m | 60.868 m |
| `510` | `vehicle` | 41.033 m | 41.033 m | 0.000 m | False | `target_too_far_from_lane` | 253.212 m | 41.033 m | 41.033 m |
| `518` | `vehicle` | 54.442 m | 54.442 m | 0.000 m | False | `target_too_far_from_lane` | 257.531 m | 54.442 m | 54.442 m |
| `515` | `vehicle` | 44.394 m | 44.394 m | 0.000 m | False | `target_too_far_from_lane` | 238.692 m | 44.394 m | 44.394 m |

## Context eval seed 5: `ef4c5d0e40fdea48`

- Source: `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`
- Why selected: Selected from the context evaluation set; groups: Lane-aware regressions.
- Constant-velocity FDE: 46.688 m
- Lane-aware FDE: 110.266 m
- FDE improvement: -63.578 m
- Map-used / fallback targets: 1 / 0

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback | Lane distance | Last CV error | Last lane error |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `755` | `vehicle` | 46.688 m | 110.266 m | -63.578 m | True | `none` | 0.038 m | 46.688 m | 110.266 m |

## Interpretation

- The improvement cases show where map-conditioned motion can reduce a simple forecast error.
- The regression cases are useful warnings: nearest-lane following can be wrong when lane choice, direction, or intent is ambiguous.
- The fallback-heavy cases show production-minded behavior for a diagnostic baseline: when inputs are not trustworthy, it records why and returns to the safer baseline.
- Context-eval cases keep signal, topology, regression, and fallback groups visible so follow-up replay does not overfit one failure mode.
- This is still an evaluation/debugging framework, not a production prediction model or Waymo benchmark claim.
