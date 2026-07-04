# ScenarioLens Lane-Continuation Validation Study

This report scans scenario inputs for targets whose nearest-lane rollout would clamp at the end of the selected lane polyline, then evaluates whether following parsed lane `entry_lanes`/`exit_lanes` changes the diagnosis. It turns the one-case lane-link prototype into a small repeatable validation workflow.

It is intentionally scoped: this is not route planning, not a default scorer change, not closed-loop simulation, and not a Waymo benchmark claim. Raw Waymo files and local per-case packets stay out of git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Ready for analysis: True
- Sources scanned: 4
- Scenarios scanned: 200
- Candidate cases: 170
- Candidate tracks: 451
- Max scenarios per input: 50
- Max lane-link hops: 2
- Lane-match threshold: 3.500 m
- Waymo map feature cap: 240
- Raw scenario data committed: no

## Executive Findings

| Metric | Value |
| --- | ---: |
| Candidate tracks | 451 |
| Tracks using linked lanes | 421 |
| Tracks improved over nearest lane | 290 |
| Tracks regressed vs nearest lane | 122 |
| Topology gaps | 30 |
| Tracks still clamped after links | 134 |
| Mean nearest FDE | 50.808 m |
| Mean lane-link FDE | 32.938 m |
| Mean lane-link improvement over nearest | +17.870 m |

## Per-Source Summary

| Source | Scenarios | Candidate cases | Candidate tracks | Linked tracks | Improvements | Regressions | Topology gaps | Mean improvement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 50 | 42 | 125 | 122 | 81 | 37 | 3 | +16.582 m |
| `validation.tfrecord-00008-of-00150` | 50 | 39 | 97 | 89 | 60 | 28 | 8 | +16.515 m |
| `validation.tfrecord-00009-of-00150` | 50 | 45 | 114 | 108 | 75 | 31 | 6 | +21.639 m |
| `validation.tfrecord-00010-of-00150` | 50 | 44 | 115 | 102 | 74 | 26 | 13 | +16.677 m |

## Largest Lane-Link Improvements

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00010-of-00150` | `2f7869c277b1a86e` | `1925` | 156.670 m | 4.583 m | +152.087 m | 215 -> 283 -> 288 | 4.990 m / 175.345 m | `lane_link_improvement` |
| 2 | `validation.tfrecord-00010-of-00150` | `2f7869c277b1a86e` | `1972` | 144.033 m | 0.198 m | +143.835 m | 212 -> 282 -> 285 | 17.464 m / 248.473 m | `lane_link_improvement` |
| 3 | `validation.tfrecord-00009-of-00150` | `36d053842cc29487` | `576` | 148.987 m | 5.941 m | +143.046 m | 184 -> 502 -> 497 | 16.842 m / 173.903 m | `lane_link_improvement` |
| 4 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | `1466` | 144.514 m | 3.143 m | +141.371 m | 153 -> 344 -> 343 | 12.820 m / 230.044 m | `lane_link_improvement` |
| 5 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | `979` | 151.676 m | 10.354 m | +141.322 m | 312 -> 319 -> 246 | 19.637 m / 160.970 m | `lane_link_improvement` |
| 6 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1059` | 148.345 m | 9.068 m | +139.277 m | 220 -> 210 | 11.325 m / 239.589 m | `lane_link_improvement` |
| 7 | `validation.tfrecord-00010-of-00150` | `a863e5638dfff0ca` | `1765` | 144.122 m | 7.919 m | +136.203 m | 249 -> 244 -> 275 | 38.092 m / 174.882 m | `lane_link_improvement` |
| 8 | `validation.tfrecord-00008-of-00150` | `236c78eb10435d60` | `1022` | 133.790 m | 9.368 m | +124.422 m | 153 -> 372 -> 394 | 26.831 m / 319.532 m | `lane_link_improvement` |
| 9 | `validation.tfrecord-00008-of-00150` | `278f11a4922dfe46` | `277` | 118.450 m | 12.195 m | +106.255 m | 455 -> 411 -> 431 | 19.215 m / 153.436 m | `lane_link_improvement` |
| 10 | `validation.tfrecord-00009-of-00150` | `8807e9963f411c48` | `722` | 103.862 m | 3.700 m | +100.162 m | 337 -> 559 -> 553 | 19.057 m / 188.109 m | `lane_link_improvement` |
| 11 | `validation.tfrecord-00008-of-00150` | `deef8f1a414f64de` | `520` | 112.240 m | 19.976 m | +92.264 m | 461 -> 282 -> 289 | 0.000 m / 128.043 m | `lane_link_improvement` |
| 12 | `validation.tfrecord-00008-of-00150` | `f70b6e59cc0b762` | `2135` | 97.626 m | 6.340 m | +91.286 m | 312 -> 310 -> 296 | 31.279 m / 173.091 m | `lane_link_improvement` |
| 13 | `validation.tfrecord-00007-of-00150` | `c52455a0495c9bdb` | `1937` | 121.451 m | 30.242 m | +91.209 m | 295 -> 811 -> 806 | 6.738 m / 97.949 m | `lane_link_improvement` |
| 14 | `validation.tfrecord-00009-of-00150` | `4fd2b7f2c4f5a7eb` | `2259` | 97.007 m | 7.370 m | +89.637 m | 309 -> 326 -> 414 | 17.689 m / 107.922 m | `lane_link_improvement` |
| 15 | `validation.tfrecord-00009-of-00150` | `a18114a865e728ef` | `849` | 122.776 m | 34.209 m | +88.567 m | 350 -> 206 -> 196 | 18.986 m / 107.664 m | `lane_link_improvement` |
| 16 | `validation.tfrecord-00010-of-00150` | `e69798d7a1b75fbd` | `1170` | 126.585 m | 38.166 m | +88.419 m | 284 -> 267 -> 348 | 7.688 m / 96.115 m | `lane_link_improvement` |
| 17 | `validation.tfrecord-00009-of-00150` | `a18114a865e728ef` | `844` | 133.196 m | 44.986 m | +88.210 m | 349 -> 190 -> 195 | 14.023 m / 102.313 m | `lane_link_improvement` |
| 18 | `validation.tfrecord-00010-of-00150` | `e69798d7a1b75fbd` | `1179` | 105.073 m | 17.005 m | +88.068 m | 283 -> 268 -> 349 | 34.372 m / 122.446 m | `lane_link_improvement` |
| 19 | `validation.tfrecord-00007-of-00150` | `a050aed2c972ccfa` | `3784` | 88.838 m | 2.268 m | +86.570 m | 234 -> 226 -> 198 | 0.496 m / 112.638 m | `lane_link_improvement` |
| 20 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | `967` | 101.866 m | 16.289 m | +85.577 m | 313 -> 317 -> 320 | 8.752 m / 132.771 m | `lane_link_improvement` |

## Largest Lane-Link Regressions

Negative improvements mean linked-lane following was worse than the clamped nearest-lane rollout. Those are useful route-choice and map-topology diagnostics, not failures of the framework.

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `260785192cf6c991` | `1754` | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | 2.418 m / 106.102 m | `route_horizon_still_exceeds_chain` |
| 2 | `validation.tfrecord-00008-of-00150` | `21590f9487feb1f9` | `660` | 3.561 m | 54.718 m | -51.157 m | 210 -> 200 -> 194 | 14.399 m / 76.387 m | `continuation_regression` |
| 3 | `validation.tfrecord-00009-of-00150` | `b682b4171243133d` | `281` | 4.181 m | 50.434 m | -46.253 m | 387 -> 300 -> 349 | 17.064 m / 151.250 m | `continuation_regression` |
| 4 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | `741` | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | 24.653 m / 125.444 m | `continuation_regression` |
| 5 | `validation.tfrecord-00008-of-00150` | `9c8241f6a2ee5f51` | `46` | 1.183 m | 43.719 m | -42.536 m | 221 -> 243 -> 245 | 31.573 m / 100.492 m | `continuation_regression` |
| 6 | `validation.tfrecord-00008-of-00150` | `21590f9487feb1f9` | `664` | 11.394 m | 52.816 m | -41.422 m | 210 -> 200 -> 194 | 33.737 m / 95.725 m | `continuation_regression` |
| 7 | `validation.tfrecord-00009-of-00150` | `550141acae08d1f9` | `1104` | 17.148 m | 56.412 m | -39.264 m | 146 -> 154 -> 159 | 11.070 m / 145.374 m | `continuation_regression` |
| 8 | `validation.tfrecord-00009-of-00150` | `435ea5885e237e87` | `1516` | 51.230 m | 89.620 m | -38.390 m | 223 -> 204 | 18.467 m / 57.698 m | `route_horizon_still_exceeds_chain` |
| 9 | `validation.tfrecord-00007-of-00150` | `5af2afa0d471262d` | `394` | 11.213 m | 48.861 m | -37.648 m | 347 -> 257 -> 457 | 7.016 m / 118.363 m | `continuation_regression` |
| 10 | `validation.tfrecord-00008-of-00150` | `6b1c4e2891909916` | `2371` | 1.919 m | 38.579 m | -36.660 m | 330 -> 343 -> 296 | 11.143 m / 74.759 m | `continuation_regression` |
| 11 | `validation.tfrecord-00007-of-00150` | `d30709cd60e60395` | `164` | 16.292 m | 52.496 m | -36.204 m | 603 -> 610 -> 371 | 31.155 m / 112.428 m | `continuation_regression` |
| 12 | `validation.tfrecord-00007-of-00150` | `66bba4646960dab5` | `533` | 39.970 m | 74.018 m | -34.048 m | 198 -> 316 -> 337 | 0.000 m / 121.999 m | `continuation_regression` |
| 13 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | `2627` | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | 19.404 m / 111.686 m | `continuation_regression` |
| 14 | `validation.tfrecord-00010-of-00150` | `ee1bd0b59fc008b3` | `1689` | 30.486 m | 62.915 m | -32.429 m | 312 -> 211 -> 215 | 6.318 m / 108.337 m | `route_horizon_still_exceeds_chain` |
| 15 | `validation.tfrecord-00007-of-00150` | `f13124876e8f9c3c` | `1673` | 87.337 m | 119.314 m | -31.977 m | 314 -> 312 -> 310 | 11.760 m / 73.671 m | `continuation_regression` |
| 16 | `validation.tfrecord-00007-of-00150` | `e9db41e904b349a2` | `406` | 6.776 m | 38.292 m | -31.516 m | 295 -> 228 -> 201 | 11.866 m / 144.318 m | `continuation_regression` |
| 17 | `validation.tfrecord-00010-of-00150` | `d8dde10f514a501c` | `651` | 73.197 m | 104.290 m | -31.093 m | 134 -> 143 -> 146 | 12.534 m / 76.738 m | `continuation_regression` |
| 18 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | `1542` | 68.229 m | 99.159 m | -30.930 m | 434 -> 439 -> 198 | 21.517 m / 73.873 m | `route_horizon_still_exceeds_chain` |
| 19 | `validation.tfrecord-00009-of-00150` | `e5d86b1e27302416` | `1298` | 10.847 m | 41.056 m | -30.209 m | 227 -> 135 -> 149 | 18.586 m / 81.187 m | `continuation_regression` |
| 20 | `validation.tfrecord-00008-of-00150` | `4077d5e01ce99fa2` | `289` | 4.490 m | 34.323 m | -29.833 m | 369 -> 365 -> 303 | 14.323 m / 71.727 m | `continuation_regression` |

## Topology Gaps

These candidates still could not use a linked-lane chain. They point to parser coverage, missing linked features, or map topology limits that are worth auditing before changing baseline behavior.

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1061` | 133.872 m | 133.872 m | 0.000 m | 219 | 26.476 m / 26.476 m | `topology_gap` |
| 2 | `validation.tfrecord-00010-of-00150` | `8ce92d09a94bf2c8` | `2516` | 115.282 m | 115.282 m | 0.000 m | 183 | 11.827 m / 27.472 m | `topology_gap` |
| 3 | `validation.tfrecord-00010-of-00150` | `95fa94d3b3e1f3c6` | `205` | 108.346 m | 108.346 m | 0.000 m | 644 | 3.899 m / 3.899 m | `topology_gap` |
| 4 | `validation.tfrecord-00010-of-00150` | `74a5b3325a534a87` | `3178` | 88.934 m | 88.934 m | 0.000 m | 333 | 15.947 m / 23.515 m | `topology_gap` |
| 5 | `validation.tfrecord-00009-of-00150` | `28f34edeb361e955` | `987` | 62.626 m | 62.626 m | 0.000 m | 158 | 32.851 m / 32.851 m | `topology_gap` |
| 6 | `validation.tfrecord-00010-of-00150` | `634b468a246a77d6` | `116` | 56.572 m | 56.572 m | 0.000 m | 99 | 16.502 m / 16.502 m | `topology_gap` |
| 7 | `validation.tfrecord-00007-of-00150` | `8c9eaa71b6a696c5` | `797` | 55.294 m | 55.294 m | 0.000 m | 718 | 3.481 m / 3.481 m | `topology_gap` |
| 8 | `validation.tfrecord-00008-of-00150` | `4dfe7c285670839f` | `0` | 51.637 m | 51.637 m | 0.000 m | 44 | 15.863 m / 15.863 m | `topology_gap` |
| 9 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `519` | 51.599 m | 51.599 m | 0.000 m | 73 | 21.194 m / 21.194 m | `topology_gap` |
| 10 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `520` | 49.691 m | 49.691 m | 0.000 m | 72 | 20.811 m / 20.811 m | `topology_gap` |
| 11 | `validation.tfrecord-00010-of-00150` | `8abe59aee39f351e` | `4650` | 49.177 m | 49.177 m | 0.000 m | 161 | 4.367 m / 4.367 m | `topology_gap` |
| 12 | `validation.tfrecord-00008-of-00150` | `9c8241f6a2ee5f51` | `88` | 48.172 m | 48.172 m | 0.000 m | 223 | 24.718 m / 24.718 m | `topology_gap` |
| 13 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `522` | 48.129 m | 48.129 m | 0.000 m | 77 | 32.738 m / 32.738 m | `topology_gap` |
| 14 | `validation.tfrecord-00010-of-00150` | `634b468a246a77d6` | `115` | 42.629 m | 42.629 m | 0.000 m | 91 | 15.502 m / 15.502 m | `topology_gap` |
| 15 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | `816` | 41.649 m | 41.649 m | 0.000 m | 155 | 14.029 m / 14.029 m | `topology_gap` |
| 16 | `validation.tfrecord-00008-of-00150` | `7cf8d52450cd49f7` | `242` | 38.397 m | 38.397 m | 0.000 m | 361 | 7.738 m / 13.831 m | `topology_gap` |
| 17 | `validation.tfrecord-00008-of-00150` | `48d09bf094654ba1` | `525` | 35.094 m | 35.094 m | 0.000 m | 428 | 12.414 m / 12.414 m | `topology_gap` |
| 18 | `validation.tfrecord-00008-of-00150` | `8cef75ad6ea6d26` | `2454` | 33.857 m | 33.857 m | 0.000 m | 226 | 24.111 m / 24.111 m | `topology_gap` |
| 19 | `validation.tfrecord-00010-of-00150` | `2f035a284480e981` | `732` | 33.227 m | 33.227 m | 0.000 m | 265 | 12.753 m / 12.753 m | `topology_gap` |
| 20 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | `150` | 28.584 m | 28.584 m | 0.000 m | 269 | 27.667 m / 27.667 m | `topology_gap` |

## Interpretation

- Improvements show cases where nearest-lane clamping was a diagnostic artifact that parsed lane links can explain.
- Regressions and topology gaps are just as valuable: they identify route-choice, map topology, parser coverage, or horizon limits for the next audit.
- The default ScenarioLens scoring baseline remains unchanged; this is a validation workflow around a follow-up experiment.
- Public artifacts stay aggregate and diagnostic; raw Waymo TFRecords and local per-case packets remain ignored.
