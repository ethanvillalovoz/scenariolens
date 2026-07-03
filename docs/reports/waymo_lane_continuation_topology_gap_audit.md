# ScenarioLens Lane-Continuation Topology Gap Audit

This audit works down the branch coverage queue's topology/parser blockers. For each topology-audit replay case, ScenarioLens reloads the local source slice, compares the capped ScenarioLens map features against raw parsed map-feature ids, and asks whether missing lane-link targets are recoverable by improving map materialization.

The report is intentionally narrow: it does not change the default baseline, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready: True
- Map feature cap: 240
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Cases audited | 5 |
| Ready cases | 5 |
| Cap-recovered cases | 0 |
| Still cap-recoverable cases | 1 |
| Terminal lanes confirmed | 4 |
| Raw target still missing | 0 |
| Selected feature missing in capped map | 0 |
| Capped maps at feature cap | 3 |
| Mean route gap to horizon | +69.780 m |

## Decisions

| Rank | Scenario | Track | Status | Selected lane | Link field | Link targets | Raw lanes | Capped lanes | Diagnosis | First next action |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 11 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | `219` | `exit_lanes` | none | 100 | 100 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 12 | `74a5b3325a534a87` | `3178` | `no_entry_lanes` | `333` | `entry_lanes` | none | 395 | 242 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 13 | `f64f295c8083bfd6` | `894` | `linked_feature_missing` | `349` | `exit_lanes` | `405` | 494 | 318 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 14 | `4dfe7c285670839f` | `0` | `no_exit_lanes` | `44` | `exit_lanes` | none | 58 | 58 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 15 | `f672132039e83c40` | `519` | `no_exit_lanes` | `73` | `exit_lanes` | none | 54 | 54 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |

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
- Raw/capped map features: 528 / 351
- Raw/capped lane features: 395 / 242
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

## `f64f295c8083bfd6` / track `894`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `349`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 657 / 440
- Raw/capped lane features: 494 / 318
- Capped map at feature cap: True
- Horizon / route remaining: 90.986 m / 20.926 m
- Route gap to horizon: +70.060 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `405` | False | True | 332 | True |

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

## Interpretation

- Cap-recovered cases mean a referenced lane target from beyond the raw feature cap is now available in the capped ScenarioLens map feature set.
- Cap-recoverable cases mean the referenced lane target exists in the raw parsed map but was not available inside the capped ScenarioLens map feature set.
- Terminal-lane confirmations mean the selected lane has no parsed continuation in either the capped or raw parsed map; these need selected-lane or topology-neighborhood work rather than a simple cap increase.
- Raw-missing targets stay parser/proto-source audits until the referenced id can be found.
- This audit turns topology blockers into engineering tasks before expanding branch-selection and route-context guard claims.
