# ScenarioLens Terminal-Neighborhood Selector Experiment

This experiment turns the accepted terminal-neighborhood replay case into a bounded, non-oracle selector policy. The selector uses local geometry and route-extension checks to decide whether a nearby lane should replace a selected terminal lane; replay-gate labels are used only afterward to measure agreement.

The result is intentionally narrow. It is not a route planner, not a default scorer change, and not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded/manifest.json`
- Terminal-neighborhood audit manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_expanded/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_expanded/manifest.json`
- Ready for selector experiment: True
- Replay cases: 6
- Replayed cases: 6
- Replay-gate accepted cases: 3
- Replay-gate held cases: 3
- Perturbation trials behind replay labels: 24
- Max alternate distance: 5.000 m
- Minimum heading alignment: 0.95
- Minimum route extension: 50.000 m
- Chain extension required: True
- Raw scenario data committed: no
- Raw map geometry published: no

## Selector Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 6 |
| Ready cases | 6 |
| Selector promotions | 1 |
| Selector holds | 5 |
| Not evaluable | 0 |
| Replay-gate accepted | 3 |
| Replay-gate held | 3 |
| Selector/replay-gate matches | 4 |
| Selector false promotions | 0 |
| Selector false holds | 2 |
| Mean promoted replay gain | +125.481 m |
| Mean held replay gain | +7.144 m |
| Mean promoted route extension | 228.779 m |

## Selector Decisions

| Rank | Scenario | Track | Selector | Replay gate | Alternate distance | Heading min | Route extension | Chain extended | Replay gain | First next action |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| 21 | `2f366a31ab03f8b` | `1061` | `promote_terminal_neighborhood_alternate` | `accept_for_selector_experiment` | 3.534 m | 1.000 | 228.779 m | True | +125.481 m | Evaluate this selector rule on a broader terminal-neighborhood queue. |
| 22 | `74a5b3325a534a87` | `3178` | `hold_for_terminal_neighborhood_context` | `hold_recovery_regressed` | 2.533 m | 0.690 | 72.451 m | True | -15.163 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 27 | `fe4a6425278fbd5b` | `816` | `hold_for_terminal_neighborhood_context` | `accept_for_selector_experiment` | 0.988 m | 0.984 | 48.036 m | True | +37.105 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 28 | `2f035a284480e981` | `732` | `hold_for_terminal_neighborhood_context` | `accept_for_selector_experiment` | 1.659 m | 0.999 | 42.611 m | True | +22.865 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 29 | `d30e6448f14e4c75` | `150` | `hold_for_terminal_neighborhood_context` | `hold_recovery_regressed` | 2.509 m | 0.974 | 16.421 m | True | -9.087 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 30 | `d508bc55d1510865` | `2283` | `hold_for_terminal_neighborhood_context` | `hold_recovery_regressed` | 5.548 m | 0.992 | 5.542 m | True | 0.000 m | Add richer route, heading, or map-neighborhood context before promotion. |

## Promote Queue

- `2f366a31ab03f8b` track `1061`: choose alternate lane `220` with +125.481 m replay gain and 228.779 m route extension.

## Hold Queue

- `74a5b3325a534a87` track `3178`: `hold_for_terminal_neighborhood_context` because selected_heading_below_gate, alternate_heading_below_gate. Replay label: `hold_recovery_regressed`.
- `fe4a6425278fbd5b` track `816`: `hold_for_terminal_neighborhood_context` because route_extension_below_gate. Replay label: `accept_for_selector_experiment`.
- `2f035a284480e981` track `732`: `hold_for_terminal_neighborhood_context` because route_extension_below_gate. Replay label: `accept_for_selector_experiment`.
- `d30e6448f14e4c75` track `150`: `hold_for_terminal_neighborhood_context` because route_extension_below_gate. Replay label: `hold_recovery_regressed`.
- `d508bc55d1510865` track `2283`: `hold_for_terminal_neighborhood_context` because alternate_too_far, route_extension_below_gate. Replay label: `hold_recovery_regressed`.

## `2f366a31ab03f8b` / track `1061`

- Source: `validation.tfrecord-00007-of-00150`
- Selector label: **promote_terminal_neighborhood_alternate**
- Selector reason: The nearby alternate lane is close, heading-aligned, route-extending, and chain-extending under the bounded selector policy.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: True
- Selected chain: 219
- Alternate chain: 220 -> 210
- Selector-selected chain: 220 -> 210
- Hold flags: none

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 3.534 m | <= 5.000 m |
| Selected heading alignment | True | 1.000 | >= 0.95 |
| Alternate heading alignment | True | 1.000 | >= 0.95 |
| Route extension | True | 228.779 m | >= 50.000 m |
| Chain extension | True | True | true |

## `74a5b3325a534a87` / track `3178`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **hold_recovery_regressed**
- Selector matched replay gate: True
- Selected chain: 333
- Alternate chain: 331 -> 205
- Selector-selected chain: 333
- Hold flags: selected_heading_below_gate, alternate_heading_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 2.533 m | <= 5.000 m |
| Selected heading alignment | False | 0.691 | >= 0.95 |
| Alternate heading alignment | False | 0.690 | >= 0.95 |
| Route extension | True | 72.451 m | >= 50.000 m |
| Chain extension | True | True | true |

## `fe4a6425278fbd5b` / track `816`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: False
- Selected chain: 155
- Alternate chain: 344 -> 346 -> 353
- Selector-selected chain: 155
- Hold flags: route_extension_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 0.988 m | <= 5.000 m |
| Selected heading alignment | True | 0.997 | >= 0.95 |
| Alternate heading alignment | True | 0.984 | >= 0.95 |
| Route extension | False | 48.036 m | >= 50.000 m |
| Chain extension | True | True | true |

## `2f035a284480e981` / track `732`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: False
- Selected chain: 265
- Alternate chain: 264 -> 262 -> 332
- Selector-selected chain: 265
- Hold flags: route_extension_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 1.659 m | <= 5.000 m |
| Selected heading alignment | True | 1.000 | >= 0.95 |
| Alternate heading alignment | True | 0.999 | >= 0.95 |
| Route extension | False | 42.611 m | >= 50.000 m |
| Chain extension | True | True | true |

## `d30e6448f14e4c75` / track `150`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **hold_recovery_regressed**
- Selector matched replay gate: True
- Selected chain: 269
- Alternate chain: 268 -> 265 -> 263
- Selector-selected chain: 269
- Hold flags: route_extension_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 2.509 m | <= 5.000 m |
| Selected heading alignment | True | 0.975 | >= 0.95 |
| Alternate heading alignment | True | 0.974 | >= 0.95 |
| Route extension | False | 16.421 m | >= 50.000 m |
| Chain extension | True | True | true |

## `d508bc55d1510865` / track `2283`

- Source: `validation.tfrecord-00009-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **hold_recovery_regressed**
- Selector matched replay gate: True
- Selected chain: 191
- Alternate chain: 186 -> 191
- Selector-selected chain: 191
- Hold flags: alternate_too_far, route_extension_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | False | 5.548 m | <= 5.000 m |
| Selected heading alignment | True | 0.992 | >= 0.95 |
| Alternate heading alignment | True | 0.992 | >= 0.95 |
| Route extension | False | 5.542 m | >= 50.000 m |
| Chain extension | True | True | true |

## Interpretation

- Selector promotions are bounded experiment candidates, not default behavior.
- Replay-gate labels validate the selector after the policy decision; they are not used as selector inputs.
- Held cases remain useful because they show which local geometry cues prevent over-promotion.
- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.
