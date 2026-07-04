# ScenarioLens Terminal-Neighborhood Selector Calibration

This report calibrates the conservative terminal-neighborhood selector that held replay-accepted nearby-lane candidates. It sweeps small distance, heading, and route-extension gate grids, compares each policy against replay-gate labels, and recommends the least-relaxed policy that removes the current false holds on this queue without adding false promotions.

The calibration is intentionally narrow. It is not a route planner, not a learned policy, not a default scorer change, and not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded/manifest.json`
- Terminal-neighborhood audit manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_expanded/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_expanded/manifest.json`
- Ready for calibration: True
- Replay cases: 6
- Replayed cases: 6
- Replay-gate accepted cases: 3
- Replay-gate held cases: 3
- Perturbation trials behind replay labels: 24
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
| Minimum heading alignment | 0.950 | 0.950 |
| Minimum route extension | 50.000 m | 40.000 m |
| Promoted candidates | 1 | 3 |
| Held candidates | 5 | 3 |
| Replay-gate matches | 4 | 6 |
| False promotions | 0 | 0 |
| False holds | 2 | 0 |
| Mean promoted replay gain | +125.481 m | +61.817 m |

Recommended action:

- Use this as a provisional calibration target for the next expanded terminal-neighborhood queue; do not change the default selector until negative coverage improves.

## Policy Sweep

| Max distance | Heading gate | Route gate | Promotes | Holds | Matches | False promotes | False holds | Mean promoted gain |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.000 m | 0.950 | 10.000 m | 3 | 3 | 4 | 1 | 1 | +16.961 m |
| 3.000 m | 0.950 | 25.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.950 | 40.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.950 | 50.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 3.000 m | 0.950 | 75.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 3.000 m | 0.900 | 10.000 m | 3 | 3 | 4 | 1 | 1 | +16.961 m |
| 3.000 m | 0.900 | 25.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.900 | 40.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.900 | 50.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 3.000 m | 0.900 | 75.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 3.000 m | 0.700 | 10.000 m | 3 | 3 | 4 | 1 | 1 | +16.961 m |
| 3.000 m | 0.700 | 25.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.700 | 40.000 m | 2 | 4 | 5 | 0 | 1 | +29.985 m |
| 3.000 m | 0.700 | 50.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 3.000 m | 0.700 | 75.000 m | 0 | 6 | 3 | 0 | 3 | n/a |
| 5.000 m | 0.950 | 10.000 m | 4 | 2 | 5 | 1 | 0 | +44.091 m |
| 5.000 m | 0.950 | 25.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.950 | 40.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.950 | 50.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |
| 5.000 m | 0.950 | 75.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |
| 5.000 m | 0.900 | 10.000 m | 4 | 2 | 5 | 1 | 0 | +44.091 m |
| 5.000 m | 0.900 | 25.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.900 | 40.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.900 | 50.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |
| 5.000 m | 0.900 | 75.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |
| 5.000 m | 0.700 | 10.000 m | 4 | 2 | 5 | 1 | 0 | +44.091 m |
| 5.000 m | 0.700 | 25.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.700 | 40.000 m | 3 | 3 | 6 | 0 | 0 | +61.817 m |
| 5.000 m | 0.700 | 50.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |
| 5.000 m | 0.700 | 75.000 m | 1 | 5 | 4 | 0 | 2 | +125.481 m |

## Case Impact

| Rank | Scenario | Track | Replay gate | Alternate distance | Heading min | Route extension | Current decision | Recommended decision | Changed | Replay gain |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| 21 | `2f366a31ab03f8b` | `1061` | `accept_for_selector_experiment` | 3.534 m | 1.000 | 228.779 m | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | False | +125.481 m |
| 22 | `74a5b3325a534a87` | `3178` | `hold_recovery_regressed` | 2.533 m | 0.690 | 72.451 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | -15.163 m |
| 27 | `fe4a6425278fbd5b` | `816` | `accept_for_selector_experiment` | 0.988 m | 0.984 | 48.036 m | `hold_for_terminal_neighborhood_context` | `promote_terminal_neighborhood_alternate` | True | +37.105 m |
| 28 | `2f035a284480e981` | `732` | `accept_for_selector_experiment` | 1.659 m | 0.999 | 42.611 m | `hold_for_terminal_neighborhood_context` | `promote_terminal_neighborhood_alternate` | True | +22.865 m |
| 29 | `d30e6448f14e4c75` | `150` | `hold_recovery_regressed` | 2.509 m | 0.974 | 16.421 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | -9.087 m |
| 30 | `d508bc55d1510865` | `2283` | `hold_recovery_regressed` | 5.548 m | 0.992 | 5.542 m | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | False | 0.000 m |

## Interpretation

- The current selector is intentionally conservative and creates 2 false holds on this queue.
- The recommended selector gates are calibration candidates, not an automatic default-policy change.
- The current queue includes 3 replay-held negative controls, so false-promotion counts are measured on this queue; broader safety still requires more terminal-neighborhood negatives across shards.
- The next stronger validation step is to rerun this sweep after broadening terminal-neighborhood replay cases across more shards.
