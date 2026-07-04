# ScenarioLens Terminal-Neighborhood Selector Route/Context Audit

This report follows the selector error audit by joining the remaining false holds to derived replay and route-context diagnostics. The goal is to separate a reasonable heading-relaxation candidate from a case that should stay held for deeper map/context inspection.

The audit is intentionally narrow. It is not a route planner, not a learned model, not closed-loop simulation, and not a Waymo benchmark claim.

## Scope

- Selector transfer manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json`
- Terminal-neighborhood replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json`
- Ready for route/context audit: True
- Validation cases: 7
- Transfer false holds audited: 2
- Joined replay false holds: 2
- Transfer heading gate: 0.950
- Diagnostic heading gate: 0.700
- Raw scenario data committed: no
- Raw map geometry published: no

## Context Summary

| Metric | Value |
| --- | ---: |
| Transfer cases | 7 |
| False holds | 2 |
| Joined false holds | 2 |
| Stable recovery false holds | 2 |
| No-exit to linked-chain cases | 2 |
| Heading-relaxation candidates | 1 |
| Route/context holds | 1 |
| Mean selected terminal deficit | 18.670 m |
| Mean route extension | 63.511 m |
| Mean replay gain | +32.505 m |

## False-Hold Route/Context Table

| Rank | Scenario | Track | Classification | Gain | Min perturbation gain | Heading selected/alternate | Route selected -> alternate | Context read | Next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 35 | `28f34edeb361e955` | `987` | heading_relaxation_candidate | +26.119 m | +20.340 m | 0.997 / 0.886 | no_exit_lanes -> linked_lane_chain | Stable linked-chain recovery; only the strict heading gate blocks promotion. | Retest a heading-relaxed selector with more replay-held negatives before changing defaults. |
| 42 | `9c8241f6a2ee5f51` | `88` | route_context_hold | +38.890 m | +35.260 m | 0.122 / 0.741 | no_exit_lanes -> linked_lane_chain | Stable replay recovery but selected-lane heading disagrees severely, so route context wins over gate relaxation. | Audit lane direction, route context, and coordinate alignment before any heading relaxation. |

## Case 35: `28f34edeb361e955` / track `987`

- Source: `validation.tfrecord-00009-of-00150`
- Classification: **heading_relaxation_candidate**.
- Selected feature `158` has 32.851 m remaining; alternate feature `157` has 89.733 m remaining.
- Horizon travel: 57.799 m; selected terminal deficit: 24.948 m; alternate linked extension: 82.055 m.
- FDE selected/alternate: 62.626 m / 36.507 m; replay gain: +26.119 m.
- Perturbation stability: stable_recovery with minimum gain +20.340 m.
- Context labels: selected_terminal_no_exit, alternate_linked_chain, selected_route_shorter_than_horizon, alternate_chain_extends_route, stable_replay_recovery, within_diagnostic_heading_gate.
- Next action: Retest a heading-relaxed selector with more replay-held negatives before changing defaults.

## Case 42: `9c8241f6a2ee5f51` / track `88`

- Source: `validation.tfrecord-00008-of-00150`
- Classification: **route_context_hold**.
- Selected feature `223` has 24.718 m remaining; alternate feature `237` has 94.858 m remaining.
- Horizon travel: 37.110 m; selected terminal deficit: 12.392 m; alternate linked extension: 83.831 m.
- FDE selected/alternate: 48.172 m / 9.282 m; replay gain: +38.890 m.
- Perturbation stability: stable_recovery with minimum gain +35.260 m.
- Context labels: selected_terminal_no_exit, alternate_linked_chain, selected_route_shorter_than_horizon, alternate_chain_extends_route, stable_replay_recovery, selected_heading_disagreement.
- Next action: Audit lane direction, route context, and coordinate alignment before any heading relaxation.

## Recommendation

Keep the default selector unchanged. Move the borderline heading-relaxation case into the next diagnostic validation queue, but keep the severe heading-disagreement case held for route, lane direction, and coordinate-frame inspection.

## Interpretation

- The audit reuses derived replay packets; it does not inspect or publish raw map polylines.
- A heading-relaxation candidate remains diagnostic until replay-held negative coverage grows.
- A severe selected-lane heading disagreement is treated as a context problem, not evidence to relax gates globally.
