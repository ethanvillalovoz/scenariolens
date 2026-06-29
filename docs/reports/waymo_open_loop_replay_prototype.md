# ScenarioLens Open-Loop Replay Prototype

This report takes the replay-candidate queue one step further: it reloads selected local Waymo Motion scenarios, replays the constant-velocity and lane-aware open-loop rollouts from the same anchor state, and applies small deterministic anchor-velocity perturbations to test whether each diagnostic remains stable.

It is intentionally scoped: this is not a closed-loop simulator, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local per-case replay packets stay out of git.

## Scope

- Candidate manifest: `data/processed/waymo_replay_candidates/manifest.json`
- Debug manifest: `data/processed/waymo_lane_aware_debug_casebook/manifest.json`
- Ready for replay analysis: True
- Requested top candidates: 2
- Replay cases evaluated: 2
- Perturbations per case: 4
- Raw Waymo files committed: no
- Local replay packets and SVG overlays committed: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Replayed cases | 2 |
| Replayed targets | 4 |
| Perturbation trials | 8 |
| Sign-preserving trials | 8 |
| Sign-preservation rate | 100.0% |
| Regression cases replayed | 1 |
| Improvement cases replayed | 1 |

## Perturbation Set

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Replayed Candidates

| Rank | Scenario | Case | Readiness | Targets | CV FDE | Lane FDE | FDE delta | Sign stability | Max delta swing |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `fc8c647623f81bb4` | Largest regression | `ready_for_regression_replay` | 1 | 3.152 m | 144.514 m | -141.362 m | 4/4 | 16.040 m |
| 2 | `b2b7c2ad7bcd134b` | Largest improvement | `ready_for_improvement_replay` | 3 | 55.051 m | 40.900 m | +14.151 m | 4/4 | 2.784 m |

## `fc8c647623f81bb4`

- Case: Largest regression
- Source: `validation.tfrecord-00009-of-00150`
- Readiness: `ready_for_regression_replay`
- Why replayed: Regression candidate: replay checks whether the lane-aware warning persists under small anchor-state perturbations.
- Nominal winner: constant_velocity
- Nominal FDE delta: -141.362 m
- Perturbation stability label: `stable_regression_warning`
- Sign-preservation rate: 100.0%
- Local replay packet: `data/processed/waymo_replay_prototype/cases/1-largest-regression-fc8c647623f81bb4/replay_packet.json`
- Local SVG overlay: `data/processed/waymo_replay_prototype/cases/1-largest-regression-fc8c647623f81bb4/nominal_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `1466` | `vehicle` | 3.152 m | 144.514 m | -141.362 m | True | `none` |

Perturbation trials:

| Trial | FDE delta | Preserves expected sign | CV FDE | Lane FDE |
| --- | ---: | --- | ---: | ---: |
| `speed_minus_10pct` | -131.607 m | True | 12.907 m | 144.514 m |
| `speed_plus_10pct` | -125.322 m | True | 19.192 m | 144.514 m |
| `heading_left_5deg` | -130.063 m | True | 14.451 m | 144.514 m |
| `heading_right_5deg` | -130.537 m | True | 13.977 m | 144.514 m |

## `b2b7c2ad7bcd134b`

- Case: Largest improvement
- Source: `validation.tfrecord-00009-of-00150`
- Readiness: `ready_for_improvement_replay`
- Why replayed: Improvement candidate: replay checks whether the map-conditioned advantage survives small anchor-state perturbations.
- Nominal winner: lane_aware
- Nominal FDE delta: +14.151 m
- Perturbation stability label: `stable_positive_control`
- Sign-preservation rate: 100.0%
- Local replay packet: `data/processed/waymo_replay_prototype/cases/2-largest-improvement-b2b7c2ad7bcd134b/replay_packet.json`
- Local SVG overlay: `data/processed/waymo_replay_prototype/cases/2-largest-improvement-b2b7c2ad7bcd134b/nominal_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `4357` | `vehicle` | 44.237 m | 47.331 m | -3.094 m | True | `none` |
| `4365` | `vehicle` | 74.805 m | 46.831 m | +27.974 m | True | `none` |
| `4364` | `vehicle` | 46.111 m | 28.539 m | +17.572 m | True | `none` |

Perturbation trials:

| Trial | FDE delta | Preserves expected sign | CV FDE | Lane FDE |
| --- | ---: | --- | ---: | ---: |
| `speed_minus_10pct` | +11.637 m | True | 52.457 m | 40.820 m |
| `speed_plus_10pct` | +16.935 m | True | 57.915 m | 40.980 m |
| `heading_left_5deg` | +14.126 m | True | 55.026 m | 40.900 m |
| `heading_right_5deg` | +14.129 m | True | 55.029 m | 40.900 m |

## Interpretation

- Stable improvement candidates are useful positive controls for the lane-aware baseline.
- Stable regression candidates are useful debugging targets because the warning persists under small anchor-state changes.
- Sensitive candidates are still valuable: they identify cases where evaluation conclusions depend on small state-estimation differences.
- Fallback-heavy candidates remain outside this replay prototype until map matching and coordinate-frame checks are resolved.
- This is open-loop diagnostic evidence, not a production prediction model or closed-loop autonomy simulator.
