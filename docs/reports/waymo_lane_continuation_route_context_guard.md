# ScenarioLens Route-Context Guard Study

This study follows the branch rollout gate by testing a stricter non-oracle promotion guard for motion-context branch candidates. The guard asks whether a branch improvement also has enough route-context support to be promoted for broader selector evaluation.

The guard does not replace ScenarioLens scoring or the existing motion-context selector. It is a laptop-safe diagnostic: route features decide the guard, while branch replay outcomes are used only to check whether the guard agrees with the current replay gate.

## Scope

- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection/manifest.json`
- Branch-replay manifest: `data/processed/waymo_lane_continuation_branch_replay/manifest.json`
- Ready for route-context guard study: True
- Route-fit delta gate: `0.0`
- Endpoint-alignment delta gate: `-0.05`
- Speed-limit-drop delta gate: `0.1`
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Guard Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 2 |
| Ready cases | 2 |
| Guard promotions | 1 |
| Guard holds | 1 |
| Replay gate accepted | 1 |
| Replay route-context holds | 1 |
| Guard/replay gate matches | 2 |
| Guard false promotions | 0 |
| Guard false holds | 0 |
| Speed-minus margin cases held | 1 |
| Mean promoted nominal gain | +37.766 m |
| Mean held nominal gain | +3.301 m |

## Guard Decisions

| Rank | Scenario | Track | Guard | Replay gate | Route context | Motion gain | Endpoint delta | Speed-limit delta | Route-fit delta | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `promote_motion_context_candidate` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +37.766 m | -0.001 | 0.000 | +0.077 | Keep this branch in the broader selector-evaluation queue. |
| 4 | `5c49e681a66c720` | `2627` | `hold_for_route_context_evidence` | `needs_route_context_margin` | `speed_minus_route_context_margin` | +3.301 m | -0.234 | +0.286 | +0.200 | Add turn-lane, downstream topology, and traffic-control context before selector rollout. |

## `260785192cf6c991` / track `1754`

- Source: `validation.tfrecord-00009-of-00150`
- Guard label: **promote_motion_context_candidate**
- Guard reason: The motion-context branch improves route fit without triggering the endpoint-alignment or downstream speed-limit guardrails.
- Replay acceptance: **accepted_for_selector_rollout**
- Replay route-context label: **accepted_no_route_context_followup**
- Guard matched replay gate: True
- Default chain: 235 -> 241 -> 315
- Motion-context chain: 235 -> 307 -> 306
- Guard-selected chain: 235 -> 307 -> 306
- Nominal recoverable FDE: +37.766 m
- Route-context flags: none

Guard checks:

| Check | Value | Passed |
| --- | ---: | --- |
| Route-fit delta | +0.077 | True |
| Endpoint-alignment delta | -0.001 | True |
| Speed-limit-drop delta | 0.000 | True |

## `5c49e681a66c720` / track `2627`

- Source: `validation.tfrecord-00010-of-00150`
- Guard label: **hold_for_route_context_evidence**
- Guard reason: The branch has nominal recoverable FDE, but route-context guardrails fired: endpoint_alignment_drop, downstream_speed_limit_drop.
- Replay acceptance: **needs_route_context_margin**
- Replay route-context label: **speed_minus_route_context_margin**
- Guard matched replay gate: True
- Default chain: 285 -> 120 -> 119
- Motion-context chain: 285 -> 286 -> 287
- Guard-selected chain: 285 -> 120 -> 119
- Nominal recoverable FDE: +3.301 m
- Route-context flags: endpoint_alignment_drop, downstream_speed_limit_drop

Guard checks:

| Check | Value | Passed |
| --- | ---: | --- |
| Route-fit delta | +0.200 | True |
| Endpoint-alignment delta | -0.234 | False |
| Speed-limit-drop delta | +0.286 | False |

## Interpretation

- A guard promotion means the current motion-context branch has route-fit support without obvious endpoint or downstream speed context warnings.
- A guard hold is still valuable evidence: it turns a marginal nominal improvement into a concrete route-context follow-up before broader selector rollout.
- The replay gate remains the stricter evidence source. This guard is a candidate policy to test on a larger branchable queue, not a route planner, production release policy, or benchmark result.
- Public outputs stay summary-oriented; raw Waymo TFRecords and local replay packets remain ignored.
