# ScenarioLens Terminal-Neighborhood Selector Experiment

This experiment turns the accepted terminal-neighborhood replay case into a bounded, non-oracle selector policy. The selector uses local geometry and route-extension checks to decide whether a nearby lane should replace a selected terminal lane; replay-gate labels are used only afterward to measure agreement.

The result is intentionally narrow. It is not a route planner, not a default scorer change, and not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json`
- Terminal-neighborhood audit manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_200/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_200/manifest.json`
- Ready for selector experiment: True
- Replay cases: 7
- Replayed cases: 7
- Replay-gate accepted cases: 5
- Replay-gate held cases: 2
- Perturbation trials behind replay labels: 28
- Max alternate distance: 5.000 m
- Minimum heading alignment: 0.95
- Minimum route extension: 50.000 m
- Chain extension required: True
- Raw scenario data committed: no
- Raw map geometry published: no

## Selector Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 7 |
| Ready cases | 7 |
| Selector promotions | 2 |
| Selector holds | 5 |
| Not evaluable | 0 |
| Replay-gate accepted | 5 |
| Replay-gate held | 2 |
| Selector/replay-gate matches | 4 |
| Selector false promotions | 0 |
| Selector false holds | 3 |
| Mean promoted replay gain | +71.052 m |
| Mean held replay gain | +14.144 m |
| Mean promoted route extension | 155.286 m |

## Selector Decisions

| Rank | Scenario | Track | Selector | Replay gate | Alternate distance | Heading min | Route extension | Chain extended | Replay gain | First next action |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| 31 | `2f366a31ab03f8b` | `1061` | `promote_terminal_neighborhood_alternate` | `accept_for_selector_experiment` | 3.534 m | 1.000 | 228.779 m | True | +125.481 m | Evaluate this selector rule on a broader terminal-neighborhood queue. |
| 34 | `74a5b3325a534a87` | `3178` | `hold_for_terminal_neighborhood_context` | `hold_recovery_regressed` | 2.533 m | 0.690 | 72.451 m | True | -15.163 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 35 | `28f34edeb361e955` | `987` | `hold_for_terminal_neighborhood_context` | `accept_for_selector_experiment` | 4.719 m | 0.886 | 56.882 m | True | +26.119 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 36 | `634b468a246a77d6` | `116` | `hold_for_terminal_neighborhood_context` | `hold_recovery_regressed` | 0.269 m | 0.823 | 32.514 m | True | -16.230 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 41 | `8abe59aee39f351e` | `4650` | `promote_terminal_neighborhood_alternate` | `accept_for_selector_experiment` | 4.426 m | 0.999 | 81.794 m | True | +16.623 m | Evaluate this selector rule on a broader terminal-neighborhood queue. |
| 42 | `9c8241f6a2ee5f51` | `88` | `hold_for_terminal_neighborhood_context` | `accept_for_selector_experiment` | 2.070 m | 0.122 | 70.140 m | True | +38.890 m | Add richer route, heading, or map-neighborhood context before promotion. |
| 45 | `fe4a6425278fbd5b` | `816` | `hold_for_terminal_neighborhood_context` | `accept_for_selector_experiment` | 0.988 m | 0.984 | 48.036 m | True | +37.105 m | Add richer route, heading, or map-neighborhood context before promotion. |

## Promote Queue

- `2f366a31ab03f8b` track `1061`: choose alternate lane `220` with +125.481 m replay gain and 228.779 m route extension.
- `8abe59aee39f351e` track `4650`: choose alternate lane `143` with +16.623 m replay gain and 81.794 m route extension.

## Hold Queue

- `74a5b3325a534a87` track `3178`: `hold_for_terminal_neighborhood_context` because selected_heading_below_gate, alternate_heading_below_gate. Replay label: `hold_recovery_regressed`.
- `28f34edeb361e955` track `987`: `hold_for_terminal_neighborhood_context` because alternate_heading_below_gate. Replay label: `accept_for_selector_experiment`.
- `634b468a246a77d6` track `116`: `hold_for_terminal_neighborhood_context` because alternate_heading_below_gate, route_extension_below_gate. Replay label: `hold_recovery_regressed`.
- `9c8241f6a2ee5f51` track `88`: `hold_for_terminal_neighborhood_context` because selected_heading_below_gate, alternate_heading_below_gate. Replay label: `accept_for_selector_experiment`.
- `fe4a6425278fbd5b` track `816`: `hold_for_terminal_neighborhood_context` because route_extension_below_gate. Replay label: `accept_for_selector_experiment`.

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

## `28f34edeb361e955` / track `987`

- Source: `validation.tfrecord-00009-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: False
- Selected chain: 158
- Alternate chain: 157 -> 156 -> 162
- Selector-selected chain: 158
- Hold flags: alternate_heading_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 4.719 m | <= 5.000 m |
| Selected heading alignment | True | 0.997 | >= 0.95 |
| Alternate heading alignment | False | 0.886 | >= 0.95 |
| Route extension | True | 56.882 m | >= 50.000 m |
| Chain extension | True | True | true |

## `634b468a246a77d6` / track `116`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **hold_recovery_regressed**
- Selector matched replay gate: True
- Selected chain: 99
- Alternate chain: 85 -> 89
- Selector-selected chain: 99
- Hold flags: alternate_heading_below_gate, route_extension_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 0.269 m | <= 5.000 m |
| Selected heading alignment | True | 0.999 | >= 0.95 |
| Alternate heading alignment | False | 0.823 | >= 0.95 |
| Route extension | False | 32.514 m | >= 50.000 m |
| Chain extension | True | True | true |

## `8abe59aee39f351e` / track `4650`

- Source: `validation.tfrecord-00010-of-00150`
- Selector label: **promote_terminal_neighborhood_alternate**
- Selector reason: The nearby alternate lane is close, heading-aligned, route-extending, and chain-extending under the bounded selector policy.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: True
- Selected chain: 161
- Alternate chain: 143 -> 174
- Selector-selected chain: 143 -> 174
- Hold flags: none

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 4.426 m | <= 5.000 m |
| Selected heading alignment | True | 0.999 | >= 0.95 |
| Alternate heading alignment | True | 0.999 | >= 0.95 |
| Route extension | True | 81.794 m | >= 50.000 m |
| Chain extension | True | True | true |

## `9c8241f6a2ee5f51` / track `88`

- Source: `validation.tfrecord-00008-of-00150`
- Selector label: **hold_for_terminal_neighborhood_context**
- Selector reason: The nearby alternate lane does not clear every bounded selector check, so it stays held for context before broader rollout.
- Replay-gate label: **accept_for_selector_experiment**
- Selector matched replay gate: False
- Selected chain: 223
- Alternate chain: 237 -> 234 -> 130
- Selector-selected chain: 223
- Hold flags: selected_heading_below_gate, alternate_heading_below_gate

Selector checks:

| Check | Passed | Value | Gate |
| --- | --- | ---: | ---: |
| Alternate distance | True | 2.070 m | <= 5.000 m |
| Selected heading alignment | False | 0.122 | >= 0.95 |
| Alternate heading alignment | False | 0.741 | >= 0.95 |
| Route extension | True | 70.140 m | >= 50.000 m |
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

## Interpretation

- Selector promotions are bounded experiment candidates, not default behavior.
- Replay-gate labels validate the selector after the policy decision; they are not used as selector inputs.
- Held cases remain useful because they show which local geometry cues prevent over-promotion.
- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.
