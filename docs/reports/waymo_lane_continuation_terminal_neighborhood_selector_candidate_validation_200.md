# ScenarioLens Terminal-Neighborhood Selector Candidate Validation

This report tests a narrow diagnostic selector candidate after the route/context audit. It keeps the transferred selector policy intact and adds exactly one public-safe promotion rule: recover false holds only when the route/context audit classifies them as `heading_relaxation_candidate`.

The candidate is intentionally narrow. It is not a default selector change, not a route planner, not a learned model, not closed-loop simulation, and not a Waymo benchmark claim.

## Scope

- Selector transfer manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json`
- Route/context audit manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200/manifest.json`
- Ready for candidate validation: True
- Validation cases: 7
- Route/context false holds available: 2
- Candidate policy: `context_aware_heading_candidate`
- Default selector changed: False
- Raw scenario data committed: no
- Raw map geometry published: no

## Validation Summary

| Metric | Transfer policy | Candidate policy |
| --- | ---: | ---: |
| Replay-gate matches | 5 | 6 |
| False promotions | 0 | 0 |
| False holds | 2 | 1 |
| Promoted cases | 3 | 4 |
| Held cases | 4 | 3 |

Additional checks:

- Recovered transfer false holds: 1
- Replay-held negatives preserved: 2 / 2
- Route/context holds retained: 1

## Candidate Outcomes

| Rank | Split | Scenario | Track | Replay label | Transfer | Candidate | Candidate match | Context class | Gain | Rationale |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| 31 | overlap | `2f366a31ab03f8b` | `1061` | accepted | promote_terminal_neighborhood_alternate | promote_terminal_neighborhood_alternate | true_positive_recovery | not_a_false_hold | +125.481 m | already promoted by transferred selector |
| 34 | overlap | `74a5b3325a534a87` | `3178` | held | hold_for_terminal_neighborhood_context | hold_for_terminal_neighborhood_context | true_hold | not_a_false_hold | -15.163 m | preserved replay-held negative control |
| 35 | novel | `28f34edeb361e955` | `987` | accepted | hold_for_terminal_neighborhood_context | promote_terminal_neighborhood_alternate | true_positive_recovery | heading_relaxation_candidate | +26.119 m | promoted by route/context heading candidate |
| 36 | novel | `634b468a246a77d6` | `116` | held | hold_for_terminal_neighborhood_context | hold_for_terminal_neighborhood_context | true_hold | not_a_false_hold | -16.230 m | preserved replay-held negative control |
| 41 | novel | `8abe59aee39f351e` | `4650` | accepted | promote_terminal_neighborhood_alternate | promote_terminal_neighborhood_alternate | true_positive_recovery | not_a_false_hold | +16.623 m | already promoted by transferred selector |
| 42 | novel | `9c8241f6a2ee5f51` | `88` | accepted | hold_for_terminal_neighborhood_context | hold_for_terminal_neighborhood_context | false_hold | route_context_hold | +38.890 m | held by route/context audit |
| 45 | overlap | `fe4a6425278fbd5b` | `816` | accepted | promote_terminal_neighborhood_alternate | promote_terminal_neighborhood_alternate | true_positive_recovery | not_a_false_hold | +37.105 m | already promoted by transferred selector |

## Recovered Cases

| Rank | Scenario | Track | Context labels | Heading selected/alternate | Route extension | Next validation step |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 35 | `28f34edeb361e955` | `987` | selected_terminal_no_exit, alternate_linked_chain, selected_route_shorter_than_horizon, alternate_chain_extends_route, stable_replay_recovery, within_diagnostic_heading_gate | 0.997 / 0.886 | 56.882 m | Retest on a broader replay queue with additional held negatives. |

## Negative Controls

| Rank | Scenario | Track | Replay gain | Candidate decision | Reason held |
| ---: | --- | --- | ---: | --- | --- |
| 34 | `74a5b3325a534a87` | `3178` | -15.163 m | hold_for_terminal_neighborhood_context | preserved replay-held negative control |
| 36 | `634b468a246a77d6` | `116` | -16.230 m | hold_for_terminal_neighborhood_context | preserved replay-held negative control |

## Recommendation

Keep the default selector unchanged, but carry the context-aware heading candidate into the next validation queue. It recovers one transfer false hold, preserves replay-held negative controls, and keeps the severe route/context case held.

## Interpretation

- This candidate is evaluated against the existing replay-label queue; it is not trained on raw trajectory data.
- Preserving replay-held negative controls matters more than recovering every replay-accepted alternate.
- The severe route/context hold remains held, so this is still diagnostic evidence rather than selector adoption.
