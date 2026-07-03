# Case Study: Finding Baseline Motion-Prediction Failures

This case study is the recruiter-facing technical story for ScenarioLens.

## Question

Which Waymo Motion scenarios are most useful for evaluating a simple
motion-prediction baseline?

## Method

ScenarioLens loads a local Waymo Motion validation shard, extracts the fields
needed for motion analysis, evaluates a constant-velocity baseline on prediction
targets, and groups the results by scenario tags and score components.

The public report avoids raw gated data. It publishes aggregate statistics,
scenario IDs, tags, and reproducible commands.

## Current Evidence

- Real-slice failure study:
  [`docs/reports/waymo_motion_failure_study.md`](../reports/waymo_motion_failure_study.md)
- Failure distribution stability study:
  [`docs/reports/waymo_motion_failure_stability.md`](../reports/waymo_motion_failure_stability.md)
- Cross-shard failure stability study:
  [`docs/reports/waymo_motion_failure_stability_cross_shard.md`](../reports/waymo_motion_failure_stability_cross_shard.md)
- Shard expansion plan:
  [`docs/reports/waymo_motion_shard_plan.md`](../reports/waymo_motion_shard_plan.md)
- Map-match threshold audit:
  [`docs/reports/waymo_map_match_audit.md`](../reports/waymo_map_match_audit.md)
- Heading-aware lane-selection study:
  [`docs/reports/waymo_heading_aware_lane_selection_study.md`](../reports/waymo_heading_aware_lane_selection_study.md)
- Heading-aware debug casebook:
  [`docs/reports/waymo_heading_aware_debug_casebook.md`](../reports/waymo_heading_aware_debug_casebook.md)
- Heading-aware replay candidate plan:
  [`docs/reports/waymo_heading_aware_replay_candidate_plan.md`](../reports/waymo_heading_aware_replay_candidate_plan.md)
- Heading-aware replay prototype:
  [`docs/reports/waymo_heading_aware_replay_prototype.md`](../reports/waymo_heading_aware_replay_prototype.md)
- Context open-loop replay prototype:
  [`docs/reports/waymo_context_open_loop_replay_prototype.md`](../reports/waymo_context_open_loop_replay_prototype.md)

The current local evidence includes the original 75-scenario windowed study and
a true cross-shard run over four validation shards, covering 100 real scenarios
and 418 evaluated prediction targets. The cross-shard report shows mean FDE
varying from 21.20 m to 28.89 m across sampled shards, with cyclist interaction
the most variable shared tag. The follow-up map-match audit shows that simply
widening the lane-match threshold on a fallback-heavy case makes FDE worse, so
the next matcher work should focus on lane coverage, coordinate frames, heading,
and route/intent priors. The heading-aware lane-selection study takes that next
step as an ablation: it improves mean FDE by 0.489 m relative to nearest-lane
selection over the same 418 prediction targets, while still trailing constant
velocity overall. The heading-aware debug casebook then connects six selected
cases to ignored local SVG overlays, per-track metrics, heading-alignment
diagnostics, and fallback reasons. The heading-aware replay candidate plan
then ranks those six cases into replay-ready improvement/regression targets and
a map-match audit case before making any heavier simulation claim. The
heading-aware replay prototype then reloads all five heading-ready cases, runs
nearest-lane vs heading-aware rollouts with deterministic perturbations, and
shows the expected selector sign is stable across the current local slice. The
context replay prototype then executes the two context replay-ready eval seeds:
one stable lane-aware regression warning and one sensitive positive control.
The route/intent audit then follows the stable warning and identifies a concrete
lane-continuity follow-up: the target travels much farther than the remaining
matched-lane polyline over the forecast horizon.
The lane-link continuation prototype then tests that hypothesis. It proves the
mechanism on a deterministic linked-lane fixture and resolves the real stable
warning's parsed lane chain `144 -> 190 -> 193`, cutting the clamped
nearest-lane FDE by 63.578 m on that case.
The lane-continuation validation study then scans the same 100-scenario local
Waymo slice and finds 209 lane-end clamp candidates after linked-lane closure
materialization: 133 improve with linked lanes, 57 regress, and 17 remain
topology gaps.
The candidate plan then promotes 15 rows into concrete follow-up queues: five
replay controls, five regression debug targets, and five topology-audit
blockers.
The lane-continuation replay prototype executes those queued rows as 10
target-track replay cases, 40 deterministic perturbation trials, and five
topology probes. The replay pass preserves the expected improvement/regression
signs on all perturbation trials while keeping topology gaps framed as blockers.
The route diagnostics report then classifies the follow-up work: three stable
route-choice regressions, one horizon-limit case, one linked route that is worse
than constant velocity, and five topology blockers.
The branch-selection diagnostic then sweeps parsed alternatives for the five
continuation regression diagnostics. Two cases expose branch alternatives with
motion-context and oracle upper-bound gains, three cases have only a single
parsed chain, and the simple anchor-heading selector improves none of them.
That is useful evidence: recent speed, horizon length, route-chain length, and
downstream speed limits can recover some branch-choice error without using the
observed future trajectory.
The follow-up branch replay diagnostic then replays those two motion-context
branch choices under eight deterministic perturbations. The selected branch is
preserved in all eight trials, positive recoverable FDE holds in all eight
trials, both branches are accepted for broader selector evaluation, and the
minimum robustness margin is +28.627 m. A simple history-speed-prior replay
ablation preserves both accepted cases, so the sharper policy target becomes
guard calibration and broader branchable coverage rather than speed smoothing.
The branch rollout gate then converts those replay outcomes into a
release-style promote/hold queue: both replayed motion-context branches are
promoted for broader selector evaluation. The stricter route-context guard stays
more conservative: it promotes 1 branch, holds 1 accepted replay candidate for
route-feature follow-up, and records that false hold as calibration evidence.
The follow-up calibration sweep tests endpoint-alignment gates against those
replay labels and recommends a provisional -0.25 gate that would promote both
accepted replay candidates on this queue, while explicitly noting that broader
negative-control coverage is still missing.
The branch coverage audit then zooms out and turns the limitation into a
measurable expansion queue: 15 continuation candidates, 10 replay-ready
candidates, 5 branch-selection cases, 3 branchable cases, 1 route-guard
promotion, 5 topology blockers, and 8 named expansion items.

The topology gap audit follows the largest blocker class directly. After
linked-lane closure materialization, the 100-scenario study now finds 209
lane-continuation candidates, 133 linked-lane improvements, and 17 topology
gaps. The top replay blockers are now 2 cap-recoverable cases and 3 terminal or
directional-link cases with no raw target misses, turning the next step into
selected-lane neighborhood and guard-calibration work.

The terminal-neighborhood audit then reloads those 3 terminal/directional
blockers and asks a sharper map-selection question: is the selected lane truly
terminal, or is there a nearby heading-aligned lane with parsed continuation?
On the current slice, 2 cases have nearby alternate-lane recovery candidates
and 1 case is a directional-link mismatch. Those are not promoted as selector
wins yet; they become replay and gating targets for the next branch-queue pass.

The terminal-neighborhood replay gate now force-replays those 2 nearby recovery
candidates against the selected terminal lanes. One alternate lane passes the
gate with a +125.481 m nominal FDE gain and 4/4 stable perturbation trials; the
other regresses and remains held as diagnostic evidence. That gives the next
selector experiment one bounded promotion target without pretending every
nearby lane is better.

The terminal-neighborhood selector experiment then applies a non-oracle
geometry and route-extension policy to those 2 replay cases. It promotes the
heading-aligned alternate lane, holds the low-heading regression case, and
matches the replay gate on 2/2 decisions, turning the replay result into a
testable selector rule rather than a hand-picked claim.

## Why It Matters

Autonomy teams need tooling that finds where average-case performance hides
long-tail weaknesses. ScenarioLens demonstrates that workflow on public-data
boundaries: ingest a slice, score the scenario, evaluate a baseline, group the
failures, and produce reviewable evidence.

## Next Step

Broaden the terminal-neighborhood selector experiment, expose alternatives for
the two single-chain branch-selection cases, validate route-context guard
calibration on expanded negative controls, and expand the closure-enabled
branch queue beyond shards `00007` through `00010`.
