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
| Stable motion-context cases | 2 |
| Sensitive motion-context cases | 0 |
| Branch-preserving trials | 8 |
| Positive-gain trials | 8 |
| Stable positive trials | 8 |
| Accepted branch cases | 2 |
| Route-context follow-up cases | 0 |
| Selector-stability follow-up cases | 0 |
| History speed-prior accepted cases | 2 |
| Margin follow-ups resolved by speed prior | 0 |
| History speed-prior stable positive trials | 8 |
| Route-context margin diagnostics | 0 |
| Speed-minus margin diagnostics | 0 |
| Speed-prior unresolved margin cases | 0 |
| Mean nominal recoverable FDE | +40.301 m |
| Mean perturbed recoverable FDE | +39.819 m |
| Min perturbed recoverable FDE | +29.627 m |
| Max perturbed recoverable FDE | +52.054 m |
| Min robustness margin | +28.627 m |
| Mean robustness margin | +29.834 m |
| History speed-prior min margin | +28.627 m |
| History speed-prior mean margin | +31.523 m |

## Perturbations

- `speed_minus_10pct`: Anchor velocity magnitude reduced by 10%.
- `speed_plus_10pct`: Anchor velocity magnitude increased by 10%.
- `heading_left_5deg`: Anchor velocity heading rotated left by 5 degrees.
- `heading_right_5deg`: Anchor velocity heading rotated right by 5 degrees.

## Case Results

| Rank | Scenario | Track | Default chain | Motion-context chain | Nominal gain | Stable trials | Margin | Speed-prior margin | Acceptance | Route context | Stability |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | `260785192cf6c991` | `1754` | 235 -> 241 -> 315 -> 337 | 235 -> 307 -> 306 -> 314 | +40.840 m | 4/4 | +28.627 m | +28.627 m | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | `stable_motion_context_branch` |
| 3 | `d30709cd60e60395` | `164` | 603 -> 610 -> 371 -> 394 | 603 -> 609 -> 606 -> 597 | +39.762 m | 4/4 | +31.042 m | +34.418 m | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | `stable_motion_context_branch` |

## Route-Context Margin Diagnostics

| Rank | Scenario | Track | Diagnostic | Priority | Worst trial | Gap to gate | Oracle match | Speed-prior resolved | First next action |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | --- | --- |
| 1 | `260785192cf6c991` | `1754` | `accepted_no_route_context_followup` | 0.00 | `speed_minus_10pct` | 0.000 m | True | False | Broaden the branch replay queue with the same acceptance gate. |
| 3 | `d30709cd60e60395` | `164` | `accepted_no_route_context_followup` | 0.00 | `speed_minus_10pct` | 0.000 m | True | False | Broaden the branch replay queue with the same acceptance gate. |

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
- Default linked-route FDE: 87.147 m
- Motion-context route FDE: 46.307 m
- History speed-prior route FDE: 46.307 m
- Nominal recoverable FDE: +40.840 m
- Nominal history speed-prior recoverable FDE: +40.840 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 4/4
- Stable positive trials: 4/4
- Worst perturbation: `speed_minus_10pct`
- Robustness margin: +28.627 m
- History speed-prior stable positive trials: 4/4
- History speed-prior worst perturbation: `speed_minus_10pct`
- History speed-prior robustness margin: +28.627 m
- Selected route matches diagnostic oracle: True
- Selected vs default route context: route fit +0.493, endpoint alignment -0.010, downstream speed-limit drop 0.000, remaining route -55.283 m

Route-context next actions:

- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Speed-prior gain | Branch preserved | Positive gain | Speed-prior positive | Verdict |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| `speed_minus_10pct` | 235 -> 307 -> 306 -> 314 | +29.627 m | +29.627 m | True | True | True | `stable_positive_motion_context_branch` |
| `speed_plus_10pct` | 235 -> 307 -> 306 -> 314 | +52.054 m | +52.054 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 235 -> 307 -> 306 -> 314 | +40.840 m | +40.840 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 235 -> 307 -> 306 -> 314 | +40.840 m | +40.840 m | True | True | True | `stable_positive_motion_context_branch` |

## `d30709cd60e60395` / track `164`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00007-of-00150`
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
- Default linked-route FDE: 52.496 m
- Motion-context route FDE: 12.734 m
- History speed-prior route FDE: 12.341 m
- Nominal recoverable FDE: +39.762 m
- Nominal history speed-prior recoverable FDE: +40.155 m
- Branch-preserving trials: 4/4
- Positive-gain trials: 4/4
- Stable positive trials: 4/4
- Worst perturbation: `speed_minus_10pct`
- Robustness margin: +31.042 m
- History speed-prior stable positive trials: 4/4
- History speed-prior worst perturbation: `speed_minus_10pct`
- History speed-prior robustness margin: +34.418 m
- Selected route matches diagnostic oracle: True
- Selected vs default route context: route fit +0.578, endpoint alignment -0.236, downstream speed-limit drop 0.000, remaining route -43.858 m

Route-context next actions:

- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

Perturbation trials:

| Perturbation | Motion-context chain | Gain vs default | Speed-prior gain | Branch preserved | Positive gain | Speed-prior positive | Verdict |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| `speed_minus_10pct` | 603 -> 609 -> 606 -> 597 | +32.042 m | +35.418 m | True | True | True | `stable_positive_motion_context_branch` |
| `speed_plus_10pct` | 603 -> 609 -> 606 -> 597 | +43.627 m | +44.023 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_left_5deg` | 603 -> 609 -> 606 -> 597 | +39.762 m | +40.155 m | True | True | True | `stable_positive_motion_context_branch` |
| `heading_right_5deg` | 603 -> 609 -> 606 -> 597 | +39.762 m | +40.155 m | True | True | True | `stable_positive_motion_context_branch` |

## Interpretation

- Stable motion-context cases preserve the selected branch and keep positive recoverable FDE across all deterministic perturbations.
- Accepted branch cases pass the stricter rollout gate: branch preservation plus at least 1.0 m recoverable FDE in every valid perturbation trial.
- History speed-prior accepted cases show whether a simple non-oracle speed calibration would clear the same replay gate; they are candidates for the next selector experiment, not a new default metric.
- Route-context margin diagnostics identify stable branch choices whose gains are too thin for rollout and name the route features that should be tested before promoting the selector.
- Sensitive cases are still useful: they identify where a hand-built selector needs richer route context or a learned candidate scorer.
- The oracle upper bound from the branch-selection report remains a diagnostic ceiling only; this replay does not use oracle futures to choose a branch.
- Public outputs stay aggregate and case-summary oriented; raw Waymo TFRecords and local packets remain ignored.
