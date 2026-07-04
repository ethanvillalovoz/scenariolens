# ScenarioLens Lane-Continuation Terminal Neighborhood Audit

This report takes the topology-gap audit's terminal/directional blockers and asks whether the selected lane is truly terminal, directionally ambiguous, or recoverable by considering nearby aligned lanes before expanding branch selection.

The report is intentionally narrow: it does not change the default prediction baseline, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_200/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_200/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates_200/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study_200/manifest.json`
- Ready: True
- Max scenarios per source: 50
- Neighborhood radius: 6.000 m
- Heading alignment minimum: 0.65
- Max lane-link hops: 2
- Raw scenario data committed: no
- Raw map geometry published: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Source topology cases | 15 |
| Terminal/directional cases selected | 13 |
| Cases audited | 13 |
| Ready cases | 13 |
| Nearby alternate-lane recovery candidates | 7 |
| Directional-link mismatch candidates | 5 |
| True terminal / map-boundary cases | 1 |
| Selected-lane issue candidates | 7 |
| Mean nearby lane candidates | 4.077 |
| Mean linked alternate count | 1.846 |
| Mean route gap to horizon | +50.263 m |

## Decisions

| Rank | Scenario | Track | Selected lane | Link field | Decision | Selected distance | Nearby lanes | Linked alternates | Best alternate | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 31 | `2f366a31ab03f8b` | `1061` | `219` | `exit_lanes` | `nearby_alternate_lane_recovery` | 0.223 m | 3 | 1 | `220` (255.255 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 32 | `8ce92d09a94bf2c8` | `2516` | `183` | `entry_lanes` | `true_terminal_or_map_boundary` | 3.166 m | 1 | 0 | none | Keep this case as a map-boundary/topology-source blocker. |
| 34 | `74a5b3325a534a87` | `3178` | `333` | `entry_lanes` | `nearby_alternate_lane_recovery` | 0.163 m | 10 | 6 | `331` (95.966 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 35 | `28f34edeb361e955` | `987` | `158` | `exit_lanes` | `nearby_alternate_lane_recovery` | 3.490 m | 5 | 3 | `157` (89.733 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 36 | `634b468a246a77d6` | `116` | `99` | `exit_lanes` | `nearby_alternate_lane_recovery` | 0.237 m | 7 | 4 | `85` (49.016 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 38 | `4dfe7c285670839f` | `0` | `44` | `exit_lanes` | `directional_link_mismatch` | 0.323 m | 2 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |
| 39 | `f672132039e83c40` | `519` | `73` | `exit_lanes` | `directional_link_mismatch` | 0.094 m | 2 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |
| 40 | `f672132039e83c40` | `520` | `72` | `exit_lanes` | `directional_link_mismatch` | 0.004 m | 2 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |
| 41 | `8abe59aee39f351e` | `4650` | `161` | `exit_lanes` | `nearby_alternate_lane_recovery` | 2.337 m | 5 | 4 | `143` (86.161 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 42 | `9c8241f6a2ee5f51` | `88` | `223` | `exit_lanes` | `nearby_alternate_lane_recovery` | 0.805 m | 6 | 3 | `237` (94.858 m) | Add a bounded selected-lane neighborhood search before branch selection. |
| 43 | `f672132039e83c40` | `522` | `77` | `exit_lanes` | `directional_link_mismatch` | 0.530 m | 3 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |
| 44 | `634b468a246a77d6` | `115` | `91` | `exit_lanes` | `directional_link_mismatch` | 0.541 m | 3 | 0 | none | Audit anchor heading, lane direction, and entry/exit semantics for this case. |
| 45 | `fe4a6425278fbd5b` | `816` | `155` | `exit_lanes` | `nearby_alternate_lane_recovery` | 0.284 m | 4 | 3 | `344` (62.065 m) | Add a bounded selected-lane neighborhood search before branch selection. |

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

## `8ce92d09a94bf2c8` / track `2516`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **true_terminal_or_map_boundary**
- Reason: No close, heading-aligned lane with parsed continuation was found around the selected terminal lane.
- Selected feature: `183`
- Lane-link status: `no_entry_lanes`
- Link field: `entry_lanes`
- Selected distance / alignment: 3.166 m / 1.0
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 125.303 m / 27.472 m
- Route gap to horizon: +97.831 m
- Nearby aligned lanes / linked alternates: 1 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `183` | True | 3.166 m | 1.0 | `entry_lanes` | 0 | `no_entry_lanes` | 27.472 m | False |

Recommended next actions:
- Keep this case as a map-boundary/topology-source blocker.
- Do not promote it into branch selection without new map context.

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
| `361` | False | 3.604 m | 0.713 | `entry_lanes` | 1 | `linked_lane_chain` | 67.714 m | True |
| `343` | False | 4.517 m | 0.709 | `exit_lanes` | 1 | `linked_lane_chain` | 69.711 m | True |
| `355` | False | 5.718 m | 0.997 | `exit_lanes` | 1 | `linked_lane_chain` | 74.460 m | True |
| `330` | False | 5.778 m | 0.69 | `entry_lanes` | 1 | `linked_lane_chain` | 96.242 m | True |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `331` before changing default scoring behavior.

## `28f34edeb361e955` / track `987`

- Source: `validation.tfrecord-00009-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `158`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 3.490 m / 0.997
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 57.799 m / 32.851 m
- Route gap to horizon: +24.948 m
- Nearby aligned lanes / linked alternates: 5 / 3

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `157` | False | 4.719 m | 0.886 | `exit_lanes` | 1 | `linked_lane_chain` | 89.733 m | True |
| `127` | False | 5.243 m | 0.884 | `exit_lanes` | 1 | `linked_lane_chain` | 48.728 m | True |
| `147` | False | 5.243 m | 0.884 | `exit_lanes` | 1 | `linked_lane_chain` | 48.728 m | True |
| `159` | False | 5.660 m | 0.996 | `exit_lanes` | 0 | `no_exit_lanes` | 32.864 m | False |
| `158` | True | 3.490 m | 0.997 | `exit_lanes` | 0 | `no_exit_lanes` | 32.851 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `157` before changing default scoring behavior.

## `634b468a246a77d6` / track `116`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `99`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.237 m / 0.999
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 75.123 m / 16.502 m
- Route gap to horizon: +58.621 m
- Nearby aligned lanes / linked alternates: 5 / 4

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `85` | False | 0.269 m | 0.823 | `exit_lanes` | 1 | `no_exit_lanes` | 49.016 m | True |
| `92` | False | 2.252 m | 1.0 | `exit_lanes` | 1 | `no_exit_lanes` | 55.602 m | True |
| `86` | False | 3.032 m | 0.933 | `exit_lanes` | 1 | `no_exit_lanes` | 53.001 m | True |
| `87` | False | 3.563 m | 0.77 | `entry_lanes` | 1 | `no_entry_lanes` | 143.037 m | True |
| `99` | True | 0.237 m | 0.999 | `exit_lanes` | 0 | `no_exit_lanes` | 16.502 m | False |
| `84` | False | 3.149 m | 0.103 | `exit_lanes` | 1 | `no_exit_lanes` | 47.991 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `85` before changing default scoring behavior.

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

## `f672132039e83c40` / track `519`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **directional_link_mismatch**
- Reason: The selected lane has links only opposite the inferred travel direction, so the blocker may be direction or anchor-context sensitive.
- Selected feature: `73`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.094 m / 1.0
- Selected directional/opposite links: 0 / 1
- Horizon / selected route remaining: 55.400 m / 21.194 m
- Route gap to horizon: +34.206 m
- Nearby aligned lanes / linked alternates: 2 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `77` | False | 3.268 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 21.106 m | False |
| `73` | True | 0.094 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 21.194 m | False |

Recommended next actions:
- Audit anchor heading, lane direction, and entry/exit semantics for this case.
- Require replay evidence before allowing opposite-direction link recovery.

## `f672132039e83c40` / track `520`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **directional_link_mismatch**
- Reason: The selected lane has links only opposite the inferred travel direction, so the blocker may be direction or anchor-context sensitive.
- Selected feature: `72`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.004 m / 1.0
- Selected directional/opposite links: 0 / 2
- Horizon / selected route remaining: 54.924 m / 20.811 m
- Route gap to horizon: +34.113 m
- Nearby aligned lanes / linked alternates: 2 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `77` | False | 3.433 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 20.845 m | False |
| `72` | True | 0.004 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 20.811 m | False |

Recommended next actions:
- Audit anchor heading, lane direction, and entry/exit semantics for this case.
- Require replay evidence before allowing opposite-direction link recovery.

## `8abe59aee39f351e` / track `4650`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `161`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 2.337 m / 0.999
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 29.126 m / 4.367 m
- Route gap to horizon: +24.759 m
- Nearby aligned lanes / linked alternates: 5 / 4

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `143` | False | 4.426 m | 0.999 | `exit_lanes` | 1 | `no_exit_lanes` | 86.161 m | True |
| `144` | False | 4.426 m | 0.999 | `exit_lanes` | 1 | `no_exit_lanes` | 82.252 m | True |
| `160` | False | 4.807 m | 1.0 | `exit_lanes` | 1 | `linked_lane_chain` | 56.352 m | True |
| `151` | False | 5.757 m | 1.0 | `exit_lanes` | 1 | `linked_lane_chain` | 115.408 m | True |
| `161` | True | 2.337 m | 0.999 | `exit_lanes` | 0 | `no_exit_lanes` | 4.367 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `143` before changing default scoring behavior.

## `9c8241f6a2ee5f51` / track `88`

- Source: `validation.tfrecord-00008-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `223`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.805 m / 0.122
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 37.110 m / 24.718 m
- Route gap to horizon: +12.392 m
- Nearby aligned lanes / linked alternates: 3 / 3

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `237` | False | 2.070 m | 0.741 | `exit_lanes` | 1 | `linked_lane_chain` | 94.858 m | True |
| `240` | False | 3.684 m | 1.0 | `exit_lanes` | 1 | `linked_lane_chain` | 93.004 m | True |
| `220` | False | 4.196 m | 0.987 | `exit_lanes` | 1 | `linked_lane_chain` | 92.326 m | True |
| `235` | False | 3.361 m | 0.087 | `exit_lanes` | 1 | `linked_lane_chain` | 106.937 m | False |
| `251` | False | 5.805 m | 0.094 | `exit_lanes` | 2 | `linked_lane_chain` | 56.771 m | False |
| `223` | True | 0.805 m | 0.122 | `exit_lanes` | 0 | `no_exit_lanes` | 24.718 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `237` before changing default scoring behavior.

## `f672132039e83c40` / track `522`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **directional_link_mismatch**
- Reason: The selected lane has links only opposite the inferred travel direction, so the blocker may be direction or anchor-context sensitive.
- Selected feature: `77`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.530 m / 0.992
- Selected directional/opposite links: 0 / 2
- Horizon / selected route remaining: 45.100 m / 32.738 m
- Route gap to horizon: +12.362 m
- Nearby aligned lanes / linked alternates: 3 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `73` | False | 2.873 m | 0.992 | `exit_lanes` | 0 | `no_exit_lanes` | 32.821 m | False |
| `72` | False | 3.990 m | 0.992 | `exit_lanes` | 0 | `no_exit_lanes` | 32.696 m | False |
| `77` | True | 0.530 m | 0.992 | `exit_lanes` | 0 | `no_exit_lanes` | 32.738 m | False |

Recommended next actions:
- Audit anchor heading, lane direction, and entry/exit semantics for this case.
- Require replay evidence before allowing opposite-direction link recovery.

## `634b468a246a77d6` / track `115`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **directional_link_mismatch**
- Reason: The selected lane has links only opposite the inferred travel direction, so the blocker may be direction or anchor-context sensitive.
- Selected feature: `91`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.541 m / 1.0
- Selected directional/opposite links: 0 / 3
- Horizon / selected route remaining: 72.616 m / 15.502 m
- Route gap to horizon: +57.114 m
- Nearby aligned lanes / linked alternates: 3 / 0

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `100` | False | 2.303 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 16.241 m | False |
| `90` | False | 3.989 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 16.756 m | False |
| `91` | True | 0.541 m | 1.0 | `exit_lanes` | 0 | `no_exit_lanes` | 15.502 m | False |

Recommended next actions:
- Audit anchor heading, lane direction, and entry/exit semantics for this case.
- Require replay evidence before allowing opposite-direction link recovery.

## `fe4a6425278fbd5b` / track `816`

- Source: `validation.tfrecord-00010-of-00150`
- Diagnosis: **nearby_alternate_lane_recovery**
- Reason: The selected lane is terminal for the requested direction, but a nearby heading-aligned lane has parsed directional continuation.
- Selected feature: `155`
- Lane-link status: `no_exit_lanes`
- Link field: `exit_lanes`
- Selected distance / alignment: 0.284 m / 0.997
- Selected directional/opposite links: 0 / 0
- Horizon / selected route remaining: 66.469 m / 14.029 m
- Route gap to horizon: +52.440 m
- Nearby aligned lanes / linked alternates: 4 / 3

Nearby lane candidates:

| Feature | Selected | Distance | Alignment | Link field | Directional links | Route status | Route remaining | Recovery candidate |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| `344` | False | 0.988 m | 0.984 | `exit_lanes` | 1 | `linked_lane_chain` | 62.065 m | True |
| `345` | False | 2.586 m | 0.997 | `exit_lanes` | 1 | `linked_lane_chain` | 85.423 m | True |
| `157` | False | 5.933 m | 0.997 | `exit_lanes` | 1 | `linked_lane_chain` | 86.733 m | True |
| `155` | True | 0.284 m | 0.997 | `exit_lanes` | 0 | `no_exit_lanes` | 14.029 m | False |

Recommended next actions:
- Add a bounded selected-lane neighborhood search before branch selection.
- Replay alternate lane `344` before changing default scoring behavior.

## Interpretation

- Nearby alternate-lane recovery candidates mean the selected lane was terminal, but another close, heading-aligned lane has parsed continuation that could seed a bounded neighborhood search.
- Directional-link mismatch candidates mean the selected lane has links only opposite the inferred travel direction; those cases need direction/anchor validation before adding branches.
- True terminal/map-boundary cases are held as map-boundary or topology-source follow-up rather than promoted into branch-selection claims.
- This is still a diagnostic framework, not a production planner: the next implementation step is to gate any alternate-lane recovery through replay evidence before changing default behavior.
