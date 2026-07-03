# ScenarioLens Lane-Continuation Terminal Neighborhood Audit

This report takes the topology-gap audit's terminal/directional blockers and asks whether the selected lane is truly terminal, directionally ambiguous, or recoverable by considering nearby aligned lanes before expanding branch selection.

The report is intentionally narrow: it does not change the default prediction baseline, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready: True
- Max scenarios per source: 25
- Neighborhood radius: 6.000 m
- Heading alignment minimum: 0.65
- Max lane-link hops: 2
- Raw scenario data committed: no
- Raw map geometry published: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Source topology cases | 5 |
| Terminal/directional cases selected | 3 |
| Cases audited | 3 |
| Ready cases | 3 |
| Nearby alternate-lane recovery candidates | 2 |
| Directional-link mismatch candidates | 1 |
| True terminal / map-boundary cases | 0 |
| Selected-lane issue candidates | 2 |
| Mean nearby lane candidates | 5.0 |
| Mean linked alternate count | 2.333 |
| Mean route gap to horizon | +81.545 m |

## Decisions

| Rank | Scenario | Track | Selected lane | Link field | Decision | Selected distance | Nearby lanes | Linked alternates | Best alternate | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 12 | `2f366a31ab03f8b` | `1061` | `219` | `exit_lanes` | `nearby_alternate_lane_recovery` | 0.223 m | 3 | 1 | `220` (255.255 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 13 | `74a5b3325a534a87` | `3178` | `333` | `entry_lanes` | `nearby_alternate_lane_recovery` | 0.163 m | 10 | 6 | `331` (95.966 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 15 | `4dfe7c285670839f` | `0` | `44` | `exit_lanes` | `directional_link_mismatch` | 0.323 m | 2 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |

## `2f366a31ab03f8b` / track `1061`

- Source: `validation.tfrecord-00007-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `219`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.223 m / 1.0
- Selected directional/opposite links: 0 / 1
- Horizon / selected route remaining: 165.493 m / 26.476 m
- Route gap to horizon: +139.017 m
- Nearby aligned lanes / linked alternates: 3 / 1

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `220` | False | 3.534 m | 1.0 | `exit_lanes` | 2 | `no_exit_lanes` | 255.255 m | True |
| `218` | False | 3.155 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 25.897 m | False |
| `219` | True | 0.223 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 26.476 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `220` before changing default scoring behavior.

## `74a5b3325a534a87` / track `3178`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `333`
- Lane-link status: `no_entry_lanes`
- Link field: `entry_lanes`
- Selected distance / alignment: 0.163 m / 0.691
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 59.581 m / 23.515 m
- Route gap to horizon: +36.066 m
- Nearby aligned lanes / linked alternates: 7 / 6

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `331` | False | 2.533 m | 0.69 | `entry_lanes` | 1 | `no_entry_lanes` | 95.966 m | True |
| `354` | False | 2.963 m | 0.961 | `exit_lanes` | 1 | `linked_lane_chain` | 71.449 m | True |
| `361` | False | 3.604 m | 0.713 | `entry_lanes` | 1 | `linked_feature_missing` | 50.734 m | True |
| `343` | False | 4.517 m | 0.709 | `exit_lanes` | 1 | `linked_lane_chain` | 69.711 m | True |
| `355` | False | 5.718 m | 0.997 | `exit_lanes` | 1 | `linked_lane_chain` | 74.460 m | True |
| `330` | False | 5.778 m | 0.69 | `entry_lanes` | 1 | `linked_lane_chain` | 96.242 m | True |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `331` before changing default scoring behavior.

## `4dfe7c285670839f` / track `0`

- Source: `validation.tfrecord-00008-of-00150`
- Diagnosis: **directional_link_mismatch**
- Reason: The selected lane has links only opposite the inferred travel direction, so the blocker may be direction or anchor-context sensitive.
- Selected feature: `44`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.323 m / 1.0
- Selected directional/opposite links: 0 / 2
- Horizon / selected route remaining: 85.416 m / 15.863 m
- Route gap to horizon: +69.553 m
- Nearby aligned lanes / linked alternates: 2 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `45` | False | 3.413 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 16.302 m | False |
| `44` | True | 0.323 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 15.863 m | False |

Recommended next actions:
- Audit anchor heading, lane direction, and entry/exit semantics for this case.
- Require replay evidence before allowing opposite-direction link recovery.

## Interpretation

- Nearby alternate-lane recovery candidates mean the selected lane was terminal, but another close, heading-aligned lane has parsed continuation that could seed a bounded neighborhood search.
- Directional-link mismatch candidates mean the selected lane has links only opposite the inferred travel direction; those cases need direction/anchor validation before adding branches.
- True terminal/map-boundary cases are held as map-boundary or topology-source follow-up rather than promoted into branch-selection claims.
- This is still a diagnostic framework, not a production planner: the next implementation step is to gate any alternate-lane recovery through replay evidence before changing default behavior.
