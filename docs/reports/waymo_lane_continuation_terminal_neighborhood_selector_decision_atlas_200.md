# ScenarioLens Terminal Selector Decision Atlas

This atlas connects the 7-card terminal-neighborhood selector casebook to the candidate-validation outcome for each case. It is meant to be read visually: every card is a derived metric diagram that explains whether the candidate policy promotes, holds, recovers, or preserves a negative control.

The atlas is intentionally narrow. It is not a default selector change, not a route planner, not closed-loop simulation, and not a Waymo benchmark claim.

## Scope

- Casebook manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_casebook_200/manifest.json`
- Candidate-validation manifest: `data/processed/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200/manifest.json`
- Ready for atlas: True
- Visual cards: 7
- Candidate matches: 6 / 7
- Candidate false promotions: 0
- Candidate false holds: 1
- Recovered transfer false holds: 1
- Replay-held negatives preserved: 2
- Raw scenario data committed: no
- Raw map geometry published: no

## Category Summary

| Category | Count | Meaning |
| --- | ---: | --- |
| Recovered false hold | 1 | The candidate promotes a replay-accepted case that the transfer policy held. |
| Accepted recovery | 3 | The candidate keeps an already promoted replay-accepted recovery. |
| Negative control | 2 | The candidate preserves a replay-held regression as held. |
| Retained hold | 1 | The candidate holds a replay-accepted case because context is still too risky. |
| False promotion | 0 | The candidate would promote a replay-held regression. |

## Decision Index

| Case | Scenario | Track | Category | Replay | Transfer | Candidate | Gain | Route extension | Visual |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| Case 01 | `2f366a31ab03f8b` | `1061` | Accepted recovery | accepted | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | +125.481 m | 228.779 m | [card](assets/terminal_selector_casebook_200_01.svg) |
| Case 02 | `74a5b3325a534a87` | `3178` | Negative control | held | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | -15.163 m | 72.451 m | [card](assets/terminal_selector_casebook_200_02.svg) |
| Case 03 | `28f34edeb361e955` | `987` | Recovered false hold | accepted | `hold_for_terminal_neighborhood_context` | `promote_terminal_neighborhood_alternate` | +26.119 m | 56.882 m | [card](assets/terminal_selector_casebook_200_03.svg) |
| Case 04 | `634b468a246a77d6` | `116` | Negative control | held | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | -16.230 m | 32.514 m | [card](assets/terminal_selector_casebook_200_04.svg) |
| Case 05 | `8abe59aee39f351e` | `4650` | Accepted recovery | accepted | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | +16.623 m | 81.794 m | [card](assets/terminal_selector_casebook_200_05.svg) |
| Case 06 | `9c8241f6a2ee5f51` | `88` | Retained hold | accepted | `hold_for_terminal_neighborhood_context` | `hold_for_terminal_neighborhood_context` | +38.890 m | 70.140 m | [card](assets/terminal_selector_casebook_200_06.svg) |
| Case 07 | `fe4a6425278fbd5b` | `816` | Accepted recovery | accepted | `promote_terminal_neighborhood_alternate` | `promote_terminal_neighborhood_alternate` | +37.105 m | 48.036 m | [card](assets/terminal_selector_casebook_200_07.svg) |

## Case 01: Accepted recovery

![Case 01 selector diagnostic](assets/terminal_selector_casebook_200_01.svg)

- Scenario / track: `2f366a31ab03f8b` / `1061`
- Source: `validation.tfrecord-00007-of-00150`
- Candidate match: `true_positive_recovery`
- Route/context class: `not_a_false_hold`
- Replay label: `accepted` with +125.481 m nominal gain.
- Transfer decision: `promote_terminal_neighborhood_alternate`; candidate decision: `promote_terminal_neighborhood_alternate`.
- Heading selected/alternate: 1.000 / 1.000.
- Route extension: 228.779 m.
- Hold flags: none.
- Rationale: already promoted by transferred selector
- Next validation step: No route/context candidate action.

## Case 02: Negative control

![Case 02 selector diagnostic](assets/terminal_selector_casebook_200_02.svg)

- Scenario / track: `74a5b3325a534a87` / `3178`
- Source: `validation.tfrecord-00010-of-00150`
- Candidate match: `true_hold`
- Route/context class: `not_a_false_hold`
- Replay label: `held` with -15.163 m nominal gain.
- Transfer decision: `hold_for_terminal_neighborhood_context`; candidate decision: `hold_for_terminal_neighborhood_context`.
- Heading selected/alternate: 0.691 / 0.690.
- Route extension: 72.451 m.
- Hold flags: selected_heading_below_gate, alternate_heading_below_gate.
- Rationale: preserved replay-held negative control
- Next validation step: No route/context candidate action.

## Case 03: Recovered false hold

![Case 03 selector diagnostic](assets/terminal_selector_casebook_200_03.svg)

- Scenario / track: `28f34edeb361e955` / `987`
- Source: `validation.tfrecord-00009-of-00150`
- Candidate match: `true_positive_recovery`
- Route/context class: `heading_relaxation_candidate`
- Replay label: `accepted` with +26.119 m nominal gain.
- Transfer decision: `hold_for_terminal_neighborhood_context`; candidate decision: `promote_terminal_neighborhood_alternate`.
- Heading selected/alternate: 0.997 / 0.886.
- Route extension: 56.882 m.
- Hold flags: alternate_heading_below_gate.
- Rationale: promoted by route/context heading candidate
- Next validation step: Retest on a broader replay queue with additional held negatives.

## Case 04: Negative control

![Case 04 selector diagnostic](assets/terminal_selector_casebook_200_04.svg)

- Scenario / track: `634b468a246a77d6` / `116`
- Source: `validation.tfrecord-00010-of-00150`
- Candidate match: `true_hold`
- Route/context class: `not_a_false_hold`
- Replay label: `held` with -16.230 m nominal gain.
- Transfer decision: `hold_for_terminal_neighborhood_context`; candidate decision: `hold_for_terminal_neighborhood_context`.
- Heading selected/alternate: 0.999 / 0.823.
- Route extension: 32.514 m.
- Hold flags: alternate_heading_below_gate, route_extension_below_gate.
- Rationale: preserved replay-held negative control
- Next validation step: No route/context candidate action.

## Case 05: Accepted recovery

![Case 05 selector diagnostic](assets/terminal_selector_casebook_200_05.svg)

- Scenario / track: `8abe59aee39f351e` / `4650`
- Source: `validation.tfrecord-00010-of-00150`
- Candidate match: `true_positive_recovery`
- Route/context class: `not_a_false_hold`
- Replay label: `accepted` with +16.623 m nominal gain.
- Transfer decision: `promote_terminal_neighborhood_alternate`; candidate decision: `promote_terminal_neighborhood_alternate`.
- Heading selected/alternate: 0.999 / 0.999.
- Route extension: 81.794 m.
- Hold flags: none.
- Rationale: already promoted by transferred selector
- Next validation step: No route/context candidate action.

## Case 06: Retained hold

![Case 06 selector diagnostic](assets/terminal_selector_casebook_200_06.svg)

- Scenario / track: `9c8241f6a2ee5f51` / `88`
- Source: `validation.tfrecord-00008-of-00150`
- Candidate match: `false_hold`
- Route/context class: `route_context_hold`
- Replay label: `accepted` with +38.890 m nominal gain.
- Transfer decision: `hold_for_terminal_neighborhood_context`; candidate decision: `hold_for_terminal_neighborhood_context`.
- Heading selected/alternate: 0.122 / 0.741.
- Route extension: 70.140 m.
- Hold flags: selected_heading_below_gate, alternate_heading_below_gate.
- Rationale: held by route/context audit
- Next validation step: Inspect lane direction, route context, and coordinate frame first.

## Case 07: Accepted recovery

![Case 07 selector diagnostic](assets/terminal_selector_casebook_200_07.svg)

- Scenario / track: `fe4a6425278fbd5b` / `816`
- Source: `validation.tfrecord-00010-of-00150`
- Candidate match: `true_positive_recovery`
- Route/context class: `not_a_false_hold`
- Replay label: `accepted` with +37.105 m nominal gain.
- Transfer decision: `promote_terminal_neighborhood_alternate`; candidate decision: `promote_terminal_neighborhood_alternate`.
- Heading selected/alternate: 0.997 / 0.984.
- Route extension: 48.036 m.
- Hold flags: route_extension_below_gate.
- Rationale: already promoted by transferred selector
- Next validation step: No route/context candidate action.

## Interpretation

- The recovered case is useful because it improves replay-label agreement without broadening the default selector.
- The negative controls are useful because they show the candidate did not promote replay-held regressions.
- The remaining hold is useful because it keeps a severe route/context disagreement out of the promotion set.
- The next stronger validation step is a broader replay queue before changing default scoring behavior.
