# ScenarioLens Lane-Continuation Replay Prototype

This report executes the next laptop-safe step after the lane-continuation candidate plan. It reloads selected local scenarios, replays nearest-lane and linked-lane continuation rollouts for the queued target tracks, and applies small deterministic anchor-velocity perturbations to check whether each improvement or regression remains stable.

Topology-audit candidates are re-probed as blockers instead of being treated as valid route predictions. The report is intentionally scoped: this is not route planning, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local replay packets stay out of git.

## Scope

- Candidate manifest: `data/processed/waymo_lane_continuation_candidates/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready for replay analysis: True
- Input format: `native`
- Max scenarios per source: 25
- Top candidates per bucket: 5
- Selected candidates: 15
- Raw scenario data committed: no
- Local replay packets committed: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Evaluated cases | 15 |
| Replay cases | 10 |
| Topology probes | 5 |
| Replay targets | 10 |
| Perturbation trials | 40 |
| Sign-preserving trials | 40 |
| Sign-preservation rate | 100.0% |
| Nominal lane-link improvements | 5 |
| Nominal lane-link regressions | 5 |
| Topology blockers confirmed | 5 |

## Perturbation Set

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Replayed Candidates

| Rank | Queue | Scenario | Track | Readiness | Nearest FDE | Lane-link FDE | Delta | Link status | Sign stability | Max swing |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | `improvement_replay_control` | `a863e5638dfff0ca` | `1765` | `ready_for_improvement_replay_with_horizon_caution` | 144.122 m | 7.919 m | +136.203 m | `linked_lane_chain` | 4/4 | 15.483 m |
| 2 | `improvement_replay_control` | `2f366a31ab03f8b` | `1059` | `ready_for_continuation_improvement_replay` | 148.345 m | 9.068 m | +139.277 m | `no_exit_lanes` | 4/4 | 16.874 m |
| 3 | `improvement_replay_control` | `65d7afd24453a1ba` | `510` | `ready_for_improvement_replay_with_horizon_caution` | 90.668 m | 5.454 m | +85.214 m | `linked_lane_chain` | 4/4 | 1.391 m |
| 4 | `improvement_replay_control` | `77c44d1768793143` | `34` | `ready_for_continuation_improvement_replay` | 87.044 m | 3.732 m | +83.312 m | `linked_lane_chain` | 4/4 | 9.947 m |
| 5 | `improvement_replay_control` | `564a6bcc85c4f72f` | `1143` | `ready_for_continuation_improvement_replay` | 81.835 m | 6.818 m | +75.017 m | `linked_lane_chain` | 4/4 | 8.250 m |
| 6 | `regression_replay_debug` | `260785192cf6c991` | `1754` | `ready_for_regression_replay_with_horizon_caution` | 22.573 m | 81.112 m | -58.539 m | `linked_lane_chain` | 4/4 | 5.178 m |
| 7 | `regression_replay_debug` | `d8dde10f514a501c` | `651` | `ready_for_continuation_regression_replay` | 73.197 m | 104.290 m | -31.093 m | `linked_lane_chain` | 4/4 | 5.240 m |
| 8 | `regression_replay_debug` | `e3f6a29b59e42c1` | `741` | `ready_for_continuation_regression_replay` | 15.869 m | 58.942 m | -43.073 m | `linked_lane_chain` | 4/4 | 9.947 m |
| 9 | `regression_replay_debug` | `5c49e681a66c720` | `2627` | `ready_for_continuation_regression_replay` | 4.595 m | 38.598 m | -34.003 m | `linked_lane_chain` | 4/4 | 6.084 m |
| 10 | `regression_replay_debug` | `e9db41e904b349a2` | `406` | `ready_for_continuation_regression_replay` | 6.776 m | 38.292 m | -31.516 m | `linked_lane_chain` | 4/4 | 5.692 m |

## Topology Probes

| Rank | Scenario | Track | Link status | Link count | Nearest FDE | Lane-link FDE | First blocker |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 11 | `fc8c647623f81bb4` | `1466` | `linked_feature_missing` | 0 | 144.514 m | 144.514 m | No usable parsed linked-lane chain is available yet. |
| 12 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | 0 | 133.872 m | 133.872 m | No usable parsed linked-lane chain is available yet. |
| 13 | `770fec53ec3e0395` | `1105` | `linked_feature_missing` | 0 | 131.434 m | 131.434 m | No usable parsed linked-lane chain is available yet. |
| 14 | `c52455a0495c9bdb` | `1937` | `linked_feature_missing` | 0 | 121.451 m | 121.451 m | No usable parsed linked-lane chain is available yet. |
| 15 | `c45b209a75ff4610` | `1815` | `linked_feature_missing` | 0 | 117.044 m | 117.044 m | No usable parsed linked-lane chain is available yet. |

## `a863e5638dfff0ca` / track `1765`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 249 -> 244 -> 275
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/1-improvement-replay-control-a863e5638dfff0ca-1765/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10.628 m | 144.122 m | 144.122 m | 7.919 m | +136.203 m | +2.709 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +120.720 m | True | 144.122 m | 23.402 m | `linked_lane_chain` |
| `speed_plus_10pct` | +136.203 m | True | 144.122 m | 7.919 m | `linked_lane_chain` |
| `heading_left_5deg` | +136.203 m | True | 144.122 m | 7.919 m | `linked_lane_chain` |
| `heading_right_5deg` | +136.203 m | True | 144.122 m | 7.919 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `2f366a31ab03f8b` / track `1059`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 220 -> 210
- Link status/count: `no_exit_lanes` / 1
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/2-improvement-replay-control-2f366a31ab03f8b-1059/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 9.071 m | 148.345 m | 148.345 m | 9.068 m | +139.277 m | +0.003 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +140.539 m | True | 148.345 m | 7.806 m | `no_exit_lanes` |
| `speed_plus_10pct` | +122.403 m | True | 148.345 m | 25.942 m | `no_exit_lanes` |
| `heading_left_5deg` | +139.277 m | True | 148.345 m | 9.068 m | `no_exit_lanes` |
| `heading_right_5deg` | +139.277 m | True | 148.345 m | 9.068 m | `no_exit_lanes` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `65d7afd24453a1ba` / track `510`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 159 -> 146 -> 140
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/3-improvement-replay-control-65d7afd24453a1ba-510/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6.452 m | 90.668 m | 90.668 m | 5.454 m | +85.214 m | +0.998 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +86.605 m | True | 90.668 m | 4.063 m | `linked_lane_chain` |
| `speed_plus_10pct` | +85.214 m | True | 90.668 m | 5.454 m | `linked_lane_chain` |
| `heading_left_5deg` | +85.214 m | True | 90.668 m | 5.454 m | `linked_lane_chain` |
| `heading_right_5deg` | +85.214 m | True | 90.668 m | 5.454 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `77c44d1768793143` / track `34`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 176 -> 164 -> 148
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/4-improvement-replay-control-77c44d1768793143-34/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 8.927 m | 87.044 m | 87.044 m | 3.732 m | +83.312 m | +5.195 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +73.365 m | True | 87.044 m | 13.679 m | `linked_lane_chain` |
| `speed_plus_10pct` | +80.814 m | True | 87.044 m | 6.230 m | `linked_lane_chain` |
| `heading_left_5deg` | +83.312 m | True | 87.044 m | 3.732 m | `linked_lane_chain` |
| `heading_right_5deg` | +83.312 m | True | 87.044 m | 3.732 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `564a6bcc85c4f72f` / track `1143`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 167 -> 173 -> 255
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/5-improvement-replay-control-564a6bcc85c4f72f-1143/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6.816 m | 81.835 m | 81.835 m | 6.818 m | +75.017 m | -0.002 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +66.767 m | True | 81.835 m | 15.068 m | `linked_lane_chain` |
| `speed_plus_10pct` | +77.895 m | True | 81.835 m | 3.940 m | `linked_lane_chain` |
| `heading_left_5deg` | +75.017 m | True | 81.835 m | 6.818 m | `linked_lane_chain` |
| `heading_right_5deg` | +75.017 m | True | 81.835 m | 6.818 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `260785192cf6c991` / track `1754`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 235 -> 241 -> 315
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/6-regression-replay-debug-260785192cf6c991-1754/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 87.149 m | 22.573 m | 22.573 m | 81.112 m | -58.539 m | +6.037 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -53.361 m | True | 22.573 m | 75.934 m | `linked_lane_chain` |
| `speed_plus_10pct` | -58.539 m | True | 22.573 m | 81.112 m | `linked_lane_chain` |
| `heading_left_5deg` | -58.539 m | True | 22.573 m | 81.112 m | `linked_lane_chain` |
| `heading_right_5deg` | -58.539 m | True | 22.573 m | 81.112 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `d8dde10f514a501c` / track `651`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 134 -> 143 -> 146
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/7-regression-replay-debug-d8dde10f514a501c-651/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 57.742 m | 73.197 m | 73.197 m | 104.290 m | -31.093 m | -46.548 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -25.853 m | True | 73.197 m | 99.050 m | `linked_lane_chain` |
| `speed_plus_10pct` | -36.333 m | True | 73.197 m | 109.530 m | `linked_lane_chain` |
| `heading_left_5deg` | -31.093 m | True | 73.197 m | 104.290 m | `linked_lane_chain` |
| `heading_right_5deg` | -31.093 m | True | 73.197 m | 104.290 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `e3f6a29b59e42c1` / track `741`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 161 -> 127 -> 116
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/8-regression-replay-debug-e3f6a29b59e42c1-741/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 58.947 m | 15.869 m | 15.869 m | 58.942 m | -43.073 m | +0.005 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -33.126 m | True | 15.869 m | 48.995 m | `linked_lane_chain` |
| `speed_plus_10pct` | -53.019 m | True | 15.869 m | 68.888 m | `linked_lane_chain` |
| `heading_left_5deg` | -43.073 m | True | 15.869 m | 58.942 m | `linked_lane_chain` |
| `heading_right_5deg` | -43.073 m | True | 15.869 m | 58.942 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `5c49e681a66c720` / track `2627`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 285 -> 120 -> 119
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/9-regression-replay-debug-5c49e681a66c720-2627/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 38.406 m | 4.595 m | 4.595 m | 38.598 m | -34.003 m | -0.192 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -27.924 m | True | 4.595 m | 32.519 m | `linked_lane_chain` |
| `speed_plus_10pct` | -40.087 m | True | 4.595 m | 44.682 m | `linked_lane_chain` |
| `heading_left_5deg` | -34.003 m | True | 4.595 m | 38.598 m | `linked_lane_chain` |
| `heading_right_5deg` | -34.003 m | True | 4.595 m | 38.598 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `e9db41e904b349a2` / track `406`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 295 -> 228 -> 201
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/10-regression-replay-debug-e9db41e904b349a2-406/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 38.292 m | 6.776 m | 6.776 m | 38.292 m | -31.516 m | 0.000 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -25.825 m | True | 6.776 m | 32.601 m | `linked_lane_chain` |
| `speed_plus_10pct` | -37.208 m | True | 6.776 m | 43.984 m | `linked_lane_chain` |
| `heading_left_5deg` | -31.516 m | True | 6.776 m | 38.292 m | `linked_lane_chain` |
| `heading_right_5deg` | -31.516 m | True | 6.776 m | 38.292 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `fc8c647623f81bb4` / track `1466`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 153
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/11-topology-audit-fc8c647623f81bb4-1466/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 3.152 m | 144.514 m | 144.514 m | 144.514 m | 0.000 m | -141.362 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `2f366a31ab03f8b` / track `1061`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 219
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/12-topology-audit-2f366a31ab03f8b-1061/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6.081 m | 133.872 m | 133.872 m | 133.872 m | 0.000 m | -127.791 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `770fec53ec3e0395` / track `1105`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 306
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/13-topology-audit-770fec53ec3e0395-1105/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 14.075 m | 131.434 m | 131.434 m | 131.434 m | 0.000 m | -117.359 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `c52455a0495c9bdb` / track `1937`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 295
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/14-topology-audit-c52455a0495c9bdb-1937/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 14.497 m | 121.451 m | 121.451 m | 121.451 m | 0.000 m | -106.954 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `c45b209a75ff4610` / track `1815`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 248
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/15-topology-audit-c45b209a75ff4610-1815/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 37.477 m | 117.044 m | 117.044 m | 117.044 m | 0.000 m | -79.567 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## Interpretation

- Stable improvement controls are useful because they prove the lane-link mechanism on cases where nearest-lane clamping was misleading.
- Stable regressions are useful debugging targets because linked-lane following can still choose the wrong route or out-run available topology.
- Topology probes are blockers, not model-performance claims; they identify missing links, map-feature caps, or parser coverage work.
- This keeps ScenarioLens honest: public outputs are diagnostic summaries, while raw Waymo files and local replay packets remain ignored.
