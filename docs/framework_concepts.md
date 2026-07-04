# Framework Concepts

ScenarioLens is organized as a small evaluation framework. Each layer has a
clear data boundary so the project can grow without becoming a one-off demo.

```text
Dataset Adapter
-> Scenario Schema
-> Metrics
-> Baseline Evaluator
-> Lane-Selection Study
-> Debug Casebook
-> Replay Candidate Plan
-> Open-Loop Replay Prototype
-> Map-Match Audit
-> Reports
-> Explorer
```

## Dataset Adapter

Adapters convert raw or fixture data into the ScenarioLens schema. Current
inputs include synthetic scenarios, row-wise CSV, Waymo Motion-shaped JSON/CSV,
binary Scenario protos, and small Motion TFRecord shards.

## Scenario Schema

The schema is intentionally compact: scenario metadata, agent tracks, typed
states, tags, and evaluation metadata such as Waymo prediction targets. This is
the stable boundary between ingestion, metrics, reports, and the dashboard.

## Metrics

Metrics are interpretable by design: vulnerable road users, density, proximity,
path conflict, screened TTC, dynamics, taxonomy tags, and baseline failure
evidence. ScenarioLens ranks scenarios by review value, not by a certified
safety score.

## Baseline Evaluator

The default evaluator is a constant-velocity prediction baseline. It computes
ADE, FDE, max FDE, miss rate, and a failure score on prediction targets. A
second lane-aware comparison baseline uses parsed lane polylines for
vehicle/cyclist targets when map context is available, then falls back to
constant velocity for pedestrians, missing maps, low-speed tracks, or distant
lane matches. This keeps the core baseline stable while showing how map context
can reduce forecast error on curved-road cases.

## Lane-Selection Study

The lane-selection study is an ablation for improving the map baseline without
changing the default scorer. It compares the existing nearest-lane selector
against a heading-aware selector that prefers lane tangents aligned with the
target's anchor velocity. The current real-data study shows a small FDE
improvement over nearest-lane selection while still trailing constant velocity
overall, so it is evidence for matcher iteration rather than a production
prediction claim.

## Debug Casebook

The debug casebook turns a baseline comparison or lane-selection study into
selected examples: improvements, regressions, and fallback-heavy cases. Local
artifacts include SVG overlays, per-track error timelines, lane-match distance,
heading-alignment diagnostics, and fallback reasons. Public copies keep the raw
trajectories and local debug manifests out of git while preserving the
interpretation.

## Replay Candidate Plan

The replay candidate plan is the bridge from scenario mining to simulation. It
reads a debug casebook, ranks cases by replay priority, and labels each one as
ready for improvement replay, ready for regression replay, or requiring a
map-match audit first. It is a planning artifact for future Waymax/JAX work,
not a claim that replay simulation is already complete.

## Open-Loop Replay Prototype

The replay prototype is the first executable step after planning. It reloads
the replay-ready local scenarios, reruns constant-velocity and lane-aware
rollouts from the same anchor state, and applies small deterministic
anchor-velocity perturbations. The output is a public-safe stability report:
which diagnostics preserve their expected improvement/regression sign, which
are sensitive to small state changes, and which cases should remain blocked on
map matching. It is still open-loop evaluation, not closed-loop simulation.

## Route/Intent Audit

The route/intent audit follows stable replay regressions that survived
perturbation checks. It reloads the local scenario, compares constant-velocity,
nearest-lane, and heading-aware rollouts, and labels whether the case points to
heading selection, lane continuity, route/topology hints, or manual review. It
does not infer an official route or change the default scorer; it decides what
the next engineering experiment should be.

## Lane-Link Continuation

Lane-link continuation is the next experiment for lane-continuity cases. The
single-case prototype follows parsed `exit_lanes` or `entry_lanes` for a small
number of hops and compares the result against constant velocity, nearest-lane,
and heading-aware rollouts. The validation study then scans scenario inputs for
lane-end clamp candidates and ranks linked-lane improvements, regressions, and
topology gaps. The candidate plan turns those ranked rows into replay controls,
regression debug targets, and topology-audit blockers. The replay prototype
then executes the queued replay rows under deterministic perturbations and
keeps topology probes as blockers. The route-diagnostics report then separates
stable route-choice regressions, horizon-limit cases, link-worse-than-constant
velocity cases, and parser/topology blockers. If linked lanes improve FDE, the
diagnosis becomes evidence for continuation-aware follow-up. If the chain
regresses or cannot resolve, the case becomes route-choice or topology coverage
work rather than a baseline tuning claim.

The branch-selection diagnostic is the next layer: it reloads continuation
regression cases, enumerates parsed linked-lane branch alternatives, compares a
non-oracle anchor-heading selector, a non-oracle motion-context selector, and
an observed-future oracle upper bound, then reports whether the error is
recoverable by branch choice. The motion-context selector uses recent speed,
known forecast horizon, route-chain length, and downstream lane speed limits.
The oracle column is deliberately an upper-bound debugging tool, not a
deployable route selector.

The branch replay diagnostic is the stability layer after branch selection. It
reloads the motion-context-improved branch cases, applies the same deterministic
anchor perturbations used elsewhere in ScenarioLens, and checks whether the
selected branch and positive recoverable FDE survive. The current real-data
run preserves the branch in 8/8 perturbation trials and positive gain in 8/8.
Its acceptance gate marks 1 branch ready for broader selector evaluation and
holds 1 speed-sensitive route-context margin case. The experimental
history-speed-prior replay score preserves the accepted case while keeping the
route-context margin case held, so the next iteration moves to guard
calibration and larger negative-control queues.

The branch rollout gate is the triage layer after replay. It does not change
the selector or claim production readiness; it turns replay outcomes into a
public-safe promote/hold queue. The current real-data report promotes 1
branch for broader selector evaluation and holds 1 route-context margin case,
making the diagnostic feel closer to an autonomy evaluation workflow.

The route-context guard study is the conservative policy layer after branch
replay. It keeps the existing selector unchanged, then tests a stricter
non-oracle promotion guard using route-fit, endpoint-alignment, and downstream
speed-limit deltas from branch selection. On the current 2-case replay queue it
promotes 1 robust branch, holds 1 route-context margin case for route-feature
follow-up, and matches replay labels on 2/2 cases with 0 false holds.

The route-context guard calibration layer keeps that agreement visible as a
repeatable threshold sweep. It compares endpoint-alignment gate candidates
against the existing branch-replay labels and keeps the current -0.05 gate
with 0 false holds and 0 false promotions on the current 2-case queue.

The branch coverage audit is the planning layer after the guard. It joins the
continuation candidate plan, replay prototype, route diagnostics, branch
selection, branch replay, and route-context guard manifests into one funnel.
The current real-data audit shows why the next milestone is not "ship the
selector": from 15 continuation candidates, 3 are branchable today and 1 passes
the strict route guard. It also names 5 topology blockers, 2 single-chain
branch-expansion targets, and the route-context margin hold as the next
expansion queue.

The expanded branch coverage pass raises that same local-slice queue to 30
continuation candidates. It produces 20 replay cases, 10 topology probes, 10
branch-selection cases, 6 branchable cases, 1 accepted branch replay, and 1
route-context margin negative control. The paired expanded guard calibration
keeps the current -0.05 endpoint gate as the provisional target with 0 false
holds and 0 false promotions on the expanded 2-case replay queue.

The expanded topology follow-up turns those 10 topology probes into a sharper
work queue. It finds no cap-recoverable linked-target materialization gaps and
10 terminal/directional selected-lane cases. The terminal-neighborhood
audit then finds 6 nearby recovery candidates, replay accepts 3 of 6 ready
candidates under deterministic perturbation gates, and the bounded selector
promotes 1 candidate while holding 5 for additional context.

The topology gap audit now measures what remains after linked-lane closure
materialization. The ingestion layer preserves the first 240 map features and
adds a bounded seven-hop closure set for referenced lane links, cutting study
topology gaps from 33 to 13. The remaining top replay blockers are 0
cap-recoverable cases and 5 terminal or directional-link cases.

The terminal-neighborhood audit follows those 5 terminal/directional cases.
It reloads the local slices, inspects nearby heading-aligned lane alternatives,
and finds 2 nearby alternate-lane recovery candidates plus 3 directional-link
mismatches. The important boundary is that these are replay/gating inputs, not a
selector change: ScenarioLens now knows where to test bounded neighborhood
recovery before claiming broader branch behavior.

The terminal-neighborhood replay gate then force-replays those 2 nearby
recovery candidates against their selected terminal lanes. It accepts 1
alternate lane for a bounded selector experiment, holds 1 regression case, and
keeps the result public-safe by publishing derived replay/gate summaries rather
than raw map geometry or per-scenario packets.

The terminal-neighborhood selector experiment turns that replay evidence into
a bounded non-oracle policy. It promotes the heading-aligned alternate lane,
holds the low-heading regression case, and matches the replay gate on 2/2
decisions while using replay labels only as validation after the selector
decision.

The expanded terminal-neighborhood selector calibration layer takes the larger
6-case replay queue and sweeps 30 distance, heading, and route-extension gate
candidates. It recommends a provisional 40 m route-extension gate that changes
2 replay-accepted false holds into promotions, preserves 0 false promotions on
the current queue, and keeps the default selector unchanged until broader
negative coverage exists.

The terminal selector casebook then turns that calibration manifest into a
public-safe visual artifact. It writes six derived SVG cards with replay gain,
route extension, heading alignment, alternate-lane distance, current decision,
recommended decision, and hold flags. These cards are metric diagrams for
reviewers, not raw trajectory or map overlays.

## Map-Match Audit

The map-match audit handles cases that are not ready to be treated as replay
evidence. It reloads fallback-heavy debug examples, sweeps lane-match
thresholds, and asks a narrow engineering question: would accepting farther
lanes improve the diagnostic, or would it make the forecast less trustworthy?
The current real-data audit shows that widening the radius can worsen FDE, so
the correct follow-up is coordinate-frame, lane-coverage, and lane-selection
work before changing the default matcher.

## Reports

Reports are public-safe artifacts. They summarize aggregate metrics, tag-level
failures, score components, stability across slices, curated evaluation sets,
debug/replay queues, replay stability checks, and the hardest scenario IDs
without publishing raw gated dataset records.

## Explorer

The static explorer consumes deterministic JSON and SVG assets. It is the
portfolio front door for the framework: filters, rankings, trajectory previews,
score components, baseline failures, public-safe heading-aware case diagnostics,
and links to the public reports.

## Extension Points

- Add a dataset adapter for another public motion dataset.
- Add another prediction baseline or calibrate the lane-aware matcher on more
  public data.
- Broaden the calibrated terminal-neighborhood selector queue across more
  candidates.
- Rerun the expanded closure-enabled branch queue across more validation shards.
- Add more replay-held branch negatives.
- Add richer map-match diagnostics for lane coverage, heading alignment, and
  route/intent priors.
- Analyze heading-aware replay stability across more validation shards.
- Graduate stable replay-prototype candidates into an optional Waymax/JAX path.
- Add additional public-safe report types.
