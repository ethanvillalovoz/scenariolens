# ScenarioLens Motion-Context Branch Replay Diagnostic

This report takes the non-oracle `motion_context` branch selector from the lane-continuation branch sweep and replays the selected branch under deterministic anchor-velocity perturbations. The goal is to check whether the selector's branch choice and positive FDE gain are stable when the anchor state is nudged.

The replay still uses open-loop ground-truth future states for scoring. It is a diagnostic stability check, not a route planner, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim.

## Scope

- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Ready for branch replay: True
- Motion-context cases selected: 2
- Perturbations per case: 4
- Minimum stable gain: 1.000 m
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Replay Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 2 |
| Replayed cases | 2 |
| Perturbation trials | 8 |
| Stable motion-context cases | 1 |
| Sensitive motion-context cases | 1 |
| Branch-preserving trials | 8 |
| Positive-gain trials | 7 |
| Stable positive trials | 7 |
| Mean nominal recoverable FDE | +20.534 m |
| Mean perturbed recoverable FDE | +19.883 m |
| Min perturbed recoverable FDE | +0.557 m |
| Max perturbed recoverable FDE | +37.766 m |

## Perturbations

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Case Results

| Rank | Scenario | Track | Default chain | Motion-context chain | Nominal gain | Stable trials | Trial gain range | Stability |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `260785192cf6c991` | `1754` | 235 -> 241 -> 315 | 235 -> 307 -> 306 | +37.766 m | 4/4 | +32.588 m to +37.766 m | `stable_motion_context_branch` |
| 4 | `5c49e681a66c720` | `2627` | 285 -> 120 -> 119 | 285 -> 286 -> 287 | +3.301 m | 3/4 | +0.557 m to +6.023 m | `branch_stable_gain_sensitive` |

## `260785192cf6c991` / track `1754`

- Diagnosis source: `route_horizon_limit`
- Source: `validation.tfrecord-00009-of-00150`
- Ready: True
- Stability: **stable_motion_context_branch**
- Why it matters: The non-oracle branch choice stayed on the same parsed route and kept positive recoverable FDE under all deterministic perturbations.
- Default linked-route FDE: 81.112 m
- Motion-context route FDE: 43.346 m
- Nominal recoverable FDE: +37.766 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 4/4
- Stable positive trials: 4/4

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Branch preserved | Positive gain | Verdict |
| --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 235 -> 307 -> 306 | +32.588 m | True | True | `stable_positive_motion_context_branch` |
| `speed_plus_10pct` | 235 -> 307 -> 306 | +37.766 m | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 235 -> 307 -> 306 | +37.766 m | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 235 -> 307 -> 306 | +37.766 m | True | True | `stable_positive_motion_context_branch` |

## `5c49e681a66c720` / track `2627`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Stability: **branch_stable_gain_sensitive**
- Why it matters: The motion-context prior stayed on the same parsed branch, but its recoverable FDE became sensitive to anchor perturbations.
- Default linked-route FDE: 38.598 m
- Motion-context route FDE: 35.297 m
- Nominal recoverable FDE: +3.301 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 3/4
- Stable positive trials: 3/4

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Branch preserved | Positive gain | Verdict |
| --- | --- | ---: | --- | --- | --- |
| `speed_minus_10pct` | 285 -> 286 -> 287 | +0.557 m | True | False | `branch_preserved_gain_sensitive` |
| `speed_plus_10pct` | 285 -> 286 -> 287 | +6.023 m | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 285 -> 286 -> 287 | +3.301 m | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 285 -> 286 -> 287 | +3.301 m | True | True | `stable_positive_motion_context_branch` |

## Interpretation

- Stable motion-context cases preserve the selected branch and keep positive recoverable FDE across all deterministic perturbations.
- Sensitive cases are still useful: they identify where a hand-built selector needs richer route context or a learned candidate scorer.
- The oracle upper bound from the branch-selection report remains a diagnostic ceiling only; this replay does not use oracle futures to choose a branch.
- Public outputs stay aggregate and case-summary oriented; raw Waymo TFRecords and local packets remain ignored.
