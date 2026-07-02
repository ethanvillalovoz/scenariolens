# Changelog

All notable changes to ScenarioLens are documented here.

## [Unreleased]

### Added

- Baseline ablation CLI/report comparing constant velocity, default lane-aware,
  and strict lane-aware variants without gated Waymo downloads.
- `scenariolens baseline-compare-study` for repeated Waymo Motion or
  ScenarioLens JSON inputs, with public-safe manifest/report outputs.
- 100-scenario real Waymo lane-aware baseline diagnostic across four local
  validation shards, including top improvements, top regressions, map-used
  counts, and fallback reasons.
- `scenariolens baseline-debug` casebook workflow that selects improvement,
  regression, and fallback-heavy cases from a comparison study, writes local SVG
  overlays, and publishes a public-safe summary.
- `scenariolens replay-candidates` workflow that converts a baseline-debug
  manifest into a public-safe Waymax/JAX replay candidate queue.
- `scenariolens replay-prototype` workflow that reloads replay-ready local
  scenarios, reruns open-loop baseline rollouts, and applies deterministic
  anchor-velocity perturbations before publishing a public-safe stability
  report.
- `scenariolens map-match-audit` workflow that reloads fallback-heavy debug
  cases, sweeps lane-match thresholds, and publishes a public-safe diagnostic
  before changing matcher behavior.
- `scenariolens lane-selection-study` workflow and heading-aware lane-selection
  baseline variant comparing nearest-lane and heading-aware map matching across
  the 100-scenario local Waymo slice.
- Public-safe heading-aware case diagnostics in the static Scenario Explorer,
  including improvement, regression, and fallback-heavy cases from the local
  100-scenario study.
- Heading-aware debug casebook mode for `scenariolens baseline-debug`, including
  local CV/nearest/heading-aware SVG overlays and the public-safe
  `docs/reports/waymo_heading_aware_debug_casebook.md` report.
- Heading-aware replay candidate planning in `scenariolens replay-candidates`,
  including nearest-lane vs heading-aware readiness labels and the public-safe
  `docs/reports/waymo_heading_aware_replay_candidate_plan.md` report.
- `scenariolens heading-replay-prototype` workflow that reloads selected
  heading-ready cases, compares nearest-lane and heading-aware open-loop
  rollouts, applies deterministic perturbations, and publishes
  `docs/reports/waymo_heading_aware_replay_prototype.md`.
- `scenariolens context-study` workflow and
  `docs/reports/waymo_context_study_cross_shard.md`, summarizing public-safe
  map-feature, traffic-signal, stop-point, and lane-topology coverage over the
  100-scenario local Waymo slice.
- `scenariolens context-failure-study` workflow and
  `docs/reports/waymo_context_failure_study_cross_shard.md`, joining map/signal
  context with ScenarioLens scores, constant-velocity FDE, lane-aware deltas,
  fallback counts, and context-rich failure rankings.
- `scenariolens context-eval-set` workflow and
  `docs/reports/waymo_context_eval_set.md`, turning context-failure rankings
  into grouped public-safe scenario IDs with acceptance checks for follow-up
  experiments.
- `baseline-debug` support for context-eval-set manifests, with
  `docs/reports/waymo_context_eval_debug_casebook.md` and
  `docs/reports/waymo_context_replay_candidate_plan.md` publishing a
  context-derived debug/replay queue.
- Context replay prototype support in `scenariolens replay-prototype`, with
  `docs/reports/waymo_context_open_loop_replay_prototype.md` publishing
  public-safe perturbation stability results for the replay-ready context eval
  seeds.
- `scenariolens route-intent-audit` workflow and
  `docs/reports/waymo_context_route_intent_audit.md`, following the stable
  context replay warning into lane-continuity, route/topology, and heading
  diagnostics without changing the default scorer.
- `scenariolens lane-continuation-prototype` workflow and
  `docs/reports/waymo_lane_continuation_prototype.md`, testing parsed
  `entry_lanes`/`exit_lanes` continuation for lane-continuity audit cases.
- Waymo Motion ingestion now retains enough lightweight map features for the
  current lane-continuation proof case to resolve chain `144 -> 190 -> 193`,
  reducing nearest-lane FDE by 63.578 m in the checked-in diagnostic report.
- `scenariolens lane-continuation-study` workflow and
  `docs/reports/waymo_lane_continuation_study.md`, scanning the 100-scenario
  local Waymo slice for lane-end clamp candidates and publishing linked-lane
  improvements, regressions, and topology gaps.
- `scenariolens lane-continuation-candidates` workflow and
  `docs/reports/waymo_lane_continuation_candidate_plan.md`, turning the study
  into replay controls, regression debug targets, and topology-audit blockers.
- `scenariolens lane-continuation-replay-prototype` workflow and
  `docs/reports/waymo_lane_continuation_replay_prototype.md`, executing all 15
  queued continuation cases as 10 target-track replays, 40 deterministic
  perturbation trials, and 5 topology probes.
- `scenariolens lane-continuation-route-diagnostics` workflow and
  `docs/reports/waymo_lane_continuation_route_diagnostics.md`, classifying
  replayed continuation regressions and topology blockers into route-choice,
  horizon-limit, and parser/topology follow-up buckets.
- `scenariolens lane-continuation-branch-selection` workflow and
  `docs/reports/waymo_lane_continuation_branch_selection.md`, sweeping parsed
  branch alternatives for continuation regressions and separating non-oracle
  anchor-heading and motion-context selectors from observed-future oracle
  upper-bound diagnostics.
- `scenariolens lane-continuation-branch-replay` workflow and
  `docs/reports/waymo_lane_continuation_branch_replay.md`, replaying
  motion-context branch choices under deterministic perturbations and
  separating accepted branch evidence from route-context margin follow-up cases.
- `scenariolens lane-continuation-branch-rollout-gate` workflow and
  `docs/reports/waymo_lane_continuation_branch_rollout_gate.md`, converting
  branch replay evidence into public-safe promote/hold rollout triage.
- Lane-aware fallback reason summaries in Markdown/JSON reports and the static
  Scenario Explorer dashboard payload.
- Short animated demo GIF for the README public surface.

## [0.2.0] - 2026-06-28

### Added

- Product-quality public README surface with live demo, evidence links, and
  quick-start workflows.
- Contributor, citation, release, and issue/PR metadata for an open-source
  baseline release.
- Scenario Explorer evidence band and baseline-failure summary card.
- CLI workflow documentation and framework concepts guide.
- Lane-aware prediction baseline comparison using parsed lane polylines when
  map context is available.
- `scenariolens baseline-compare` Markdown/JSON reports, a curved-lane fixture,
  dashboard comparison metrics, and the checked-in lane-aware study report.

### Deferred

- True cross-shard Waymo Motion failure stability report after authenticated
  shard downloads are available.
- Small Waymax/JAX replay or perturbation path for selected high-value
  scenarios.

## [0.1.0] - 2026-06-28

### Added

- Scenario schema, synthetic corpus, CSV ingestion, Waymo Motion-shaped JSON/CSV
  ingestion, and lightweight native Motion TFRecord/proto reader.
- Interpretable scenario ranking metrics for VRUs, proximity, TTC proxy, path
  conflict, density, dynamics, and taxonomy.
- Constant-velocity prediction baseline with ADE/FDE, miss rate, and failure
  score.
- Public-safe real-slice failure and stability studies.
- Static Scenario Explorer with deterministic dashboard JSON and SVG assets.
- GitHub Actions CI for unit tests and static JavaScript syntax checks.
