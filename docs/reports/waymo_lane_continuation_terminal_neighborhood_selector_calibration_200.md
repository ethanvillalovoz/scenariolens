# ScenarioLens Terminal-Neighborhood Selector Calibration

This report stress-tests the conservative terminal-neighborhood selector on a broader nearby-lane replay queue. It sweeps small distance, heading, and route-extension gate grids, then reports the best zero-false-promotion calibration candidate it found while making clear that false holds remain.

The calibration is intentionally narrow. It is not a route planner, not a learned policy, not a default scorer change, and not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json`
- Terminal-neighborhood audit manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_200/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_200/manifest.json`
- Ready for calibration: True
- Replay cases: 7
- Replayed cases: 7
- Replay-gate accepted cases: 5
- Replay-gate held cases: 2
- Perturbation trials behind replay labels: 28
- Current max alternate distance: 5.000 m
- Current minimum heading alignment: 0.950
- Current minimum route extension: 50.000 m
- Distance gate search: 3.000 m, 5.000 m
- Heading gate search: 0.950, 0.900, 0.700
- Route-extension gate search: 10.000 m, 25.000 m, 40.000 m, 50.000 m, 75.000 m
- Raw scenario data committed: no
- Raw map geometry published: no

## Calibration Summary

| Metric | Current | Recommended |
| --- | ---: | ---: |
| Max alternate distance | 5.000 m | 5.000 m |
| Minimum heading alignment | 0.950 | 0.700 |
| Minimum route extension | 50.000 m | 40.000 m |
| Promoted candidates | 2 | 4 |
| Held candidates | 5 | 3 |
| Replay-gate matches | 4 | 6 |
| False promotions | 0 | 0 |
| False holds | 3 | 1 |
| Mean promoted replay gain | +71.052 m | +51.332 m |

Recommended action:

- Use this only as a diagnostic calibration candidate for the next expanded queue; do not change the default selector because no grid candidate cleared both false holds and false promotions.

## Policy Sweep

| Max distance | Heading gate | Route gate | Promotes | Holds | Matches | False promotes | False holds | Mean promoted gain |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.000 m | 0.950 | 10.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.950 | 25.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.950 | 40.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.950 | 50.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 3.000 m | 0.950 | 75.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 3.000 m | 0.900 | 10.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.900 | 25.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.900 | 40.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.900 | 50.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 3.000 m | 0.900 | 75.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 3.000 m | 0.700 | 10.000 m | 2 | 5 | 2 | 1 | 4 | +10.437 m |
| 3.000 m | 0.700 | 25.000 m | 2 | 5 | 2 | 1 | 4 | +10.437 m |
| 3.000 m | 0.700 | 40.000 m | 1 | 6 | 3 | 0 | 4 | +37.105 m |
| 3.000 m | 0.700 | 50.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 3.000 m | 0.700 | 75.000 m | 0 | 7 | 2 | 0 | 5 | n/a |
| 5.000 m | 0.950 | 10.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.950 | 25.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.950 | 40.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.950 | 50.000 m | 2 | 5 | 4 | 0 | 3 | +71.052 m |
| 5.000 m | 0.950 | 75.000 m | 2 | 5 | 4 | 0 | 3 | +71.052 m |
| 5.000 m | 0.900 | 10.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.900 | 25.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.900 | 40.000 m | 3 | 4 | 5 | 0 | 2 | +59.736 m |
| 5.000 m | 0.900 | 50.000 m | 2 | 5 | 4 | 0 | 3 | +71.052 m |
| 5.000 m | 0.900 | 75.000 m | 2 | 5 | 4 | 0 | 3 | +71.052 m |
| 5.000 m | 0.700 | 10.000 m | 5 | 2 | 5 | 1 | 1 | +37.820 m |
| 5.000 m | 0.700 | 25.000 m | 5 | 2 | 5 | 1 | 1 | +37.820 m |
| 5.000 m | 0.700 | 40.000 m | 4 | 3 | 6 | 0 | 1 | +51.332 m |
| 5.000 m | 0.700 | 50.000 m | 3 | 4 | 5 | 0 | 2 | +56.074 m |
| 5.000 m | 0.700 | 75.000 m | 2 | 5 | 4 | 0 | 3 | +71.052 m |

## Case Impact

| Rank | Scenario | Track | Replay gate | Alternate distance | Heading min | Route extension | Current decision | Recommended decision | Changed | Replay gain |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| 31 | `2f366a31ab03f8b` | `1061` | `accept_for_selector_experiment` | 3.534 m | 1.000 | 228.779 m | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | False | +125.481 m |
| 34 | `74a5b3325a534a87` | `3178` | `hold_recovery_regressed` | 2.533 m | 0.690 | 72.451 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | -15.163 m |
| 35 | `28f34edeb361e955` | `987` | `accept_for_selector_experiment` | 4.719 m | 0.886 | 56.882 m | `hold_for_terminal_neighborhood_context` | `promote_terminal_neighborhood_alternate` | True | +26.119 m |
| 36 | `634b468a246a77d6` | `116` | `hold_recovery_regressed` | 0.269 m | 0.823 | 32.514 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | -16.230 m |
| 41 | `8abe59aee39f351e` | `4650` | `accept_for_selector_experiment` | 4.426 m | 0.999 | 81.794 m | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | False | +16.623 m |
| 42 | `9c8241f6a2ee5f51` | `88` | `accept_for_selector_experiment` | 2.070 m | 0.122 | 70.140 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | +38.890 m |
| 45 | `fe4a6425278fbd5b` | `816` | `accept_for_selector_experiment` | 0.988 m | 0.984 | 48.036 m | `hold_for_terminal_neighborhood_context` | `promote_terminal_neighborhood_alternate` | True | +37.105 m |

## Interpretation

- The current selector is intentionally conservative and creates 3 false holds on this queue.
- The recommended selector gates are calibration candidates, not an automatic default-policy change.
- The current queue includes 2 replay-held negative controls, so false-promotion counts are measured on this queue; broader safety still requires more terminal-neighborhood negatives across shards.
- The next stronger validation step is to rerun this sweep after broadening terminal-neighborhood replay cases across more shards.
