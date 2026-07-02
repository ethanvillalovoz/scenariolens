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
| Cap-recoverable cases | 4 |
| Terminal lanes confirmed | 1 |
| Raw target still missing | 0 |
| Selected feature missing in capped map | 0 |
| Capped maps at feature cap | 5 |
| Mean route gap to horizon | +123.601 m |

## Decisions

| Rank | Scenario | Track | Status | Selected lane | Link field | Link targets | Raw lanes | Capped lanes | Diagnosis | First next action |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 11 | `fc8c647623f81bb4` | `1466` | `linked_feature_missing` | `153` | `exit_lanes` | `344` | 211 | 148 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 12 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | `219` | `exit_lanes` | none | 100 | 100 | `terminal_lane_confirmed` | Audit selected-lane quality and nearby alternate lanes before expanding branch selection. |
| 13 | `770fec53ec3e0395` | `1105` | `linked_feature_missing` | `306` | `exit_lanes` | `336`, `335` | 231 | 141 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 14 | `c52455a0495c9bdb` | `1937` | `linked_feature_missing` | `295` | `exit_lanes` | `811`, `823` | 484 | 87 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |
| 15 | `c45b209a75ff4610` | `1815` | `linked_feature_missing` | `248` | `exit_lanes` | `413` | 380 | 116 | `cap_recoverable_link_target` | Materialize closure features referenced by selected lane links before applying the map-feature cap. |

## `fc8c647623f81bb4` / track `1466`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `153`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 363 / 240
- Raw/capped lane features: 211 / 148
- Capped map at feature cap: True
- Horizon / route remaining: 160.476 m / 12.820 m
- Route gap to horizon: +147.656 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `344` | False | True | 276 | True |

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

## `770fec53ec3e0395` / track `1105`

- Source: `validation.tfrecord-00007-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `306`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 379 / 240
- Raw/capped lane features: 231 / 141
- Capped map at feature cap: True
- Horizon / route remaining: 115.837 m / 0.000 m
- Route gap to horizon: +115.837 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `336` | False | True | 258 | True |
| `335` | False | True | 257 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## `c52455a0495c9bdb` / track `1937`

- Source: `validation.tfrecord-00007-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `295`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 727 / 240
- Raw/capped lane features: 484 / 87
- Capped map at feature cap: True
- Horizon / route remaining: 142.662 m / 6.738 m
- Route gap to horizon: +135.924 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `811` | False | True | 570 | True |
| `823` | False | True | 582 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## `c45b209a75ff4610` / track `1815`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **cap_recoverable_link_target**
- Selected feature: `248`
- Link field: `exit_lanes`
- Lane-link status: `linked_feature_missing`
- Raw/capped map features: 573 / 240
- Raw/capped lane features: 380 / 116
- Capped map at feature cap: True
- Horizon / route remaining: 93.731 m / 14.162 m
- Route gap to horizon: +79.569 m
- Reason: At least one referenced link target exists in the raw parsed map but is absent from the capped ScenarioLens map feature set.

Link target presence:

| Target | In capped map | In raw map | Raw index | Beyond cap |
| --- | --- | --- | ---: | --- |
| `413` | False | True | 331 | True |

Recommended next actions:
- Materialize closure features referenced by selected lane links before applying the map-feature cap.
- Rerun lane-continuation replay and branch coverage after link-closure loading.

## Interpretation

- Cap-recoverable cases mean the referenced lane target exists in the raw parsed map but was not available inside the capped ScenarioLens map feature set.
- Terminal-lane confirmations mean the selected lane has no parsed continuation in either the capped or raw parsed map; these need selected-lane or topology-neighborhood work rather than a simple cap increase.
- Raw-missing targets stay parser/proto-source audits until the referenced id can be found.
- This audit turns topology blockers into engineering tasks before expanding branch-selection and route-context guard claims.
