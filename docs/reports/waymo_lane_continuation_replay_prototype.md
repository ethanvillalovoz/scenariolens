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
| 1 | `improvement_replay_control` | `937eb2fa17da45c0` | `979` | `ready_for_improvement_replay_with_horizon_caution` | 151.676 m | 10.354 m | +141.322 m | `linked_lane_chain` | 4/4 | 16.070 m |
| 2 | `improvement_replay_control` | `a863e5638dfff0ca` | `1765` | `ready_for_improvement_replay_with_horizon_caution` | 144.122 m | 7.919 m | +136.203 m | `linked_lane_chain` | 4/4 | 15.483 m |
| 3 | `improvement_replay_control` | `fc8c647623f81bb4` | `1466` | `ready_for_continuation_improvement_replay` | 144.514 m | 3.143 m | +141.371 m | `linked_lane_chain` | 4/4 | 16.047 m |
| 4 | `improvement_replay_control` | `2f366a31ab03f8b` | `1059` | `ready_for_continuation_improvement_replay` | 148.345 m | 9.068 m | +139.277 m | `no_exit_lanes` | 4/4 | 16.874 m |
| 5 | `improvement_replay_control` | `8807e9963f411c48` | `722` | `ready_for_continuation_improvement_replay` | 103.862 m | 3.700 m | +100.162 m | `linked_lane_chain` | 4/4 | 12.629 m |
| 6 | `regression_replay_debug` | `260785192cf6c991` | `1754` | `ready_for_regression_replay_with_horizon_caution` | 22.573 m | 81.112 m | -58.539 m | `linked_lane_chain` | 4/4 | 5.178 m |
| 7 | `regression_replay_debug` | `e3f6a29b59e42c1` | `741` | `ready_for_continuation_regression_replay` | 15.869 m | 58.942 m | -43.073 m | `linked_lane_chain` | 4/4 | 9.947 m |
| 8 | `regression_replay_debug` | `d30709cd60e60395` | `164` | `ready_for_continuation_regression_replay` | 16.292 m | 52.496 m | -36.204 m | `linked_lane_chain` | 4/4 | 4.263 m |
| 9 | `regression_replay_debug` | `5c49e681a66c720` | `2627` | `ready_for_continuation_regression_replay` | 4.595 m | 38.598 m | -34.003 m | `linked_lane_chain` | 4/4 | 6.084 m |
| 10 | `regression_replay_debug` | `e9db41e904b349a2` | `406` | `ready_for_continuation_regression_replay` | 6.776 m | 38.292 m | -31.516 m | `linked_lane_chain` | 4/4 | 5.692 m |

## Topology Probes

| Rank | Scenario | Track | Link status | Link count | Nearest FDE | Lane-link FDE | First blocker |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 11 | `6bdc7f92afefff73` | `59` | `linked_feature_missing` | 0 | 134.082 m | 134.082 m | No usable parsed linked-lane chain is available yet. |
| 12 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | 0 | 133.872 m | 133.872 m | No usable parsed linked-lane chain is available yet. |
| 13 | `74a5b3325a534a87` | `3178` | `no_entry_lanes` | 0 | 88.934 m | 88.934 m | No usable parsed linked-lane chain is available yet. |
| 14 | `2f035a284480e981` | `715` | `linked_feature_missing` | 0 | 58.747 m | 58.747 m | No usable parsed linked-lane chain is available yet. |
| 15 | `4dfe7c285670839f` | `0` | `no_exit_lanes` | 0 | 51.637 m | 51.637 m | No usable parsed linked-lane chain is available yet. |

## `937eb2fa17da45c0` / track `979`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 312 -> 319 -> 246
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/1-improvement-replay-control-937eb2fa17da45c0-979/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 13.028 m | 151.676 m | 151.676 m | 10.354 m | +141.322 m | +2.674 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +125.252 m | True | 151.676 m | 26.424 m | `linked_lane_chain` |
| `speed_plus_10pct` | +141.322 m | True | 151.676 m | 10.354 m | `linked_lane_chain` |
| `heading_left_5deg` | +141.322 m | True | 151.676 m | 10.354 m | `linked_lane_chain` |
| `heading_right_5deg` | +141.322 m | True | 151.676 m | 10.354 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `a863e5638dfff0ca` / track `1765`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 249 -> 244 -> 275
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/2-improvement-replay-control-a863e5638dfff0ca-1765/lane_continuation_replay_packet.json`

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

## `fc8c647623f81bb4` / track `1466`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 153 -> 344 -> 343
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/3-improvement-replay-control-fc8c647623f81bb4-1466/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 3.152 m | 144.514 m | 144.514 m | 3.143 m | +141.371 m | +0.009 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +131.609 m | True | 144.514 m | 12.905 m | `linked_lane_chain` |
| `speed_plus_10pct` | +125.324 m | True | 144.514 m | 19.190 m | `linked_lane_chain` |
| `heading_left_5deg` | +141.371 m | True | 144.514 m | 3.143 m | `linked_lane_chain` |
| `heading_right_5deg` | +141.371 m | True | 144.514 m | 3.143 m | `linked_lane_chain` |

Blockers / cautions:
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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/4-improvement-replay-control-2f366a31ab03f8b-1059/lane_continuation_replay_packet.json`

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

## `8807e9963f411c48` / track `722`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 337 -> 559 -> 553
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/5-improvement-replay-control-8807e9963f411c48-722/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4.193 m | 103.862 m | 103.862 m | 3.700 m | +100.162 m | +0.493 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +94.851 m | True | 103.862 m | 9.011 m | `linked_lane_chain` |
| `speed_plus_10pct` | +87.533 m | True | 103.862 m | 16.329 m | `linked_lane_chain` |
| `heading_left_5deg` | +100.162 m | True | 103.862 m | 3.700 m | `linked_lane_chain` |
| `heading_right_5deg` | +100.162 m | True | 103.862 m | 3.700 m | `linked_lane_chain` |

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

## `e3f6a29b59e42c1` / track `741`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 161 -> 127 -> 116
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/7-regression-replay-debug-e3f6a29b59e42c1-741/lane_continuation_replay_packet.json`

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

## `d30709cd60e60395` / track `164`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 603 -> 610 -> 371
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/8-regression-replay-debug-d30709cd60e60395-164/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 61.024 m | 16.292 m | 16.292 m | 52.496 m | -36.204 m | +8.528 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -32.143 m | True | 16.292 m | 48.435 m | `linked_lane_chain` |
| `speed_plus_10pct` | -40.467 m | True | 16.292 m | 56.759 m | `linked_lane_chain` |
| `heading_left_5deg` | -36.204 m | True | 16.292 m | 52.496 m | `linked_lane_chain` |
| `heading_right_5deg` | -36.204 m | True | 16.292 m | 52.496 m | `linked_lane_chain` |

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

## `6bdc7f92afefff73` / track `59`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 1056
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/11-topology-audit-6bdc7f92afefff73-59/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 15.263 m | 134.082 m | 134.082 m | 134.082 m | 0.000 m | -118.819 m | True |

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

## `74a5b3325a534a87` / track `3178`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 333
- Link status/count: `no_entry_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/13-topology-audit-74a5b3325a534a87-3178/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 56.254 m | 88.934 m | 88.934 m | 88.934 m | 0.000 m | -32.680 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `2f035a284480e981` / track `715`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 513
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/14-topology-audit-2f035a284480e981-715/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 22.381 m | 58.747 m | 58.747 m | 58.747 m | 0.000 m | -36.366 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `4dfe7c285670839f` / track `0`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 44
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype/cases/15-topology-audit-4dfe7c285670839f-0/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 17.949 m | 51.637 m | 51.637 m | 51.637 m | 0.000 m | -33.688 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## Interpretation

- Stable improvement controls are useful because they prove the lane-link mechanism on cases where nearest-lane clamping was misleading.
- Stable regressions are useful debugging targets because linked-lane following can still choose the wrong route or out-run available topology.
- Topology probes are blockers, not model-performance claims; they identify missing links, map-feature caps, or parser coverage work.
- This keeps ScenarioLens honest: public outputs are diagnostic summaries, while raw Waymo files and local replay packets remain ignored.
