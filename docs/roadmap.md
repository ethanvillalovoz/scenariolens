# Roadmap

## Milestone 1: Local Scenario Core

Goal: a complete local prototype with synthetic scenarios.

- define scenario schema,
- implement interaction/risk metrics,
- implement scenario tags,
- rank scenarios by evaluation value,
- add unit tests,
- export a Markdown or JSON report,
- render scenarios as dependency-free SVG trajectory views.

Status: implemented for the first synthetic corpus. ScenarioLens now includes
taxonomy scoring, ranked Markdown/JSON reports, and dependency-free SVG
trajectory rendering. Scenario JSON export/load and GitHub Actions CI are now
part of the bridge toward real data.

## Milestone 1A: Waymo-Aligned Stack Rationale

Goal: make the technology choices explicit and recruiter-readable.

- keep the default Python package dependency-free,
- document Waymo Motion `Scenario`-shaped records as the dataset boundary,
- explain the lightweight TFRecord/protobuf reader for local Motion slices,
- identify JAX/Waymax as the future simulation path,
- keep frontend/dashboard work secondary to the autonomy data stack.

Status: implemented in `docs/tech_stack.md`.

## Milestone 2: Small Real Data Slice

Goal: replace synthetic records with a small public dataset slice.

- document ingestion boundaries and Waymo Open Dataset access steps,
- support generic CSV ingestion for small external fixtures,
- parse a small motion dataset subset,
- generate a compact feature index,
- compare synthetic and real scenario distributions,
- create 3-5 curated scenario collections.

Status: initial downloaded Waymo Motion validation shard smoke run completed and
summarized in `docs/reports/waymo_motion_validation_summary.md` and
`docs/reports/waymo_motion_case_study.md`. Broader distribution comparison and
curated collections remain next work.

## Milestone 2A: Native Waymo Motion Mini-Slice

Goal: make the real-data adapter credible without making the repo heavy.

- ingest protobuf-shaped Waymo Motion JSON records without extra dependencies,
- read binary protobuf and TFRecord shard inputs without extra dependencies,
- map `sdc_track_index` to ScenarioLens ego tracks,
- skip invalid states and preserve timestamps, object types, and velocities,
- add a preflight command for local downloaded slices,
- document the exact field boundary and raw-data workflow.

Status: implemented for native JSON mini-slices, binary Scenario protos, and
sharded TFRecord slices. Local slice preflight, the downloaded-slice recipe, the
validation packet command, prediction-target metadata, object-of-interest
metadata, map-feature extraction, lane-topology summaries, and traffic-signal
lane-state summaries are implemented.

## Milestone 3: Searchable Demo

Goal: make the project immediately understandable.

- generate a portfolio report with top-ranked scenarios and SVG assets,
- generate a stable dashboard data contract,
- build a dashboard or lightweight web app,
- add scenario filtering and ranking views,
- visualize trajectories on a 2D map/canvas,
- show why each scenario was ranked highly.

Status: portfolio report implemented in `docs/reports/portfolio_report.md`.
Dashboard data contract implemented in `docs/demo/scenarios.json`. Static
Scenario Explorer UI implemented in `docs/demo/index.html`, with filtering,
sorting, trajectory previews, score components, and mobile-responsive layout.

## Milestone 3B: Interaction Metrics Upgrade

Goal: make ranking more interpretable and autonomy-specific.

- break final scores into named components,
- add VRU proximity and sampled path-conflict proximity,
- add max speed, ego max speed, and max deceleration features,
- add quality filtering and raw-vs-scored count reporting for real slices,
- expose component scores in JSON, Markdown, and portfolio reports.

Status: implemented for synthetic, Waymo-shaped fixtures, and small real Waymo
Motion validation slices.

## Milestone 3C: Dashboard Data Contract

Goal: make the future dashboard a thin presentation layer over a tested data
contract.

- combine synthetic, native Waymo-shaped JSON, and normalized Waymo-shaped CSV
  scenarios,
- export ranked scenario cards with score components, metrics, tags, reasons,
  sources, datasets, and SVG paths,
- generate matching SVG trajectory assets,
- document the static payload shape for future UI work.

Status: implemented in `docs/demo/scenarios.json` and `docs/demo/assets/`,
including baseline ADE/FDE, lane-aware comparison, and failure-score fields.

## Milestone 3D: Baseline Failure Mining

Goal: turn scenario ranking into measurable downstream evaluation.

- select prediction targets from Waymo Motion metadata when available,
- run a lightweight constant-velocity trajectory baseline,
- compute ADE, FDE, max FDE, miss rate, and baseline failure score,
- add baseline failure as an interpretable score component,
- render dashed forecast overlays in SVG previews,
- expose baseline metrics in Markdown/JSON reports, validation packets, and
  the Scenario Explorer.

Status: implemented for synthetic fixtures, Waymo-shaped JSON/CSV fixtures,
and local Waymo Motion validation slices. Broader real-slice distribution
analysis remains next work.

## Milestone 4: Portfolio Polish

Goal: make the repo recruiter- and engineer-readable.

- write a concise technical report,
- add screenshots/GIFs,
- add reproducible commands,
- add limitations and future work,
- prepare resume bullets and a project page.

Status: in progress. The repo has CI, a portfolio report, a local Scenario
Explorer demo, a `docs/` entrypoint ready for GitHub Pages publishing, a product
strategy, an architecture map, recruiting notes, and suggested GitHub metadata.

## Milestone 4B: Lane-Aware Baseline Comparison

Goal: show that ScenarioLens can move beyond constant-velocity scoring while
remaining laptop-friendly.

- add a second prediction baseline using parsed lane polylines,
- keep constant velocity as the default scoring baseline,
- preserve fallback behavior for pedestrians, missing maps, low-speed tracks,
  and distant lane matches,
- add a curved-lane fixture with an obvious comparison win,
- expose comparison metrics in CLI reports and the Scenario Explorer.
- run the lane-aware comparison on downloaded Waymo Motion validation shards
  and publish public-safe aggregate wins/regressions.

Status: implemented in `src/scenariolens/prediction.py`,
`src/scenariolens/baseline_compare.py`,
`src/scenariolens/baseline_compare_study.py`,
`docs/reports/lane_aware_baseline_study.md`,
`docs/reports/waymo_lane_aware_baseline_cross_shard.md`, and the static
explorer payload. The four-shard diagnostic intentionally publishes both wins
and regressions: the naive lane-aware baseline improves some scenarios but
regresses overall, which makes the next richer-map or replay step concrete.

## Milestone 4D: Baseline Debug Casebook

Goal: make the lane-aware diagnostic explainable, not just numeric.

- select representative real-data cases from a baseline comparison study,
- render local SVG overlays with ground truth, constant velocity, lane-aware
  forecast, and map context,
- write per-track metric timelines and lane-match diagnostics locally,
- publish a public-safe casebook with scenario IDs, metric summaries,
  fallback reasons, and interpretation.

Status: implemented in `scenariolens baseline-debug`,
`src/scenariolens/baseline_debug.py`, and
`docs/reports/waymo_lane_aware_debug_casebook.md`. Raw Waymo files, local SVG
overlays, and per-case debug manifests remain ignored under `data/processed/`.

## Milestone 4E: Replay Candidate Planning

Goal: make the bridge from scenario mining to simulation explicit before adding
heavier Waymax/JAX dependencies.

- read a baseline-debug manifest,
- rank replay candidates by FDE delta, map usage, target count, and fallback
  behavior,
- label cases as improvement replay, regression replay, mixed fallback audit,
  or map-match audit,
- publish a public-safe plan that says what should be replayed next and what
  should not be trusted yet.

Status: implemented in `scenariolens replay-candidates`,
`src/scenariolens/replay_candidates.py`, and
`docs/reports/waymo_replay_candidate_plan.md`. This is not a completed replay
simulator; it is the candidate queue for the next Waymax/JAX experiment.

## Milestone 4F: Open-Loop Replay Prototype

Goal: make the replay queue executable without introducing heavyweight
simulation dependencies.

- read a replay-candidate manifest,
- reload replay-ready local Waymo Motion scenarios,
- replay constant-velocity and lane-aware rollouts from the same anchor state,
- apply small deterministic anchor-velocity perturbations,
- publish a public-safe report with stability labels while keeping local replay
  packets and SVG overlays ignored.

Status: implemented in `scenariolens replay-prototype`,
`src/scenariolens/replay_prototype.py`, and
`docs/reports/waymo_open_loop_replay_prototype.md`. The current real-data run
evaluates two replay-ready Waymo Motion scenarios, four prediction targets, and
eight perturbation trials. This is open-loop diagnostic evidence, not
Waymax/JAX execution or closed-loop simulation.

## Milestone 4G: Map-Match Threshold Audit

Goal: turn fallback-heavy lane-aware cases into actionable map diagnostics
before changing matcher behavior.

- read a baseline-debug manifest,
- select fallback-heavy cases that should not yet be treated as replay evidence,
- reload the local source scenarios,
- sweep lane-match thresholds,
- publish target-level lane-distance summaries and aggregate FDE deltas while
  keeping raw trajectories and per-case packets ignored,
- separate "raise the threshold" hypotheses from coordinate-frame, lane-set,
  and lane-selection audit work.

Status: implemented in `scenariolens map-match-audit`,
`src/scenariolens/map_match_audit.py`, and
`docs/reports/waymo_map_match_audit.md`. The current real-data run audits the
fallback-heavy debug case from the 100-scenario lane-aware study and shows that
widening the match radius uses more lanes but worsens FDE. That makes the next
engineering step more specific: improve map matching with heading, coverage,
coordinate-frame, and intent checks instead of loosening the default threshold.

## Milestone 4H: Heading-Aware Lane Selection Study

Goal: turn the map-match audit conclusion into a tested map-selection ablation.

- keep constant velocity as the default scoring baseline,
- keep the existing nearest-lane baseline for comparison,
- add a heading-aware lane-selection variant that prefers lane tangents aligned
  with the target's anchor velocity,
- preserve fallback behavior for pedestrians, missing maps, low-speed targets,
  distant lanes, and poorly aligned lanes,
- publish a real 100-scenario study that compares constant velocity,
  nearest-lane, and heading-aware lane selection without raw data.

Status: implemented in `scenariolens lane-selection-study`,
`src/scenariolens/lane_selection_study.py`, and
`docs/reports/waymo_heading_aware_lane_selection_study.md`. The current
four-shard run covers 100 scenarios and 418 evaluated prediction targets.
Heading-aware selection improves mean FDE by 0.489 m relative to nearest-lane
selection, while still trailing constant velocity overall. That makes it a
useful matcher ablation, not a production prediction claim. The live Explorer
surfaces public-safe improvement, regression, and fallback-heavy cases from this
run, and `docs/reports/waymo_heading_aware_debug_casebook.md` connects six of
those rows to ignored local SVG overlays and per-case manifests.

## Milestone 4I: Heading-Aware Replay Candidate Planning

Goal: turn heading-aware selector diagnostics into an explicit replay/debug
queue before adding heavier simulation dependencies.

- read a heading-aware `baseline-debug` manifest produced from
  `lane-selection-study`,
- rank nearest-lane vs heading-aware wins and regressions by FDE delta, target
  count, map usage, fallback count, and worst track delta,
- keep constant velocity as context so improvements over nearest-lane are not
  overclaimed,
- label cases as heading improvement replay, heading regression replay,
  mixed fallback audit, or heading map-match audit,
- publish a public-safe queue with scenario IDs, readiness labels, blockers,
  and next actions while local manifests and overlays stay ignored.

Status: implemented in `scenariolens replay-candidates`,
`src/scenariolens/replay_candidates.py`, and
`docs/reports/waymo_heading_aware_replay_candidate_plan.md`. The current
four-shard run produces six heading-aware replay candidates: four improvement
controls, one regression target, and one map-match audit case. This is a
planning artifact for heading-aware replay experiments, not completed Waymax/JAX
simulation.

## Milestone 4J: Heading-Aware Open-Loop Replay Prototype

Goal: execute the strongest heading-aware selector candidates without adding
heavy simulation dependencies.

- read a heading-aware replay-candidate manifest,
- reload selected local Waymo Motion scenarios,
- replay nearest-lane and heading-aware open-loop rollouts from the same anchor
  state,
- keep constant velocity as context without making it the comparison target,
- apply small deterministic speed and heading perturbations,
- publish a public-safe stability report while keeping local replay packets and
  SVG overlays ignored.

Status: implemented in `scenariolens heading-replay-prototype`,
`src/scenariolens/heading_replay_prototype.py`, and
`docs/reports/waymo_heading_aware_replay_prototype.md`. The current real-data
run evaluates five heading-ready cases, 30 prediction targets, and 20
perturbation trials; all improvement and regression cases preserve their
expected selector sign under the perturbations. This is open-loop diagnostic
evidence, not Waymax/JAX execution or closed-loop simulation.

## Milestone 4C: No-Auth Baseline Ablation

Goal: keep technical progress visible even when Waymo shard auth is blocked.

- compare constant velocity, default lane-aware, and strict lane-aware variants,
- summarize map-used/fallback counts and fallback reasons,
- publish a checked-in ablation report from fixture data,
- show fallback reason summaries in the explorer.

Status: implemented in `scenariolens baseline-ablation`,
`docs/reports/baseline_ablation_study.md`, and the dashboard payload.

## Milestone 4A: Production-Grade Repo Story

Goal: make the end goal and system boundary obvious before a reviewer reads any
code.

- explain the target user and product strategy,
- document what the project is and is not claiming,
- map ingestion, scoring, reports, rendering, and dashboard modules,
- connect the live demo to data provenance and the real-data case study,
- keep the README focused on the engineering artifact.

Status: implemented in `docs/project_strategy.md`, `docs/architecture.md`, the
README, and the Scenario Explorer navigation/status panel.

## Milestone 5: Real-Slice Distribution Study

Goal: make the baseline failure analysis credible on more real data.

- select larger real-data scenario collections from downloaded validation
  shards,
- compare baseline errors by scenario tag and score component,
- report which ranked scenarios are hardest for the baseline,
- evaluate whether selected scenarios should be replayed or perturbed in
  Waymax/JAX.

Status: initial implementation complete for one local Waymo Motion validation
shard in `docs/reports/waymo_motion_failure_study.md`, plus a 75-scenario
windowed stability report in
`docs/reports/waymo_motion_failure_stability.md` and a 100-scenario cross-shard
stability report across four validation shards in
`docs/reports/waymo_motion_failure_stability_cross_shard.md`. A matching
100-scenario lane-aware baseline diagnostic is checked in at
`docs/reports/waymo_lane_aware_baseline_cross_shard.md`, with a public-safe
debug casebook at `docs/reports/waymo_lane_aware_debug_casebook.md` and replay
candidate queue at `docs/reports/waymo_replay_candidate_plan.md`. The first
open-loop replay prototype is checked in at
`docs/reports/waymo_open_loop_replay_prototype.md`, and the fallback-heavy
map-match threshold audit is checked in at
`docs/reports/waymo_map_match_audit.md`. The heading-aware lane-selection
ablation is checked in at
`docs/reports/waymo_heading_aware_lane_selection_study.md`. The context-joined
failure study at
`docs/reports/waymo_context_failure_study_cross_shard.md` now feeds a curated
context evaluation set at `docs/reports/waymo_context_eval_set.md`, a context
debug casebook at `docs/reports/waymo_context_eval_debug_casebook.md`, and a
context replay-candidate queue at
`docs/reports/waymo_context_replay_candidate_plan.md`. The replay-ready
context cases now feed
`docs/reports/waymo_context_open_loop_replay_prototype.md`, which preserves one
stable regression warning and flags one sensitive positive control under
deterministic perturbations. The follow-up route/intent audit is checked in at
`docs/reports/waymo_context_route_intent_audit.md` and diagnoses the stable
warning as a lane-continuity or route-link follow-up. The lane-link
continuation prototype at
`docs/reports/waymo_lane_continuation_prototype.md` proves linked-lane
following on a deterministic fixture and resolves the real stable warning's
parsed lane chain, reducing the clamped nearest-lane FDE by 63.578 m. The
validation study at `docs/reports/waymo_lane_continuation_study.md` then scans
100 local Waymo scenarios and finds 209 lane-continuation candidates after
linked-lane closure materialization, including 133 linked-lane improvements,
57 regressions, and 17 topology gaps. The
candidate plan at `docs/reports/waymo_lane_continuation_candidate_plan.md`
promotes 15 of those rows into replay controls, regression debug targets, and
topology-audit blockers. The replay prototype at
`docs/reports/waymo_lane_continuation_replay_prototype.md` executes those 15
rows as 10 target-track replays, 40 deterministic perturbation trials, and 5
topology probes. The route diagnostics report at
`docs/reports/waymo_lane_continuation_route_diagnostics.md` classifies the
follow-up set into 4 stable route-choice regressions, 1 horizon-limit case, 0
link-worse-than-constant-velocity cases, and 5 topology blockers. The branch
selection diagnostic at
`docs/reports/waymo_lane_continuation_branch_selection.md` then sweeps parsed
branch alternatives for the 5 continuation regression diagnostics, finding 3
branchable cases, 2 single-chain cases, 2 non-oracle motion-context
improvements, and 3 oracle upper-bound improvements with 27.968 m mean
recoverable FDE. The branch replay diagnostic at
`docs/reports/waymo_lane_continuation_branch_replay.md` then replays those 2
motion-context choices under 8 deterministic perturbations: branch choice is
preserved in 8/8 trials, positive recoverable FDE holds in 8/8 trials, and the
acceptance gate marks 2 branches ready for broader selector evaluation with a
+28.627 m minimum robustness margin. An experimental history-speed-prior replay
score preserves both accepted cases and leaves no speed-prior margin target
unresolved. The branch rollout gate at
`docs/reports/waymo_lane_continuation_branch_rollout_gate.md` turns those
outcomes into a promote/hold queue: 2 branches are ready for broader selector
evaluation and 0 route-context margin cases remain held. The route-context
guard study at
`docs/reports/waymo_lane_continuation_route_context_guard.md` tests a stricter
non-oracle promotion policy over those two branchable candidates, promoting the
robust branch, holding one replay-accepted branch for route-feature follow-up,
and matching the replay gate on one of the two replay-accepted cases. The branch
coverage audit at
`docs/reports/waymo_lane_continuation_branch_coverage.md` connects the full
continuation-to-branch funnel: 15 continuation candidates, 10 replay-ready
candidates, 5 branch-selection cases, 3 branchable cases, 1 route-guard
promotion, 5 topology blockers, and 8 expansion queue items. Linked-lane
closure materialization now cuts study topology gaps from 33 to 17 and raises
linked-lane improvements from 96 to 133. Next work should audit terminal and
directional topology cases, calibrate the route-context guard false hold, and
expand the closure-enabled queue before claiming broader selector readiness.

## Stretch Goals

- open-vocabulary scenario search,
- embedding-based retrieval,
- Waymax or sim-agent integration,
- city/ODD gap comparison for Seattle or Bellevue.
