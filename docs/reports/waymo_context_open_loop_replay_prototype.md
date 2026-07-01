# ScenarioLens Context Open-Loop Replay Prototype

This report executes the replay-ready portion of the context replay queue. It reloads selected context-evaluation seeds from local Waymo Motion shards, replays constant-velocity and lane-aware open-loop rollouts from the same anchor state, and applies small deterministic anchor-velocity perturbations to test whether each context-derived diagnostic remains stable.

It is intentionally scoped: this is not a closed-loop simulator, not Waymax/JAX execution, and not a Waymo benchmark claim. Raw Waymo files and local per-case replay packets stay out of git.

## Scope

- Candidate manifest: `data/processed/waymo_context_replay_candidates/manifest.json`
- Source kind: `context_eval_set`
- Debug manifest: `data/processed/waymo_context_eval_debug_casebook/manifest.json`
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
| Replayed targets | 9 |
| Perturbation trials | 8 |
| Sign-preserving trials | 7 |
| Sign-preservation rate | 87.5% |
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
| 1 | `ef4c5d0e40fdea48` | Context eval seed 5 | `ready_for_regression_replay` | 1 | 46.688 m | 110.266 m | -63.578 m | 4/4 | 8.027 m |
| 2 | `7fc449ae179c29ac` | Context eval seed 2 | `ready_for_improvement_replay` | 8 | 46.985 m | 45.303 m | +1.682 m | 3/4 | 1.808 m |

## `ef4c5d0e40fdea48`

- Case: Context eval seed 5
- Source: `validation.tfrecord-00008-of-00150`
- Readiness: `ready_for_regression_replay`
- Why replayed: Regression candidate: replay checks whether the lane-aware warning persists under small anchor-state perturbations.
- Nominal winner: constant_velocity
- Nominal FDE delta: -63.578 m
- Perturbation stability label: `stable_regression_warning`
- Sign-preservation rate: 100.0%
- Local replay packet: `data/processed/waymo_context_replay_prototype/cases/1-context-eval-seed-5-ef4c5d0e40fdea48/replay_packet.json`
- Local SVG overlay: `data/processed/waymo_context_replay_prototype/cases/1-context-eval-seed-5-ef4c5d0e40fdea48/nominal_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `755` | `vehicle` | 46.688 m | 110.266 m | -63.578 m | True | `none` |

Perturbation trials:

| Trial | FDE delta | Preserves expected sign | CV FDE | Lane FDE |
| --- | ---: | --- | ---: | ---: |
| `speed_minus_10pct` | -55.551 m | True | 54.715 m | 110.266 m |
| `speed_plus_10pct` | -71.604 m | True | 38.662 m | 110.266 m |
| `heading_left_5deg` | -62.814 m | True | 47.452 m | 110.266 m |
| `heading_right_5deg` | -62.695 m | True | 47.571 m | 110.266 m |

## `7fc449ae179c29ac`

- Case: Context eval seed 2
- Source: `validation.tfrecord-00007-of-00150`
- Readiness: `ready_for_improvement_replay`
- Why replayed: Improvement candidate: replay checks whether the map-conditioned advantage survives small anchor-state perturbations.
- Nominal winner: lane_aware
- Nominal FDE delta: +1.682 m
- Perturbation stability label: `sensitive_to_anchor_perturbation`
- Sign-preservation rate: 75.0%
- Local replay packet: `data/processed/waymo_context_replay_prototype/cases/2-context-eval-seed-2-7fc449ae179c29ac/replay_packet.json`
- Local SVG overlay: `data/processed/waymo_context_replay_prototype/cases/2-context-eval-seed-2-7fc449ae179c29ac/nominal_replay.svg`

Target replay rows:

| Track | Type | CV FDE | Lane FDE | Delta | Map used | Fallback |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `1238` | `vehicle` | 45.440 m | 21.410 m | +24.030 m | True | `none` |
| `1239` | `vehicle` | 42.521 m | 30.540 m | +11.981 m | True | `none` |
| `1230` | `vehicle` | 64.155 m | 86.709 m | -22.554 m | True | `none` |
| `1221` | `vehicle` | 60.743 m | 60.743 m | 0.000 m | False | `target_too_far_from_lane` |
| `1220` | `vehicle` | 50.094 m | 50.094 m | 0.000 m | False | `target_too_far_from_lane` |
| `1256` | `vehicle` | 36.073 m | 36.073 m | 0.000 m | False | `target_too_far_from_lane` |
| `1225` | `vehicle` | 51.355 m | 51.355 m | 0.000 m | False | `target_too_far_from_lane` |
| `1233` | `vehicle` | 25.496 m | 25.496 m | 0.000 m | False | `target_too_far_from_lane` |

Perturbation trials:

| Trial | FDE delta | Preserves expected sign | CV FDE | Lane FDE |
| --- | ---: | --- | ---: | ---: |
| `speed_minus_10pct` | +1.045 m | True | 45.833 m | 44.788 m |
| `speed_plus_10pct` | +2.546 m | True | 48.652 m | 46.106 m |
| `heading_left_5deg` | -0.126 m | False | 42.976 m | 43.102 m |
| `heading_right_5deg` | +3.480 m | True | 51.003 m | 47.523 m |

## Interpretation

- Stable improvement candidates are useful positive controls for the lane-aware baseline.
- Stable regression candidates are useful debugging targets because the warning persists under small anchor-state changes.
- Sensitive candidates are still valuable: they identify cases where evaluation conclusions depend on small state-estimation differences.
- Context-derived candidates keep their eval-set seed labels so signal, topology, regression, and fallback follow-up does not collapse into one aggregate score.
- Fallback-heavy candidates remain outside this replay prototype until map matching and coordinate-frame checks are resolved.
- This is open-loop diagnostic evidence, not a production prediction model or closed-loop autonomy simulator.
