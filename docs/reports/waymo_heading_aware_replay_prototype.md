# ScenarioLens Heading-Aware Replay Prototype

This report executes the next laptop-safe step after the heading-aware replay candidate plan: it reloads selected local scenarios, replays nearest-lane and heading-aware open-loop rollouts from the same anchor state, and applies small deterministic anchor-velocity perturbations to check whether the selector win or regression is stable.

It is intentionally scoped: this is not a closed-loop simulator, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local per-case replay packets stay out of git.

## Scope

- Candidate manifest: `data/processed/waymo_heading_aware_replay_candidates/manifest.json`
- Debug manifest: `data/processed/waymo_heading_aware_debug_casebook/manifest.json`
- Ready for replay analysis: True
- Requested top candidates: 2
- Heading replay cases evaluated: 2
- Perturbations per case: 4
- Raw Waymo files committed: no
- Local replay packets and SVG overlays committed: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Replayed cases | 2 |
| Replayed targets | 15 |
| Perturbation trials | 8 |
| Sign-preserving trials | 8 |
| Sign-preservation rate | 100.0% |
| Heading improvement cases replayed | 1 |
| Heading regression cases replayed | 1 |
| Heading map-used targets | 7 |
| Heading fallback targets | 8 |

## Perturbation Set

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Replayed Candidates

| Rank | Scenario | Case | Readiness | Targets | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Sign stability | Max delta swing |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `d30e6448f14e4c75` | Largest heading improvement | `ready_for_heading_improvement_replay` | 8 | 27.509 m | 48.599 m | 36.443 m | +12.156 m | 4/4 | 2.292 m |
| 2 | `706fecd25045c8d` | Largest heading regression | `ready_for_heading_regression_replay` | 7 | 32.547 m | 31.232 m | 35.605 m | -4.373 m | 4/4 | 0.001 m |

## `d30e6448f14e4c75`

- Case: Largest heading improvement
- Source: `validation.tfrecord-00010-of-00150`
- Readiness: `ready_for_heading_improvement_replay`
- Why replayed: Heading improvement candidate: replay checks whether the heading-aware selector advantage survives small anchor-state perturbations.
- Nominal selector winner: heading_aware
- Heading vs nearest FDE delta: +12.156 m
- Heading vs constant-velocity FDE delta: -8.934 m
- Perturbation stability label: `stable`
- Sign-preservation rate: 100.0%
- Local replay packet: `data/processed/waymo_heading_aware_replay_prototype/cases/1-largest-heading-improvement-d30e6448f14e4c75/heading_replay_packet.json`
- Local SVG overlay: `data/processed/waymo_heading_aware_replay_prototype/cases/1-largest-heading-improvement-d30e6448f14e4c75/heading_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest map | Heading map | Heading fallback |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `201` | `vehicle` | 12.224 m | 61.338 m | 12.224 m | +49.114 m | True | False | `lane_heading_misaligned` |
| `205` | `vehicle` | 24.908 m | 24.908 m | 24.908 m | 0.000 m | False | False | `target_too_far_from_lane` |
| `195` | `vehicle` | 13.915 m | 62.053 m | 13.915 m | +48.138 m | True | False | `lane_heading_misaligned` |
| `150` | `vehicle` | 42.804 m | 28.584 m | 28.584 m | 0.000 m | True | True | `none` |
| `149` | `vehicle` | 35.931 m | 35.931 m | 35.931 m | 0.000 m | False | False | `target_too_far_from_lane` |
| `155` | `vehicle` | 32.745 m | 83.171 m | 83.171 m | 0.000 m | True | True | `none` |
| `164` | `vehicle` | 30.705 m | 65.970 m | 65.970 m | 0.000 m | True | True | `none` |
| `148` | `vehicle` | 26.838 m | 26.838 m | 26.838 m | 0.000 m | False | False | `target_too_far_from_lane` |

Perturbation trials:

| Trial | Heading vs nearest | Preserves expected sign | CV FDE | Nearest FDE | Heading FDE |
| --- | ---: | --- | ---: | ---: | ---: |
| `speed_minus_10pct` | +11.142 m | True | 30.205 m | 49.800 m | 38.658 m |
| `speed_plus_10pct` | +13.162 m | True | 24.863 m | 47.402 m | 34.240 m |
| `heading_left_5deg` | +11.871 m | True | 28.144 m | 48.636 m | 36.765 m |
| `heading_right_5deg` | +9.864 m | True | 27.786 m | 46.671 m | 36.807 m |

## `706fecd25045c8d`

- Case: Largest heading regression
- Source: `validation.tfrecord-00007-of-00150`
- Readiness: `ready_for_heading_regression_replay`
- Why replayed: Heading regression candidate: replay checks whether the nearest-lane vs heading-aware warning persists under small anchor-state perturbations.
- Nominal selector winner: nearest_lane
- Heading vs nearest FDE delta: -4.373 m
- Heading vs constant-velocity FDE delta: -3.058 m
- Perturbation stability label: `stable`
- Sign-preservation rate: 100.0%
- Local replay packet: `data/processed/waymo_heading_aware_replay_prototype/cases/2-largest-heading-regression-706fecd25045c8d/heading_replay_packet.json`
- Local SVG overlay: `data/processed/waymo_heading_aware_replay_prototype/cases/2-largest-heading-regression-706fecd25045c8d/heading_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Nearest FDE | Heading FDE | Heading vs nearest | Nearest map | Heading map | Heading fallback |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `1079` | `pedestrian` | 6.498 m | 6.498 m | 6.498 m | 0.000 m | False | False | `non_vehicle_or_cyclist_target` |
| `714` | `vehicle` | 60.406 m | 54.351 m | 84.959 m | -30.608 m | True | True | `none` |
| `708` | `vehicle` | 29.903 m | 19.639 m | 19.639 m | 0.000 m | True | True | `none` |
| `752` | `vehicle` | 31.210 m | 31.210 m | 31.210 m | 0.000 m | False | False | `target_too_far_from_lane` |
| `746` | `vehicle` | 37.353 m | 52.350 m | 52.350 m | 0.000 m | True | True | `none` |
| `738` | `vehicle` | 52.906 m | 45.026 m | 45.026 m | 0.000 m | True | True | `none` |
| `710` | `vehicle` | 9.550 m | 9.550 m | 9.550 m | 0.000 m | False | False | `target_too_far_from_lane` |

Perturbation trials:

| Trial | Heading vs nearest | Preserves expected sign | CV FDE | Nearest FDE | Heading FDE |
| --- | ---: | --- | ---: | ---: | ---: |
| `speed_minus_10pct` | -4.373 m | True | 30.118 m | 30.547 m | 34.920 m |
| `speed_plus_10pct` | -4.372 m | True | 35.255 m | 32.002 m | 36.374 m |
| `heading_left_5deg` | -4.373 m | True | 31.197 m | 31.532 m | 35.905 m |
| `heading_right_5deg` | -4.372 m | True | 34.045 m | 30.953 m | 35.325 m |

## Skipped Candidates

- `2f035a284480e981`: not_heading_replay_ready
- `7912ee9523cb6fd`: not_selected_due_to_top_limit
- `e3f6a29b59e42c1`: not_selected_due_to_top_limit
- `46c1c1fbe5ef29d1`: not_selected_due_to_top_limit

## Interpretation

- Stable heading-improvement cases are useful positive controls for the selector because the nearest-lane advantage survives small anchor-state perturbations.
- Stable heading-regression cases are useful debugging targets because the warning persists under small state-estimation differences.
- Sensitive cases are still useful: they show where selector conclusions depend on small changes in anchor velocity.
- Fallback-heavy cases remain outside this prototype until map matching, coordinate frames, and target eligibility are audited.
- This is open-loop diagnostic evidence, not a production prediction model or closed-loop autonomy simulator.
