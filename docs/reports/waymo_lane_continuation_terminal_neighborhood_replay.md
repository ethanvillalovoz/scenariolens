# ScenarioLens Terminal-Neighborhood Replay Gate

This report follows the terminal-neighborhood audit by force-replaying the proposed nearby lane alternatives against their selected terminal lanes. The goal is to decide whether each alternate lane is ready for broader selector experiments or should stay held as diagnostic evidence.

The replay is intentionally narrow: it does not change the default ScenarioLens scorer, does not publish raw map geometry, and is not a Waymo benchmark claim.

## Scope

- Terminal-neighborhood manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_audit/manifest.json`
- Topology manifest: `data/processed/waymo_lane_continuation_topology_gap_audit/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Ready: True
- Max scenarios per source: 25
- Max lane-link hops: 2
- Selected candidates: 2
- Minimum stable gain: 1.000 m
- Acceptance gate: Accept a terminal-neighborhood recovery candidate only when the forced alternate lane improves selected-lane FDE by at least 1.0 m nominally and every valid perturbation preserves the alternate chain with the same minimum gain.
- Raw scenario data committed: no
- Raw map geometry published: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 2 |
| Replayed cases | 2 |
| Accepted recovery candidates | 1 |
| Held candidates | 1 |
| Nominal improvement cases | 1 |
| Nominal regression cases | 1 |
| Perturbation trials | 8 |
| Chain-preserving trials | 8 |
| Stable-gain trials | 4 |
| Mean nominal gain | +55.159 m |
| Mean perturbed gain | +52.742 m |
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
| 11 | `2f366a31ab03f8b` | `1061` | 219 | 220 -> 210 | 133.872 m | 8.391 m | +125.481 m | 4/4 | `accept_for_selector_experiment` | Promote this alternate-lane recovery into the next bounded selector experiment. |
| 12 | `74a5b3325a534a87` | `3178` | 333 | 331 -> 205 | 88.934 m | 104.097 m | -15.163 m | 0/4 | `hold_recovery_regressed` | Do not promote this alternate; inspect selected-lane quality and local topology manually. |

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

## Interpretation

- Accepted recovery candidates are not default behavior; they are next-pass selector candidates with replay evidence.
- Held candidates remain useful: they explain why a nearby lane looked plausible in topology but was not robust enough under open-loop replay.
- The gate requires both chain preservation and a positive FDE margin under deterministic speed and heading perturbations.
- Public outputs stay derived and aggregate; raw Waymo records and local per-case artifacts remain ignored.
