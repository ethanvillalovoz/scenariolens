# ScenarioLens Terminal-Neighborhood Replay Gate

This report follows the terminal-neighborhood audit by force-replaying the proposed nearby lane alternatives against their selected terminal lanes. The goal is to decide whether each alternate lane is ready for broader selector experiments or should stay held as diagnostic evidence.

The replay is intentionally narrow: it does not change the default ScenarioLens scorer, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit_200/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit_200/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_200/manifest.json`
- Ready: True
- Max scenarios per source: 50
- Max lane-link hops: 2
- Selected candidates: 7
- Minimum stable gain: 1.000 m
- Acceptance gate: Accept a terminal-neighborhood recovery candidate only when the forced alternate lane improves selected-lane FDE by at least 1.0 m nominally and every valid perturbation preserves the alternate chain with the same minimum gain.
- Raw scenario data committed: no
- Raw map geometry published: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 7 |
| Replayed cases | 7 |
| Accepted recovery candidates | 5 |
| Held candidates | 2 |
| Nominal improvement cases | 5 |
| Nominal regression cases | 2 |
| Perturbation trials | 28 |
| Chain-preserving trials | 28 |
| Stable-gain trials | 20 |
| Mean nominal gain | +30.404 m |
| Mean perturbed gain | +29.793 m |
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
| 31 | `2f366a31ab03f8b` | `1061` | 219 | 220 -> 210 | 133.872 m | 8.391 m | +125.481 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 34 | `74a5b3325a534a87` | `3178` | 333 | 331 -> 205 | 88.934 m | 104.097 m | -15.163 m | 0/4 | `hold_recovery_regressed` | Do not promote this alternate; inspect selected-lane quality and local topology manually. |
| 35 | `28f34edeb361e955` | `987` | 158 | 157 -> 156 -> 162 | 62.626 m | 36.507 m | +26.119 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 36 | `634b468a246a77d6` | `116` | 99 | 85 -> 89 | 56.572 m | 72.802 m | -16.230 m | 0/4 | `hold_recovery_regressed` | Do not promote this alternate; inspect selected-lane quality and local topology manually. |
| 41 | `8abe59aee39f351e` | `4650` | 161 | 143 -> 174 | 49.177 m | 32.554 m | +16.623 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 42 | `9c8241f6a2ee5f51` | `88` | 223 | 237 -> 234 -> 130 | 48.172 m | 9.282 m | +38.890 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 45 | `fe4a6425278fbd5b` | `816` | 155 | 344 -> 346 -> 353 | 41.649 m | 4.544 m | +37.105 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |

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

## `28f34edeb361e955` / track `987`

- Source: `validation.tfrecord-00009-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `158`
- Alternate feature: `157`
- Selected chain: 158
- Alternate chain: 157 -> 156 -> 162
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `linked_lane_chain` / 2
- Selected/alternate lane distance: 3.490 m / 4.719 m
- Selected/alternate heading alignment: 0.997 / 0.886
- Selected/alternate route remaining: 32.851 m / 89.733 m
- Selected/alternate FDE: 62.626 m / 36.507 m
- Nominal gain: +26.119 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: +20.340 m / +26.119 m / +31.899 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 158 | 157 -> 156 -> 162 | +20.340 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 158 | 157 -> 156 -> 162 | +31.899 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 158 | 157 -> 156 -> 162 | +26.119 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 158 | 157 -> 156 -> 162 | +26.119 m | True | True | `stable_recovery` |

## `634b468a246a77d6` / track `116`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **hold_recovery_regressed**
- Reason: The alternate lane does not beat the selected terminal-lane replay on this open-loop check.
- Recommended next action: Do not promote this alternate; inspect selected-lane quality and local topology manually.
- Selected feature: `99`
- Alternate feature: `85`
- Selected chain: 99
- Alternate chain: 85 -> 89
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `no_exit_lanes` / 1
- Selected/alternate lane distance: 0.237 m / 0.269 m
- Selected/alternate heading alignment: 0.999 / 0.823
- Selected/alternate route remaining: 16.502 m / 49.016 m
- Selected/alternate FDE: 56.572 m / 72.802 m
- Nominal gain: -16.230 m
- Stable trials: 0/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: -16.230 m / -16.230 m / -16.230 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 99 | 85 -> 89 | -16.230 m | True | False | `alternate_regressed` |
| `speed_plus_10pct` | 99 | 85 -> 89 | -16.230 m | True | False | `alternate_regressed` |
| `heading_left_5deg` | 99 | 85 -> 89 | -16.230 m | True | False | `alternate_regressed` |
| `heading_right_5deg` | 99 | 85 -> 89 | -16.230 m | True | False | `alternate_regressed` |

## `8abe59aee39f351e` / track `4650`

- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `161`
- Alternate feature: `143`
- Selected chain: 161
- Alternate chain: 143 -> 174
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `no_exit_lanes` / 1
- Selected/alternate lane distance: 2.337 m / 4.426 m
- Selected/alternate heading alignment: 0.999 / 0.999
- Selected/alternate route remaining: 4.367 m / 86.161 m
- Selected/alternate FDE: 49.177 m / 32.554 m
- Nominal gain: +16.623 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: +14.789 m / +16.688 m / +18.715 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 161 | 143 -> 174 | +14.789 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 161 | 143 -> 174 | +18.715 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 161 | 143 -> 174 | +16.623 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 161 | 143 -> 174 | +16.623 m | True | True | `stable_recovery` |

## `9c8241f6a2ee5f51` / track `88`

- Source: `validation.tfrecord-00008-of-00150`
- Ready: True
- Decision: **accept_for_selector_experiment**
- Reason: The alternate lane beats the selected terminal lane nominally and under every deterministic perturbation.
- Recommended next action: Promote this alternate-lane recovery into the next bounded selector experiment.
- Selected feature: `223`
- Alternate feature: `237`
- Selected chain: 223
- Alternate chain: 237 -> 234 -> 130
- Selected route status/count: `no_exit_lanes` / 0
- Alternate route status/count: `linked_lane_chain` / 2
- Selected/alternate lane distance: 0.805 m / 2.070 m
- Selected/alternate heading alignment: 0.122 / 0.741
- Selected/alternate route remaining: 24.718 m / 94.858 m
- Selected/alternate FDE: 48.172 m / 9.282 m
- Nominal gain: +38.890 m
- Stable trials: 4/4
- Chain-preserving trials: 4/4
- Worst trial: `speed_minus_10pct`
- Min/mean/max perturbed gain: +35.260 m / +38.862 m / +42.410 m

Perturbation trials:

| Trial | Selected chain | Alternate chain | Gain | Chain preserved | Stable gain | Verdict |
| --- | --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 223 | 237 -> 234 -> 130 | +35.260 m | True | True | `stable_recovery` |
| `speed_plus_10pct` | 223 | 237 -> 234 -> 130 | +42.410 m | True | True | `stable_recovery` |
| `heading_left_5deg` | 223 | 237 -> 234 -> 130 | +38.890 m | True | True | `stable_recovery` |
| `heading_right_5deg` | 223 | 237 -> 234 -> 130 | +38.890 m | True | True | `stable_recovery` |

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

## Interpretation

- Accepted recovery candidates are not default behavior; they are next-pass selector candidates with replay evidence.
- Held candidates remain useful: they explain why a nearby lane looked plausible in topology but was not robust enough under open-loop replay.
- The gate requires both chain preservation and a positive FDE margin under deterministic speed and heading perturbations.
- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.
