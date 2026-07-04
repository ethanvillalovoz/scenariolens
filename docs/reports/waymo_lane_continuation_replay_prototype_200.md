# ScenarioLens Lane-Continuation Replay Prototype

This report executes the next laptop-safe step after the lane-continuation candidate plan. It reloads selected local scenarios, replays nearest-lane and linked-lane continuation rollouts for the queued target tracks, and applies small deterministic anchor-velocity perturbations to check whether each improvement or regression remains stable.

Topology-audit candidates are re-probed as blockers instead of being treated as valid route predictions. The report is intentionally scoped: this is not route planning, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local replay packets stay out of git.

## Scope

- Candidate manifest: `data/processed/waymo_lane_continuation_candidates_200/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study_200/manifest.json`
- Ready for replay analysis: True
- Input format: `native`
- Max scenarios per source: 50
- Top candidates per bucket: 15
- Selected candidates: 45
- Raw scenario data committed: no
- Local replay packets committed: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Evaluated cases | 45 |
| Replay cases | 30 |
| Topology probes | 15 |
| Replay targets | 30 |
| Perturbation trials | 120 |
| Sign-preserving trials | 120 |
| Sign-preservation rate | 100.0% |
| Nominal lane-link improvements | 15 |
| Nominal lane-link regressions | 15 |
| Topology blockers confirmed | 15 |

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
| 3 | `improvement_replay_control` | `2f7869c277b1a86e` | `1925` | `ready_for_continuation_improvement_replay` | 156.670 m | 4.583 m | +152.087 m | `linked_lane_chain` | 4/4 | 14.729 m |
| 4 | `improvement_replay_control` | `36d053842cc29487` | `576` | `ready_for_continuation_improvement_replay` | 148.987 m | 5.941 m | +143.046 m | `linked_lane_chain` | 4/4 | 6.055 m |
| 5 | `improvement_replay_control` | `fc8c647623f81bb4` | `1466` | `ready_for_continuation_improvement_replay` | 144.514 m | 3.143 m | +141.371 m | `linked_lane_chain` | 4/4 | 16.047 m |
| 6 | `improvement_replay_control` | `2f7869c277b1a86e` | `1972` | `ready_for_continuation_improvement_replay` | 144.033 m | 0.198 m | +143.835 m | `linked_lane_chain` | 4/4 | 16.024 m |
| 7 | `improvement_replay_control` | `236c78eb10435d60` | `1022` | `ready_for_continuation_improvement_replay` | 133.790 m | 9.368 m | +124.422 m | `linked_lane_chain` | 4/4 | 16.615 m |
| 8 | `improvement_replay_control` | `2f366a31ab03f8b` | `1059` | `ready_for_continuation_improvement_replay` | 148.345 m | 9.068 m | +139.277 m | `no_exit_lanes` | 4/4 | 16.874 m |
| 9 | `improvement_replay_control` | `278f11a4922dfe46` | `277` | `ready_for_continuation_improvement_replay` | 118.450 m | 12.195 m | +106.255 m | `linked_lane_chain` | 4/4 | 12.391 m |
| 10 | `improvement_replay_control` | `c52455a0495c9bdb` | `1937` | `ready_for_improvement_replay_with_horizon_caution` | 121.451 m | 30.242 m | +91.209 m | `linked_lane_chain` | 4/4 | 0.000 m |
| 11 | `improvement_replay_control` | `a18114a865e728ef` | `849` | `ready_for_improvement_replay_with_horizon_caution` | 122.776 m | 34.209 m | +88.567 m | `linked_lane_chain` | 4/4 | 5.016 m |
| 12 | `improvement_replay_control` | `8807e9963f411c48` | `722` | `ready_for_continuation_improvement_replay` | 103.862 m | 3.700 m | +100.162 m | `linked_lane_chain` | 4/4 | 12.629 m |
| 13 | `improvement_replay_control` | `4fd2b7f2c4f5a7eb` | `2259` | `ready_for_improvement_replay_with_horizon_caution` | 97.007 m | 7.370 m | +89.637 m | `linked_lane_chain` | 4/4 | 0.000 m |
| 14 | `improvement_replay_control` | `deef8f1a414f64de` | `520` | `ready_for_continuation_improvement_replay` | 112.240 m | 19.976 m | +92.264 m | `linked_lane_chain` | 4/4 | 9.145 m |
| 15 | `improvement_replay_control` | `f70b6e59cc0b762` | `2135` | `ready_for_continuation_improvement_replay` | 97.626 m | 6.340 m | +91.286 m | `linked_lane_chain` | 4/4 | 13.525 m |
| 16 | `regression_replay_debug` | `260785192cf6c991` | `1754` | `ready_for_regression_replay_with_horizon_caution` | 22.573 m | 81.112 m | -58.539 m | `linked_lane_chain` | 4/4 | 5.178 m |
| 17 | `regression_replay_debug` | `f13124876e8f9c3c` | `1673` | `ready_for_continuation_regression_replay` | 87.337 m | 119.314 m | -31.977 m | `linked_lane_chain` | 4/4 | 4.818 m |
| 18 | `regression_replay_debug` | `21590f9487feb1f9` | `660` | `ready_for_continuation_regression_replay` | 3.561 m | 54.718 m | -51.157 m | `linked_lane_chain` | 4/4 | 6.558 m |
| 19 | `regression_replay_debug` | `435ea5885e237e87` | `1516` | `ready_for_regression_replay_with_horizon_caution` | 51.230 m | 89.620 m | -38.390 m | `no_exit_lanes` | 4/4 | 31.411 m |
| 20 | `regression_replay_debug` | `ee1bd0b59fc008b3` | `1689` | `ready_for_regression_replay_with_horizon_caution` | 30.486 m | 62.915 m | -32.429 m | `linked_lane_chain` | 4/4 | 0.000 m |
| 21 | `regression_replay_debug` | `b682b4171243133d` | `281` | `ready_for_continuation_regression_replay` | 4.181 m | 50.434 m | -46.253 m | `linked_lane_chain` | 4/4 | 6.334 m |
| 22 | `regression_replay_debug` | `e3f6a29b59e42c1` | `741` | `ready_for_continuation_regression_replay` | 15.869 m | 58.942 m | -43.073 m | `linked_lane_chain` | 4/4 | 9.947 m |
| 23 | `regression_replay_debug` | `21590f9487feb1f9` | `664` | `ready_for_continuation_regression_replay` | 11.394 m | 52.816 m | -41.422 m | `linked_lane_chain` | 4/4 | 7.516 m |
| 24 | `regression_replay_debug` | `66bba4646960dab5` | `533` | `ready_for_continuation_regression_replay` | 39.970 m | 74.018 m | -34.048 m | `linked_lane_chain` | 4/4 | 11.399 m |
| 25 | `regression_replay_debug` | `550141acae08d1f9` | `1104` | `ready_for_continuation_regression_replay` | 17.148 m | 56.412 m | -39.264 m | `linked_lane_chain` | 4/4 | 8.419 m |
| 26 | `regression_replay_debug` | `9c8241f6a2ee5f51` | `46` | `ready_for_continuation_regression_replay` | 1.183 m | 43.719 m | -42.536 m | `linked_lane_chain` | 4/4 | 7.415 m |
| 27 | `regression_replay_debug` | `5af2afa0d471262d` | `394` | `ready_for_continuation_regression_replay` | 11.213 m | 48.861 m | -37.648 m | `linked_lane_chain` | 4/4 | 6.709 m |
| 28 | `regression_replay_debug` | `d30709cd60e60395` | `164` | `ready_for_continuation_regression_replay` | 16.292 m | 52.496 m | -36.204 m | `linked_lane_chain` | 4/4 | 4.263 m |
| 29 | `regression_replay_debug` | `6b1c4e2891909916` | `2371` | `ready_for_continuation_regression_replay` | 1.919 m | 38.579 m | -36.660 m | `linked_lane_chain` | 4/4 | 5.164 m |
| 30 | `regression_replay_debug` | `5c49e681a66c720` | `2627` | `ready_for_continuation_regression_replay` | 4.595 m | 38.598 m | -34.003 m | `linked_lane_chain` | 4/4 | 6.084 m |

## Topology Probes

| Rank | Scenario | Track | Link status | Link count | Nearest FDE | Lane-link FDE | First blocker |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 31 | `2f366a31ab03f8b` | `1061` | `no_exit_lanes` | 0 | 133.872 m | 133.872 m | No usable parsed linked-lane chain is available yet. |
| 32 | `8ce92d09a94bf2c8` | `2516` | `no_entry_lanes` | 0 | 115.282 m | 115.282 m | No usable parsed linked-lane chain is available yet. |
| 33 | `95fa94d3b3e1f3c6` | `205` | `linked_feature_missing` | 0 | 108.346 m | 108.346 m | No usable parsed linked-lane chain is available yet. |
| 34 | `74a5b3325a534a87` | `3178` | `no_entry_lanes` | 0 | 88.934 m | 88.934 m | No usable parsed linked-lane chain is available yet. |
| 35 | `28f34edeb361e955` | `987` | `no_exit_lanes` | 0 | 62.626 m | 62.626 m | No usable parsed linked-lane chain is available yet. |
| 36 | `634b468a246a77d6` | `116` | `no_exit_lanes` | 0 | 56.572 m | 56.572 m | No usable parsed linked-lane chain is available yet. |
| 37 | `8c9eaa71b6a696c5` | `797` | `linked_feature_missing` | 0 | 55.294 m | 55.294 m | No usable parsed linked-lane chain is available yet. |
| 38 | `4dfe7c285670839f` | `0` | `no_exit_lanes` | 0 | 51.637 m | 51.637 m | No usable parsed linked-lane chain is available yet. |
| 39 | `f672132039e83c40` | `519` | `no_exit_lanes` | 0 | 51.599 m | 51.599 m | No usable parsed linked-lane chain is available yet. |
| 40 | `f672132039e83c40` | `520` | `no_exit_lanes` | 0 | 49.691 m | 49.691 m | No usable parsed linked-lane chain is available yet. |
| 41 | `8abe59aee39f351e` | `4650` | `no_exit_lanes` | 0 | 49.177 m | 49.177 m | No usable parsed linked-lane chain is available yet. |
| 42 | `9c8241f6a2ee5f51` | `88` | `no_exit_lanes` | 0 | 48.172 m | 48.172 m | No usable parsed linked-lane chain is available yet. |
| 43 | `f672132039e83c40` | `522` | `no_exit_lanes` | 0 | 48.129 m | 48.129 m | No usable parsed linked-lane chain is available yet. |
| 44 | `634b468a246a77d6` | `115` | `no_exit_lanes` | 0 | 42.629 m | 42.629 m | No usable parsed linked-lane chain is available yet. |
| 45 | `fe4a6425278fbd5b` | `816` | `no_exit_lanes` | 0 | 41.649 m | 41.649 m | No usable parsed linked-lane chain is available yet. |

## `937eb2fa17da45c0` / track `979`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 312 -> 319 -> 246
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/1-improvement-replay-control-937eb2fa17da45c0-979/lane_continuation_replay_packet.json`

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/2-improvement-replay-control-a863e5638dfff0ca-1765/lane_continuation_replay_packet.json`

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

## `2f7869c277b1a86e` / track `1925`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 215 -> 283 -> 288
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/3-improvement-replay-control-2f7869c277b1a86e-1925/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 3.179 m | 156.670 m | 156.670 m | 4.583 m | +152.087 m | -1.404 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +137.358 m | True | 156.670 m | 19.312 m | `linked_lane_chain` |
| `speed_plus_10pct` | +143.588 m | True | 156.670 m | 13.082 m | `linked_lane_chain` |
| `heading_left_5deg` | +152.087 m | True | 156.670 m | 4.583 m | `linked_lane_chain` |
| `heading_right_5deg` | +152.087 m | True | 156.670 m | 4.583 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `36d053842cc29487` / track `576`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 184 -> 502 -> 497
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/4-improvement-replay-control-36d053842cc29487-576/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5.686 m | 148.987 m | 148.987 m | 5.941 m | +143.046 m | -0.255 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +136.991 m | True | 148.987 m | 11.996 m | `linked_lane_chain` |
| `speed_plus_10pct` | +140.795 m | True | 148.987 m | 8.192 m | `linked_lane_chain` |
| `heading_left_5deg` | +143.046 m | True | 148.987 m | 5.941 m | `linked_lane_chain` |
| `heading_right_5deg` | +143.046 m | True | 148.987 m | 5.941 m | `linked_lane_chain` |

Blockers / cautions:
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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/5-improvement-replay-control-fc8c647623f81bb4-1466/lane_continuation_replay_packet.json`

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

## `2f7869c277b1a86e` / track `1972`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 212 -> 282 -> 285
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/6-improvement-replay-control-2f7869c277b1a86e-1972/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.240 m | 144.033 m | 144.033 m | 0.198 m | +143.835 m | +0.042 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +127.811 m | True | 144.033 m | 16.222 m | `linked_lane_chain` |
| `speed_plus_10pct` | +127.970 m | True | 144.033 m | 16.063 m | `linked_lane_chain` |
| `heading_left_5deg` | +143.835 m | True | 144.033 m | 0.198 m | `linked_lane_chain` |
| `heading_right_5deg` | +143.835 m | True | 144.033 m | 0.198 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `236c78eb10435d60` / track `1022`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 153 -> 372 -> 394
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/7-improvement-replay-control-236c78eb10435d60-1022/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 8.858 m | 133.790 m | 133.790 m | 9.368 m | +124.422 m | -0.510 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +125.150 m | True | 133.790 m | 8.640 m | `linked_lane_chain` |
| `speed_plus_10pct` | +107.807 m | True | 133.790 m | 25.983 m | `linked_lane_chain` |
| `heading_left_5deg` | +124.422 m | True | 133.790 m | 9.368 m | `linked_lane_chain` |
| `heading_right_5deg` | +124.422 m | True | 133.790 m | 9.368 m | `linked_lane_chain` |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/8-improvement-replay-control-2f366a31ab03f8b-1059/lane_continuation_replay_packet.json`

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

## `278f11a4922dfe46` / track `277`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 455 -> 411 -> 431
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/9-improvement-replay-control-278f11a4922dfe46-277/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 11.819 m | 118.450 m | 118.450 m | 12.195 m | +106.255 m | -0.376 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +93.864 m | True | 118.450 m | 24.586 m | `linked_lane_chain` |
| `speed_plus_10pct` | +115.325 m | True | 118.450 m | 3.125 m | `linked_lane_chain` |
| `heading_left_5deg` | +106.255 m | True | 118.450 m | 12.195 m | `linked_lane_chain` |
| `heading_right_5deg` | +106.255 m | True | 118.450 m | 12.195 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `c52455a0495c9bdb` / track `1937`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 295 -> 811 -> 806
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/10-improvement-replay-control-c52455a0495c9bdb-1937/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 14.497 m | 121.451 m | 121.451 m | 30.242 m | +91.209 m | -15.745 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +91.209 m | True | 121.451 m | 30.242 m | `linked_lane_chain` |
| `speed_plus_10pct` | +91.209 m | True | 121.451 m | 30.242 m | `linked_lane_chain` |
| `heading_left_5deg` | +91.209 m | True | 121.451 m | 30.242 m | `linked_lane_chain` |
| `heading_right_5deg` | +91.209 m | True | 121.451 m | 30.242 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `a18114a865e728ef` / track `849`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 350 -> 206 -> 196
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/11-improvement-replay-control-a18114a865e728ef-849/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 28.047 m | 122.776 m | 122.776 m | 34.209 m | +88.567 m | -6.162 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +83.551 m | True | 122.776 m | 39.225 m | `linked_lane_chain` |
| `speed_plus_10pct` | +88.567 m | True | 122.776 m | 34.209 m | `linked_lane_chain` |
| `heading_left_5deg` | +88.567 m | True | 122.776 m | 34.209 m | `linked_lane_chain` |
| `heading_right_5deg` | +88.567 m | True | 122.776 m | 34.209 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/12-improvement-replay-control-8807e9963f411c48-722/lane_continuation_replay_packet.json`

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

## `4fd2b7f2c4f5a7eb` / track `2259`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 309 -> 326 -> 414
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/13-improvement-replay-control-4fd2b7f2c4f5a7eb-2259/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 42.057 m | 97.007 m | 97.007 m | 7.370 m | +89.637 m | +34.687 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +89.637 m | True | 97.007 m | 7.370 m | `linked_lane_chain` |
| `speed_plus_10pct` | +89.637 m | True | 97.007 m | 7.370 m | `linked_lane_chain` |
| `heading_left_5deg` | +89.637 m | True | 97.007 m | 7.370 m | `linked_lane_chain` |
| `heading_right_5deg` | +89.637 m | True | 97.007 m | 7.370 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `deef8f1a414f64de` / track `520`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 461 -> 282 -> 289
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/14-improvement-replay-control-deef8f1a414f64de-520/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 17.425 m | 112.240 m | 112.240 m | 19.976 m | +92.264 m | -2.551 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +83.119 m | True | 112.240 m | 29.121 m | `linked_lane_chain` |
| `speed_plus_10pct` | +101.228 m | True | 112.240 m | 11.012 m | `linked_lane_chain` |
| `heading_left_5deg` | +92.264 m | True | 112.240 m | 19.976 m | `linked_lane_chain` |
| `heading_right_5deg` | +92.264 m | True | 112.240 m | 19.976 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `f70b6e59cc0b762` / track `2135`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_improvement_control**
- Why: Lane-link continuation improves the nearest-lane rollout for this replayed target.
- Recommended next action: Use this as a positive control before tuning harder continuation regressions.
- Feature chain: 312 -> 310 -> 296
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/15-improvement-replay-control-f70b6e59cc0b762-2135/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 15.950 m | 97.626 m | 97.626 m | 6.340 m | +91.286 m | +9.610 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | +90.441 m | True | 97.626 m | 7.185 m | `linked_lane_chain` |
| `speed_plus_10pct` | +77.761 m | True | 97.626 m | 19.865 m | `linked_lane_chain` |
| `heading_left_5deg` | +91.286 m | True | 97.626 m | 6.340 m | `linked_lane_chain` |
| `heading_right_5deg` | +91.286 m | True | 97.626 m | 6.340 m | `linked_lane_chain` |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/16-regression-replay-debug-260785192cf6c991-1754/lane_continuation_replay_packet.json`

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

## `f13124876e8f9c3c` / track `1673`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 314 -> 312 -> 310
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/17-regression-replay-debug-f13124876e8f9c3c-1673/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 65.111 m | 87.337 m | 87.337 m | 119.314 m | -31.977 m | -54.203 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -27.159 m | True | 87.337 m | 114.496 m | `linked_lane_chain` |
| `speed_plus_10pct` | -36.785 m | True | 87.337 m | 124.122 m | `linked_lane_chain` |
| `heading_left_5deg` | -31.977 m | True | 87.337 m | 119.314 m | `linked_lane_chain` |
| `heading_right_5deg` | -31.977 m | True | 87.337 m | 119.314 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `21590f9487feb1f9` / track `660`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 210 -> 200 -> 194
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/18-regression-replay-debug-21590f9487feb1f9-660/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 54.723 m | 3.561 m | 3.561 m | 54.718 m | -51.157 m | +0.005 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -44.599 m | True | 3.561 m | 48.160 m | `linked_lane_chain` |
| `speed_plus_10pct` | -57.715 m | True | 3.561 m | 61.276 m | `linked_lane_chain` |
| `heading_left_5deg` | -51.157 m | True | 3.561 m | 54.718 m | `linked_lane_chain` |
| `heading_right_5deg` | -51.157 m | True | 3.561 m | 54.718 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `435ea5885e237e87` / track `1516`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 223 -> 204
- Link status/count: `no_exit_lanes` / 1
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/19-regression-replay-debug-435ea5885e237e87-1516/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 55.091 m | 51.230 m | 35.244 m | 89.620 m | -38.390 m | -34.529 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -38.390 m | True | 51.230 m | 89.620 m | `no_exit_lanes` |
| `speed_plus_10pct` | -38.390 m | True | 51.230 m | 89.620 m | `no_exit_lanes` |
| `heading_left_5deg` | -38.390 m | True | 51.230 m | 89.620 m | `no_exit_lanes` |
| `heading_right_5deg` | -6.979 m | True | 41.011 m | 47.990 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `ee1bd0b59fc008b3` / track `1689`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 312 -> 211 -> 215
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/20-regression-replay-debug-ee1bd0b59fc008b3-1689/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 87.688 m | 30.486 m | 30.486 m | 62.915 m | -32.429 m | +24.773 m | True |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -32.429 m | True | 30.486 m | 62.915 m | `linked_lane_chain` |
| `speed_plus_10pct` | -32.429 m | True | 30.486 m | 62.915 m | `linked_lane_chain` |
| `heading_left_5deg` | -32.429 m | True | 30.486 m | 62.915 m | `linked_lane_chain` |
| `heading_right_5deg` | -32.429 m | True | 30.486 m | 62.915 m | `linked_lane_chain` |

Blockers / cautions:
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `b682b4171243133d` / track `281`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 387 -> 300 -> 349
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/21-regression-replay-debug-b682b4171243133d-281/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 50.432 m | 4.181 m | 4.181 m | 50.434 m | -46.253 m | -0.002 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -39.919 m | True | 4.181 m | 44.100 m | `linked_lane_chain` |
| `speed_plus_10pct` | -52.587 m | True | 4.181 m | 56.768 m | `linked_lane_chain` |
| `heading_left_5deg` | -46.253 m | True | 4.181 m | 50.434 m | `linked_lane_chain` |
| `heading_right_5deg` | -46.253 m | True | 4.181 m | 50.434 m | `linked_lane_chain` |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/22-regression-replay-debug-e3f6a29b59e42c1-741/lane_continuation_replay_packet.json`

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

## `21590f9487feb1f9` / track `664`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 210 -> 200 -> 194
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/23-regression-replay-debug-21590f9487feb1f9-664/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 51.224 m | 11.394 m | 11.394 m | 52.816 m | -41.422 m | -1.592 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -33.906 m | True | 11.394 m | 45.300 m | `linked_lane_chain` |
| `speed_plus_10pct` | -48.938 m | True | 11.394 m | 60.332 m | `linked_lane_chain` |
| `heading_left_5deg` | -41.422 m | True | 11.394 m | 52.816 m | `linked_lane_chain` |
| `heading_right_5deg` | -41.422 m | True | 11.394 m | 52.816 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `66bba4646960dab5` / track `533`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 198 -> 316 -> 337
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/24-regression-replay-debug-66bba4646960dab5-533/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 74.538 m | 39.970 m | 39.970 m | 74.018 m | -34.048 m | +0.520 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -22.649 m | True | 39.970 m | 62.619 m | `linked_lane_chain` |
| `speed_plus_10pct` | -42.059 m | True | 39.970 m | 82.029 m | `linked_lane_chain` |
| `heading_left_5deg` | -34.048 m | True | 39.970 m | 74.018 m | `linked_lane_chain` |
| `heading_right_5deg` | -34.048 m | True | 39.970 m | 74.018 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `550141acae08d1f9` / track `1104`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 146 -> 154 -> 159
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/25-regression-replay-debug-550141acae08d1f9-1104/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 56.144 m | 17.148 m | 17.148 m | 56.412 m | -39.264 m | -0.268 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -30.847 m | True | 17.148 m | 47.995 m | `linked_lane_chain` |
| `speed_plus_10pct` | -47.683 m | True | 17.148 m | 64.831 m | `linked_lane_chain` |
| `heading_left_5deg` | -39.264 m | True | 17.148 m | 56.412 m | `linked_lane_chain` |
| `heading_right_5deg` | -39.264 m | True | 17.148 m | 56.412 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `9c8241f6a2ee5f51` / track `46`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 221 -> 243 -> 245
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/26-regression-replay-debug-9c8241f6a2ee5f51-46/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 43.715 m | 1.183 m | 1.183 m | 43.719 m | -42.536 m | -0.004 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -35.122 m | True | 1.183 m | 36.305 m | `linked_lane_chain` |
| `speed_plus_10pct` | -49.951 m | True | 1.183 m | 51.134 m | `linked_lane_chain` |
| `heading_left_5deg` | -42.536 m | True | 1.183 m | 43.719 m | `linked_lane_chain` |
| `heading_right_5deg` | -42.536 m | True | 1.183 m | 43.719 m | `linked_lane_chain` |

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `5af2afa0d471262d` / track `394`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 347 -> 257 -> 457
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/27-regression-replay-debug-5af2afa0d471262d-394/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 48.861 m | 11.213 m | 11.213 m | 48.861 m | -37.648 m | 0.000 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -30.939 m | True | 11.213 m | 42.152 m | `linked_lane_chain` |
| `speed_plus_10pct` | -44.357 m | True | 11.213 m | 55.570 m | `linked_lane_chain` |
| `heading_left_5deg` | -37.648 m | True | 11.213 m | 48.861 m | `linked_lane_chain` |
| `heading_right_5deg` | -37.648 m | True | 11.213 m | 48.861 m | `linked_lane_chain` |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/28-regression-replay-debug-d30709cd60e60395-164/lane_continuation_replay_packet.json`

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

## `6b1c4e2891909916` / track `2371`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **stable_regression_debug**
- Why: Lane-link continuation remains worse than nearest-lane for this replayed target.
- Recommended next action: Inspect route choice, lane geometry, and future intent before changing the selector.
- Feature chain: 330 -> 343 -> 296
- Link status/count: `linked_lane_chain` / 2
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/29-regression-replay-debug-6b1c4e2891909916-2371/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 38.579 m | 1.919 m | 1.919 m | 38.579 m | -36.660 m | 0.000 m | False |

Perturbation trials:

| Trial | Link vs nearest | Preserves expected sign | Nearest FDE | Lane-link FDE | Link status |
| --- | ---: | --- | ---: | ---: | --- |
| `speed_minus_10pct` | -31.496 m | True | 1.919 m | 33.415 m | `linked_lane_chain` |
| `speed_plus_10pct` | -41.824 m | True | 1.919 m | 43.743 m | `linked_lane_chain` |
| `heading_left_5deg` | -36.660 m | True | 1.919 m | 38.579 m | `linked_lane_chain` |
| `heading_right_5deg` | -36.660 m | True | 1.919 m | 38.579 m | `linked_lane_chain` |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/30-regression-replay-debug-5c49e681a66c720-2627/lane_continuation_replay_packet.json`

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

## `2f366a31ab03f8b` / track `1061`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 219
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/31-topology-audit-2f366a31ab03f8b-1061/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6.081 m | 133.872 m | 133.872 m | 133.872 m | 0.000 m | -127.791 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `8ce92d09a94bf2c8` / track `2516`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 183
- Link status/count: `no_entry_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/32-topology-audit-8ce92d09a94bf2c8-2516/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 17.625 m | 115.282 m | 115.282 m | 115.282 m | 0.000 m | -97.657 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `95fa94d3b3e1f3c6` / track `205`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 644
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/33-topology-audit-95fa94d3b3e1f3c6-205/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 52.850 m | 108.346 m | 108.346 m | 108.346 m | 0.000 m | -55.496 m | True |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/34-topology-audit-74a5b3325a534a87-3178/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 56.254 m | 88.934 m | 88.934 m | 88.934 m | 0.000 m | -32.680 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `28f34edeb361e955` / track `987`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00009-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 158
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/35-topology-audit-28f34edeb361e955-987/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 38.369 m | 62.626 m | 62.626 m | 62.626 m | 0.000 m | -24.257 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `634b468a246a77d6` / track `116`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 99
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/36-topology-audit-634b468a246a77d6-116/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10.495 m | 56.572 m | 56.572 m | 56.572 m | 0.000 m | -46.077 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `8c9eaa71b6a696c5` / track `797`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00007-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 718
- Link status/count: `linked_feature_missing` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/37-topology-audit-8c9eaa71b6a696c5-797/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 67.262 m | 55.294 m | 55.294 m | 55.294 m | 0.000 m | +11.968 m | True |

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
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/38-topology-audit-4dfe7c285670839f-0/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 17.949 m | 51.637 m | 51.637 m | 51.637 m | 0.000 m | -33.688 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `f672132039e83c40` / track `519`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 73
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/39-topology-audit-f672132039e83c40-519/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 17.399 m | 51.599 m | 51.599 m | 51.599 m | 0.000 m | -34.200 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `f672132039e83c40` / track `520`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 72
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/40-topology-audit-f672132039e83c40-520/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 15.627 m | 49.691 m | 49.691 m | 49.691 m | 0.000 m | -34.064 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `8abe59aee39f351e` / track `4650`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 161
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/41-topology-audit-8abe59aee39f351e-4650/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 38.216 m | 49.177 m | 49.177 m | 49.177 m | 0.000 m | -10.961 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `9c8241f6a2ee5f51` / track `88`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00008-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 223
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/42-topology-audit-9c8241f6a2ee5f51-88/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 7.275 m | 48.172 m | 35.163 m | 48.172 m | 0.000 m | -40.897 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `f672132039e83c40` / track `522`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 77
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/43-topology-audit-f672132039e83c40-522/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 36.497 m | 48.129 m | 48.129 m | 48.129 m | 0.000 m | -11.632 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `634b468a246a77d6` / track `115`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 91
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/44-topology-audit-634b468a246a77d6-115/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 15.169 m | 42.629 m | 42.629 m | 42.629 m | 0.000 m | -27.460 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `fe4a6425278fbd5b` / track `816`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Source: `validation.tfrecord-00010-of-00150`
- Result: **topology_blocker**
- Why: The selected feature still lacks a usable linked-lane chain.
- Recommended next action: Audit parsed lane links, map-feature caps, and link direction before replaying this case.
- Feature chain: 155
- Link status/count: `no_exit_lanes` / 0
- Local replay packet: `data/processed/waymo_lane_continuation_replay_prototype_200/cases/45-topology-audit-fe4a6425278fbd5b-816/lane_continuation_replay_packet.json`

Target replay row:

| CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link vs nearest | Link vs CV | Clamp after link |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 10.969 m | 41.649 m | 41.649 m | 41.649 m | 0.000 m | -30.680 m | True |

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## Interpretation

- Stable improvement controls are useful because they prove the lane-link mechanism on cases where nearest-lane clamping was misleading.
- Stable regressions are useful debugging targets because linked-lane following can still choose the wrong route or out-run available topology.
- Topology probes are blockers, not model-performance claims; they identify missing links, map-feature caps, or parser coverage work.
- This keeps ScenarioLens honest: public outputs are diagnostic summaries, while raw Waymo files and local replay packets remain ignored.
