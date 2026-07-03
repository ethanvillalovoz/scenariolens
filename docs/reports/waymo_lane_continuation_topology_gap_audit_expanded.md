# ScenarioLens Lane-Continuation Topology Gap Audit

This audit works down the branch coverage queue's topology/parser blockers. For each topology-audit replay case, ScenarioLens reloads the local source slice, compares the capped ScenarioLens map features against raw parsed map-feature ids, and asks whether missing lane-link targets are recoverable by improving map materialization.

The report is intentionally narrow: it does not change the default baseline, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates_expanded/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready: True
- Map feature cap: 240
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Cases audited | 10 |
| Ready cases | 10 |
| Cap-recovered cases | 0 |
| Still cap-recoverable cases | 3 |
| Terminal lanes confirmed | 7 |
| Raw target still missing | 0 |
| Selected feature missing in capped map | 0 |
| Capped maps at feature cap | 6 |
| Mean route gap to horizon | +57.707 m |

## Decisions

| Rank | Scenario | Track | Status | Selected lane | Link field | Link targets | Raw lanes | Capped lanes | Diagnosis | First next action |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 21 | `6bdc7f92afefff73` | `59` | `linked_feature_missing` | `1056` | `exit_lanes` | `1047` | 712 | 141 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 22 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | `219` | `exit_lanes` | none | 100 | 100 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 23 | `74a5b3325a534a87` | `3178` | `no_entry_lanes` | `333` | `entry_lanes` | none | 395 | 177 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 24 | `2f035a284480e981` | `715` | `linked_feature_missing` | `513` | `exit_lanes` | `326` | 402 | 143 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 25 | `4dfe7c285670839f` | `0` | `no_exit_lanes` | `44` | `exit_lanes` | none | 58 | 58 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 26 | `f672132039e83c40` | `519` | `no_exit_lanes` | `73` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 27 | `f672132039e83c40` | `520` | `no_exit_lanes` | `72` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 28 | `f672132039e83c40` | `522` | `no_exit_lanes` | `77` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 29 | `fe4a6425278fbd5b` | `816` | `no_exit_lanes` | `155` | `exit_lanes` | none | 186 | 183 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 30 | `c45b209a75ff4610` | `1869` | `linked_feature_missing` | `400` | `exit_lanes` | `405` | 380 | 214 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |

## `6bdc7f92afefff73` / track `59`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `1056`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 903 / 294
- Raw/capped lane features: 712 / 141
- Capped map at feature cap: True
- Horizon / route remaining: 150.972 m / 1.793 m
- Route gap to horizon: +149.179 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `1047` | False | True | 695 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

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

## `74a5b3325a534a87` / track `3178`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **terminal_lane_confirmed**
- Selected feature: `333`
- Link field: `entry_lanes`
- Lane-link status: `no_entry_lanes`
- Raw/capped map features: 528 / 286
- Raw/capped lane features: 395 / 177
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

## `2f035a284480e981` / track `715`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `513`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 556 / 285
- Raw/capped lane features: 402 / 143
- Capped map at feature cap: True
- Horizon / route remaining: 35.054 m / 0.000 m
- Route gap to horizon: +35.054 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `326` | False | True | 244 | True |

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

## `c45b209a75ff4610` / track `1869`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `400`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 573 / 338
- Raw/capped lane features: 380 / 214
- Capped map at feature cap: True
- Horizon / route remaining: 15.525 m / 0.446 m
- Route gap to horizon: +15.079 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `405` | False | True | 323 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## Interpretation

- Cap-recovered cases mean a referenced lane target from beyond the raw feature cap is now available in the capped ScenarioLens map feature set.
- Cap-recoverable cases mean the referenced lane target exists in the raw parsed map but was not available inside the capped ScenarioLens map feature set.
- Terminal-lane confirmations mean the selected lane has no parsed continuation in either the capped or raw parsed map; these need selected-lane or topology-neighborhood work rather than a simple cap increase.
- Raw-missing targets stay parser/proto-source audits until the referenced id can be found.
- This audit turns topology blockers into engineering tasks before expanding branch-selection and route-context guard claims.
