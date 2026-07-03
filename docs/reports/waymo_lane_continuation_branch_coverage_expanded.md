# ScenarioLens Expanded Branch Coverage Audit

This expanded audit raises the lane-continuation queue size before connecting the candidate queue, replay prototype, route diagnostics, branch selection, branch replay, and route-context guard into one evidence funnel.
Its job is to show whether a broader real-slice queue produces more branchable cases, selector evidence, topology blockers, and route-context negative controls before ScenarioLens claims broader selector readiness.

It is intentionally public-safe. It reads summary manifests only, publishes counts and scenario identifiers, and is not a Waymo benchmark claim.

## Scope

- Candidate manifest: `data/processed/waymo_lane_continuation_candidates_expanded/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json`
- Diagnostics manifest: `data/processed/waymo_lane_continuation_route_diagnostics_expanded/manifest.json`
- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection_expanded/manifest.json`
- Branch-replay manifest: `data/processed/waymo_lane_continuation_branch_replay_expanded/manifest.json`
- Route-context guard manifest: `data/processed/waymo_lane_continuation_route_context_guard_expanded/manifest.json`
- Ready: True
- Raw scenario data committed: no
- Local replay packets committed: no

## Coverage Summary

| Metric | Value |
| --- | ---: |
| Continuation candidates | 30 |
| Replay-ready candidates | 20 |
| Regression-debug candidates | 10 |
| Topology-audit candidates | 10 |
| Route diagnostics | 20 |
| Branch-selection cases | 10 |
| Branchable cases | 6 |
| Single-chain cases | 4 |
| Motion-context branch improvements | 2 |
| Branch-replay cases | 2 |
| Route-guard promotions | 1 |
| Route-guard holds | 1 |
| Topology blockers | 10 |
| Expansion queue items | 15 |
| Branchable coverage of candidates | 20.0% |
| Branchable coverage of branch-selection cases | 60.0% |
| Route-guard promotion coverage of candidates | 3.3% |

## Funnel

| Stage | Count | Conversion | What it proves | Next action |
| --- | ---: | ---: | --- | --- |
| Continuation candidates | 30 | n/a | ScenarioLens found continuation cases worth replay or topology audit. | Keep this as the broad local queue for v1.0 expansion. |
| Replay/probe selected queue | 30 | 100.0% | Candidates selected for replay controls, regression replay, or topology probes. | Broaden top-per-bucket when raw-data budget allows. |
| Replayed cases | 20 | 66.7% | Improvement controls and regression-debug targets were replayed. | Keep topology probes separate from replay evidence. |
| Route diagnostics | 20 | n/a | Replayed regressions and topology blockers have named failure labels. | Use labels to separate route-choice work from parser/topology work. |
| Branch-selection cases | 10 | 50.0% | Regression diagnostics were reloaded and branch-swept. | Increase alternatives by improving topology parsing and search depth. |
| Branchable cases | 6 | 60.0% | Parsed map topology exposed multiple continuations. | Use these as selector/guard evidence, not as whole-dataset coverage. |
| Motion-context improvements | 2 | 33.3% | A non-oracle branch selector improved FDE on branchable cases. | Replay and guard these before changing selector defaults. |
| Route-guard promotions | 1 | 50.0% | Strict route-context guard accepted a branch for broader evaluation. | Treat this as the positive control for expanding the queue. |

## Bottlenecks

| Bottleneck | Count | Evidence | Expansion move |
| --- | ---: | --- | --- |
| `topology_parser_gap` | 10 | missing_linked_feature: 3, terminal_lane_or_parser_gap: 7 | Audit missing linked features, terminal lanes, and parser feature caps before expanding branch replay. |
| `single_chain_no_branch_choice` | 4 | e3f6a29b59e42c1 / track 741, d8dde10f514a501c / track 651, 65d7afd24453a1ba / track 508, plus 1 more | Expose alternate continuations through deeper topology search, better selected-lane choice, or richer lane-link parsing. |
| `route_context_margin_hold` | 1 | 5c49e681a66c720 / track 2627 | Add endpoint-alignment, downstream topology, traffic-control, and speed-limit context before selector rollout. |
| `narrow_regression_branch_queue` | 10 | 10 regression-debug candidates feed the current branch-selection stage. | After topology blockers shrink, raise top-per-bucket and rerun continuation replay, route diagnostics, branch selection, replay, and guard reports. |

## Expansion Queue

| Rank | Type | Scenario | Track | Source | Why it matters | First next action |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `route_context_margin` | `5c49e681a66c720` | `2627` | `validation.tfrecord-00010-of-00150` | The branch has nominal recoverable FDE, but route-context guardrails fired: endpoint_alignment_drop, downstream_speed_limit_drop. | Add turn-lane, downstream topology, and traffic-control context before selector rollout. |
| 2 | `single_chain_branch_expansion` | `e3f6a29b59e42c1` | `741` | `validation.tfrecord-00008-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 3 | `single_chain_branch_expansion` | `d8dde10f514a501c` | `651` | `validation.tfrecord-00010-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 4 | `single_chain_branch_expansion` | `65d7afd24453a1ba` | `508` | `validation.tfrecord-00008-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 5 | `single_chain_branch_expansion` | `e9db41e904b349a2` | `406` | `validation.tfrecord-00007-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 6 | `topology_parser_gap` | `6bdc7f92afefff73` | `59` | `validation.tfrecord-00009-of-00150` | The selected feature references a continuation that the lightweight parser did not make usable. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 7 | `topology_parser_gap` | `2f366a31ab03f8b` | `1061` | `validation.tfrecord-00007-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 8 | `topology_parser_gap` | `74a5b3325a534a87` | `3178` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 9 | `topology_parser_gap` | `2f035a284480e981` | `715` | `validation.tfrecord-00010-of-00150` | The selected feature references a continuation that the lightweight parser did not make usable. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 10 | `topology_parser_gap` | `4dfe7c285670839f` | `0` | `validation.tfrecord-00008-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 11 | `topology_parser_gap` | `f672132039e83c40` | `519` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 12 | `topology_parser_gap` | `f672132039e83c40` | `520` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 13 | `topology_parser_gap` | `f672132039e83c40` | `522` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 14 | `topology_parser_gap` | `fe4a6425278fbd5b` | `816` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 15 | `topology_parser_gap` | `c45b209a75ff4610` | `1869` | `validation.tfrecord-00009-of-00150` | The selected feature references a continuation that the lightweight parser did not make usable. | Audit the selected map feature's parsed entry/exit lane IDs. |

## Source Coverage

| Source | Candidates | Branch-selection cases | Branchable | Guard promotions | Guard holds |
| --- | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 7 | 3 | 2 | 0 | 0 |
| `validation.tfrecord-00008-of-00150` | 5 | 2 | 0 | 0 | 0 |
| `validation.tfrecord-00009-of-00150` | 8 | 2 | 2 | 1 | 0 |
| `validation.tfrecord-00010-of-00150` | 10 | 3 | 2 | 0 | 1 |

## Interpretation

- The current branch selector is real but narrow: it promotes evidence only where parsed topology exposes multiple continuations.
- Single-chain cases are useful negative evidence. They show that route-choice scoring cannot help until topology coverage, selected lane choice, or search depth exposes alternatives.
- Topology-audit cases are the highest-leverage expansion path because they turn missing or terminal lane links into measurable parser/map-coverage work.
- Route-context holds stay held. The audit records them as follow-up work instead of quietly counting them as selector wins.
- This is not a benchmark or production rollout claim; it is a framework coverage audit for deciding what evidence to collect next.
