# ScenarioLens Branch Coverage Audit

This audit connects the lane-continuation candidate queue, replay prototype, route diagnostics, branch selection, branch replay, and route-context guard into one evidence funnel. Its job is to make the current bottleneck explicit: only a small subset of continuation failures is branchable today, so the next v1.0 work should expand topology/parser coverage and route-context guard coverage before claiming broader selector readiness.

It is intentionally public-safe. It reads summary manifests only, publishes counts and scenario identifiers, and is not a Waymo benchmark claim.

## Scope

- Candidate manifest: `data/processed/waymo_lane_continuation_candidates/manifest.json`
- Replay manifest: `data/processed/waymo_lane_continuation_replay_prototype/manifest.json`
- Diagnostics manifest: `data/processed/waymo_lane_continuation_route_diagnostics/manifest.json`
- Branch-selection manifest: `data/processed/waymo_lane_continuation_branch_selection/manifest.json`
- Branch-replay manifest: `data/processed/waymo_lane_continuation_branch_replay/manifest.json`
- Route-context guard manifest: `data/processed/waymo_lane_continuation_route_context_guard/manifest.json`
- Ready: True
- Raw scenario data committed: no
- Local replay packets committed: no

## Coverage Summary

| Metric | Value |
| --- | ---: |
| Continuation candidates | 15 |
| Replay-ready candidates | 10 |
| Regression-debug candidates | 5 |
| Topology-audit candidates | 5 |
| Route diagnostics | 10 |
| Branch-selection cases | 5 |
| Branchable cases | 3 |
| Single-chain cases | 2 |
| Motion-context branch improvements | 2 |
| Branch-replay cases | 2 |
| Route-guard promotions | 1 |
| Route-guard holds | 1 |
| Topology blockers | 5 |
| Expansion queue items | 8 |
| Branchable coverage of candidates | 20.0% |
| Branchable coverage of branch-selection cases | 60.0% |
| Route-guard promotion coverage of candidates | 6.7% |

## Funnel

| Stage | Count | Conversion | What it proves | Next action |
| --- | ---: | ---: | --- | --- |
| Continuation candidates | 15 | n/a | ScenarioLens found continuation cases worth replay or topology audit. | Keep this as the broad local queue for v1.0 expansion. |
| Replay/probe selected queue | 15 | 100.0% | Candidates selected for replay controls, regression replay, or topology probes. | Broaden top-per-bucket when raw-data budget allows. |
| Replayed cases | 10 | 66.7% | Improvement controls and regression-debug targets were replayed. | Keep topology probes separate from replay evidence. |
| Route diagnostics | 10 | n/a | Replayed regressions and topology blockers have named failure labels. | Use labels to separate route-choice work from parser/topology work. |
| Branch-selection cases | 5 | 50.0% | Regression diagnostics were reloaded and branch-swept. | Increase alternatives by improving topology parsing and search depth. |
| Branchable cases | 3 | 60.0% | Parsed map topology exposed multiple continuations. | Use these as selector/guard evidence, not as whole-dataset coverage. |
| Motion-context improvements | 2 | 66.7% | A non-oracle branch selector improved FDE on branchable cases. | Replay and guard these before changing selector defaults. |
| Route-guard promotions | 1 | 50.0% | Strict route-context guard accepted a branch for broader evaluation. | Treat this as the positive control for expanding the queue. |

## Bottlenecks

| Bottleneck | Count | Evidence | Expansion move |
| --- | ---: | --- | --- |
| `topology_parser_gap` | 5 | missing_linked_feature: 2, terminal_lane_or_parser_gap: 3 | Audit missing linked features, terminal lanes, and parser feature caps before expanding branch replay. |
| `single_chain_no_branch_choice` | 2 | e3f6a29b59e42c1 / track 741, e9db41e904b349a2 / track 406 | Expose alternate continuations through deeper topology search, better selected-lane choice, or richer lane-link parsing. |
| `route_context_margin_hold` | 1 | d30709cd60e60395 / track 164 | Add endpoint-alignment, downstream topology, traffic-control, and speed-limit context before selector rollout. |
| `narrow_regression_branch_queue` | 5 | 5 regression-debug candidates feed the current branch-selection stage. | After topology blockers shrink, raise top-per-bucket and rerun continuation replay, route diagnostics, branch selection, replay, and guard reports. |

## Expansion Queue

| Rank | Type | Scenario | Track | Source | Why it matters | First next action |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `route_context_margin` | `d30709cd60e60395` | `164` | `validation.tfrecord-00007-of-00150` | The branch has nominal recoverable FDE, but route-context guardrails fired: endpoint_alignment_drop. | Collect richer route-context evidence before promoting this branch. |
| 2 | `single_chain_branch_expansion` | `e3f6a29b59e42c1` | `741` | `validation.tfrecord-00008-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 3 | `single_chain_branch_expansion` | `e9db41e904b349a2` | `406` | `validation.tfrecord-00007-of-00150` | The parsed topology exposes only one usable linked chain, so this case needs richer topology or a different selected lane before branch selection can help. | Audit lane topology depth, missing links, and selected-lane quality. |
| 4 | `topology_parser_gap` | `6bdc7f92afefff73` | `59` | `validation.tfrecord-00009-of-00150` | The selected feature references a continuation that the lightweight parser did not make usable. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 5 | `topology_parser_gap` | `2f366a31ab03f8b` | `1061` | `validation.tfrecord-00007-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 6 | `topology_parser_gap` | `74a5b3325a534a87` | `3178` | `validation.tfrecord-00010-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 7 | `topology_parser_gap` | `2f035a284480e981` | `715` | `validation.tfrecord-00010-of-00150` | The selected feature references a continuation that the lightweight parser did not make usable. | Audit the selected map feature's parsed entry/exit lane IDs. |
| 8 | `topology_parser_gap` | `4dfe7c285670839f` | `0` | `validation.tfrecord-00008-of-00150` | The selected lane appears terminal or lacks parsed exit/entry links even though the target continues beyond it. | Audit the selected map feature's parsed entry/exit lane IDs. |

## Source Coverage

| Source | Candidates | Branch-selection cases | Branchable | Guard promotions | Guard holds |
| --- | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 4 | 2 | 1 | 0 | 1 |
| `validation.tfrecord-00008-of-00150` | 2 | 1 | 0 | 0 | 0 |
| `validation.tfrecord-00009-of-00150` | 5 | 1 | 1 | 1 | 0 |
| `validation.tfrecord-00010-of-00150` | 4 | 1 | 1 | 0 | 0 |

## Interpretation

- The current branch selector is real but narrow: it promotes evidence only where parsed topology exposes multiple continuations.
- Single-chain cases are useful negative evidence. They show that route-choice scoring cannot help until topology coverage, selected lane choice, or search depth exposes alternatives.
- Topology-audit cases are the highest-leverage expansion path because they turn missing or terminal lane links into measurable parser/map-coverage work.
- Route-context holds stay held. The audit records them as follow-up work instead of quietly counting them as selector wins.
- This is not a benchmark or production rollout claim; it is a framework coverage audit for deciding what evidence to collect next.
