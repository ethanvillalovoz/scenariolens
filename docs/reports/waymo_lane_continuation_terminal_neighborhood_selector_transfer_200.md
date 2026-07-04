# ScenarioLens Terminal-Neighborhood Selector Transfer Validation

This report applies a terminal-neighborhood selector policy calibrated on one replay queue to a broader replay manifest. The goal is to test whether the policy transfers without false promotions, not to change ScenarioLens default behavior.

The validation is intentionally narrow. It is not a route planner, not a learned policy, not closed-loop simulation, and not a Waymo benchmark claim.

## Scope

- Calibration manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded/manifest.json`
- Validation replay manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json`
- Policy source: recommended
- Ready for transfer validation: True
- Calibration training cases: 6
- Validation cases: 7
- Overlap with calibration queue: 3
- Novel validation cases: 4
- Validation replay-gate accepted cases: 5
- Validation replay-gate held cases: 2
- Perturbation trials behind validation labels: 28
- Raw scenario data committed: no
- Raw map geometry published: no

## Policy Transfer Summary

| Metric | Current default on validation | Transferred policy on validation |
| --- | ---: | ---: |
| Max alternate distance | 5.000 m | 5.000 m |
| Minimum heading alignment | 0.950 | 0.950 |
| Minimum route extension | 50.000 m | 40.000 m |
| Selector promotions | 2 | 3 |
| Selector holds | 5 | 4 |
| Replay-gate matches | 4 | 5 |
| False promotions | 0 | 0 |
| False holds | 3 | 2 |
| Mean promoted replay gain | +71.052 m | +59.736 m |

## Split Summary

| Split | Cases | Matches | False promotions | False holds |
| --- | ---: | ---: | ---: | ---: |
| Calibration overlap | 3 | 3 | 0 | 0 |
| Novel validation cases | 4 | 2 | 0 | 2 |

## Validation Decisions

| Rank | Split | Scenario | Track | Replay gate | Current default | Transferred policy | Transfer match | Replay gain | Distance | Heading min | Route extension | Hold flags |
| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 31 | overlap | `2f366a31ab03f8b` | `1061` | accept_for_selector_experiment | promote | promote | true_positive_recovery | +125.481 m | 3.534 m | 1.000 | 228.779 m | none |
| 34 | overlap | `74a5b3325a534a87` | `3178` | hold_recovery_regressed | hold | hold | true_hold | -15.163 m | 2.533 m | 0.690 | 72.451 m | selected_heading_below_gate, alternate_heading_below_gate |
| 35 | novel | `28f34edeb361e955` | `987` | accept_for_selector_experiment | hold | hold | false_hold | +26.119 m | 4.719 m | 0.886 | 56.882 m | alternate_heading_below_gate |
| 36 | novel | `634b468a246a77d6` | `116` | hold_recovery_regressed | hold | hold | true_hold | -16.230 m | 0.269 m | 0.823 | 32.514 m | alternate_heading_below_gate, route_extension_below_gate |
| 41 | novel | `8abe59aee39f351e` | `4650` | accept_for_selector_experiment | promote | promote | true_positive_recovery | +16.623 m | 4.426 m | 0.999 | 81.794 m | none |
| 42 | novel | `9c8241f6a2ee5f51` | `88` | accept_for_selector_experiment | hold | hold | false_hold | +38.890 m | 2.070 m | 0.122 | 70.140 m | selected_heading_below_gate, alternate_heading_below_gate |
| 45 | overlap | `fe4a6425278fbd5b` | `816` | accept_for_selector_experiment | hold | promote | true_positive_recovery | +37.105 m | 0.988 m | 0.984 | 48.036 m | none |

## Recommendation

Keep the default selector unchanged. The transferred policy keeps false promotions at zero on this queue but still leaves false holds, including validation coverage over 4 novel case(s). Treat it as a diagnostic candidate for the next expanded queue, not a default-policy change.

## Interpretation

- The transferred selector is evaluated against replay-gate labels only after it makes geometry-only decisions.
- Overlap and novel-case counts are reported so this is not mistaken for a fully independent benchmark.
- Zero false promotions preserves the conservative safety posture on this validation queue.
- 2 false hold(s) remain, so the result supports continued calibration work rather than default adoption.
- Novel validation cases did not introduce false promotions, which is useful transfer evidence but still small-sample.
