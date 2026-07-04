# ScenarioLens Terminal-Neighborhood Replay Gate

This report follows the terminal-neighborhood audit by force-replaying the proposed nearby lane alternatives against their selected terminal lanes. The goal is to decide whether each alternate lane is ready for broader selector experiments or should stay held as diagnostic evidence.

The replay is intentionally narrow: it does not change the default ScenarioLens scorer, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_expanded/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_expanded/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json`
- Ready: True
- Max scenarios per source: 25
- Max lane-link hops: 2
- Selected candidates: 5
- Minimum stable gain: 1.000 m
- Acceptance gate: Accept a terminal-neighborhood recovery candidate only when the forced alternate lane improves selected-lane FDE by at least 1.0 m nominally and every valid perturbation preserves the alternate chain with the same minimum gain.
- Raw scenario data committed: no
- Raw map geometry published: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 5 |
| Replayed cases | 5 |
| Accepted recovery candidates | 3 |
| Held candidates | 2 |
| Nominal improvement cases | 3 |
| Nominal regression cases | 2 |
| Perturbation trials | 20 |
| Chain-preserving trials | 20 |
| Stable-gain trials | 12 |
| Mean nominal gain | +32.240 m |
| Mean perturbed gain | +31.378 m |
| Min perturbed gain | -18.328 m |
| Max perturbed gain | +125.481 m |

## Perturbations

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Gate Decisions

| Rank | Scenario | Track | Selected lane | Alternate lane | Selected FDE | Alternate FDE | Gain | Stable trials | Decision | First next action |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 21 | `2f366a31ab03f8b` | `1061` | 219 | 220 -> 210 | 133.872 m | 8.391 m | +125.481 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 22 | `74a5b3325a534a87` | `3178` | 333 | 331 -> 205 | 88.934 m | 104.097 m | -15.163 m | 0/4 | `hold_recovery_regressed` | Do not promote this alternate; inspect selected-lane quality and local topology manually. |
| 27 | `fe4a6425278fbd5b` | `816` | 155 | 344 -> 346 -> 353 | 41.649 m | 4.544 m | +37.105 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 28 | `2f035a284480e981` | `732` | 265 | 264 -> 262 -> 332 | 33.227 m | 10.362 m | +22.865 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 29 | `d30e6448f14e4c75` | `150` | 269 | 268 -> 265 -> 263 | 28.584 m | 37.671 m | -9.087 m | 0/4 | `hold_recovery_regressed` | Do not promote this alternate; inspect selected-lane quality and local topology manually. |

## `2f366a31ab03f8b` / track `1061`

- Source: `validation.tfrecord-00007-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `219`
- Alternate feature: `220`
- Selected chain: 219
- Alternate chain: 220 -> 210
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `no_exit_lanes` / 1
- Selected/alternate lane distance: 0.223 m / 3.534 m
- Selected/alternate heading alignment: 1.0 / 1.0
- Selected/alternate route remaining: 26.476 m / 255.255 m
- Selected/alternate FDE: 133.872 m / 8.391 m
- Nominal gain: +125.481 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_plus_10pct`
- Min/mean/max perturbed gain: +111.157 m / +120.713 m / +125.481 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 219 | 220 -> 210 | +120.734 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 219 | 220 -> 210 | +111.157 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 219 | 220 -> 210 | +125.481 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 219 | 220 -> 210 | +125.481 m | True | True | `stable_recovery` |

## `74a5b3325a534a87` / track `3178`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **hold_recovery_regressed**
- Reason: The alternate lane does not beat the selected terminal-lane replay on this open-loop check.
- Recommended next action: Do not promote this alternate; inspect selected-lane quality and local topology manually.
- Selected feature: `333`
- Alternate feature: `331`
- Selected chain: 333
- Alternate chain: 331 -> 205
- Selected route status/count: `no_entry_lanes` / 0
- Alternate route status/count: `no_entry_lanes` / 1
- Selected/alternate lane distance: 0.163 m / 2.533 m
- Selected/alternate heading alignment: 0.691 / 0.69
- Selected/alternate route remaining: 23.515 m / 95.966 m
- Selected/alternate FDE: 88.934 m / 104.097 m
- Nominal gain: -15.163 m
- Stable trials: 0/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_plus_10pct`
- Min/mean/max perturbed gain: -18.328 m / -15.230 m / -12.266 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 333 | 331 -> 205 | -12.266 m | True | False | `alternate_regressed` |
| `speed_plus_10pct` | 333 | 331 -> 205 | -18.328 m | True | False | `alternate_regressed` |
| `heading_left_5deg` | 333 | 331 -> 205 | -15.163 m | True | False | `alternate_regressed` |
| `heading_right_5deg` | 333 | 331 -> 205 | -15.163 m | True | False | `alternate_regressed` |

## `fe4a6425278fbd5b` / track `816`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `155`
- Alternate feature: `344`
- Selected chain: 155
- Alternate chain: 344 -> 346 -> 353
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `linked_lane_chain` / 2
- Selected/alternate lane distance: 0.284 m / 0.988 m
- Selected/alternate heading alignment: 0.997 / 0.984
- Selected/alternate route remaining: 14.029 m / 62.065 m
- Selected/alternate FDE: 41.649 m / 4.544 m
- Nominal gain: +37.105 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_plus_10pct`
- Min/mean/max perturbed gain: +37.105 m / +37.627 m / +39.192 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 155 | 344 -> 346 -> 353 | +39.192 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 155 | 344 -> 346 -> 353 | +37.105 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 155 | 344 -> 346 -> 353 | +37.105 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 155 | 344 -> 346 -> 353 | +37.105 m | True | True | `stable_recovery` |

## `2f035a284480e981` / track `732`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `265`
- Alternate feature: `264`
- Selected chain: 265
- Alternate chain: 264 -> 262 -> 332
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `linked_lane_chain` / 2
- Selected/alternate lane distance: 1.101 m / 1.659 m
- Selected/alternate heading alignment: 1.0 / 0.999
- Selected/alternate route remaining: 12.753 m / 55.364 m
- Selected/alternate FDE: 33.227 m / 10.362 m
- Nominal gain: +22.865 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: +22.865 m / +22.865 m / +22.865 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 265 | 264 -> 262 -> 332 | +22.865 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 265 | 264 -> 262 -> 332 | +22.865 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 265 | 264 -> 262 -> 332 | +22.865 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 265 | 264 -> 262 -> 332 | +22.865 m | True | True | `stable_recovery` |

## `d30e6448f14e4c75` / track `150`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **hold_recovery_regressed**
- Reason: The alternate lane does not beat the selected terminal-lane replay on this open-loop check.
- Recommended next action: Do not promote this alternate; inspect selected-lane quality and local topology manually.
- Selected feature: `269`
- Alternate feature: `268`
- Selected chain: 269
- Alternate chain: 268 -> 265 -> 263
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `linked_lane_chain` / 2
- Selected/alternate lane distance: 0.016 m / 2.509 m
- Selected/alternate heading alignment: 0.975 / 0.974
- Selected/alternate route remaining: 27.667 m / 44.088 m
- Selected/alternate FDE: 28.584 m / 37.671 m
- Nominal gain: -9.087 m
- Stable trials: 0/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: -9.087 m / -9.087 m / -9.087 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 269 | 268 -> 265 -> 263 | -9.087 m | True | False | `alternate_regressed` |
| `speed_plus_10pct` | 269 | 268 -> 265 -> 263 | -9.087 m | True | False | `alternate_regressed` |
| `heading_left_5deg` | 269 | 268 -> 265 -> 263 | -9.087 m | True | False | `alternate_regressed` |
| `heading_right_5deg` | 269 | 268 -> 265 -> 263 | -9.087 m | True | False | `alternate_regressed` |

## Interpretation

- Accepted recovery candidates are not default behavior; they are next-pass selector candidates with replay evidence.
- Held candidates remain useful: they explain why a nearby lane looked plausible in topology but was not robust enough under open-loop replay.
- The gate requires both chain preservation and a positive FDE margin under deterministic speed and heading perturbations.
- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.
