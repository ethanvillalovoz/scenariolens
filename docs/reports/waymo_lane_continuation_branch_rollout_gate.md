# ScenarioLens Branch Rollout Gate

This report converts the motion-context branch replay diagnostic into a promote/hold decision table. A case is promoted only when the branch replay accepted it for broader selector evaluation; thin route-context margins and selector instability stay held with their next engineering action.

The gate is intentionally conservative. It is useful because it shows how ScenarioLens can move from metric reporting to release-style evidence triage without claiming to be a planner or a benchmark. It is not a route planner.

## Scope

- Branch replay manifest: `data/processed/waymo_lane_continuation_branch_replay/manifest.json`
- Branch selection manifest: `data/processed/waymo_lane_continuation_branch_selection/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Ready for rollout triage: True
- Replay cases: 2
- Replayed cases: 2
- Perturbation trials: 8
- Minimum stable gain: 1.000 m
- Gate: Promote only cases whose branch replay accepted the motion-context selector for broader rollout. Hold stable thin-margin cases for route-context work and unstable choices for selector-stability work.
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Rollout Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 2 |
| Replayed cases | 2 |
| Promoted candidates | 2 |
| Held for route context | 0 |
| Held for selector stability | 0 |
| Held for route and selector context | 0 |
| Manual-review holds | 0 |
| Not evaluable | 0 |
| Speed-minus margin holds | 0 |
| Speed-prior resolved holds | 0 |
| Oracle-matched holds | 0 |
| Mean promoted margin | +29.834 m |
| Min promoted margin | +28.627 m |
| Max hold priority | n/a |
| Max hold gap to gate | n/a |

## Decisions

| Rank | Scenario | Track | Decision | Acceptance | Route context | Margin | Speed-prior margin | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `promote_for_broader_selector_eval` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +28.627 m | +28.627 m | Evaluate this selector behavior on a broader branchable continuation queue. |
| 3 | `d30709cd60e60395` | `164` | `promote_for_broader_selector_eval` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +31.042 m | +34.418 m | Evaluate this selector behavior on a broader branchable continuation queue. |

## Promote Queue

- `260785192cf6c991` track `1754`: +28.627 m margin, default chain 235 -> 241 -> 315 -> 337, motion-context chain 235 -> 307 -> 306 -> 314.
- `d30709cd60e60395` track `164`: +31.042 m margin, default chain 603 -> 610 -> 371 -> 394, motion-context chain 603 -> 609 -> 606 -> 597.

## Hold Queue

- No cases are held by this rollout gate.

## `260785192cf6c991` / track `1754`

- Source: `validation.tfrecord-00009-of-00150`
- Decision: **promote_for_broader_selector_eval**
- Decision reason: the branch preserved its choice and cleared the recoverable-FDE gate.
- Acceptance: **accepted_for_selector_rollout**
- Stability: **stable_motion_context_branch**
- Route-context diagnostic: **accepted_no_route_context_followup**
- History speed-prior acceptance: **accepted_for_selector_rollout**
- Nominal recoverable FDE: +40.840 m
- Minimum perturbed recoverable FDE: +29.627 m
- Robustness margin: +28.627 m
- Route-context gap to gate: 0.000 m
- Route-context priority: 0.000
- Selected route matches diagnostic oracle: True

Next actions:

- Evaluate this selector behavior on a broader branchable continuation queue.
- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

## `d30709cd60e60395` / track `164`

- Source: `validation.tfrecord-00007-of-00150`
- Decision: **promote_for_broader_selector_eval**
- Decision reason: the branch preserved its choice and cleared the recoverable-FDE gate.
- Acceptance: **accepted_for_selector_rollout**
- Stability: **stable_motion_context_branch**
- Route-context diagnostic: **accepted_no_route_context_followup**
- History speed-prior acceptance: **accepted_for_selector_rollout**
- Nominal recoverable FDE: +39.762 m
- Minimum perturbed recoverable FDE: +32.042 m
- Robustness margin: +31.042 m
- Route-context gap to gate: 0.000 m
- Route-context priority: 0.000
- Selected route matches diagnostic oracle: True

Next actions:

- Evaluate this selector behavior on a broader branchable continuation queue.
- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

## Interpretation

- The promote queue is a candidate set for broader selector evaluation, not a production release.
- The hold queue is the interesting research queue: it names where the current branch selector needs route context, selector margin, or replay readiness work.
- Publishing both promoted and held cases keeps the evidence honest and makes regressions useful rather than embarrassing.
- Public outputs stay aggregate and case-summary oriented; raw Waymo TFRecords and local per-case packets remain ignored.
