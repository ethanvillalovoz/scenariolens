# ScenarioLens Lane-Continuation Candidate Plan

This report turns the lane-continuation validation study into an actionable queue for the next replay or topology-audit pass. It keeps positive controls, regressions, and unresolved topology gaps separate so follow-up work does not collapse them into one average score.

It is intentionally scoped: this is not route planning, not closed-loop simulation, not a completed Waymax/JAX integration, and not a Waymo benchmark claim. Raw Waymo files stay local.

## Scope

- Source study manifest: `data/processed/waymo_lane_continuation_study/manifest.json`
- Ready for planning: True
- Top rows per bucket: 5
- Study scenarios scanned: 100
- Study candidate tracks: 178
- Raw scenario data committed: no

## Source Study Snapshot

| Metric | Count / Value |
| --- | ---: |
| Tracks using linked lanes | 145 |
| Tracks improved over nearest lane | 96 |
| Tracks regressed vs nearest lane | 47 |
| Topology gaps | 33 |
| Mean lane-link improvement | +12.675 m |

## Queue Summary

| Queue | Count |
| --- | ---: |
| Replay candidates | 10 |
| Improvement controls | 5 |
| Regression debug targets | 5 |
| Topology audit targets | 5 |
| Candidates still clamped after links | 8 |

## Replay Controls: Largest Improvements

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `validation.tfrecord-00010-of-00150` | `a863e5638dfff0ca` | `1765` | 12.83 | 144.122 m | 7.919 m | +136.203 m | 249 -> 244 -> 275 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 2 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1059` | 11.57 | 148.345 m | 9.068 m | +139.277 m | 220 -> 210 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 3 | `validation.tfrecord-00008-of-00150` | `65d7afd24453a1ba` | `510` | 9.44 | 90.668 m | 5.454 m | +85.214 m | 159 -> 146 -> 140 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 4 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | `34` | 8.49 | 87.044 m | 3.732 m | +83.312 m | 176 -> 164 -> 148 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 5 | `validation.tfrecord-00008-of-00150` | `564a6bcc85c4f72f` | `1143` | 7.84 | 81.835 m | 6.818 m | +75.017 m | 167 -> 173 -> 255 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |

## Replay Debug Targets: Largest Regressions

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 6 | `validation.tfrecord-00009-of-00150` | `260785192cf6c991` | `1754` | 7.47 | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 7 | `validation.tfrecord-00010-of-00150` | `d8dde10f514a501c` | `651` | 5.36 | 73.197 m | 104.290 m | -31.093 m | 134 -> 143 -> 146 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 8 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | `741` | 5.25 | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 9 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | `2627` | 4.24 | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 10 | `validation.tfrecord-00007-of-00150` | `e9db41e904b349a2` | `406` | 4.07 | 6.776 m | 38.292 m | -31.516 m | 295 -> 228 -> 201 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |

## Topology Audit Queue

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 11 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | `1466` | 5.14 | 144.514 m | 144.514 m | 0.000 m | 153 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 12 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1061` | 4.93 | 133.872 m | 133.872 m | 0.000 m | 219 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 13 | `validation.tfrecord-00007-of-00150` | `770fec53ec3e0395` | `1105` | 4.88 | 131.434 m | 131.434 m | 0.000 m | 306 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 14 | `validation.tfrecord-00007-of-00150` | `c52455a0495c9bdb` | `1937` | 4.68 | 121.451 m | 121.451 m | 0.000 m | 295 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 15 | `validation.tfrecord-00009-of-00150` | `c45b209a75ff4610` | `1815` | 4.59 | 117.044 m | 117.044 m | 0.000 m | 248 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |

## `a863e5638dfff0ca` / track `1765`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 12.83
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 249 -> 244 -> 275
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 144.122 m
- Lane-link FDE: 7.919 m
- Link improvement: +136.203 m
- Before/after remaining lane distance: 38.092 m / 174.882 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `2f366a31ab03f8b` / track `1059`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 11.57
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 220 -> 210
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 148.345 m
- Lane-link FDE: 9.068 m
- Link improvement: +139.277 m
- Before/after remaining lane distance: 11.325 m / 239.589 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `65d7afd24453a1ba` / track `510`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 9.44
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 159 -> 146 -> 140
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 90.668 m
- Lane-link FDE: 5.454 m
- Link improvement: +85.214 m
- Before/after remaining lane distance: 0.000 m / 96.121 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `77c44d1768793143` / track `34`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 8.49
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 176 -> 164 -> 148
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 87.044 m
- Lane-link FDE: 3.732 m
- Link improvement: +83.312 m
- Before/after remaining lane distance: 16.109 m / 138.217 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `564a6bcc85c4f72f` / track `1143`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 7.84
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 167 -> 173 -> 255
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 81.835 m
- Lane-link FDE: 6.818 m
- Link improvement: +75.017 m
- Before/after remaining lane distance: 7.487 m / 85.384 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `260785192cf6c991` / track `1754`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Priority score: 7.47
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 235 -> 241 -> 315
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 22.573 m
- Lane-link FDE: 81.112 m
- Link improvement: -58.539 m
- Before/after remaining lane distance: 2.418 m / 106.102 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `d8dde10f514a501c` / track `651`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.36
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 134 -> 143 -> 146
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 73.197 m
- Lane-link FDE: 104.290 m
- Link improvement: -31.093 m
- Before/after remaining lane distance: 12.534 m / 76.738 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `e3f6a29b59e42c1` / track `741`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.25
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 161 -> 127 -> 116
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 15.869 m
- Lane-link FDE: 58.942 m
- Link improvement: -43.073 m
- Before/after remaining lane distance: 24.653 m / 125.444 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `5c49e681a66c720` / track `2627`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.24
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 285 -> 120 -> 119
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 4.595 m
- Lane-link FDE: 38.598 m
- Link improvement: -34.003 m
- Before/after remaining lane distance: 19.404 m / 111.686 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `e9db41e904b349a2` / track `406`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.07
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 295 -> 228 -> 201
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 6.776 m
- Lane-link FDE: 38.292 m
- Link improvement: -31.516 m
- Before/after remaining lane distance: 11.866 m / 144.318 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `fc8c647623f81bb4` / track `1466`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 5.14
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 153
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 144.514 m
- Lane-link FDE: 144.514 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 12.820 m / 12.820 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `2f366a31ab03f8b` / track `1061`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.93
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 219
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 133.872 m
- Lane-link FDE: 133.872 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 26.476 m / 26.476 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `770fec53ec3e0395` / track `1105`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.88
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 306
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 131.434 m
- Lane-link FDE: 131.434 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 0.000 m / 0.000 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `c52455a0495c9bdb` / track `1937`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.68
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 295
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 121.451 m
- Lane-link FDE: 121.451 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 6.738 m / 6.738 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `c45b209a75ff4610` / track `1815`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.59
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 248
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 117.044 m
- Lane-link FDE: 117.044 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 14.162 m / 14.162 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## Interpretation

- Improvement controls are useful for proving the lane-link mechanism under replay before debugging harder cases.
- Regression targets are high-value because they expose route choice, map topology, and future-intent assumptions.
- Topology audit targets should be fixed or explained before they are treated as model-performance evidence.
- This is a planning artifact for the next experiment, not a completed simulation or planner integration.
