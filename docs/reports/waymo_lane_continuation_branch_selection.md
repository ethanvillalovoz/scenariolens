# ScenarioLens Lane-Continuation Branch Selection Diagnostic

This report follows the route-diagnostics casebook with a branch sweep: for each replayed continuation regression, ScenarioLens reloads the local scenario, enumerates parsed linked-lane alternatives, and compares the current geometric route against two diagnostic selectors.

The `anchor_heading` selector uses only the anchor velocity and parsed route geometry. The `oracle_upper_bound` selector is an oracle upper bound that uses the observed future trajectory only to quantify whether choosing another parsed branch could explain the failure. It is intentionally not a route planner, not closed-loop simulation, not Waymax/JAX execution, and not a Waymo benchmark claim.

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
| Branchable cases | 2 |
| Single-chain cases | 3 |
| Oracle upper-bound improvements | 2 |
| Anchor-heading selector improvements | 0 |
| Anchor-heading selector changed route | 0 |
| Default route still best | 3 |
| Mean oracle recoverable FDE | +20.534 m |
| Max oracle recoverable FDE | +37.766 m |

## Case Results

| Rank | Scenario | Track | Diagnosis | Routes | Default chain | Anchor-heading chain | Oracle chain | Oracle gain | Verdict |
| ---: | --- | --- | --- | ---: | --- | --- | --- | ---: | --- |
| 1 | `260785192cf6c991` | `1754` | `route_horizon_limit` | 2 | 235 -> 241 -> 315 | 235 -> 241 -> 315 | 235 -> 307 -> 306 | +37.766 m | `oracle_branch_upper_bound_improves` |
| 2 | `e3f6a29b59e42c1` | `741` | `stable_route_choice_regression` | 1 | 161 -> 127 -> 116 | 161 -> 127 -> 116 | 161 -> 127 -> 116 | 0.000 m | `single_chain_no_branch_choice` |
| 3 | `d8dde10f514a501c` | `651` | `linked_route_worse_than_constant_velocity` | 1 | 134 -> 143 -> 146 | 134 -> 143 -> 146 | 134 -> 143 -> 146 | 0.000 m | `single_chain_no_branch_choice` |
| 4 | `5c49e681a66c720` | `2627` | `stable_route_choice_regression` | 2 | 285 -> 120 -> 119 | 285 -> 120 -> 119 | 285 -> 286 -> 287 | +3.301 m | `oracle_branch_upper_bound_improves` |
| 5 | `e9db41e904b349a2` | `406` | `stable_route_choice_regression` | 1 | 295 -> 228 -> 201 | 295 -> 228 -> 201 | 295 -> 228 -> 201 | 0.000 m | `single_chain_no_branch_choice` |

## `260785192cf6c991` / track `1754`

- Diagnosis source: `route_horizon_limit`
- Source: `validation.tfrecord-00009-of-00150`
- Ready: True
- Verdict: **oracle_branch_upper_bound_improves**
- Why it matters: Another parsed branch fits the observed future better, proving branch choice is a plausible source of the continuation regression.
- Default linked-route FDE: 81.112 m
- Anchor-heading route FDE: 81.112 m
- Oracle upper-bound route FDE: 43.346 m
- Oracle recoverable FDE: +37.766 m
- Route candidate count: 2

Route candidates:

| Chain | Status | Heading score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | --- |
| 235 -> 241 -> 315 | `linked_lane_chain` | 0.966 | 81.112 m | 0.000 m | default, anchor_heading |
| 235 -> 307 -> 306 | `linked_lane_chain` | 0.629 | 43.346 m | +37.766 m | oracle_upper_bound |

Recommended next actions:
- Add a richer non-oracle route prior using route context, traffic controls, or near-term intent cues.
- Use the oracle branch only as an upper-bound diagnostic, not as a deployed predictor.
- Rerun perturbation checks after adding the non-oracle prior.

## `e3f6a29b59e42c1` / track `741`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00008-of-00150`
- Ready: True
- Verdict: **single_chain_no_branch_choice**
- Why it matters: The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help.
- Default linked-route FDE: 58.942 m
- Anchor-heading route FDE: 58.942 m
- Oracle upper-bound route FDE: 58.942 m
- Oracle recoverable FDE: 0.000 m
- Route candidate count: 1

Route candidates:

| Chain | Status | Heading score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | --- |
| 161 -> 127 -> 116 | `linked_lane_chain` | 1.020 | 58.942 m | 0.000 m | default, anchor_heading, oracle_upper_bound |

Recommended next actions:
- Audit lane topology depth, missing links, and selected-lane quality.
- Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.
- Keep this case separate from branch-selector performance claims.

## `d8dde10f514a501c` / track `651`

- Diagnosis source: `linked_route_worse_than_constant_velocity`
- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Verdict: **single_chain_no_branch_choice**
- Why it matters: The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help.
- Default linked-route FDE: 104.290 m
- Anchor-heading route FDE: 104.290 m
- Oracle upper-bound route FDE: 104.290 m
- Oracle recoverable FDE: 0.000 m
- Route candidate count: 1

Route candidates:

| Chain | Status | Heading score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | --- |
| 134 -> 143 -> 146 | `linked_lane_chain` | -0.077 | 104.290 m | 0.000 m | default, anchor_heading, oracle_upper_bound |

Recommended next actions:
- Audit lane topology depth, missing links, and selected-lane quality.
- Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.
- Keep this case separate from branch-selector performance claims.

## `5c49e681a66c720` / track `2627`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00010-of-00150`
- Ready: True
- Verdict: **oracle_branch_upper_bound_improves**
- Why it matters: Another parsed branch fits the observed future better, proving branch choice is a plausible source of the continuation regression.
- Default linked-route FDE: 38.598 m
- Anchor-heading route FDE: 38.598 m
- Oracle upper-bound route FDE: 35.297 m
- Oracle recoverable FDE: +3.301 m
- Route candidate count: 2

Route candidates:

| Chain | Status | Heading score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | --- |
| 285 -> 120 -> 119 | `linked_lane_chain` | 1.020 | 38.598 m | 0.000 m | default, anchor_heading |
| 285 -> 286 -> 287 | `linked_lane_chain` | 0.785 | 35.297 m | +3.301 m | oracle_upper_bound |

Recommended next actions:
- Add a richer non-oracle route prior using route context, traffic controls, or near-term intent cues.
- Use the oracle branch only as an upper-bound diagnostic, not as a deployed predictor.
- Rerun perturbation checks after adding the non-oracle prior.

## `e9db41e904b349a2` / track `406`

- Diagnosis source: `stable_route_choice_regression`
- Source: `validation.tfrecord-00007-of-00150`
- Ready: True
- Verdict: **single_chain_no_branch_choice**
- Why it matters: The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help.
- Default linked-route FDE: 38.292 m
- Anchor-heading route FDE: 38.292 m
- Oracle upper-bound route FDE: 38.292 m
- Oracle recoverable FDE: 0.000 m
- Route candidate count: 1

Route candidates:

| Chain | Status | Heading score | FDE | Gain vs default | Selector flags |
| --- | --- | ---: | ---: | ---: | --- |
| 295 -> 228 -> 201 | `linked_lane_chain` | 1.020 | 38.292 m | 0.000 m | default, anchor_heading, oracle_upper_bound |

Recommended next actions:
- Audit lane topology depth, missing links, and selected-lane quality.
- Try longer route-chain search only if the parsed topology remains public-safe and laptop-friendly.
- Keep this case separate from branch-selector performance claims.

## Interpretation

- Branchable cases show where the parsed map topology exposes more than one continuation from the selected lane.
- Oracle upper-bound improvements prove that a different parsed branch can reduce open-loop error, but they are not deployable predictor results because they use observed future motion.
- If the anchor-heading selector does not change the route, the next step is a richer prior, such as route context, signals, near-term intent, or a learned candidate scorer.
- Single-chain cases need longer topology, parser coverage, or a different selected lane before branch selection can help.
- Public outputs stay diagnostic; raw Waymo TFRecords and local packets remain ignored.
