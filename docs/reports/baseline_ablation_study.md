# Baseline Ablation Study

This no-auth study compares the default constant-velocity predictor with two lane-aware variants over the checked-in ScenarioLens fixture corpus. It is meant to show baseline behavior and fallback discipline without requiring gated Waymo downloads.

Scenarios analyzed: 11

## Variant Summary

| Variant | Lane threshold | Tracks | ADE | FDE | Miss rate | FDE improvement vs CV | Map used | Fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| constant_velocity | n/a | 18 | 0.273 m | 0.385 m | 5.6% | n/a | 0 | 0 |
| lane_aware_default | 3.50 m | 18 | 0.096 m | 0.095 m | 0.0% | 0.290 m | 1 | 17 |
| lane_aware_strict | 0.50 m | 18 | 0.096 m | 0.095 m | 0.0% | 0.290 m | 1 | 17 |

## Fallback Reasons

- `no_lane_map_features`: 13
- `non_vehicle_or_cyclist_target`: 4

## Highest Default Lane-Aware Improvements

| Rank | Scenario | CV FDE | Lane FDE | Improvement | Map used | Fallbacks |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `synthetic_curved_lane_prediction` | 5.831 m | 0.615 m | 5.216 m | 1 | 0 |
| 2 | `synthetic_pedestrian_crossing` | 0.000 m | 0.000 m | 0.000 m | 0 | 1 |
| 3 | `synthetic_dense_merge` | 0.000 m | 0.000 m | 0.000 m | 0 | 3 |
| 4 | `synthetic_cyclist_close_pass` | 0.100 m | 0.100 m | 0.000 m | 0 | 1 |
| 5 | `synthetic_unprotected_left_turn` | 0.000 m | 0.000 m | 0.000 m | 0 | 2 |
| 6 | `synthetic_blocked_lane_yield` | 0.000 m | 0.000 m | 0.000 m | 0 | 2 |
| 7 | `synthetic_hard_braking_lead_vehicle` | 1.000 m | 1.000 m | 0.000 m | 0 | 1 |
| 8 | `synthetic_dense_intersection_vru` | 0.000 m | 0.000 m | 0.000 m | 0 | 3 |

## Notes

- Constant velocity remains the default scoring baseline for backward compatibility.
- Lane-aware variants only use map context for supported vehicle/cyclist tracks.
- Strict matching is useful as a sensitivity check; it should not be treated as a tuned production threshold.
- This fixture-level study complements, but does not replace, future cross-shard Waymo Motion analysis.
