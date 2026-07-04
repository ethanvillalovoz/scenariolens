# ScenarioLens Lane-Continuation Topology Gap Audit

This audit works down the branch coverage queue's topology/parser blockers. For each topology-audit replay case, ScenarioLens reloads the local source slice, compares the capped ScenarioLens map features against raw parsed map-feature ids, and asks whether missing lane-link targets are recoverable by improving map materialization.

The report is intentionally narrow: it does not change the default baseline, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_200/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates_200/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study_200/manifest.json`
- Ready: True
- Map feature cap: 240
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Cases audited | 15 |
| Ready cases | 15 |
| Cap-recovered cases | 0 |
| Still cap-recoverable cases | 2 |
| Terminal lanes confirmed | 13 |
| Raw target still missing | 0 |
| Selected feature missing in capped map | 0 |
| Capped maps at feature cap | 5 |
| Mean route gap to horizon | +55.696 m |

## Decisions

| Rank | Scenario | Track | Status | Selected lane | Link field | Link targets | Raw lanes | Capped lanes | Diagnosis | First next action |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 31 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | `219` | `exit_lanes` | none | 100 | 100 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 32 | `8ce92d09a94bf2c8` | `2516` | `no_entry_lanes` | `183` | `entry_lanes` | none | 82 | 82 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 33 | `95fa94d3b3e1f3c6` | `205` | `linked_feature_missing` | `644` | `exit_lanes` | `645` | 637 | 198 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 34 | `74a5b3325a534a87` | `3178` | `no_entry_lanes` | `333` | `entry_lanes` | none | 395 | 287 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 35 | `28f34edeb361e955` | `987` | `no_exit_lanes` | `158` | `exit_lanes` | none | 110 | 110 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 36 | `634b468a246a77d6` | `116` | `no_exit_lanes` | `99` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 37 | `8c9eaa71b6a696c5` | `797` | `linked_feature_missing` | `718` | `exit_lanes` | `726` | 463 | 324 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 38 | `4dfe7c285670839f` | `0` | `no_exit_lanes` | `44` | `exit_lanes` | none | 58 | 58 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 39 | `f672132039e83c40` | `519` | `no_exit_lanes` | `73` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 40 | `f672132039e83c40` | `520` | `no_exit_lanes` | `72` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 41 | `8abe59aee39f351e` | `4650` | `no_exit_lanes` | `161` | `exit_lanes` | none | 97 | 97 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 42 | `9c8241f6a2ee5f51` | `88` | `no_exit_lanes` | `223` | `exit_lanes` | none | 129 | 129 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 43 | `f672132039e83c40` | `522` | `no_exit_lanes` | `77` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 44 | `634b468a246a77d6` | `115` | `no_exit_lanes` | `91` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 45 | `fe4a6425278fbd5b` | `816` | `no_exit_lanes` | `155` | `exit_lanes` | none | 186 | 183 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |

## `2f366a31ab03f8b` / track `1061`

- Source: `validation.tfrecord-00007-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `219`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 255 / 240
- Raw/capped lane features: 100 / 100
- Capped map at feature cap: True
- Horizon / route remaining: 165.493 m / 26.476 m
- Route gap to horizon: +139.017 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `8ce92d09a94bf2c8` / track `2516`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `183`
- Link field: `entry_lanes`
- Lane-link status: `no_entry_lanes`
- Raw/capped map features: 191 / 191
- Raw/capped lane features: 82 / 82
- Capped map at feature cap: False
- Horizon / route remaining: 125.303 m / 27.472 m
- Route gap to horizon: +97.831 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `95fa94d3b3e1f3c6` / track `205`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `644`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 905 / 408
- Raw/capped lane features: 637 / 198
- Capped map at feature cap: True
- Horizon / route remaining: 63.361 m / 3.899 m
- Route gap to horizon: +59.462 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `645` | False | True | 463 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## `74a5b3325a534a87` / track `3178`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `333`
- Link field: `entry_lanes`
- Lane-link status: `no_entry_lanes`
- Raw/capped map features: 528 / 396
- Raw/capped lane features: 395 / 287
- Capped map at feature cap: True
- Horizon / route remaining: 59.581 m / 23.515 m
- Route gap to horizon: +36.066 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `28f34edeb361e955` / track `987`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `158`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 230 / 230
- Raw/capped lane features: 110 / 110
- Capped map at feature cap: False
- Horizon / route remaining: 57.799 m / 32.851 m
- Route gap to horizon: +24.948 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `634b468a246a77d6` / track `116`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `99`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 127 / 127
- Raw/capped lane features: 54 / 54
- Capped map at feature cap: False
- Horizon / route remaining: 75.123 m / 16.502 m
- Route gap to horizon: +58.621 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `8c9eaa71b6a696c5` / track `797`

- Source: `validation.tfrecord-00007-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `718`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 654 / 480
- Raw/capped lane features: 463 / 324
- Capped map at feature cap: True
- Horizon / route remaining: 126.036 m / 3.481 m
- Route gap to horizon: +122.555 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `726` | False | True | 486 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## `4dfe7c285670839f` / track `0`

- Source: `validation.tfrecord-00008-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `44`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 108 / 108
- Raw/capped lane features: 58 / 58
- Capped map at feature cap: False
- Horizon / route remaining: 85.416 m / 15.863 m
- Route gap to horizon: +69.553 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `f672132039e83c40` / track `519`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `73`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 100 / 100
- Raw/capped lane features: 54 / 54
- Capped map at feature cap: False
- Horizon / route remaining: 55.400 m / 21.194 m
- Route gap to horizon: +34.206 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `f672132039e83c40` / track `520`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `72`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 100 / 100
- Raw/capped lane features: 54 / 54
- Capped map at feature cap: False
- Horizon / route remaining: 54.924 m / 20.811 m
- Route gap to horizon: +34.113 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `8abe59aee39f351e` / track `4650`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `161`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 171 / 171
- Raw/capped lane features: 97 / 97
- Capped map at feature cap: False
- Horizon / route remaining: 29.126 m / 4.367 m
- Route gap to horizon: +24.759 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `9c8241f6a2ee5f51` / track `88`

- Source: `validation.tfrecord-00008-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `223`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 233 / 233
- Raw/capped lane features: 129 / 129
- Capped map at feature cap: False
- Horizon / route remaining: 37.110 m / 24.718 m
- Route gap to horizon: +12.392 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `f672132039e83c40` / track `522`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `77`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 100 / 100
- Raw/capped lane features: 54 / 54
- Capped map at feature cap: False
- Horizon / route remaining: 45.100 m / 32.738 m
- Route gap to horizon: +12.362 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `634b468a246a77d6` / track `115`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `91`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 127 / 127
- Raw/capped lane features: 54 / 54
- Capped map at feature cap: False
- Horizon / route remaining: 72.616 m / 15.502 m
- Route gap to horizon: +57.114 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## `fe4a6425278fbd5b` / track `816`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `155`
- Link field: `exit_lanes`
- Lane-link status: `no_exit_lanes`
- Raw/capped map features: 290 / 257
- Raw/capped lane features: 186 / 183
- Capped map at feature cap: True
- Horizon / route remaining: 66.469 m / 14.029 m
- Route gap to horizon: +52.440 m
- Reason: The selected lane has no parsed continuation in either capped or raw parsed map features.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| n/a | n/a | n/a | n/a | n/a |

Recommended next actions:
- Audit selected-lane quality and nearby alternate lanes before expanding branch selection.
- Treat this as selected-lane/topology-neighborhood work, not a simple cap increase.

## Interpretation

- Cap-recovered cases mean a referenced lane target from beyond the raw feature cap is now available in the capped ScenarioLens map feature set.
- Cap-recoverable cases mean the referenced lane target exists in the raw parsed map but was not available inside the capped ScenarioLens map feature set.
- Terminal-lane confirmations mean the selected lane has no parsed continuation in either the capped or raw parsed map; these need selected-lane or topology-neighborhood work rather than a simple cap increase.
- Raw-missing targets stay parser/proto-source audits until the referenced id can be found.
- This audit turns topology blockers into engineering tasks before expanding branch-selection and route-context guard claims.
