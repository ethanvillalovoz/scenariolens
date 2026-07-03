# ScenarioLens Lane-Continuation Branch Selection Diagnostic

This report follows the route-diagnostics casebook with a branch sweep: for each replayed continuation regression, ScenarioLens reloads the local scenario, enumerates parsed linked-lane alternatives, and compares the current geometric route against three diagnostic selectors.

The `anchor_heading` selector uses only the anchor velocity and parsed route geometry. The `motion_context` selector adds a non-oracle route prior from recent target speed, known forecast horizon, route-chain length, and downstream lane speed limits. The `oracle_upper_bound` selector is an oracle upper bound that uses the observed future trajectory only to quantify whether choosing another parsed branch could explain the failure. It is intentionally not a route planner, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim.

## Scope

- Diagnostics manifest: `data/processed/waymo_lane_continuation_route_diagnostics/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Ready for branch diagnostics: True
- Cases analyzed: 5
- Max lane-link hops: 2
- Raw scenario data committed: no
- Local per-case replay packets committed: no

## Branch Sweep Summary

| Metric | Value |
| --- | ---: |
| Cases analyzed | 5 |
| Evaluable cases | 5 |
| Branchable cases | 3 |
| Single-chain cases | 2 |
| Oracle upper-bound improvements | 3 |
| Anchor-heading selector improvements | 1 |
| Anchor-heading selector changed route | 1 |
| Motion-context selector improvements | 3 |
| Motion-context selector changed route | 3 |
| Motion-context matched oracle on branchable cases | 3 |
| Mean motion-context recoverable FDE | +26.943 m |
| Max motion-context recoverable FDE | +39.762 m |
| Default route still best | 2 |
| Mean oracle recoverable FDE | +26.943 m |
| Max oracle recoverable FDE | +39.762 m |

## Case Results

| Rank | Scenario | Track | Diagnosis | Routes | Default chain | Motion-context chain | Oracle chain | Motion gain | Oracle gain | Verdict |
| ---: | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `route_horizon_limit` | 2 | 235 -> 241 -> 315 | 235 -> 307 -> 306 | 235 -> 307 -> 306 | +37.766 m | +37.766 m | `motion_context_selector_improves` |
| 2 | `e3f6a29b59e42c1` | `741` | `stable_route_choice_regression` | 1 | 161 -> 127 -> 116 | 161 -> 127 -> 116 | 161 -> 127 -> 116 | 0.000 m | 0.000 m | `single_chain_no_branch_choice` |
| 3 | `d30709cd60e60395` | `164` | `stable_route_choice_regression` | 2 | 603 -> 610 -> 371 | 603 -> 609 -> 606 | 603 -> 609 -> 606 | +39.762 m | +39.762 m | `anchor_heading_selector_improves` |
| 4 | `5c49e681a66c720` | `2627` | `stable_route_choice_regression` | 2 | 285 -> 120 -> 119 | 285 -> 286 -> 287 | 285 -> 286 -> 287 | +3.301 m | +3.301 m | `motion_context_selector_improves` |
| 5 | `e9db41e904b349a2` | `406` | `stable_route_choice_regression` | 1 | 295 -> 228 -> 201 | 295 -> 228 -> 201 | 295 -> 228 -> 201 | 0.000 m | 0.000 m | `single_chain_no_branch_choice` |

## `260785192cf6c991` / track `1754`

- Diagnosis source: `route_horizon_limit`
- Source: `validation.tfrecord-00009-of-00150`
- Ready: True
- Verdict: **motion_context_selector_improves**
- Why it matters: A non-oracle motion-context prior changes the parsed branch and reduces open-loop error using recent speed, route length, and downstream speed limits.
- Default linked-route FDE: 81.112 m
- Anchor-heading route FDE: 81.112 m
- Motion-context route FDE: 43.346 m
- Oracle upper-bound route FDE: 43.346 m
- Motion-context recoverable FDE: +37.766 m
- Oracle recoverable FDE: +37.766 m
- Motion-context estimated travel: 82.933 m
- Route candidate count: 2

Route candidates:

| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 235 -> 241 -> 315 | `linked_lane_chain` | 0.966 | 0.244 | 81.112 m | 0.000 m | default, anchor_heading |
| 235 -> 307 -> 306 | `linked_lane_chain` | 0.629 | 0.310 | 43.346 m | +37.766 m | motion_context, oracle_upper_bound |

Recommended next actions:
- Replay the motion-context selected branch under deterministic anchor perturbations.
- Compare the selector across the broader continuation candidate queue.
- Keep the oracle upper bound as a diagnostic ceiling, not a deployable result.

## `e3f6a29b59e42c1` / track `741`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00008-of-00150`
- Ready: True
- Verdict: **single_chain_no_branch_choice**
- Why it matters: The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help.
- Default linked-route FDE: 58.942 m
- Anchor-heading route FDE: 58.942 m
- Motion-context route FDE: 58.942 m
- Oracle upper-bound route FDE: 58.942 m
- Motion-context recoverable FDE: 0.000 m
- Oracle recoverable FDE: 0.000 m
- Motion-context estimated travel: 99.465 m
- Route candidate count: 1

Route candidates:

| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 161 -> 127 -> 116 | `linked_lane_chain` | 1.020 | 0.198 | 58.942 m | 0.000 m | default, anchor_heading, motion_context, oracle_upper_bound |

Recommended next actions:
- Audit lane topology depth, missing links, and selected-lane quality.
- Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.
- Keep this case separate from branch-selector performance claims.

## `d30709cd60e60395` / track `164`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00007-of-00150`
- Ready: True
- Verdict: **anchor_heading_selector_improves**
- Why it matters: A simple anchor-heading route prior changes the parsed branch and reduces open-loop error on this diagnostic case.
- Default linked-route FDE: 52.496 m
- Anchor-heading route FDE: 12.734 m
- Motion-context route FDE: 12.734 m
- Oracle upper-bound route FDE: 12.734 m
- Motion-context recoverable FDE: +39.762 m
- Oracle recoverable FDE: +39.762 m
- Motion-context estimated travel: 75.892 m
- Route candidate count: 2

Route candidates:

| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 603 -> 610 -> 371 | `linked_lane_chain` | 0.682 | -0.124 | 52.496 m | 0.000 m | default |
| 603 -> 609 -> 606 | `linked_lane_chain` | 0.704 | 0.224 | 12.734 m | +39.762 m | anchor_heading, motion_context, oracle_upper_bound |

Recommended next actions:
- Promote the anchor-heading route prior into the next replay pass.
- Keep the default geometric route side by side as the control.
- Verify the selector across the broader continuation candidate queue.

## `5c49e681a66c720` / track `2627`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Verdict: **motion_context_selector_improves**
- Why it matters: A non-oracle motion-context prior changes the parsed branch and reduces open-loop error using recent speed, route length, and downstream speed limits.
- Default linked-route FDE: 38.598 m
- Anchor-heading route FDE: 38.598 m
- Motion-context route FDE: 35.297 m
- Oracle upper-bound route FDE: 35.297 m
- Motion-context recoverable FDE: +3.301 m
- Oracle recoverable FDE: +3.301 m
- Motion-context estimated travel: 61.023 m
- Route candidate count: 2

Route candidates:

| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 285 -> 120 -> 119 | `linked_lane_chain` | 1.020 | -0.286 | 38.598 m | 0.000 m | default, anchor_heading |
| 285 -> 286 -> 287 | `linked_lane_chain` | 0.785 | 0.076 | 35.297 m | +3.301 m | motion_context, oracle_upper_bound |

Recommended next actions:
- Replay the motion-context selected branch under deterministic anchor perturbations.
- Compare the selector across the broader continuation candidate queue.
- Keep the oracle upper bound as a diagnostic ceiling, not a deployable result.

## `e9db41e904b349a2` / track `406`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00007-of-00150`
- Ready: True
- Verdict: **single_chain_no_branch_choice**
- Why it matters: The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help.
- Default linked-route FDE: 38.292 m
- Anchor-heading route FDE: 38.292 m
- Motion-context route FDE: 38.292 m
- Oracle upper-bound route FDE: 38.292 m
- Motion-context recoverable FDE: 0.000 m
- Oracle recoverable FDE: 0.000 m
- Motion-context estimated travel: 56.921 m
- Route candidate count: 1

Route candidates:

| Chain | Status | Heading score | Motion score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 295 -> 228 -> 201 | `linked_lane_chain` | 1.020 | -0.885 | 38.292 m | 0.000 m | default, anchor_heading, motion_context, oracle_upper_bound |

Recommended next actions:
- Audit lane topology depth, missing links, and selected-lane quality.
- Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.
- Keep this case separate from branch-selector performance claims.

## Interpretation

- Branchable cases show where the parsed map topology exposes more than one continuation from the selected lane.
- Motion-context improvements are non-oracle evidence that recent speed, horizon length, and downstream lane speed limits can choose a better parsed branch on some cases.
- Oracle upper-bound improvements prove that a different parsed branch can reduce open-loop error, but they are not deployable predictor results because they use observed future motion.
- If motion-context still misses an oracle-improvable route, the next step is richer context such as turn-lane semantics, signal state, route context, or a learned candidate scorer.
- Single-chain cases need longer topology, parser coverage, or a different selected lane before branch selection can help.
- Public outputs stay diagnostic; raw Waymo TFRecords and local packets remain ignored.
