# Data Provenance

ScenarioLens is intentionally honest about what is checked into git and what is
expected to live only on a developer machine.

## Current Public Demo Data

| Dataset in demo | Files | What it is | What it is not |
| --- | --- | --- | --- |
| Synthetic scenarios | `src/scenariolens/samples.py` | Hand-authored scenario records that exercise ranking, taxonomy, metrics, reports, and rendering. | Not recorded driving data and not a Waymo validation shard. |
| Native Waymo Motion JSON mini-slice | `docs/examples/waymo_motion_native_sample.json` | A tiny protobuf-shaped JSON fixture that mirrors key public Waymo Motion `Scenario` fields such as timestamps, SDC track index, tracks, states, object types, valid flags, velocities, objects of interest, and tracks to predict. | Not a downloaded Waymo Open Dataset file. |
| Normalized Waymo-shaped CSV fixture | `docs/examples/waymo_motion_normalized.csv` | A tiny row-wise fixture shaped like an extracted Motion slice so the CSV ingestion boundary can be tested without optional dependencies. | Not raw Waymo data and not benchmark evidence. |

The static explorer at `docs/demo/` is generated from these small fixtures so
the repository remains lightweight, reviewable, and safe to clone.

## No-Auth Technical Proof

When authenticated Waymo shard downloads are unavailable, ScenarioLens still
has a reproducible local technical path:

```bash
PYTHONPATH=src python3 -m scenariolens.cli baseline-ablation \
  --format markdown \
  --output docs/reports/baseline_ablation_study.md
```

The ablation compares constant velocity, default lane-aware matching, and a
stricter lane-aware matcher over the checked-in fixture corpus. It is not a
dataset-scale claim; it is a no-auth proof that the framework can compare
baseline assumptions, summarize map-use/fallback behavior, and publish a
public-safe report while gated downloads remain blocked.

## Real Dataset Path

ScenarioLens has a local workflow for a downloaded public Waymo Motion slice:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

This command writes a preflight summary, normalized ScenarioLens JSON, a ranked
Markdown report, a rendered SVG gallery, and a machine-readable manifest.

Raw downloaded dataset files are intentionally ignored by git. Keep them under
`data/raw/` and follow the official dataset access terms.

A local smoke run has been completed on one Waymo Motion v1.3.1 validation
shard. The summary is checked in at
[`docs/reports/waymo_motion_validation_summary.md`](reports/waymo_motion_validation_summary.md);
the aggregate case study is checked in at
[`docs/reports/waymo_motion_case_study.md`](reports/waymo_motion_case_study.md);
the raw shard, normalized scenario JSON, and generated SVG gallery remain local
ignored artifacts.

A follow-up cross-shard stability run has also been completed over four local
validation shards (`00007` through `00010`), covering 100 real scenarios and
418 evaluated baseline targets. The public-safe aggregate report is checked in
at
[`docs/reports/waymo_motion_failure_stability_cross_shard.md`](reports/waymo_motion_failure_stability_cross_shard.md).
The raw TFRecord files and per-scenario derived outputs remain ignored local
artifacts.

The same four-shard slice now has a lane-aware baseline diagnostic comparing
constant-velocity and lightweight map-following forecasts over 418 evaluated
prediction targets. The report is checked in at
[`docs/reports/waymo_lane_aware_baseline_cross_shard.md`](reports/waymo_lane_aware_baseline_cross_shard.md).
It publishes both improvements and regressions: in this run, the naive
lane-aware baseline improved several individual scenarios but regressed overall,
which is useful evidence for the next replay or richer-map baseline step.

A companion baseline-debug casebook is checked in at
[`docs/reports/waymo_lane_aware_debug_casebook.md`](reports/waymo_lane_aware_debug_casebook.md).
It summarizes one improvement, one regression, and one fallback-heavy scenario
selected from the 100-scenario lane-aware study. The public report includes
scenario IDs, metric summaries, fallback reasons, and interpretation only; the
local SVG overlays and per-case debug manifests remain ignored under
`data/processed/waymo_lane_aware_debug_casebook/`.

The replay candidate plan is checked in at
[`docs/reports/waymo_replay_candidate_plan.md`](reports/waymo_replay_candidate_plan.md).
It converts the debug casebook into a small queue for the next Waymax/JAX replay
experiment. It is intentionally framed as planning evidence: two cases are
ready for replay investigation and one fallback-heavy case is marked for
map-match audit before replay should be trusted.

The open-loop replay prototype is checked in at
[`docs/reports/waymo_open_loop_replay_prototype.md`](reports/waymo_open_loop_replay_prototype.md).
It reloads the two replay-ready local scenarios, evaluates four prediction
targets, and runs eight deterministic anchor-velocity perturbation trials. The
public report includes metric summaries and stability labels only; local replay
packets, SVG overlays, and raw TFRecords remain ignored. This is diagnostic
open-loop evidence, not Waymax/JAX execution or a closed-loop simulation claim.

The map-match threshold audit is checked in at
[`docs/reports/waymo_map_match_audit.md`](reports/waymo_map_match_audit.md).
It reloads the fallback-heavy case from the debug casebook, sweeps lane-match
thresholds, and publishes only target-level distance summaries plus aggregate
FDE deltas. In the current run, widening the threshold matched more lanes but
worsened FDE, which keeps the public claim honest: the next step is auditing
coordinate frames, lane coverage, and lane-selection logic, not simply
loosening the matcher.

The heading-aware lane-selection study is checked in at
[`docs/reports/waymo_heading_aware_lane_selection_study.md`](reports/waymo_heading_aware_lane_selection_study.md).
It compares the existing nearest-lane map baseline with a heading-aware selector
over the same four-shard, 100-scenario slice. The public report publishes
aggregate FDE deltas, map-used/fallback counts, and scenario IDs only. In this
run, heading-aware selection improves mean FDE by 0.489 m over nearest-lane
selection, but still trails constant velocity overall; that makes it an honest
ablation for matcher design, not a production model claim.

A companion heading-aware debug casebook is checked in at
[`docs/reports/waymo_heading_aware_debug_casebook.md`](reports/waymo_heading_aware_debug_casebook.md).
It selects six improvement, regression, and fallback-heavy cases from the same
study. The public copy includes scenario IDs, metric summaries, fallback
reasons, and interpretation only; local SVG overlays and per-case manifests
stay ignored under `data/processed/waymo_heading_aware_debug_casebook/`.

The heading-aware replay candidate plan is checked in at
[`docs/reports/waymo_heading_aware_replay_candidate_plan.md`](reports/waymo_heading_aware_replay_candidate_plan.md).
It reads the ignored heading-aware debug manifest and publishes only ranked
scenario IDs, aggregate queue counts, FDE deltas, readiness labels, blockers,
and recommended next actions. Local candidate manifests and overlays stay
ignored under `data/processed/waymo_heading_aware_replay_candidates/`.

The heading-aware replay prototype is checked in at
[`docs/reports/waymo_heading_aware_replay_prototype.md`](reports/waymo_heading_aware_replay_prototype.md).
It reloads all five heading-ready local scenarios from the current queue,
compares nearest-lane and heading-aware open-loop rollouts, and publishes
aggregate perturbation stability counts only. Local replay packets and SVG
overlays remain ignored under
`data/processed/waymo_heading_aware_replay_prototype/`.

The map and signal context study is checked in at
[`docs/reports/waymo_context_study_cross_shard.md`](reports/waymo_context_study_cross_shard.md).
It summarizes static map features, traffic-signal lane states, stop points,
and lane-topology hints over the same four local validation shards used by the
other 100-scenario diagnostics. The public report includes aggregate counts
and scenario IDs only; raw TFRecords and local manifests remain ignored.

The context-joined failure study is checked in at
[`docs/reports/waymo_context_failure_study_cross_shard.md`](reports/waymo_context_failure_study_cross_shard.md).
It joins those context summaries with ScenarioLens scores, constant-velocity
FDE, lane-aware deltas, map-used counts, and fallback counts. It is still a
public-safe diagnostic: raw records, local manifests, and per-scenario packets
stay ignored.

The context evaluation set is checked in at
[`docs/reports/waymo_context_eval_set.md`](reports/waymo_context_eval_set.md).
It is derived from the ignored context-failure manifest and publishes grouped
scenario IDs, selection reasons, metrics, and acceptance checks only. It does
not include raw trajectories, map packets, or per-scenario derived files.

The context eval debug casebook, replay-candidate plan, and open-loop replay
prototype are checked in at
[`docs/reports/waymo_context_eval_debug_casebook.md`](reports/waymo_context_eval_debug_casebook.md)
and
[`docs/reports/waymo_context_replay_candidate_plan.md`](reports/waymo_context_replay_candidate_plan.md)
and
[`docs/reports/waymo_context_open_loop_replay_prototype.md`](reports/waymo_context_open_loop_replay_prototype.md).
They reload selected context-eval scenario IDs locally and publish metrics,
readiness labels, blockers, replay stability counts, and next actions only.
Local SVG overlays, replay packets, per-track manifests, and raw Waymo files
remain ignored under `data/processed/` and `data/raw/`.

The context route/intent audit is checked in at
[`docs/reports/waymo_context_route_intent_audit.md`](reports/waymo_context_route_intent_audit.md).
It follows the stable context replay warning one step deeper by comparing
constant-velocity, nearest-lane, and heading-aware rollouts and publishing only
diagnosis labels, aggregate metrics, and route/topology hints. The current case
points to lane-continuity or route-link follow-up: the selected lane has
16.691 m remaining while the target travels 80.270 m over the horizon. Ignored
local route/intent packets stay under `data/processed/`.

The lane-link continuation prototype is checked in at
[`docs/reports/waymo_lane_continuation_prototype.md`](reports/waymo_lane_continuation_prototype.md).
It tests that follow-up without changing the default scorer. The fixture tests
prove parsed `exit_lanes` can extend a lane-following rollout, and the real
Waymo case resolves lane chain `144 -> 190 -> 193` after the lightweight reader
retains 240 map features per scenario. That cuts the clamped nearest-lane FDE by
63.578 m on the stable warning. Local prototype packets stay ignored under
`data/processed/`.

The lane-continuation validation study is checked in at
[`docs/reports/waymo_lane_continuation_study.md`](reports/waymo_lane_continuation_study.md).
It scans the same 100-scenario local slice for lane-end clamp candidates and
publishes aggregate/ranked diagnostics only: 223 candidate tracks, 210 linked
lane rollouts, 143 improvements, 63 regressions, and 13 topology gaps. Raw
Waymo files and ignored local manifests remain outside git.

The lane-continuation candidate plan is checked in at
[`docs/reports/waymo_lane_continuation_candidate_plan.md`](reports/waymo_lane_continuation_candidate_plan.md).
It reads the ignored local study manifest and publishes only a public-safe
queue of 15 scenario/track IDs: five replay controls, five regression debug
targets, and five topology-audit blockers.

The lane-continuation replay prototype is checked in at
[`docs/reports/waymo_lane_continuation_replay_prototype.md`](reports/waymo_lane_continuation_replay_prototype.md).
It reloads the same local source shards through the ignored candidate manifest,
publishes 10 target-track replay summaries, 40 deterministic perturbation
trials, and 5 topology probes, and keeps local replay packets under ignored
`data/processed/` paths.

The lane-continuation route diagnostics report is checked in at
[`docs/reports/waymo_lane_continuation_route_diagnostics.md`](reports/waymo_lane_continuation_route_diagnostics.md).
It reads the ignored replay manifest and publishes only derived diagnostic
labels and aggregate counts: stable route-choice regressions, horizon-limit
cases, link-worse-than-constant-velocity cases, and topology blockers.

The lane-continuation branch-selection diagnostic is checked in at
[`docs/reports/waymo_lane_continuation_branch_selection.md`](reports/waymo_lane_continuation_branch_selection.md).
It reads ignored replay/diagnostic manifests, reloads local shards, and
publishes only derived branch-sweep metrics: 5 continuation regression cases,
3 branchable parsed-topology cases, 2 single-chain cases, 3 non-oracle
motion-context improvements, and 3 oracle upper-bound improvements. The
motion-context selector uses recent speed, forecast horizon, route-chain
length, and downstream lane speed limits; the oracle branch uses observed
future motion only as a diagnostic upper bound. Local branch manifests remain
ignored under `data/processed/`.

The motion-context branch replay diagnostic is checked in at
[`docs/reports/waymo_lane_continuation_branch_replay.md`](reports/waymo_lane_continuation_branch_replay.md).
It reads the ignored branch-selection manifest, reloads the two branchable
local Waymo cases, and publishes only branch/gain stability summaries: 8
deterministic perturbation trials, 8 branch-preserving trials, 4 stable-gain
trials, 1 branch accepted for broader selector evaluation, 1 route-context
margin follow-up, and a +0.557 m minimum accepted robustness margin. The same
report also checks an experimental history-speed-prior replay score; it
preserves 1 accepted case and leaves the route-context margin case held.
Raw TFRecords and local replay packets remain ignored.

The branch rollout gate is checked in at
[`docs/reports/waymo_lane_continuation_branch_rollout_gate.md`](reports/waymo_lane_continuation_branch_rollout_gate.md).
It reads the ignored branch-replay manifest and publishes only promote/hold
decisions derived from the replay summary: 2 replayed cases, 1 branch
promoted for broader selector evaluation, 1 route-context margin hold, and 0
selector-stability holds. This is release-style evidence triage, not a
production release process or route planner.

The route-context guard study is checked in at
[`docs/reports/waymo_lane_continuation_route_context_guard.md`](reports/waymo_lane_continuation_route_context_guard.md).
It reads ignored branch-selection and branch-replay manifests, then publishes
only derived guard decisions and route-feature deltas: 2 motion-context branch
candidates, 1 guard promotion, 1 guard hold, 2/2 replay-gate matches, 0 false
promotions, and 0 false holds. The guard uses route fit, endpoint alignment,
and downstream speed-limit context; replay outcomes are used only to evaluate
the guard, not to choose a branch. Raw TFRecords and local replay packets
remain ignored.

The route-context guard calibration is checked in at
[`docs/reports/waymo_lane_continuation_route_context_guard_calibration.md`](reports/waymo_lane_continuation_route_context_guard_calibration.md).
It reads the ignored route-context guard manifest, sweeps a small
endpoint-alignment gate grid, and publishes only derived policy summaries. On
the current 2-case guard queue it preserves 0 false holds with the current
-0.05 endpoint gate, while keeping false promotions at 0.
The report does not commit raw data, does not change the default guard, and
explicitly notes that the current queue lacks replay-rejected negative controls.

The branch coverage audit is checked in at
[`docs/reports/waymo_lane_continuation_branch_coverage.md`](reports/waymo_lane_continuation_branch_coverage.md).
It reads ignored candidate, replay, route-diagnostic, branch-selection,
branch-replay, and route-context guard manifests, then publishes only a derived
coverage funnel and expansion queue: 15 continuation candidates, 10
replay-ready candidates, 5 branch-selection cases, 3 branchable cases, 1
route-guard promotion, 5 topology blockers, and 8 expansion items. It does not
read raw Waymo TFRecords and is not a benchmark coverage claim.

The expanded branch coverage audit is checked in at
[`docs/reports/waymo_lane_continuation_branch_coverage_expanded.md`](reports/waymo_lane_continuation_branch_coverage_expanded.md),
with the paired expanded guard calibration at
[`docs/reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md`](reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md).
These reports read ignored expanded manifests only. They raise the same
100-scenario local slice to 30 continuation candidates, 20 replay cases, 10
topology probes, 10 branch-selection cases, 6 branchable cases, 1 accepted
branch replay, and 1 replay-held route-context margin negative. The expanded
guard/calibration pass records 2/2 replay-gate matches with 0 false holds and
0 false promotions on that small replay queue. Raw TFRecords and local replay
packets remain ignored, and this is still not a full Waymo benchmark claim.

The expanded topology gap audit is checked in at
[`docs/reports/waymo_lane_continuation_topology_gap_audit_expanded.md`](reports/waymo_lane_continuation_topology_gap_audit_expanded.md).
It reloads the 10 topology blockers from the expanded replay manifest and
publishes only derived topology classifications: 0 cap-recoverable linked
targets, 10 terminal/directional selected lanes, 0 raw target misses, and 5 maps
at the feature cap. The paired expanded terminal-neighborhood audit, replay
gate, and selector experiment are checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md),
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md),
and
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md).
Those reports inspect 10 terminal/directional cases, find 6 nearby recovery
candidates and 4 directional gaps, replay the 6 ready recovery candidates,
accept 3 under perturbation gates, and promote 1 candidate under a bounded
non-oracle selector. Raw Waymo records, raw map geometry, and per-case local
packets remain ignored.

The topology gap audit is checked in at
[`docs/reports/waymo_lane_continuation_topology_gap_audit.md`](reports/waymo_lane_continuation_topology_gap_audit.md).
It reloads the ignored local source scenarios referenced by the replay manifest,
then publishes only derived topology classifications: 5 topology blockers
audited, 0 cap-recoverable blocker cases, 5 terminal or directional-link
confirmations, 0 raw target misses, and 2 maps at or above the base feature cap.
Raw Waymo records and local per-case packets remain ignored.

The terminal-neighborhood audit is checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_audit.md`](reports/waymo_lane_continuation_terminal_neighborhood_audit.md).
It reloads only the 5 terminal/directional blocker cases, inspects bounded
nearby-lane metadata, and publishes derived decisions: 2 nearby alternate-lane
recovery candidates, 3 directional-link mismatches, and 0 true terminal/map
boundary cases in the current queue. It does not publish raw map geometry or
change selector behavior.

The terminal-neighborhood replay gate is checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_replay.md`](reports/waymo_lane_continuation_terminal_neighborhood_replay.md).
It force-replays the 2 nearby recovery candidates, applies 8 deterministic
perturbation trials, and publishes derived gate decisions: 1 alternate lane is
accepted for a bounded selector experiment and 1 candidate is held because the
alternate regresses. Raw Waymo records, local per-case packets, and map geometry
remain ignored.

The terminal-neighborhood selector experiment is checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector.md).
It applies a bounded, non-oracle geometry and route-extension policy to those 2
replay candidates, promoting 1 alternate lane, holding 1 low-heading case, and
matching the replay gate on 2/2 decisions. Replay labels validate the selector
after the policy decision; they are not selector inputs.

The expanded terminal-neighborhood selector calibration is checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md).
It sweeps 30 distance/heading/route-extension gate candidates over 6 derived
replay cases, recommends a provisional 40 m route-extension gate, and improves
replay-label agreement from 4/6 to 6/6 with 0 false promotions on this queue.
The default selector is unchanged, and raw Waymo records plus map geometry
remain local and ignored.

The expanded terminal-neighborhood selector casebook is checked in at
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md).
It converts those 6 calibration cases into derived SVG decision cards under
[`docs/reports/assets/`](reports/assets/): 3 replay-accepted recoveries, 3
held negative controls, and the current versus recommended selector decision
for each case. The cards show metric bars for replay gain, route extension,
heading alignment, and alternate-lane distance; they do not publish raw
trajectory points or raw map polylines.

The 200-scenario lane-continuation scale-up is checked in at
[`docs/reports/waymo_lane_continuation_study_200.md`](reports/waymo_lane_continuation_study_200.md),
[`docs/reports/waymo_lane_continuation_replay_prototype_200.md`](reports/waymo_lane_continuation_replay_prototype_200.md),
[`docs/reports/waymo_lane_continuation_topology_gap_audit_200.md`](reports/waymo_lane_continuation_topology_gap_audit_200.md),
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_replay_200.md),
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md),
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md),
and
[`docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md).
It scans 50 scenarios per local validation shard, for 200 scenarios total,
and publishes only derived metrics: 451 lane-continuation targets, 45
replay/audit cases, 15 topology blockers, 7 terminal-neighborhood replay
candidates, a selector transfer validation over 4 novel cases, and 7 derived
selector cards. The broader calibration improves selector/replay agreement
from 4/7 to 6/7 with 0 false promotions, while transfer validation of the
6-case provisional policy reaches 5/7 with 0 false promotions and 2 false
holds; both artifacts treat the remaining false holds as open limitations, not
production-ready selector claims.

## Interpretation Rules

- Checked-in metrics demonstrate the ScenarioLens pipeline, not Waymo benchmark
  performance.
- Synthetic scenarios are useful for testing expected long-tail patterns before
  spending time on large downloads.
- Waymo-shaped fixtures prove field mapping and ingestion behavior, not dataset
  scale.
- The checked-in validation and stability reports document small local
  real-data runs, not full Waymo benchmark submissions.
