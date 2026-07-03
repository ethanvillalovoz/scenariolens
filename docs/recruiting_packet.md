# ScenarioLens Recruiting Packet

This packet turns ScenarioLens into a concise recruiting artifact for autonomy,
robotics, AI/ML, and software engineering internship conversations.

## Links

- Live demo: https://ethanvillalovoz.com/scenariolens/
- Repository: https://github.com/ethanvillalovoz/scenariolens
- Product strategy: `docs/project_strategy.md`
- Architecture: `docs/architecture.md`
- Portfolio report: `docs/reports/portfolio_report.md`
- Context evaluation set: `docs/reports/waymo_context_eval_set.md`
- Context eval debug casebook: `docs/reports/waymo_context_eval_debug_casebook.md`
- Context replay candidate plan: `docs/reports/waymo_context_replay_candidate_plan.md`
- Context open-loop replay prototype: `docs/reports/waymo_context_open_loop_replay_prototype.md`
- Context route/intent audit: `docs/reports/waymo_context_route_intent_audit.md`
- Lane-link continuation prototype: `docs/reports/waymo_lane_continuation_prototype.md`
- Lane-continuation validation study: `docs/reports/waymo_lane_continuation_study.md`
- Lane-continuation candidate plan: `docs/reports/waymo_lane_continuation_candidate_plan.md`
- Lane-continuation replay prototype: `docs/reports/waymo_lane_continuation_replay_prototype.md`
- Lane-continuation route diagnostics: `docs/reports/waymo_lane_continuation_route_diagnostics.md`
- Lane-continuation branch selection: `docs/reports/waymo_lane_continuation_branch_selection.md`
- Motion-context branch replay: `docs/reports/waymo_lane_continuation_branch_replay.md`
- Branch rollout gate: `docs/reports/waymo_lane_continuation_branch_rollout_gate.md`
- Route-context guard study: `docs/reports/waymo_lane_continuation_route_context_guard.md`
- Branch coverage audit: `docs/reports/waymo_lane_continuation_branch_coverage.md`
- Topology gap audit: `docs/reports/waymo_lane_continuation_topology_gap_audit.md`
- Terminal neighborhood audit: `docs/reports/waymo_lane_continuation_terminal_neighborhood_audit.md`
- Terminal neighborhood replay gate: `docs/reports/waymo_lane_continuation_terminal_neighborhood_replay.md`
- Terminal neighborhood selector experiment: `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector.md`
- Real lane-aware baseline diagnostic: `docs/reports/waymo_lane_aware_baseline_cross_shard.md`
- Lane-aware debug casebook: `docs/reports/waymo_lane_aware_debug_casebook.md`
- Replay candidate plan: `docs/reports/waymo_replay_candidate_plan.md`
- Open-loop replay prototype: `docs/reports/waymo_open_loop_replay_prototype.md`
- Map-match threshold audit: `docs/reports/waymo_map_match_audit.md`
- Heading-aware lane-selection study: `docs/reports/waymo_heading_aware_lane_selection_study.md`
- Heading-aware debug casebook: `docs/reports/waymo_heading_aware_debug_casebook.md`
- Heading-aware replay candidate plan: `docs/reports/waymo_heading_aware_replay_candidate_plan.md`
- Heading-aware replay prototype: `docs/reports/waymo_heading_aware_replay_prototype.md`
- Fixture lane-aware baseline study: `docs/reports/lane_aware_baseline_study.md`
- Baseline ablation study: `docs/reports/baseline_ablation_study.md`
- Cross-shard stability study: `docs/reports/waymo_motion_failure_stability_cross_shard.md`
- Technical case study: `docs/case_studies/waymo_baseline_failures.md`
- Real-data case study: `docs/reports/waymo_motion_case_study.md`
- Tech stack rationale: `docs/tech_stack.md`

## GitHub Repository Metadata

Recommended repository description:

> Waymo-aligned scenario mining framework for autonomy motion evaluation.

Recommended website:

> https://ethanvillalovoz.com/scenariolens/

Recommended topics are maintained in `docs/github_metadata.md`. A compact set:

- `autonomous-driving`
- `waymo-open-dataset`
- `waymo-motion`
- `scenario-mining`
- `scenario-ranking`
- `motion-forecasting`
- `safety-evaluation`
- `python`

## Resume Bullets

Use one bullet if space is tight:

- Built ScenarioLens, a Waymo-aligned autonomy evaluation tool that ingests motion scenarios, computes interpretable interaction/risk metrics, ranks long-tail driving cases, and serves a searchable static explorer.

Use two bullets if the project gets a dedicated entry:

- Built ScenarioLens, a local-first autonomy scenario evaluation tool that ingests synthetic, Waymo Motion-shaped JSON, normalized CSV, and small downloaded Waymo Motion TFRecord slices, then ranks long-tail cases using interpretable proximity, TTC, VRU, path-conflict, density, and taxonomy features.
- Shipped a tested portfolio demo with 100+ Python unit tests, GitHub Actions CI, SVG trajectory rendering, deterministic dashboard data, lane-aware baseline comparison, a 100-scenario cross-shard Waymo Motion stability report, a 100-scenario lane-aware diagnostic, a heading-aware lane-selection ablation, baseline-debug casebooks, replay-candidate plans, open-loop replay/perturbation prototypes, route/intent, lane-link, continuation-candidate/replay/diagnostic/branch-selection/branch-replay, branch rollout gates, route-context guard studies, branch coverage/topology-gap audits, and map-match audits, and a static Scenario Explorer deployed at `ethanvillalovoz.com/scenariolens`.

Short project line:

> ScenarioLens | Python, Waymo Motion-shaped data, scenario ranking, static dashboard

Stronger project line once the real-data case study is discussed:

> ScenarioLens | Python, Waymo Motion TFRecord slices, long-tail scenario triage, static explorer

## 30-Second Pitch

ScenarioLens is a small autonomy evaluation project focused on a practical
deployment question: which rare driving scenarios deserve targeted evaluation
before an AV system is trusted in a new operating domain? Instead of attempting
to build a full self-driving stack, it builds a laptop-friendly pipeline for
ingesting motion scenarios, computing interpretable interaction and risk
features, ranking long-tail cases, and showing the results in a searchable demo.
I scoped it around public Waymo Motion-style records, a real validation-shard
smoke test, and clear testing so the artifact is credible, inspectable, and
lightweight.

## Interview Story

Problem:
Autonomous-driving systems need more than strong average-case behavior. They
need evidence on rare, interactive, safety-relevant cases such as pedestrians,
cyclists, blocked lanes, unprotected turns, close-proximity interactions, and
dense multi-agent scenes.

Approach:
ScenarioLens treats motion scenarios as the evaluation unit. It normalizes small
curated scenario records, computes lightweight interaction metrics, assigns
taxonomy tags, ranks scenarios by evaluation value, and exports both human- and
machine-readable artifacts.

Architecture:

1. Scenario schema in `src/scenariolens/schema.py`.
2. Ingestion adapters for synthetic scenarios, row-wise CSV, normalized
   Waymo-shaped CSV, protobuf-shaped Waymo Motion JSON, and small native
   Waymo Motion TFRecord slices.
3. Metrics and taxonomy scoring for proximity, TTC, VRUs, path conflicts,
   density, dynamics, and scenario category.
4. Constant-velocity and lane-aware baseline comparison.
5. Baseline-debug casebook generation for selected wins, regressions, and fallbacks.
6. Replay-candidate planning for downstream replay/simulation work.
7. Open-loop replay and anchor-velocity perturbation prototype for replay-ready cases.
8. Map-match threshold audit for fallback-heavy cases before matcher changes.
9. Heading-aware lane-selection ablation for map-matching iteration.
10. Route/intent audit for stable replay regressions that need lane-continuity
    or route-link follow-up.
11. Lane-link continuation prototype, validation study, candidate planning, replay probes, route/topology diagnostics, and branch-selection sweeps for parsed entry/exit lane topology.
12. Report, portfolio, renderer, and dashboard exporters.
13. Static Scenario Explorer backed by deterministic JSON and SVG assets.

Why it is Waymo-relevant:
Waymo's public ecosystem includes Waymo Open Dataset, Waymo Motion, scenario
data, simulation, forecasting, and safety evaluation. ScenarioLens deliberately
aligns with that public boundary: it uses Waymo Motion-shaped records where
possible, reads the Motion fields needed for small downloaded slices, and
focuses on scenario triage rather than pretending to replace production
autonomy systems.

Tradeoffs:

- Chose motion/scenario data first instead of image or LiDAR because it is
  laptop-feasible and directly supports interaction analysis.
- Kept the core package dependency-free so reviewers can run tests quickly.
- Used deterministic checked-in demo data so the public artifact is stable.
- Kept the native Waymo reader narrow: it extracts the fields ScenarioLens
  needs instead of claiming full Waymo Open Dataset parity.

Testing and verification:

- Unit tests cover schema behavior, ingestion, metrics, reports, rendering, and
  dashboard data.
- GitHub Actions runs the test suite, install smoke checks, dashboard JSON
  validation, and static JavaScript syntax check.
- Public-safe reports include 100 real Waymo Motion scenarios across four local
  validation shards, with 418 evaluated prediction targets for both failure
  stability and lane-aware baseline diagnostics.
- A debug casebook explains one lane-aware improvement, one regression, and one
  fallback-heavy case while keeping local SVG overlays and per-track manifests
  out of git.
- A replay-candidate plan ranks those cases and honestly separates replay-ready
  scenarios from a fallback-heavy map-match audit.
- The open-loop replay prototype evaluates two replay-ready real Waymo
  scenarios, four prediction targets, and eight deterministic perturbation
  trials while keeping raw files and per-case replay packets out of git.
- The map-match audit reloads the fallback-heavy case, sweeps lane-match
  thresholds, and shows that widening the radius worsens FDE in the current
  case, making lane coverage and coordinate-frame checks the honest next step.
- The heading-aware lane-selection study compares nearest-lane and
  heading-aware map matching over the same 100-scenario slice; it improves mean
  FDE by 0.489 m over nearest lane but remains worse than constant velocity
  overall.
- The live Explorer now exposes public-safe heading-aware improvement,
  regression, and fallback-heavy case diagnostics from that 100-scenario run.
- A heading-aware debug casebook connects six Explorer-facing cases to ignored
  local SVG overlays, per-track metrics, heading-alignment diagnostics, and
  fallback reasons.
- A heading-aware replay candidate plan ranks those six cases into four
  improvement controls, one regression target, and one map-match audit case
  before any heavier simulation claim.
- A heading-aware replay prototype reloads all five heading-ready cases,
  evaluates 30 targets, and preserves the expected selector sign across 20
  deterministic perturbation trials.
- A map and signal context study parses 15,453 static map features, 60,583
  traffic-signal lane states, and 27,065 lane-topology links from the same
  100-scenario real-data slice without publishing raw Waymo records.
- A context-joined failure study connects those map/signal summaries to 418
  evaluated prediction targets, constant-velocity FDE, lane-aware deltas,
  fallback counts, and ranked context-rich failure cases.
- A context evaluation set turns those ranked rows into 14 unique scenario IDs
  grouped by signal context, route/topology, lane-aware regression, and fallback
  stress, with acceptance checks for follow-up experiments.
- A context eval debug casebook reloads five eval seeds into local diagnostics,
  a context replay-candidate plan separates two replay-ready cases from three
  map-match audits, and a context open-loop replay prototype evaluates those
  two ready cases across eight deterministic perturbation trials.
- A context route/intent audit follows the stable replay regression one step
  deeper and identifies a lane-continuity or route-link follow-up: the matched
  lane has 16.691 m remaining while the target travels 80.270 m through the
  forecast horizon.
- A lane-link continuation prototype proves the linked-lane mechanism on a
  deterministic fixture, resolves the real stable warning's parsed lane chain
  `144 -> 190 -> 193`, and cuts nearest-lane FDE by 63.578 m on that case.
- A lane-continuation validation study scans 100 real local Waymo scenarios and
  finds 209 lane-end clamp candidates after linked-lane closure materialization:
  133 linked-lane improvements, 57 regressions, and 17 topology gaps for
  follow-up audit work.
- A lane-continuation candidate plan turns that study into 15 follow-up items:
  five replay controls, five regression debug targets, and five topology-audit
  blockers.
- A lane-continuation replay prototype executes all 15 queued items: 10
  target-track replays, 40 deterministic perturbation trials with 100% sign
  preservation, and five confirmed topology blockers.
- A route/topology diagnostic casebook turns those replay results into follow-up
  buckets: three stable route-choice regressions, one horizon-limit case, one
  link-worse-than-constant-velocity case, and five topology blockers.
- A branch-selection diagnostic sweeps parsed alternatives for the five
  continuation regression diagnostics, finding two branchable cases, three
  single-chain cases, two non-oracle motion-context improvements, and two
  oracle upper-bound improvements while showing the simple anchor-heading
  selector is not enough.
- A motion-context branch replay diagnostic replays those two branch choices
  under eight deterministic perturbations: the selected branch is preserved in
  all eight trials, positive recoverable FDE holds in all eight trials, both
  branches are accepted for broader selector evaluation, and the minimum
  robustness margin is +28.627 m.
- An experimental history-speed-prior replay score tests a simple non-oracle
  calibration idea on the same branch choices. It preserves both accepted cases
  and leaves no speed-prior margin target unresolved.
- A branch rollout gate converts the replay outputs into a promote/hold queue:
  one branch is ready for broader selector evaluation and one route-context
  margin case remains held with a concrete next action.
- A route-context guard study tests a stricter non-oracle promotion rule over
  the same branchable queue: one robust branch is promoted, one replay-accepted
  branch is held for route-feature follow-up, and the guard records one
  replay-gate match plus one false hold for calibration.
- A branch coverage audit connects the continuation candidate, replay,
  diagnostics, branch-selection, branch-replay, and route-context guard
  manifests into one funnel: 15 continuation candidates, 10 replay-ready
  candidates, 5 branch-selection cases, 3 branchable cases, 1 route-guard
  promotion, 5 topology blockers, and 8 expansion queue items.
- A topology gap audit reloads those 5 topology blockers and compares capped
  ScenarioLens map features with raw parsed map-feature IDs: 2 blocker cases
  remain cap-recoverable, 3 are terminal or directional-link cases, and 0 raw
  target misses remain unexplained.
- A terminal-neighborhood audit reloads the 3 terminal/directional blockers and
  finds 2 nearby alternate-lane recovery candidates plus 1 directional-link
  mismatch, keeping them as replay/gating targets rather than selector claims.
- A terminal-neighborhood replay gate force-replays those 2 nearby recovery
  candidates, accepts 1 alternate lane for a bounded selector experiment, and
  holds 1 regression case instead of overclaiming a selector win.
- A terminal-neighborhood selector experiment applies a bounded non-oracle
  geometry and route-extension policy, promoting 1 heading-aligned alternate
  lane, holding 1 low-heading case, and matching the replay gate on 2/2
  decisions.
- The public demo was browser-smoke-tested locally and deployed through the
  personal portfolio site.

What I would build next:

1. Expand the Waymo Motion cross-shard stability run beyond four validation shards.
2. Compare distribution stability across true shards and scenario tags.
3. Broaden the terminal-neighborhood selector experiment and calibrate the
   conservative route-context guard false hold.
4. Create curated scenario collections for pedestrian, cyclist, merge, and
   unprotected-turn cases.

## Claims To Keep Honest

- Do say: "Waymo-aligned", "Waymo Motion-shaped", "public-data oriented", and
  "portfolio evaluation tool".
- Do not say: "used Waymo's internal stack", "built a self-driving system", or
  "validated on full-scale Waymo production data".
- The strongest claim is the engineering artifact: a tested pipeline, static
  explorer, reproducible commands, public demo, and clear next-step roadmap.
