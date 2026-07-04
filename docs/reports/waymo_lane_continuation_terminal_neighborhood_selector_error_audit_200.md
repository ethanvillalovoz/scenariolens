# ScenarioLens Terminal-Neighborhood Selector Error Audit

This audit follows the selector transfer validation by explaining the remaining false holds and testing small counterfactual selector gates. It is meant to turn transfer errors into the next evidence queue, not to tune a default policy from a small sample.

The audit is intentionally narrow. It is not a route planner, not a learned model, not closed-loop simulation, and not a Waymo benchmark claim.

## Scope

- Selector transfer manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json`
- Ready for error audit: True
- Validation cases: 7
- Novel validation cases: 4
- Transfer false promotions: 0
- Transfer false holds: 2
- Transfer policy heading gate: 0.950
- Transfer policy route-extension gate: 40.000 m
- Raw scenario data committed: no
- Raw map geometry published: no

## Error Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 7 |
| False promotions | 0 |
| False holds | 2 |
| Novel false holds | 2 |
| Overlap false holds | 0 |
| False holds with heading blockers | 2 |
| False holds with route-extension blockers | 0 |
| Mean false-hold replay gain | +32.505 m |

## Counterfactual Gate Sweep

| Policy | Heading gate | Route gate | Promotions | Matches | False promotions | False holds | Note |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| transferred_policy | 0.950 | 40.000 m | 3 | 5 | 0 | 2 | diagnostic only: false holds remain |
| relax_heading_to_0.90 | 0.900 | 40.000 m | 3 | 5 | 0 | 2 | diagnostic only: false holds remain |
| relax_heading_to_0.70 | 0.700 | 40.000 m | 4 | 6 | 0 | 1 | diagnostic only: false holds remain |
| relax_route_to_25m | 0.950 | 25.000 m | 3 | 5 | 0 | 2 | diagnostic only: false holds remain |
| relax_heading_0.70_route_25m | 0.700 | 25.000 m | 5 | 5 | 1 | 1 | reject: introduces false promotions |

## False-Hold Diagnosis

| Rank | Split | Scenario | Track | Replay gain | Heading min | Route extension | Blocking gates | Diagnosis | Next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 35 | novel | `28f34edeb361e955` | `987` | +26.119 m | 0.886 | 56.882 m | alternate_heading_below_gate | borderline heading gate miss | Try a heading-relaxed candidate on a larger validation queue with replay-held negatives. |
| 42 | novel | `9c8241f6a2ee5f51` | `88` | +38.890 m | 0.122 | 70.140 m | selected_heading_below_gate, alternate_heading_below_gate | severe heading disagreement | Audit lane direction, route context, and coordinate alignment before relaxing heading gates. |

## False-Promotion Diagnosis

| Rank | Split | Scenario | Track | Replay gain | Blocking issue | Next action |
| ---: | --- | --- | --- | ---: | --- | --- |
| n/a | n/a | n/a | n/a | n/a | none | none |

## Recommendation

Keep the default selector unchanged, but use `relax_heading_to_0.70` as the next diagnostic candidate. It reduces false holds without adding false promotions on this small transfer queue, while the remaining severe heading case needs route/context inspection.

## Interpretation

- Counterfactual policies are evaluated against the same derived replay labels; they are not trained on raw trajectory data.
- A counterfactual that reduces false holds is still only a diagnostic candidate until more replay-held negatives are added.
- Severe heading disagreement should trigger route/context inspection before relaxing heading gates globally.
