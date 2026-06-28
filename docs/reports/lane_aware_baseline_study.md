# Lane-Aware Baseline Comparison

ScenarioLens compares the default constant-velocity baseline against a lightweight lane-aware baseline that follows parsed Waymo lane polylines when map context is available.

Scenarios analyzed: 11
Scenarios reported: 8

## Aggregate

- Constant-velocity mean FDE: 0.495 m
- Lane-aware mean FDE: 0.123 m
- Mean FDE improvement: 0.373 m
- Tracks using lane map: 1
- Tracks falling back to constant velocity: 13

## Ranked Scenarios

| Rank | Scenario | Targets | CV FDE | Lane FDE | Improvement | Map used | Fallbacks |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `synthetic_curved_lane_prediction` | 1 | 5.831 m | 0.615 m | 5.216 m | 1 | 0 |
| 2 | `synthetic_pedestrian_crossing` | 1 | 0.000 m | 0.000 m | 0.000 m | 0 | 1 |
| 3 | `synthetic_dense_merge` | 3 | 0.000 m | 0.000 m | 0.000 m | 0 | 3 |
| 4 | `synthetic_cyclist_close_pass` | 1 | 0.100 m | 0.100 m | 0.000 m | 0 | 1 |
| 5 | `synthetic_unprotected_left_turn` | 2 | 0.000 m | 0.000 m | 0.000 m | 0 | 2 |
| 6 | `synthetic_blocked_lane_yield` | 2 | 0.000 m | 0.000 m | 0.000 m | 0 | 2 |
| 7 | `synthetic_hard_braking_lead_vehicle` | 1 | 1.000 m | 1.000 m | 0.000 m | 0 | 1 |
| 8 | `synthetic_dense_intersection_vru` | 3 | 0.000 m | 0.000 m | 0.000 m | 0 | 3 |

## Notes

- Positive improvement means the lane-aware baseline had lower FDE.
- Pedestrians, missing map context, low-speed targets, and distant lane matches intentionally fall back to constant velocity.
- This is a comparison baseline for scenario triage, not a certified prediction model.
