# ScenarioLens Lane-Continuation Validation Study

This report scans scenario inputs for targets whose nearest-lane rollout would clamp at the end of the selected lane polyline, then evaluates whether following parsed lane `entry_lanes`/`exit_lanes` changes the diagnosis. It turns the one-case lane-link prototype into a small repeatable validation workflow.

It is intentionally scoped: this is not route planning, not a default scorer change, not closed-loop simulation, and not a Waymo benchmark claim. Raw Waymo files and local per-case packets stay out of git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Ready for analysis: True
- Sources scanned: 4
- Scenarios scanned: 100
- Candidate cases: 79
- Candidate tracks: 209
- Max scenarios per input: 25
- Max lane-link hops: 2
- Lane-match threshold: 3.500 m
- Waymo map feature cap: 240
- Raw scenario data committed: no

## Executive Findings

| Metric | Value |
| --- | ---: |
| Candidate tracks | 209 |
| Tracks using linked lanes | 192 |
| Tracks improved over nearest lane | 133 |
| Tracks regressed vs nearest lane | 57 |
| Topology gaps | 17 |
| Tracks still clamped after links | 61 |
| Mean nearest FDE | 51.205 m |
| Mean lane-link FDE | 33.523 m |
| Mean lane-link improvement over nearest | +17.682 m |

## Per-Source Summary

| Source | Scenarios | Candidate cases | Candidate tracks | Linked tracks | Improvements | Regressions | Topology gaps | Mean improvement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 25 | 19 | 59 | 58 | 35 | 23 | 1 | +13.888 m |
| `validation.tfrecord-00008-of-00150` | 25 | 17 | 35 | 32 | 22 | 9 | 3 | +19.877 m |
| `validation.tfrecord-00009-of-00150` | 25 | 22 | 53 | 49 | 37 | 12 | 4 | +24.545 m |
| `validation.tfrecord-00010-of-00150` | 25 | 21 | 62 | 53 | 39 | 13 | 9 | +14.187 m |

## Largest Lane-Link Improvements

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | `1466` | 144.514 m | 3.143 m | +141.371 m | 153 -> 344 -> 343 | 12.820 m / 230.044 m | `lane_link_improvement` |
| 2 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | `979` | 151.676 m | 10.354 m | +141.322 m | 312 -> 319 -> 246 | 19.637 m / 160.970 m | `lane_link_improvement` |
| 3 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1059` | 148.345 m | 9.068 m | +139.277 m | 220 -> 210 | 11.325 m / 239.589 m | `lane_link_improvement` |
| 4 | `validation.tfrecord-00010-of-00150` | `a863e5638dfff0ca` | `1765` | 144.122 m | 7.919 m | +136.203 m | 249 -> 244 -> 275 | 38.092 m / 174.882 m | `lane_link_improvement` |
| 5 | `validation.tfrecord-00009-of-00150` | `8807e9963f411c48` | `722` | 103.862 m | 3.700 m | +100.162 m | 337 -> 559 -> 553 | 19.057 m / 188.109 m | `lane_link_improvement` |
| 6 | `validation.tfrecord-00007-of-00150` | `c52455a0495c9bdb` | `1937` | 121.451 m | 30.242 m | +91.209 m | 295 -> 811 -> 806 | 6.738 m / 97.949 m | `lane_link_improvement` |
| 7 | `validation.tfrecord-00009-of-00150` | `937eb2fa17da45c0` | `967` | 103.053 m | 16.601 m | +86.452 m | 312 -> 319 -> 246 | 7.768 m / 149.100 m | `lane_link_improvement` |
| 8 | `validation.tfrecord-00008-of-00150` | `65d7afd24453a1ba` | `510` | 90.668 m | 5.454 m | +85.214 m | 159 -> 146 -> 140 | 0.000 m / 96.121 m | `lane_link_improvement` |
| 9 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | `34` | 87.044 m | 3.732 m | +83.312 m | 176 -> 164 -> 148 | 16.109 m / 138.217 m | `lane_link_improvement` |
| 10 | `validation.tfrecord-00008-of-00150` | `564a6bcc85c4f72f` | `1143` | 81.835 m | 6.818 m | +75.017 m | 167 -> 173 -> 255 | 7.487 m / 85.384 m | `lane_link_improvement` |

## Largest Lane-Link Regressions

Negative improvements mean linked-lane following was worse than the clamped nearest-lane rollout. Those are useful route-choice and map-topology diagnostics, not failures of the framework.

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `260785192cf6c991` | `1754` | 22.573 m | 81.112 m | -58.539 m | 235 -> 241 -> 315 | 2.418 m / 106.102 m | `route_horizon_still_exceeds_chain` |
| 2 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | `741` | 15.869 m | 58.942 m | -43.073 m | 161 -> 127 -> 116 | 24.653 m / 125.444 m | `continuation_regression` |
| 3 | `validation.tfrecord-00007-of-00150` | `d30709cd60e60395` | `164` | 16.292 m | 52.496 m | -36.204 m | 603 -> 610 -> 371 | 31.155 m / 112.428 m | `continuation_regression` |
| 4 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | `2627` | 4.595 m | 38.598 m | -34.003 m | 285 -> 120 -> 119 | 19.404 m / 111.686 m | `continuation_regression` |
| 5 | `validation.tfrecord-00007-of-00150` | `e9db41e904b349a2` | `406` | 6.776 m | 38.292 m | -31.516 m | 295 -> 228 -> 201 | 11.866 m / 144.318 m | `continuation_regression` |
| 6 | `validation.tfrecord-00010-of-00150` | `d8dde10f514a501c` | `651` | 73.197 m | 104.290 m | -31.093 m | 134 -> 143 -> 146 | 12.534 m / 76.738 m | `continuation_regression` |
| 7 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | `1542` | 68.229 m | 99.159 m | -30.930 m | 434 -> 439 -> 198 | 21.517 m / 73.873 m | `route_horizon_still_exceeds_chain` |
| 8 | `validation.tfrecord-00009-of-00150` | `e5d86b1e27302416` | `1298` | 10.847 m | 41.056 m | -30.209 m | 227 -> 135 -> 149 | 18.586 m / 81.187 m | `continuation_regression` |
| 9 | `validation.tfrecord-00007-of-00150` | `706fecd25045c8d` | `738` | 45.026 m | 74.337 m | -29.311 m | 54 -> 69 -> 73 | 32.595 m / 101.874 m | `continuation_regression` |
| 10 | `validation.tfrecord-00008-of-00150` | `65d7afd24453a1ba` | `508` | 22.818 m | 51.531 m | -28.713 m | 135 -> 143 -> 144 | 16.913 m / 113.578 m | `continuation_regression` |

## Topology Gaps

These candidates still could not use a linked-lane chain. They point to parser coverage, missing linked features, or map topology limits that are worth auditing before changing baseline behavior.

| Rank | Source | Scenario | Track | Nearest FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `6bdc7f92afefff73` | `59` | 134.082 m | 134.082 m | 0.000 m | 1056 | 1.793 m / 1.793 m | `topology_gap` |
| 2 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | `1061` | 133.872 m | 133.872 m | 0.000 m | 219 | 26.476 m / 26.476 m | `topology_gap` |
| 3 | `validation.tfrecord-00010-of-00150` | `74a5b3325a534a87` | `3178` | 88.934 m | 88.934 m | 0.000 m | 333 | 15.947 m / 23.515 m | `topology_gap` |
| 4 | `validation.tfrecord-00010-of-00150` | `2f035a284480e981` | `715` | 58.747 m | 58.747 m | 0.000 m | 513 | 0.000 m / 0.000 m | `topology_gap` |
| 5 | `validation.tfrecord-00008-of-00150` | `4dfe7c285670839f` | `0` | 51.637 m | 51.637 m | 0.000 m | 44 | 15.863 m / 15.863 m | `topology_gap` |
| 6 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `519` | 51.599 m | 51.599 m | 0.000 m | 73 | 21.194 m / 21.194 m | `topology_gap` |
| 7 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `520` | 49.691 m | 49.691 m | 0.000 m | 72 | 20.811 m / 20.811 m | `topology_gap` |
| 8 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | `522` | 48.129 m | 48.129 m | 0.000 m | 77 | 32.738 m / 32.738 m | `topology_gap` |
| 9 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | `816` | 41.649 m | 41.649 m | 0.000 m | 155 | 14.029 m / 14.029 m | `topology_gap` |
| 10 | `validation.tfrecord-00009-of-00150` | `c45b209a75ff4610` | `1869` | 33.424 m | 33.424 m | 0.000 m | 400 | 0.446 m / 0.446 m | `topology_gap` |

## Interpretation

- Improvements show cases where nearest-lane clamping was a diagnostic artifact that parsed lane links can explain.
- Regressions and topology gaps are just as valuable: they identify route-choice, map topology, parser coverage, or horizon limits for the next audit.
- The default ScenarioLens scoring baseline remains unchanged; this is a validation workflow around a follow-up experiment.
- Public artifacts stay aggregate and diagnostic; raw Waymo TFRecords and local per-case packets remain ignored.
