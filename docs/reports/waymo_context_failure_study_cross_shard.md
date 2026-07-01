# ScenarioLens Context-Joined Failure Study

This report joins ScenarioLens baseline failure metrics with parsed Waymo Motion map, traffic-signal, stop-point, and lane-topology context. The goal is to move from 'this scenario is hard' toward 'this scenario is hard and has specific context that evaluation should preserve.'

Raw Waymo files and per-scenario derived packets remain outside git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Ready for analysis: True
- Sources analyzed: 4
- Scenarios analyzed: 100
- Max scenarios per input: 25
- Raw scenario data committed: no
- Public artifact contains aggregate counts, scenario IDs, and metrics only

## Executive Summary

| Metric | Value |
| --- | ---: |
| Scenarios | 100 |
| Evaluated prediction targets | 418 |
| Mean ScenarioLens score | 40.303 |
| Mean constant-velocity FDE | 26.217 m |
| Constant-velocity miss rate | 94.0% |
| Mean lane-aware FDE | 33.160 m |
| Mean lane-aware FDE improvement | -6.944 m |
| Signal-context scenarios | 76 |
| Route-context scenarios | 99 |
| Lane-aware map-used targets | 137 |
| Lane-aware fallback targets | 281 |

## Context Buckets

| Bucket | Scenarios | Targets | Mean score | CV FDE | CV miss | Lane FDE | Lane delta | Signal states | Route links |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All scenarios | 100 | 418 | 40.303 | 26.217 m | 94.0% | 33.160 m | -6.944 m | 60583 | 27065 |
| Traffic signal context | 76 | 331 | 42.151 | 28.641 m | 93.7% | 35.096 m | -6.455 m | 60583 | 21551 |
| No parsed signal states | 24 | 87 | 34.452 | 18.539 m | 95.4% | 27.030 m | -8.491 m | 0 | 5514 |
| Lane-topology context | 99 | 415 | 40.240 | 26.224 m | 94.0% | 33.238 m | -7.014 m | 60261 | 27065 |
| No lane-topology links | 1 | 3 | 46.558 | 25.528 m | 100.0% | 25.528 m | 0.000 m | 322 | 0 |
| Stop-dominant signal | 47 | 196 | 41.828 | 31.233 m | 93.9% | 34.661 m | -3.428 m | 39706 | 13388 |
| Go-dominant signal | 18 | 85 | 42.746 | 21.129 m | 90.6% | 25.651 m | -4.522 m | 12596 | 4726 |
| Unknown-dominant signal | 9 | 41 | 41.463 | 28.532 m | 97.6% | 56.067 m | -27.535 m | 7480 | 2704 |

## Per-Source Summary

| Source | Scenarios | Targets | Mean score | CV FDE | CV miss | Signal ctx | Route ctx |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 25 | 101 | 39.289 | 27.552 m | 96.0% | 18 | 25 |
| `validation.tfrecord-00008-of-00150` | 25 | 94 | 39.950 | 26.822 m | 94.7% | 19 | 25 |
| `validation.tfrecord-00009-of-00150` | 25 | 107 | 42.104 | 21.067 m | 94.4% | 18 | 24 |
| `validation.tfrecord-00010-of-00150` | 25 | 116 | 39.869 | 29.426 m | 91.4% | 21 | 25 |

## Hardest Context-Rich Baseline Failures

| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Map features | Signal states | Route links | Top signal |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 29.613 | 69.320 m | 100.0% | 0.000 m | 160 | 338 | 110 | `LANE_STATE_UNKNOWN (262)` |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 24.095 | 63.745 m | 100.0% | 0.000 m | 160 | 2047 | 220 | `LANE_STATE_STOP (703)` |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 31.807 | 59.535 m | 100.0% | 0.000 m | 160 | 364 | 440 | `LANE_STATE_STOP (364)` |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 23.108 | 57.623 m | 100.0% | +6.592 m | 113 | 536 | 208 | `LANE_STATE_ARROW_STOP (182)` |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 47.394 | 55.051 m | 100.0% | +14.151 m | 160 | 1440 | 364 | `LANE_STATE_STOP (720)` |
| 6 | `validation.tfrecord-00007-of-00150` | `4992809c590076fe` | 19.479 | 53.063 m | 100.0% | 0.000 m | 160 | 0 | 372 | `none` |
| 7 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 47.245 | 50.184 m | 100.0% | 0.000 m | 160 | 1052 | 14 | `LANE_STATE_ARROW_STOP (432)` |
| 8 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | 32.463 | 50.124 m | 100.0% | -3.700 m | 160 | 630 | 392 | `LANE_STATE_STOP (630)` |
| 9 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 52.283 | 48.806 m | 100.0% | 0.000 m | 160 | 1890 | 240 | `LANE_STATE_GO (801)` |
| 10 | `validation.tfrecord-00010-of-00150` | `63eca292d17e9a3a` | 28.363 | 48.569 m | 100.0% | +0.719 m | 160 | 0 | 162 | `none` |

## Signal-Context Failures

| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Signal states | Stop states | Top signal |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 29.613 | 69.320 m | 100.0% | 0.000 m | 338 | 12 | `LANE_STATE_UNKNOWN (262)` |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 24.095 | 63.745 m | 100.0% | 0.000 m | 2047 | 703 | `LANE_STATE_STOP (703)` |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 31.807 | 59.535 m | 100.0% | 0.000 m | 364 | 364 | `LANE_STATE_STOP (364)` |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 23.108 | 57.623 m | 100.0% | +6.592 m | 536 | 262 | `LANE_STATE_ARROW_STOP (182)` |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 47.394 | 55.051 m | 100.0% | +14.151 m | 1440 | 720 | `LANE_STATE_STOP (720)` |
| 6 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 47.245 | 50.184 m | 100.0% | 0.000 m | 1052 | 728 | `LANE_STATE_ARROW_STOP (432)` |
| 7 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | 32.463 | 50.124 m | 100.0% | -3.700 m | 630 | 630 | `LANE_STATE_STOP (630)` |
| 8 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 52.283 | 48.806 m | 100.0% | 0.000 m | 1890 | 720 | `LANE_STATE_GO (801)` |
| 9 | `validation.tfrecord-00007-of-00150` | `76bb4b8a12314fb2` | 47.784 | 48.446 m | 100.0% | 0.000 m | 810 | 810 | `LANE_STATE_STOP (450)` |
| 10 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 44.573 | 46.985 m | 100.0% | +1.682 m | 1800 | 1080 | `LANE_STATE_STOP (900)` |

## Route-Context Failures

| Rank | Source | Scenario | Score | CV FDE | CV miss | Lane delta | Route links | Entry | Exit | Neighbors |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 29.613 | 69.320 m | 100.0% | 0.000 m | 110 | 29 | 30 | 51 |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 24.095 | 63.745 m | 100.0% | 0.000 m | 220 | 66 | 67 | 87 |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 31.807 | 59.535 m | 100.0% | 0.000 m | 440 | 100 | 100 | 240 |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 23.108 | 57.623 m | 100.0% | +6.592 m | 208 | 47 | 47 | 114 |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 47.394 | 55.051 m | 100.0% | +14.151 m | 364 | 73 | 69 | 222 |
| 6 | `validation.tfrecord-00007-of-00150` | `4992809c590076fe` | 19.479 | 53.063 m | 100.0% | 0.000 m | 372 | 95 | 96 | 181 |
| 7 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 47.245 | 50.184 m | 100.0% | 0.000 m | 14 | 0 | 10 | 4 |
| 8 | `validation.tfrecord-00008-of-00150` | `e3f6a29b59e42c1` | 32.463 | 50.124 m | 100.0% | -3.700 m | 392 | 87 | 77 | 228 |
| 9 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 52.283 | 48.806 m | 100.0% | 0.000 m | 240 | 69 | 65 | 106 |
| 10 | `validation.tfrecord-00010-of-00150` | `63eca292d17e9a3a` | 28.363 | 48.569 m | 100.0% | +0.719 m | 162 | 51 | 51 | 60 |

## Lane-Aware Regressions With Context

Negative lane delta means the lane-aware baseline had higher FDE than constant velocity. These are useful debugging targets when they also have rich map, signal, or route context.

| Rank | Source | Scenario | CV FDE | Lane FDE | Lane delta | Map used | Fallbacks | Signal states | Route links | Top signal |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | 3.152 m | 144.514 m | -141.362 m | 1 | 0 | 249 | 245 | `LANE_STATE_UNKNOWN (125)` |
| 2 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | 7.576 m | 141.108 m | -133.532 m | 2 | 0 | 0 | 383 | `none` |
| 3 | `validation.tfrecord-00008-of-00150` | `ef4c5d0e40fdea48` | 46.688 m | 110.266 m | -63.578 m | 1 | 0 | 698 | 230 | `LANE_STATE_STOP (354)` |
| 4 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 22.523 m | 65.007 m | -42.484 m | 2 | 1 | 1359 | 388 | `LANE_STATE_UNKNOWN (639)` |
| 5 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | 11.285 m | 45.671 m | -34.386 m | 6 | 2 | 990 | 382 | `LANE_STATE_UNKNOWN (450)` |
| 6 | `validation.tfrecord-00009-of-00150` | `f2f8b5f3501ae33a` | 32.950 m | 64.437 m | -31.487 m | 1 | 1 | 551 | 428 | `LANE_STATE_STOP (496)` |
| 7 | `validation.tfrecord-00009-of-00150` | `3a2a03200cd1663e` | 25.233 m | 48.198 m | -22.965 m | 3 | 1 | 0 | 262 | `none` |
| 8 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 27.509 m | 48.599 m | -21.090 m | 5 | 3 | 1008 | 270 | `LANE_STATE_ARROW_STOP (408)` |
| 9 | `validation.tfrecord-00007-of-00150` | `46c1c1fbe5ef29d1` | 20.759 m | 41.729 m | -20.970 m | 3 | 3 | 630 | 378 | `LANE_STATE_STOP (270)` |
| 10 | `validation.tfrecord-00010-of-00150` | `f672132039e83c40` | 33.797 m | 53.772 m | -19.975 m | 3 | 1 | 623 | 256 | `LANE_STATE_STOP (623)` |

## Interpretation

- This is a diagnostic join, not a causal claim that traffic lights or route links caused a baseline failure.
- Signal-context and route-context buckets help select cases for casebooks, replay, and future route/intent features.
- Lane-aware regressions remain valuable: they show where simple lane following is not enough even when rich context is available.
- The next technical step is to turn these joined rows into curated evaluation sets and replay candidates.
