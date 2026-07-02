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
| Promoted candidates | 1 |
| Held for route context | 1 |
| Held for selector stability | 0 |
| Held for route and selector context | 0 |
| Manual-review holds | 0 |
| Not evaluable | 0 |
| Speed-minus margin holds | 1 |
| Speed-prior resolved holds | 0 |
| Oracle-matched holds | 1 |
| Mean promoted margin | +31.588 m |
| Min promoted margin | +31.588 m |
| Max hold priority | 5.182 |
| Max hold gap to gate | +0.443 m |

## Decisions

| Rank | Scenario | Track | Decision | Acceptance | Route context | Margin | Speed-prior margin | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `promote_for_broader_selector_eval` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +31.588 m | +31.588 m | Evaluate this selector behavior on a broader branchable continuation queue. |
| 4 | `5c49e681a66c720` | `2627` | `hold_for_route_context_margin` | `needs_route_context_margin` | `speed_minus_route_context_margin` | -0.443 m | -3.099 m | Add route-context features that can explain reduced-speed branch intent. |

## Promote Queue

- `260785192cf6c991` track `1754`: +31.588 m margin, default chain 235 -> 241 -> 315, motion-context chain 235 -> 307 -> 306.

## Hold Queue

- `5c49e681a66c720` track `2627`: **hold_for_route_context_margin** because the branch is stable but its route-context recoverable-FDE margin is too thin. First action: Add route-context features that can explain reduced-speed branch intent.

## `260785192cf6c991` / track `1754`

- Source: `validation.tfrecord-00009-of-00150`
- Decision: **promote_for_broader_selector_eval**
- Decision reason: the branch preserved its choice and cleared the recoverable-FDE gate.
- Acceptance: **accepted_for_selector_rollout**
- Stability: **stable_motion_context_branch**
- Route-context diagnostic: **accepted_no_route_context_followup**
- History speed-prior acceptance: **accepted_for_selector_rollout**
- Nominal recoverable FDE: +37.766 m
- Minimum perturbed recoverable FDE: +32.588 m
- Robustness margin: +31.588 m
- Route-context gap to gate: 0.000 m
- Route-context priority: 0.000
- Selected route matches diagnostic oracle: True

Next actions:

- Evaluate this selector behavior on a broader branchable continuation queue.
- Broaden the branch replay queue with the same acceptance gate.
- Keep this case as a positive control for selector rollout checks.

## `5c49e681a66c720` / track `2627`

- Source: `validation.tfrecord-00010-of-00150`
- Decision: **hold_for_route_context_margin**
- Decision reason: the branch is stable but its route-context recoverable-FDE margin is too thin.
- Acceptance: **needs_route_context_margin**
- Stability: **branch_stable_gain_sensitive**
- Route-context diagnostic: **speed_minus_route_context_margin**
- History speed-prior acceptance: **needs_route_context_margin**
- Nominal recoverable FDE: +3.301 m
- Minimum perturbed recoverable FDE: +0.557 m
- Robustness margin: -0.443 m
- Route-context gap to gate: +0.443 m
- Route-context priority: 5.182
- Selected route matches diagnostic oracle: True

Next actions:

- Add route-context features that can explain reduced-speed branch intent.
- Test turn-lane, downstream topology, and traffic-control context before selector rollout.
- Keep the speed-prior ablation as negative evidence, not a promoted default.

## Interpretation

- The promote queue is a candidate set for broader selector evaluation, not a production release.
- The hold queue is the interesting research queue: it names where the current branch selector needs route context, selector margin, or replay readiness work.
- Publishing both promoted and held cases keeps the evidence honest and makes regressions useful rather than embarrassing.
- Public outputs stay aggregate and case-summary oriented; raw Waymo TFRecords and local per-case packets remain ignored.
