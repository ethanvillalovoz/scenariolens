# ScenarioLens Lane-Continuation Route Diagnostics

This report turns the lane-continuation replay prototype into a route-choice and topology diagnostic casebook. It keeps stable regressions separate from topology blockers so the next engineering step is clear: route-choice priors for linked-lane regressions, and map/parser coverage for unresolved continuation gaps.

It is intentionally scoped: this is not a route planner, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local replay packets stay out of git.

## Scope

- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Candidate manifest: `data/processed/waymo_lane_continuation_candidates/manifest.json`
- Study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready for diagnostics: True
- Diagnostics published: 10
- Source replay cases: 10
- Source topology probes: 5
- Raw scenario data committed: no

## Diagnostic Summary

| Metric | Value |
| --- | ---: |
| Diagnostics | 10 |
| Regression diagnostics | 5 |
| Topology diagnostics | 5 |
| Stable regression warnings | 3 |
| Horizon-limit cases | 1 |
| Link worse than constant velocity | 1 |
| Topology blockers | 5 |
| Missing linked features | 4 |
| Terminal/no-exit lane probes | 1 |

## Stable Regression Diagnostics

| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| 1 | `260785192cf6c991` | `1754` | 7.57 | `route_horizon_limit` | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | Extend linked-lane search depth or route-chain coverage before tuning prediction behavior. |
| 2 | `e3f6a29b59e42c1` | `741` | 5.62 | `stable_route_choice_regression` | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | Compare alternate linked-lane branches from the same selected feature. |
| 3 | `d8dde10f514a501c` | `651` | 5.10 | `linked_route_worse_than_constant_velocity` | 73.197 m | 104.290 m | -31.093 m | 134 -> 143 -> 146 | Inspect whether the linked route turns away from the target's future motion. |
| 4 | `5c49e681a66c720` | `2627` | 4.10 | `stable_route_choice_regression` | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | Compare alternate linked-lane branches from the same selected feature. |
| 5 | `e9db41e904b349a2` | `406` | 3.86 | `stable_route_choice_regression` | 6.776 m | 38.292 m | -31.516 m | 295 -> 228 -> 201 | Compare alternate linked-lane branches from the same selected feature. |

## Topology Diagnostics

| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| 6 | `fc8c647623f81bb4` | `1466` | 5.14 | `missing_linked_feature` | 144.514 m | 144.514 m | 0.000 m | 153 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 7 | `2f366a31ab03f8b` | `1061` | 4.93 | `terminal_lane_or_parser_gap` | 133.872 m | 133.872 m | 0.000 m | 219 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 8 | `770fec53ec3e0395` | `1105` | 4.88 | `missing_linked_feature` | 131.434 m | 131.434 m | 0.000 m | 306 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 9 | `c52455a0495c9bdb` | `1937` | 4.68 | `missing_linked_feature` | 121.451 m | 121.451 m | 0.000 m | 295 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 10 | `c45b209a75ff4610` | `1815` | 4.59 | `missing_linked_feature` | 117.044 m | 117.044 m | 0.000 m | 248 | Audit the selected map feature's parsed entry/exit lane IDs. |

## `260785192cf6c991` / track `1754`

- Queue: `regression_replay_debug`
- Diagnosis: **route_horizon_limit**
- Priority score: 7.57
- Why it matters: The target still out-travels the linked lane chain, so the next fix is longer or better-connected topology before model tuning.
- Source: `validation.tfrecord-00009-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 235 -> 241 -> 315
- Nearest-lane FDE: 22.573 m
- Lane-link FDE: 81.112 m
- Link improvement over nearest: -58.539 m
- Link improvement over constant velocity: +6.037 m
- Horizon / route remaining: 112.137 m / 106.102 m

Recommended next actions:
- Extend linked-lane search depth or route-chain coverage before tuning prediction behavior.
- Check whether the target's observed future leaves the parsed lane graph.
- Rerun the replay prototype after topology coverage changes.

Blockers / cautions:
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `e3f6a29b59e42c1` / track `741`

- Queue: `regression_replay_debug`
- Diagnosis: **stable_route_choice_regression**
- Priority score: 5.62
- Why it matters: The linked route remains worse than nearest-lane under perturbation, which points to route-choice or branch-selection logic.
- Source: `validation.tfrecord-00008-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 161 -> 127 -> 116
- Nearest-lane FDE: 15.869 m
- Lane-link FDE: 58.942 m
- Link improvement over nearest: -43.073 m
- Link improvement over constant velocity: +0.005 m
- Horizon / route remaining: 99.465 m / 125.444 m

Recommended next actions:
- Compare alternate linked-lane branches from the same selected feature.
- Add a route-choice prior before accepting the first linked continuation.
- Keep nearest-lane and linked-lane results side by side in the next replay pass.

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `d8dde10f514a501c` / track `651`

- Queue: `regression_replay_debug`
- Diagnosis: **linked_route_worse_than_constant_velocity**
- Priority score: 5.10
- Why it matters: Linked-lane continuation is worse than both nearest-lane and constant velocity, making this a high-value route-prior debugging case.
- Source: `validation.tfrecord-00010-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 134 -> 143 -> 146
- Nearest-lane FDE: 73.197 m
- Lane-link FDE: 104.290 m
- Link improvement over nearest: -31.093 m
- Link improvement over constant velocity: -46.548 m
- Horizon / route remaining: 52.453 m / 76.738 m

Recommended next actions:
- Inspect whether the linked route turns away from the target's future motion.
- Test route candidates ranked by heading and future displacement consistency.
- Treat this as a route-choice regression, not a scoring-baseline failure.

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `5c49e681a66c720` / track `2627`

- Queue: `regression_replay_debug`
- Diagnosis: **stable_route_choice_regression**
- Priority score: 4.10
- Why it matters: The linked route remains worse than nearest-lane under perturbation, which points to route-choice or branch-selection logic.
- Source: `validation.tfrecord-00010-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 285 -> 120 -> 119
- Nearest-lane FDE: 4.595 m
- Lane-link FDE: 38.598 m
- Link improvement over nearest: -34.003 m
- Link improvement over constant velocity: -0.192 m
- Horizon / route remaining: 61.023 m / 111.686 m

Recommended next actions:
- Compare alternate linked-lane branches from the same selected feature.
- Add a route-choice prior before accepting the first linked continuation.
- Keep nearest-lane and linked-lane results side by side in the next replay pass.

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `e9db41e904b349a2` / track `406`

- Queue: `regression_replay_debug`
- Diagnosis: **stable_route_choice_regression**
- Priority score: 3.86
- Why it matters: The linked route remains worse than nearest-lane under perturbation, which points to route-choice or branch-selection logic.
- Source: `validation.tfrecord-00007-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 295 -> 228 -> 201
- Nearest-lane FDE: 6.776 m
- Lane-link FDE: 38.292 m
- Link improvement over nearest: -31.516 m
- Link improvement over constant velocity: 0.000 m
- Horizon / route remaining: 56.921 m / 144.318 m

Recommended next actions:
- Compare alternate linked-lane branches from the same selected feature.
- Add a route-choice prior before accepting the first linked continuation.
- Keep nearest-lane and linked-lane results side by side in the next replay pass.

Blockers / cautions:
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `fc8c647623f81bb4` / track `1466`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 5.14
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00009-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 153
- Nearest-lane FDE: 144.514 m
- Lane-link FDE: 144.514 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -141.362 m
- Horizon / route remaining: 160.476 m / 12.820 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `2f366a31ab03f8b` / track `1061`

- Queue: `topology_audit`
- Diagnosis: **terminal_lane_or_parser_gap**
- Priority score: 4.93
- Why it matters: The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it.
- Source: `validation.tfrecord-00007-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `no_exit_lanes` / 0
- Feature chain: 219
- Nearest-lane FDE: 133.872 m
- Lane-link FDE: 133.872 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -127.791 m
- Horizon / route remaining: 165.493 m / 26.476 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `770fec53ec3e0395` / track `1105`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 4.88
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00007-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 306
- Nearest-lane FDE: 131.434 m
- Lane-link FDE: 131.434 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -117.359 m
- Horizon / route remaining: 115.837 m / 0.000 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `c52455a0495c9bdb` / track `1937`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 4.68
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00007-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 295
- Nearest-lane FDE: 121.451 m
- Lane-link FDE: 121.451 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -106.954 m
- Horizon / route remaining: 142.662 m / 6.738 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `c45b209a75ff4610` / track `1815`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 4.59
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00009-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 248
- Nearest-lane FDE: 117.044 m
- Lane-link FDE: 117.044 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -79.567 m
- Horizon / route remaining: 93.731 m / 14.162 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## Interpretation

- Stable linked-lane regressions are valuable because they expose route-choice, lane-branch selection, or speed-prior assumptions after the topology mechanism is available.
- Horizon-limit cases should not be treated as model failures until the linked chain covers the prediction horizon.
- Topology blockers are parser/map coverage work, not prediction evidence.
- This report is an audit plan for the next implementation step, not a claim that ScenarioLens is a production planner.
