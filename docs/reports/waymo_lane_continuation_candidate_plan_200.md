# ScenarioLens Lane-Continuation Candidate Plan

This report turns the lane-continuation validation study into an actionable queue for the next replay or topology-audit pass. It keeps positive controls, regressions, and unresolved topology gaps separate so follow-up work does not collapse them into one average score.

It is intentionally scoped: this is not route planning, not closed-loop simulation, not a completed Waymax/JAX integration, and not a Waymo benchmark claim. Raw Waymo files stay local.

## Scope

- Source study manifest: `data/processed/waymo_lane_continuation_study_200/manifest.json`
- Ready for planning: True
- Top rows per bucket: 15
- Study scenarios scanned: 200
- Study candidate tracks: 451
- Raw scenario data committed: no

## Source Study Snapshot

| Metric | Count / Value |
| --- | ---: |
| Tracks using linked lanes | 421 |
| Tracks improved over nearest lane | 290 |
| Tracks regressed vs nearest lane | 122 |
| Topology gaps | 30 |
| Mean lane-link improvement | +17.870 m |

## Queue Summary

| Queue | Count |
| --- | ---: |
| Replay candidates | 30 |
| Improvement controls | 15 |
| Regression debug targets | 15 |
| Topology audit targets | 15 |
| Candidates still clamped after links | 23 |

## Replay Controls: Largest Improvements

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | `979` | 12.95 | 151.676 m | 10.354 m | +141.322 m | 312 -> 319 -> 246 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 2 | `validation.tfrecord-00010-of-00150` | `a863e5638dfff0ca` | `1765` | 12.83 | 144.122 m | 7.919 m | +136.203 m | 249 -> 244 -> 275 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 3 | `validation.tfrecord-00010-of-00150` | `2f7869c277b1a86e` | `1925` | 12.20 | 156.670 m | 4.583 m | +152.087 m | 215 -> 283 -> 288 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 4 | `validation.tfrecord-00009-of-00150` | `36d053842cc29487` | `576` | 12.18 | 148.987 m | 5.941 m | +143.046 m | 184 -> 502 -> 497 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 5 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | `1466` | 12.09 | 144.514 m | 3.143 m | +141.371 m | 153 -> 344 -> 343 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 6 | `validation.tfrecord-00010-of-00150` | `2f7869c277b1a86e` | `1972` | 12.08 | 144.033 m | 0.198 m | +143.835 m | 212 -> 282 -> 285 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 7 | `validation.tfrecord-00008-of-00150` | `236c78eb10435d60` | `1022` | 11.88 | 133.790 m | 9.368 m | +124.422 m | 153 -> 372 -> 394 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 8 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1059` | 11.57 | 148.345 m | 9.068 m | +139.277 m | 220 -> 210 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 9 | `validation.tfrecord-00008-of-00150` | `278f11a4922dfe46` | `277` | 10.65 | 118.450 m | 12.195 m | +106.255 m | 455 -> 411 -> 431 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 10 | `validation.tfrecord-00007-of-00150` | `c52455a0495c9bdb` | `1937` | 10.46 | 121.451 m | 30.242 m | +91.209 m | 295 -> 811 -> 806 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 11 | `validation.tfrecord-00009-of-00150` | `a18114a865e728ef` | `849` | 10.31 | 122.776 m | 34.209 m | +88.567 m | 350 -> 206 -> 196 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 12 | `validation.tfrecord-00009-of-00150` | `8807e9963f411c48` | `722` | 9.96 | 103.862 m | 3.700 m | +100.162 m | 337 -> 559 -> 553 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 13 | `validation.tfrecord-00009-of-00150` | `4fd2b7f2c4f5a7eb` | `2259` | 9.87 | 97.007 m | 7.370 m | +89.637 m | 309 -> 326 -> 414 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 14 | `validation.tfrecord-00008-of-00150` | `deef8f1a414f64de` | `520` | 9.60 | 112.240 m | 19.976 m | +92.264 m | 461 -> 282 -> 289 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |
| 15 | `validation.tfrecord-00008-of-00150` | `f70b6e59cc0b762` | `2135` | 9.24 | 97.626 m | 6.340 m | +91.286 m | 312 -> 310 -> 296 | Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control. |

## Replay Debug Targets: Largest Regressions

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 16 | `validation.tfrecord-00009-of-00150` | `260785192cf6c991` | `1754` | 7.47 | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 17 | `validation.tfrecord-00007-of-00150` | `f13124876e8f9c3c` | `1673` | 5.72 | 87.337 m | 119.314 m | -31.977 m | 314 -> 312 -> 310 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 18 | `validation.tfrecord-00008-of-00150` | `21590f9487feb1f9` | `660` | 5.71 | 3.561 m | 54.718 m | -51.157 m | 210 -> 200 -> 194 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 19 | `validation.tfrecord-00009-of-00150` | `435ea5885e237e87` | `1516` | 5.70 | 51.230 m | 89.620 m | -38.390 m | 223 -> 204 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 20 | `validation.tfrecord-00010-of-00150` | `ee1bd0b59fc008b3` | `1689` | 5.37 | 30.486 m | 62.915 m | -32.429 m | 312 -> 211 -> 215 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 21 | `validation.tfrecord-00009-of-00150` | `b682b4171243133d` | `281` | 5.29 | 4.181 m | 50.434 m | -46.253 m | 387 -> 300 -> 349 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 22 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | `741` | 5.25 | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 23 | `validation.tfrecord-00008-of-00150` | `21590f9487feb1f9` | `664` | 5.02 | 11.394 m | 52.816 m | -41.422 m | 210 -> 200 -> 194 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 24 | `validation.tfrecord-00007-of-00150` | `66bba4646960dab5` | `533` | 4.95 | 39.970 m | 74.018 m | -34.048 m | 198 -> 316 -> 337 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 25 | `validation.tfrecord-00009-of-00150` | `550141acae08d1f9` | `1104` | 4.95 | 17.148 m | 56.412 m | -39.264 m | 146 -> 154 -> 159 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 26 | `validation.tfrecord-00008-of-00150` | `9c8241f6a2ee5f51` | `46` | 4.91 | 1.183 m | 43.719 m | -42.536 m | 221 -> 243 -> 245 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 27 | `validation.tfrecord-00007-of-00150` | `5af2afa0d471262d` | `394` | 4.69 | 11.213 m | 48.861 m | -37.648 m | 347 -> 257 -> 457 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 28 | `validation.tfrecord-00007-of-00150` | `d30709cd60e60395` | `164` | 4.66 | 16.292 m | 52.496 m | -36.204 m | 603 -> 610 -> 371 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 29 | `validation.tfrecord-00008-of-00150` | `6b1c4e2891909916` | `2371` | 4.42 | 1.919 m | 38.579 m | -36.660 m | 330 -> 343 -> 296 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |
| 30 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | `2627` | 4.24 | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain. |

## Topology Audit Queue

| Rank | Source | Scenario | Track | Priority | Nearest FDE | Lane-link FDE | Delta | Chain | First action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 31 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1061` | 4.93 | 133.872 m | 133.872 m | 0.000 m | 219 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 32 | `validation.tfrecord-00010-of-00150` | `8ce92d09a94bf2c8` | `2516` | 4.56 | 115.282 m | 115.282 m | 0.000 m | 183 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 33 | `validation.tfrecord-00010-of-00150` | `95fa94d3b3e1f3c6` | `205` | 4.42 | 108.346 m | 108.346 m | 0.000 m | 644 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 34 | `validation.tfrecord-00010-of-00150` | `74a5b3325a534a87` | `3178` | 4.03 | 88.934 m | 88.934 m | 0.000 m | 333 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 35 | `validation.tfrecord-00009-of-00150` | `28f34edeb361e955` | `987` | 3.50 | 62.626 m | 62.626 m | 0.000 m | 158 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 36 | `validation.tfrecord-00010-of-00150` | `634b468a246a77d6` | `116` | 3.38 | 56.572 m | 56.572 m | 0.000 m | 99 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 37 | `validation.tfrecord-00007-of-00150` | `8c9eaa71b6a696c5` | `797` | 3.36 | 55.294 m | 55.294 m | 0.000 m | 718 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 38 | `validation.tfrecord-00008-of-00150` | `4dfe7c285670839f` | `0` | 3.28 | 51.637 m | 51.637 m | 0.000 m | 44 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 39 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `519` | 3.28 | 51.599 m | 51.599 m | 0.000 m | 73 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 40 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `520` | 3.24 | 49.691 m | 49.691 m | 0.000 m | 72 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 41 | `validation.tfrecord-00010-of-00150` | `8abe59aee39f351e` | `4650` | 3.23 | 49.177 m | 49.177 m | 0.000 m | 161 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 42 | `validation.tfrecord-00008-of-00150` | `9c8241f6a2ee5f51` | `88` | 3.21 | 48.172 m | 48.172 m | 0.000 m | 223 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 43 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `522` | 3.21 | 48.129 m | 48.129 m | 0.000 m | 77 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 44 | `validation.tfrecord-00010-of-00150` | `634b468a246a77d6` | `115` | 3.10 | 42.629 m | 42.629 m | 0.000 m | 91 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |
| 45 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | `816` | 3.08 | 41.649 m | 41.649 m | 0.000 m | 155 | Inspect parsed entry/exit links for the selected feature and its missing continuation. |

## `937eb2fa17da45c0` / track `979`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 12.95
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 312 -> 319 -> 246
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 151.676 m
- Lane-link FDE: 10.354 m
- Link improvement: +141.322 m
- Before/after remaining lane distance: 19.637 m / 160.970 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

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

## `2f7869c277b1a86e` / track `1925`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 12.20
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 215 -> 283 -> 288
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 156.670 m
- Lane-link FDE: 4.583 m
- Link improvement: +152.087 m
- Before/after remaining lane distance: 4.990 m / 175.345 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `36d053842cc29487` / track `576`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 12.18
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 184 -> 502 -> 497
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 148.987 m
- Lane-link FDE: 5.941 m
- Link improvement: +143.046 m
- Before/after remaining lane distance: 16.842 m / 173.903 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `fc8c647623f81bb4` / track `1466`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 12.09
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 153 -> 344 -> 343
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 144.514 m
- Lane-link FDE: 3.143 m
- Link improvement: +141.371 m
- Before/after remaining lane distance: 12.820 m / 230.044 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `2f7869c277b1a86e` / track `1972`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 12.08
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 212 -> 282 -> 285
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 144.033 m
- Lane-link FDE: 0.198 m
- Link improvement: +143.835 m
- Before/after remaining lane distance: 17.464 m / 248.473 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `236c78eb10435d60` / track `1022`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 11.88
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 153 -> 372 -> 394
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 133.790 m
- Lane-link FDE: 9.368 m
- Link improvement: +124.422 m
- Before/after remaining lane distance: 26.831 m / 319.532 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

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

## `278f11a4922dfe46` / track `277`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 10.65
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 455 -> 411 -> 431
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 118.450 m
- Lane-link FDE: 12.195 m
- Link improvement: +106.255 m
- Before/after remaining lane distance: 19.215 m / 153.436 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `c52455a0495c9bdb` / track `1937`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 10.46
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 295 -> 811 -> 806
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 121.451 m
- Lane-link FDE: 30.242 m
- Link improvement: +91.209 m
- Before/after remaining lane distance: 6.738 m / 97.949 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `a18114a865e728ef` / track `849`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 10.31
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 350 -> 206 -> 196
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 122.776 m
- Lane-link FDE: 34.209 m
- Link improvement: +88.567 m
- Before/after remaining lane distance: 18.986 m / 107.664 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `8807e9963f411c48` / track `722`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 9.96
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 337 -> 559 -> 553
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 103.862 m
- Lane-link FDE: 3.700 m
- Link improvement: +100.162 m
- Before/after remaining lane distance: 19.057 m / 188.109 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `4fd2b7f2c4f5a7eb` / track `2259`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_improvement_replay_with_horizon_caution`
- Priority score: 9.87
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 309 -> 326 -> 414
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 97.007 m
- Lane-link FDE: 7.370 m
- Link improvement: +89.637 m
- Before/after remaining lane distance: 17.689 m / 107.922 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `deef8f1a414f64de` / track `520`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 9.60
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 461 -> 282 -> 289
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 112.240 m
- Lane-link FDE: 19.976 m
- Link improvement: +92.264 m
- Before/after remaining lane distance: 0.000 m / 128.043 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts from the same anchor state as a positive control.
- Verify the feature chain aligns with the target's observed future before claiming route intent.
- Use this case to calibrate expected linked-lane behavior before tuning regressions.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `f70b6e59cc0b762` / track `2135`

- Queue: `improvement_replay_control`
- Readiness: `ready_for_continuation_improvement_replay`
- Priority score: 9.24
- Why it matters: Linked-lane continuation substantially improves the nearest-lane diagnostic, making this a positive replay control.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 312 -> 310 -> 296
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 97.626 m
- Lane-link FDE: 6.340 m
- Link improvement: +91.286 m
- Before/after remaining lane distance: 31.279 m / 173.091 m

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

## `f13124876e8f9c3c` / track `1673`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.72
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 314 -> 312 -> 310
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 87.337 m
- Lane-link FDE: 119.314 m
- Link improvement: -31.977 m
- Before/after remaining lane distance: 11.760 m / 73.671 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `21590f9487feb1f9` / track `660`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.71
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 210 -> 200 -> 194
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 3.561 m
- Lane-link FDE: 54.718 m
- Link improvement: -51.157 m
- Before/after remaining lane distance: 14.399 m / 76.387 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `435ea5885e237e87` / track `1516`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Priority score: 5.70
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 223 -> 204
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 51.230 m
- Lane-link FDE: 89.620 m
- Link improvement: -38.390 m
- Before/after remaining lane distance: 18.467 m / 57.698 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `ee1bd0b59fc008b3` / track `1689`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_regression_replay_with_horizon_caution`
- Priority score: 5.37
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 312 -> 211 -> 215
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 30.486 m
- Lane-link FDE: 62.915 m
- Link improvement: -32.429 m
- Before/after remaining lane distance: 6.318 m / 108.337 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- The target still out-travels the linked lane chain within the prediction horizon.

## `b682b4171243133d` / track `281`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.29
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 387 -> 300 -> 349
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 4.181 m
- Lane-link FDE: 50.434 m
- Link improvement: -46.253 m
- Before/after remaining lane distance: 17.064 m / 151.250 m

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

## `21590f9487feb1f9` / track `664`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 5.02
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 210 -> 200 -> 194
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 11.394 m
- Lane-link FDE: 52.816 m
- Link improvement: -41.422 m
- Before/after remaining lane distance: 33.737 m / 95.725 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `66bba4646960dab5` / track `533`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.95
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 198 -> 316 -> 337
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 39.970 m
- Lane-link FDE: 74.018 m
- Link improvement: -34.048 m
- Before/after remaining lane distance: 0.000 m / 121.999 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `550141acae08d1f9` / track `1104`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.95
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 146 -> 154 -> 159
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 17.148 m
- Lane-link FDE: 56.412 m
- Link improvement: -39.264 m
- Before/after remaining lane distance: 11.070 m / 145.374 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `9c8241f6a2ee5f51` / track `46`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.91
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 221 -> 243 -> 245
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 1.183 m
- Lane-link FDE: 43.719 m
- Link improvement: -42.536 m
- Before/after remaining lane distance: 31.573 m / 100.492 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `5af2afa0d471262d` / track `394`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.69
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 347 -> 257 -> 457
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 11.213 m
- Lane-link FDE: 48.861 m
- Link improvement: -37.648 m
- Before/after remaining lane distance: 7.016 m / 118.363 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `d30709cd60e60395` / track `164`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.66
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 603 -> 610 -> 371
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 16.292 m
- Lane-link FDE: 52.496 m
- Link improvement: -36.204 m
- Before/after remaining lane distance: 31.155 m / 112.428 m

Recommended next actions:
- Replay nearest-lane and lane-link rollouts side by side and inspect the selected continuation chain.
- Check whether the target actually follows a different route, turns, slows, or changes lanes.
- Use the result to decide whether route-choice priors or richer lane-candidate search are needed.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.

## `6b1c4e2891909916` / track `2371`

- Queue: `regression_replay_debug`
- Readiness: `ready_for_continuation_regression_replay`
- Priority score: 4.42
- Why it matters: Linked-lane continuation regresses against the clamped nearest-lane rollout, making this a route-choice or topology debugging target.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 330 -> 343 -> 296
- Link status: `linked_lane_chain`
- Nearest-lane FDE: 1.919 m
- Lane-link FDE: 38.579 m
- Link improvement: -36.660 m
- Before/after remaining lane distance: 11.143 m / 74.759 m

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

## `8ce92d09a94bf2c8` / track `2516`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.56
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 183
- Link status: `no_entry_lanes`
- Nearest-lane FDE: 115.282 m
- Lane-link FDE: 115.282 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 11.827 m / 27.472 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `95fa94d3b3e1f3c6` / track `205`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.42
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 644
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 108.346 m
- Lane-link FDE: 108.346 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 3.899 m / 3.899 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `74a5b3325a534a87` / track `3178`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 4.03
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 333
- Link status: `no_entry_lanes`
- Nearest-lane FDE: 88.934 m
- Lane-link FDE: 88.934 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 15.947 m / 23.515 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `28f34edeb361e955` / track `987`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.50
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00009-of-00150`
- Feature chain: 158
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 62.626 m
- Lane-link FDE: 62.626 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 32.851 m / 32.851 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `634b468a246a77d6` / track `116`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.38
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 99
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 56.572 m
- Lane-link FDE: 56.572 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 16.502 m / 16.502 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `8c9eaa71b6a696c5` / track `797`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.36
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00007-of-00150`
- Feature chain: 718
- Link status: `linked_feature_missing`
- Nearest-lane FDE: 55.294 m
- Lane-link FDE: 55.294 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 3.481 m / 3.481 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `4dfe7c285670839f` / track `0`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.28
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 44
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 51.637 m
- Lane-link FDE: 51.637 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 15.863 m / 15.863 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `f672132039e83c40` / track `519`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.28
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 73
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 51.599 m
- Lane-link FDE: 51.599 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 21.194 m / 21.194 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `f672132039e83c40` / track `520`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.24
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 72
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 49.691 m
- Lane-link FDE: 49.691 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 20.811 m / 20.811 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `8abe59aee39f351e` / track `4650`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.23
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 161
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 49.177 m
- Lane-link FDE: 49.177 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 4.367 m / 4.367 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `9c8241f6a2ee5f51` / track `88`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.21
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00008-of-00150`
- Feature chain: 223
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 48.172 m
- Lane-link FDE: 48.172 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 24.718 m / 24.718 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `f672132039e83c40` / track `522`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.21
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 77
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 48.129 m
- Lane-link FDE: 48.129 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 32.738 m / 32.738 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `634b468a246a77d6` / track `115`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.10
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 91
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 42.629 m
- Lane-link FDE: 42.629 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 15.502 m / 15.502 m

Recommended next actions:
- Inspect parsed entry/exit links for the selected feature and its missing continuation.
- Check whether the lightweight map-feature cap, link direction, or raw map topology caused the gap.
- Rerun the continuation study after parser/topology coverage changes before replaying this case.

Blockers / cautions:
- Raw Waymo TFRecords must remain local and ignored for replay.
- No usable parsed linked-lane chain is available yet.
- The target still out-travels the linked lane chain within the prediction horizon.

## `fe4a6425278fbd5b` / track `816`

- Queue: `topology_audit`
- Readiness: `needs_topology_audit`
- Priority score: 3.08
- Why it matters: The selected lane still lacks a usable parsed continuation chain, making this parser/topology coverage work before replay.
- Source: `validation.tfrecord-00010-of-00150`
- Feature chain: 155
- Link status: `no_exit_lanes`
- Nearest-lane FDE: 41.649 m
- Lane-link FDE: 41.649 m
- Link improvement: 0.000 m
- Before/after remaining lane distance: 14.029 m / 14.029 m

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
