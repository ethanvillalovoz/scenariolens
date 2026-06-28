# ScenarioLens Real-Slice Failure Study

This report summarizes public-safe aggregate findings from ScenarioLens baseline failure analysis. Raw Waymo files and per-scenario derived outputs remain outside git.

## Run Scope

- Input: `data/raw/waymo/motion/validation`
- Input format: `native`
- Ready for analysis: True
- Scenarios analyzed: 25
- Max scenarios requested: 25
- Raw scenario data committed: no

## Executive Findings

| Metric | Value |
| --- | ---: |
| Score min / median / mean / max | 19.48 / 41.06 / 39.29 / 51.43 |
| Evaluated baseline targets | 101 |
| Target-weighted mean baseline ADE | 10.17 m |
| Target-weighted mean baseline FDE | 26.66 m |
| Max baseline FDE | 101.65 m |
| Weighted miss rate | 96.04% |
| Mean baseline failure score | 9.62 |
| Interaction/FDE correlation | -0.15 |

## Failure By Tag

| Tag | Scenarios | Targets | Mean ADE | Mean FDE | Max FDE | Miss Rate | Mean Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `objects_of_interest` | 9 | 50 | 11.41 m | 29.81 m | 101.65 m | 98.00% | 38.50 |
| `map_context` | 25 | 101 | 10.17 m | 26.66 m | 101.65 m | 96.04% | 39.29 |
| `tracks_to_predict` | 25 | 101 | 10.17 m | 26.66 m | 101.65 m | 96.04% | 39.29 |
| `traffic_signal_context` | 25 | 101 | 10.17 m | 26.66 m | 101.65 m | 96.04% | 39.29 |
| `dense_multi_agent` | 24 | 100 | 10.08 m | 26.53 m | 101.65 m | 96.00% | 40.10 |
| `vulnerable_road_user` | 19 | 85 | 9.46 m | 24.59 m | 73.58 m | 95.29% | 43.31 |
| `cyclist_interaction` | 2 | 10 | 3.77 m | 8.00 m | 20.67 m | 90.00% | 43.71 |

## Failure By Score Component

| Component | Positive Scenarios | Mean Component | Mean FDE | Miss Rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline_failure` | 25 | 9.62 | 26.66 m | 96.04% |
| `density` | 25 | 2.87 | 26.66 m | 96.04% |
| `dynamics` | 25 | 2.90 | 26.66 m | 96.04% |
| `path_conflict` | 24 | 2.49 | 26.53 m | 96.00% |
| `proximity` | 24 | 6.08 | 26.53 m | 96.00% |
| `taxonomy` | 24 | 3.29 | 26.53 m | 96.00% |
| `ttc` | 24 | 6.00 | 26.40 m | 96.00% |
| `vru` | 19 | 6.08 | 24.59 m | 95.29% |
| `vru_proximity` | 15 | 3.54 | 24.55 m | 94.87% |

## Interaction/FDE Quadrants

| Quadrant | Scenarios | Mean FDE | Miss Rate |
| --- | ---: | ---: | ---: |
| High interaction / high FDE | 8 | 35.62 m | 97.56% |
| High interaction / low FDE | 5 | 12.86 m | 88.89% |
| Low interaction / high FDE | 5 | 49.26 m | 100.00% |
| Low interaction / low FDE | 7 | 17.08 m | 100.00% |

## Hardest Baseline-Failure Scenarios

| Rank | Scenario | Score | FDE | Miss Rate | Tags | Main Reason |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 1 | `5c8f9e7af4b0248a` | 29.61 | 69.32 m | 100.00% | `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` | includes 4 Waymo prediction target(s) |
| 2 | `4992809c590076fe` | 19.48 | 53.06 m | 100.00% | `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | includes 1 Waymo prediction target(s) |
| 3 | `76bb4b8a12314fb2` | 47.78 | 48.45 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | contains 6 vulnerable road user(s) |
| 4 | `7fc449ae179c29ac` | 44.57 | 46.98 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` | contains 4 vulnerable road user(s) |
| 5 | `770fec53ec3e0395` | 50.89 | 43.83 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | contains 4 vulnerable road user(s) |
| 6 | `2a3333bf80e243c6` | 19.74 | 40.11 m | 100.00% | `map_context`, `tracks_to_predict`, `traffic_signal_context` | includes 1 Waymo prediction target(s) |
| 7 | `d963287c8360ac9d` | 41.46 | 38.21 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` | contains 1 vulnerable road user(s) |
| 8 | `706fecd25045c8d` | 51.33 | 32.55 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | contains 7 vulnerable road user(s) |
| 9 | `7e969997e3e0b772` | 51.43 | 31.82 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | contains 9 vulnerable road user(s) |
| 10 | `e9db41e904b349a2` | 32.31 | 30.63 m | 100.00% | `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` | includes 3 Waymo prediction target(s) |

## Interpretation

- This is a screening study, not a benchmark claim.
- High FDE means the constant-velocity baseline is a poor explanation of the target motion in that scenario.
- Tag-level differences help identify scenario families that deserve a stronger baseline, replay, perturbation, or Waymax experiment.
- For distribution stability across windows or shards, rerun with `failure-study-stability`.
