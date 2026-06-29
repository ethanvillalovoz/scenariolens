# ScenarioLens Map-Match Audit

This report audits lane-aware fallback behavior before changing the matcher. It reloads selected fallback-heavy debug cases, sweeps lane match thresholds, and checks whether simply accepting farther lane matches improves or worsens final displacement error.

It is intentionally scoped: this is a threshold-sensitivity diagnostic, not a matcher change, not a Waymo benchmark claim, and not a production map-matching system.

## Scope

- Debug manifest: `data/processed/waymo_lane_aware_debug_casebook/manifest.json`
- Ready for audit: True
- Cases audited: 1
- Default lane-match threshold: 3.500 m
- Threshold sweep: 3.500 m, 5.000 m, 10.000 m, 25.000 m, 50.000 m, 100.000 m, 150.000 m
- Raw Waymo files committed: no
- Local audit packets committed: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Audited cases | 1 |
| Audited targets | 8 |
| Default map-used targets | 0 |
| Default fallback targets | 8 |
| Best threshold map-used targets | 0 |
| Best threshold FDE delta | 0.000 m |
| Cases where widening worsened FDE | 1 |

## Case Summary

| Rank | Scenario | Case | Targets | Default map used | Default fallbacks | Nearest-lane range | Recommendation |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | `2f035a284480e981` | Fallback-heavy case | 8 | 0 | 8 | 7.609 m - 138.703 m | audit_coordinate_frame_or_lane_set |

## `2f035a284480e981`

- Case: Fallback-heavy case
- Source: `validation.tfrecord-00010-of-00150`
- Default target handling: 0 map-used / 8 fallback
- Recommendation: **audit_coordinate_frame_or_lane_set**
- Why: Default matching falls back for every target, and widening the threshold does not improve FDE. Several targets are far from parsed lane polylines, so coordinate frames, lane coverage, and lane-selection logic should be audited first.
- Local audit packet: `data/processed/waymo_map_match_audit/cases/1-fallback-heavy-case-2f035a284480e981/map_match_audit.json`

Target lane-distance audit:

| Track | Type | Nearest lane | Anchor speed | Default fallback | First matched threshold | CV FDE |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `722` | `vehicle` | 118.156 m | 0.302 m/s | `target_too_far_from_lane` | 150.000 m | 56.508 m |
| `715` | `vehicle` | 78.585 m | 6.614 m/s | `target_too_far_from_lane` | 100.000 m | 22.381 m |
| `726` | `vehicle` | 23.999 m | 1.282 m/s | `target_too_far_from_lane` | 25.000 m | 30.847 m |
| `717` | `vehicle` | 51.799 m | 5.236 m/s | `target_too_far_from_lane` | 100.000 m | 31.953 m |
| `721` | `vehicle` | 121.153 m | 0.395 m/s | `target_too_far_from_lane` | 150.000 m | 36.929 m |
| `724` | `vehicle` | 103.781 m | 1.852 m/s | `target_too_far_from_lane` | 150.000 m | 36.177 m |
| `731` | `vehicle` | 138.703 m | 8.820 m/s | `target_too_far_from_lane` | 150.000 m | 9.968 m |
| `732` | `vehicle` | 7.609 m | 10.288 m/s | `target_too_far_from_lane` | 10.000 m | 31.195 m |

Threshold sweep:

| Threshold | Map used | Fallbacks | Lane FDE | FDE delta | Label | Fallback reasons |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 3.500 m | 0 | 8 | 31.995 m | 0.000 m | `all_targets_fallback` | `target_too_far_from_lane`: 8 |
| 5.000 m | 0 | 8 | 31.995 m | 0.000 m | `all_targets_fallback` | `target_too_far_from_lane`: 8 |
| 10.000 m | 1 | 7 | 34.777 m | -2.782 m | `worse_than_constant_velocity` | `target_too_far_from_lane`: 7 |
| 25.000 m | 2 | 6 | 37.134 m | -5.139 m | `worse_than_constant_velocity` | `target_too_far_from_lane`: 6 |
| 50.000 m | 2 | 6 | 37.134 m | -5.139 m | `worse_than_constant_velocity` | `target_too_far_from_lane`: 6 |
| 100.000 m | 4 | 4 | 50.453 m | -18.458 m | `worse_than_constant_velocity` | `target_too_far_from_lane`: 4 |
| 150.000 m | 8 | 0 | 80.772 m | -48.777 m | `worse_than_constant_velocity` | none |

## Interpretation

- The default threshold is a guardrail: when targets are far from parsed lanes, ScenarioLens falls back to constant velocity instead of trusting a bad map match.
- If wider thresholds make FDE worse, the fix is not a larger radius; it is better lane selection, coordinate-frame auditing, route/intent priors, or richer map context.
- If a wider threshold improves FDE on a case, that threshold is still only a hypothesis and should be validated against more scenarios before becoming default behavior.
- This report keeps the public artifact honest by separating map-match coverage problems from replay-ready model evidence.
