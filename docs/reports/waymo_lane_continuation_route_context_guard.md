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
| Replay gate accepted | 2 |
| Replay route-context holds | 0 |
| Guard/replay gate matches | 1 |
| Guard false promotions | 0 |
| Guard false holds | 1 |
| Speed-minus margin cases held | 0 |
| Mean promoted nominal gain | +40.840 m |
| Mean held nominal gain | +39.762 m |

## Guard Decisions

| Rank | Scenario | Track | Guard | Replay gate | Route context | Motion gain | Endpoint delta | Speed-limit delta | Route-fit delta | First next action |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `promote_motion_context_candidate` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +40.840 m | -0.010 | 0.000 | +0.493 | Keep this branch in the broader selector-evaluation queue. |
| 3 | `d30709cd60e60395` | `164` | `hold_for_route_context_evidence` | `accepted_for_selector_rollout` | `accepted_no_route_context_followup` | +39.762 m | -0.236 | 0.000 | +0.578 | Collect richer route-context evidence before promoting this branch. |

## `260785192cf6c991` / track `1754`

- Source: `validation.tfrecord-00009-of-00150`
- Guard label: **promote_motion_context_candidate**
- Guard reason: The motion-context branch improves route fit without triggering the endpoint-alignment or downstream speed-limit guardrails.
- Replay acceptance: **accepted_for_selector_rollout**
- Replay route-context label: **accepted_no_route_context_followup**
- Guard matched replay gate: True
- Default chain: 235 -> 241 -> 315 -> 337
- Motion-context chain: 235 -> 307 -> 306 -> 314
- Guard-selected chain: 235 -> 307 -> 306 -> 314
- Nominal recoverable FDE: +40.840 m
- Route-context flags: none

Guard checks:

| Check | Value | Passed |
| --- | ---: | --- |
| Route-fit delta | +0.493 | True |
| Endpoint-alignment delta | -0.010 | True |
| Speed-limit-drop delta | 0.000 | True |

## `d30709cd60e60395` / track `164`

- Source: `validation.tfrecord-00007-of-00150`
- Guard label: **hold_for_route_context_evidence**
- Guard reason: The branch has nominal recoverable FDE, but route-context guardrails fired: endpoint_alignment_drop.
- Replay acceptance: **accepted_for_selector_rollout**
- Replay route-context label: **accepted_no_route_context_followup**
- Guard matched replay gate: False
- Default chain: 603 -> 610 -> 371 -> 394
- Motion-context chain: 603 -> 609 -> 606 -> 597
- Guard-selected chain: 603 -> 610 -> 371 -> 394
- Nominal recoverable FDE: +39.762 m
- Route-context flags: endpoint_alignment_drop

Guard checks:

| Check | Value | Passed |
| --- | ---: | --- |
| Route-fit delta | +0.578 | True |
| Endpoint-alignment delta | -0.236 | False |
| Speed-limit-drop delta | 0.000 | True |

## Interpretation

- A guard promotion means the current motion-context branch has route-fit support without obvious endpoint or downstream speed context warnings.
- A guard hold is still valuable evidence: it turns a marginal nominal improvement into a concrete route-context follow-up before broader selector rollout.
- The replay gate remains the stricter evidence source. This guard is a candidate policy to test on a larger branchable queue, not a route planner, production release policy, or benchmark result.
- Public outputs stay summary-oriented; raw Waymo TFRecords and local replay packets remain ignored.
