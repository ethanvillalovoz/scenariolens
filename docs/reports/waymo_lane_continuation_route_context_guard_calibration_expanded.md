# ScenarioLens Route-Context Guard Calibration

This report validates the route-context guard against an expanded branch replay queue that includes both replay-accepted and replay-held route-context cases. It sweeps a small endpoint-alignment gate grid and checks whether the current gate still avoids false holds and false promotions on this queue.

The calibration is intentionally narrow. It is not a route planner, not a learned policy, not a default scorer change, and not a Waymo benchmark claim.

## Scope

- Route-context guard manifest: `data/processed/waymo_lane_continuation_route_context_guard_expanded/manifest.json`
- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection_expanded/manifest.json`
- Branch-replay manifest: `data/processed/waymo_lane_continuation_branch_replay_expanded/manifest.json`
- Ready for calibration: True
- Cases analyzed: 2
- Replay accepted cases: 1
- Replay held cases: 1
- Current route-fit gate: 0.000
- Current endpoint-alignment gate: -0.050
- Current speed-limit-drop gate: +0.100
- Endpoint gate search: 0.000, -0.050, -0.100, -0.150, -0.200, -0.250, -0.300
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Calibration Summary

| Metric | Current | Recommended |
| --- | ---: | ---: |
| Endpoint-alignment gate | -0.050 | -0.050 |
| Promoted candidates | 1 | 1 |
| Held candidates | 1 | 1 |
| Replay-gate matches | 2 | 2 |
| False promotions | 0 | 0 |
| False holds | 0 | 0 |
| Mean promoted gain | +37.766 m | +37.766 m |

Recommended action:

- Use this as a provisional calibration target for the next expanded branchable queue; do not change the default guard until negative coverage improves.

## Policy Sweep

| Endpoint gate | Promotes | Holds | Matches | False promotes | False holds | Mean promoted gain |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 0 | 2 | 1 | 0 | 1 | n/a |
| -0.050 | 1 | 1 | 2 | 0 | 0 | +37.766 m |
| -0.100 | 1 | 1 | 2 | 0 | 0 | +37.766 m |
| -0.150 | 1 | 1 | 2 | 0 | 0 | +37.766 m |
| -0.200 | 1 | 1 | 2 | 0 | 0 | +37.766 m |
| -0.250 | 1 | 1 | 2 | 0 | 0 | +37.766 m |
| -0.300 | 1 | 1 | 2 | 0 | 0 | +37.766 m |

## Case Impact

| Rank | Scenario | Track | Replay label | Endpoint delta | Current decision | Recommended decision | Changed | Motion gain |
| ---: | --- | --- | --- | ---: | --- | --- | --- | ---: |
| 1 | `260785192cf6c991` | `1754` | `accepted_for_selector_rollout` | -0.001 | `promote_motion_context_candidate` | `promote_motion_context_candidate` | False | +37.766 m |
| 8 | `5c49e681a66c720` | `2627` | `needs_route_context_margin` | -0.234 | `hold_for_route_context_evidence` | `hold_for_route_context_evidence` | False | +3.301 m |

## Interpretation

- The current guard has 0 false holds on this branch queue; the calibration sweep is a validation check, not a default-policy change.
- The recommended endpoint gate is a calibration candidate, not an automatic default change.
- The current real queue includes 1 replay-held negative control, so false-promotion counts are measured on this queue; broader safety still requires more branchable negatives across shards.
- The next stronger validation step is to rerun this calibration after expanding the branchable queue across more shards.
