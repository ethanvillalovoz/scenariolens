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
| Stable regression warnings | 4 |
| Horizon-limit cases | 1 |
| Link worse than constant velocity | 0 |
| Topology blockers | 5 |
| Missing linked features | 2 |
| Terminal/no-exit lane probes | 3 |

## Stable Regression Diagnostics

| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| 1 | `260785192cf6c991` | `1754` | 7.57 | `route_horizon_limit` | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | Extend linked-lane search depth or route-chain coverage before tuning prediction behavior. |
| 2 | `e3f6a29b59e42c1` | `741` | 5.62 | `stable_route_choice_regression` | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | Compare alternate linked-lane branches from the same selected feature. |
| 3 | `d30709cd60e60395` | `164` | 4.37 | `stable_route_choice_regression` | 16.292 m | 52.496 m | -36.204 m | 603 -> 610 -> 371 | Compare alternate linked-lane branches from the same selected feature. |
| 4 | `5c49e681a66c720` | `2627` | 4.10 | `stable_route_choice_regression` | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | Compare alternate linked-lane branches from the same selected feature. |
| 5 | `e9db41e904b349a2` | `406` | 3.86 | `stable_route_choice_regression` | 6.776 m | 38.292 m | -31.516 m | 295 -> 228 -> 201 | Compare alternate linked-lane branches from the same selected feature. |

## Topology Diagnostics

| Rank | Scenario | Track | Priority | Diagnosis | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| 6 | `6bdc7f92afefff73` | `59` | 4.93 | `missing_linked_feature` | 134.082 m | 134.082 m | 0.000 m | 1056 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 7 | `2f366a31ab03f8b` | `1061` | 4.93 | `terminal_lane_or_parser_gap` | 133.872 m | 133.872 m | 0.000 m | 219 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 8 | `74a5b3325a534a87` | `3178` | 4.03 | `terminal_lane_or_parser_gap` | 88.934 m | 88.934 m | 0.000 m | 333 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 9 | `2f035a284480e981` | `715` | 3.42 | `missing_linked_feature` | 58.747 m | 58.747 m | 0.000 m | 513 | Audit the selected map feature's parsed entry/exit lane IDs. |
| 10 | `4dfe7c285670839f` | `0` | 3.28 | `terminal_lane_or_parser_gap` | 51.637 m | 51.637 m | 0.000 m | 44 | Audit the selected map feature's parsed entry/exit lane IDs. |

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

## `d30709cd60e60395` / track `164`

- Queue: `regression_replay_debug`
- Diagnosis: **stable_route_choice_regression**
- Priority score: 4.37
- Why it matters: The linked route remains worse than nearest-lane under perturbation, which points to route-choice or branch-selection logic.
- Source: `validation.tfrecord-00007-of-00150`
- Replay stability: `stable_regression_warning`
- Link status/count: `linked_lane_chain` / 2
- Feature chain: 603 -> 610 -> 371
- Nearest-lane FDE: 16.292 m
- Lane-link FDE: 52.496 m
- Link improvement over nearest: -36.204 m
- Link improvement over constant velocity: +8.528 m
- Horizon / route remaining: 75.892 m / 112.428 m

Recommended next actions:
- Compare alternate linked-lane branches from the same selected feature.
- Add a route-choice prior before accepting the first linked continuation.
- Keep nearest-lane and linked-lane results side by side in the next replay pass.

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

## `6bdc7f92afefff73` / track `59`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 4.93
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00009-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 1056
- Nearest-lane FDE: 134.082 m
- Lane-link FDE: 134.082 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -118.819 m
- Horizon / route remaining: 150.972 m / 1.793 m

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

## `74a5b3325a534a87` / track `3178`

- Queue: `topology_audit`
- Diagnosis: **terminal_lane_or_parser_gap**
- Priority score: 4.03
- Why it matters: The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it.
- Source: `validation.tfrecord-00010-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `no_entry_lanes` / 0
- Feature chain: 333
- Nearest-lane FDE: 88.934 m
- Lane-link FDE: 88.934 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -32.680 m
- Horizon / route remaining: 59.581 m / 23.515 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `2f035a284480e981` / track `715`

- Queue: `topology_audit`
- Diagnosis: **missing_linked_feature**
- Priority score: 3.42
- Why it matters: The selected feature references a continuation that the lightweight parser did not make usable.
- Source: `validation.tfrecord-00010-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `linked_feature_missing` / 0
- Feature chain: 513
- Nearest-lane FDE: 58.747 m
- Lane-link FDE: 58.747 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -36.366 m
- Horizon / route remaining: 35.054 m / 0.000 m

Recommended next actions:
- Audit the selected map feature's parsed entry/exit lane IDs.
- Check whether the feature cap dropped the referenced continuation.
- Regenerate continuation studies after parser/topology changes.

Blockers / cautions:
- No usable parsed linked-lane chain is available yet.
- The linked lane chain is still shorter than the target horizon.
- Raw Waymo TFRecords and local replay packets must stay ignored.

## `4dfe7c285670839f` / track `0`

- Queue: `topology_audit`
- Diagnosis: **terminal_lane_or_parser_gap**
- Priority score: 3.28
- Why it matters: The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it.
- Source: `validation.tfrecord-00008-of-00150`
- Replay stability: `not_evaluable`
- Link status/count: `no_exit_lanes` / 0
- Feature chain: 44
- Nearest-lane FDE: 51.637 m
- Lane-link FDE: 51.637 m
- Link improvement over nearest: 0.000 m
- Link improvement over constant velocity: -33.688 m
- Horizon / route remaining: 85.416 m / 15.863 m

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
