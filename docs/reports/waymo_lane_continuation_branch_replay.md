# ScenarioLens Motion-Context Branch Replay Diagnostic

This report takes the non-oracle `motion_context` branch selector from the lane-continuation branch sweep and replays the selected branch under deterministic anchor-velocity perturbations. The goal is to check whether the selector's branch choice and positive FDE gain are stable when the anchor state is nudged.

It also reports an experimental `history_speed_prior` candidate for the same selected branch. That candidate blends anchor speed with recent target speed during replay scoring only; it does not change the branch selector, the default baseline, or the public performance claims.

The replay still uses open-loop ground-truth future states for scoring. It is a diagnostic stability check, not a route planner, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim.

## Scope

- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Ready for branch replay: True
- Motion-context cases selected: 2
- Perturbations per case: 4
- Minimum stable gain: 1.000 m
- Acceptance gate: Accept a motion-context branch for broader selector rollout only when every valid perturbation preserves the selected branch and keeps recoverable FDE above 1.0 m.
- Experimental candidate: The history-speed-prior candidate is an experimental replay score only: it blends anchor speed with recent target speed and does not change the branch selector or default ScenarioLens metrics.
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
| Accepted branch cases | 1 |
| Route-context follow-up cases | 1 |
| Selector-stability follow-up cases | 0 |
| History speed-prior accepted cases | 1 |
| Margin follow-ups resolved by speed prior | 0 |
| History speed-prior stable positive trials | 7 |
| Route-context margin diagnostics | 1 |
| Speed-minus margin diagnostics | 1 |
| Speed-prior unresolved margin cases | 1 |
| Mean nominal recoverable FDE | +20.534 m |
| Mean perturbed recoverable FDE | +19.883 m |
| Min perturbed recoverable FDE | +0.557 m |
| Max perturbed recoverable FDE | +37.766 m |
| Min robustness margin | -0.443 m |
| Mean robustness margin | +15.572 m |
| History speed-prior min margin | -3.099 m |
| History speed-prior mean margin | +14.245 m |

## Perturbations

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Case Results

| Rank | Scenario | Track | Default chain | Motion-context chain | Nominal gain | Stable trials | Margin | Speed-prior margin | Acceptance | Route context | Stability |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | `260785192cf6c991` | `1754` | 235 -> 241 -> 315 | 235 -> 307 -> 306 | +37.766 m | 4/4 | +31.588 m | +31.588 m | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | `stable_motion_context_branch` |
| 4 | `5c49e681a66c720` | `2627` | 285 -> 120 -> 119 | 285 -> 286 -> 287 | +3.301 m | 3/4 | -0.443 m | -3.099 m | `needs_route_context_margin` | `speed_minus_route_context_margin` | `branch_stable_gain_sensitive` |

## Route-Context Margin Diagnostics

| Rank | Scenario | Track | Diagnostic | Priority | Worst trial | Gap to gate | Oracle match | Speed-prior resolved | First next action |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| 1 | `260785192cf6c991` | `1754` | `accepted_no_route_context_followup` | 0.00 | `speed_minus_10pct` | 0.000 m | True | False | Broaden the branch replay queue with the same acceptance gate. |
| 4 | `5c49e681a66c720` | `2627` | `speed_minus_route_context_margin` | 5.18 | `speed_minus_10pct` | +0.443 m | True | False | Add route-context features that can explain reduced-speed branch intent. |

## `260785192cf6c991` / track `1754`

- Diagnosis source: `route_horizon_limit`
- Source: `validation.tfrecord-00009-of-00150`
- Ready: True
- Stability: **stable_motion_context_branch**
- Acceptance: **accepted_for_selector_rollout**
- History speed-prior acceptance: **accepted_for_selector_rollout**
- Route-context diagnostic: **accepted_no_route_context_followup**
- Why it matters: The motion-context branch passes the acceptance gate, making it ready for broader selector evaluation.
- Acceptance reason: All perturbations preserved the motion-context branch and kept recoverable FDE above the acceptance threshold.
- Recommended next action: Evaluate this selector behavior on a broader branchable continuation queue.
- Speed-prior reason: All perturbations preserved the history speed-prior branch and kept recoverable FDE above the acceptance threshold.
- Speed-prior next action: Evaluate this selector behavior on a broader branchable continuation queue.
- Route-context hypothesis: The branch already clears the replay gate; use it as a broader selector-evaluation candidate.
- Route-context priority: 0.00
- Default linked-route FDE: 81.112 m
- Motion-context route FDE: 43.346 m
- History speed-prior route FDE: 43.346 m
- Nominal recoverable FDE: +37.766 m
- Nominal history speed-prior recoverable FDE: +37.766 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 4/4
- Stable positive trials: 4/4
- Worst perturbation: `speed_minus_10pct`
- Robustness margin: +31.588 m
- History speed-prior stable positive trials: 4/4
- History speed-prior worst perturbation: `speed_minus_10pct`
- History speed-prior robustness margin: +31.588 m
- Selected route matches diagnostic oracle: True
- Selected vs default route context: route fit +0.077, endpoint alignment -0.001, downstream speed-limit drop 0.000, remaining route -37.679 m

Route-context next actions:

- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Speed-prior gain | Branch preserved | Positive gain | Speed-prior positive | Verdict |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| `speed_minus_10pct` | 235 -> 307 -> 306 | +32.588 m | +32.588 m | True | True | True | `stable_positive_motion_context_branch` |
| `speed_plus_10pct` | 235 -> 307 -> 306 | +37.766 m | +37.766 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 235 -> 307 -> 306 | +37.766 m | +37.766 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 235 -> 307 -> 306 | +37.766 m | +37.766 m | True | True | True | `stable_positive_motion_context_branch` |

## `5c49e681a66c720` / track `2627`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Stability: **branch_stable_gain_sensitive**
- Acceptance: **needs_route_context_margin**
- History speed-prior acceptance: **needs_route_context_margin**
- Route-context diagnostic: **speed_minus_route_context_margin**
- Why it matters: The branch choice is stable, but the gain margin is too thin under at least one perturbation.
- Acceptance reason: The selected branch is stable, but at least one perturbation falls below the recoverable-FDE threshold.
- Recommended next action: Add richer route context or speed-prior calibration before treating this branch as robust.
- Speed-prior reason: The selected branch is stable, but the history speed-prior candidate still falls below the recoverable-FDE threshold.
- Speed-prior next action: Add richer route context before treating this branch as robust.
- Route-context hypothesis: The selected branch is stable and matches the diagnostic oracle, but reduced anchor speed erases the gain margin. Add richer route-context evidence before treating this branch as robust.
- Route-context priority: 5.18
- Default linked-route FDE: 38.598 m
- Motion-context route FDE: 35.297 m
- History speed-prior route FDE: 36.060 m
- Nominal recoverable FDE: +3.301 m
- Nominal history speed-prior recoverable FDE: +2.538 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 3/4
- Stable positive trials: 3/4
- Worst perturbation: `speed_minus_10pct`
- Robustness margin: -0.443 m
- History speed-prior stable positive trials: 3/4
- History speed-prior worst perturbation: `speed_minus_10pct`
- History speed-prior robustness margin: -3.099 m
- Selected route matches diagnostic oracle: True
- Selected vs default route context: route fit +0.200, endpoint alignment -0.234, downstream speed-limit drop +0.286, remaining route -12.219 m

Route-context next actions:

- Add route-context features that can explain reduced-speed branch intent.
- Test turn-lane, downstream topology, and traffic-control context before selector rollout.
- Keep the speed-prior ablation as negative evidence, not a promoted default.

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Speed-prior gain | Branch preserved | Positive gain | Speed-prior positive | Verdict |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| `speed_minus_10pct` | 285 -> 286 -> 287 | +0.557 m | -2.099 m | True | False | False | `branch_preserved_gain_sensitive` |
| `speed_plus_10pct` | 285 -> 286 -> 287 | +6.023 m | +7.010 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 285 -> 286 -> 287 | +3.301 m | +2.538 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 285 -> 286 -> 287 | +3.301 m | +2.538 m | True | True | True | `stable_positive_motion_context_branch` |

## Interpretation

- Stable motion-context cases preserve the selected branch and keep positive recoverable FDE across all deterministic perturbations.
- Accepted branch cases pass the stricter rollout gate: branch preservation plus at least 1.0 m recoverable FDE in every valid perturbation trial.
- History speed-prior accepted cases show whether a simple non-oracle speed calibration would clear the same replay gate; they are candidates for the next selector experiment, not a new default metric.
- Route-context margin diagnostics identify stable branch choices whose gains are too thin for rollout and name the route features that should be tested before promoting the selector.
- Sensitive cases are still useful: they identify where a hand-built selector needs richer route context or a learned candidate scorer.
- The oracle upper bound from the branch-selection report remains a diagnostic ceiling only; this replay does not use oracle futures to choose a branch.
- Public outputs stay aggregate and case-summary oriented; raw Waymo TFRecords and local packets remain ignored.
