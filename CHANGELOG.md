# Changelog

All notable changes to ScenarioLens are documented here.

## [Unreleased]

### Added

- `scenariolens selector-holdout-study`, a one-command frozen-policy
  validation chain spanning continuation mining, replay, topology audit,
  terminal-neighborhood replay, selector transfer, and context-aware candidate
  validation.
- A packaged public-safe selector policy frozen at commit `ba0b37e`, plus the
  993-scenario holdout report at
  `docs/reports/waymo_selector_holdout_993.md`. The run reaches 78 selector
  decisions and passes 8/8 evaluation gates while rejecting candidate adoption
  after measuring 12 false promotions.
- Batched topology-audit source reads: 124 holdout topology cases now require
  four raw-source passes instead of rescanning a TFRecord for every case.
- Fingerprinted `selector-holdout-study --resume` recovery. Atomic `state.json`
  checkpoints preserve interruption diagnostics and completed-stage hashes;
  resume reuses only a verified contiguous prefix and rejects changed inputs,
  changed configuration, missing files, or tampered artifacts.
- `scenariolens release-check`, a 15-check clean-package gate that builds a
  byte-identical wheel twice, installs it into an isolated environment, runs
  the product outside the checkout, verifies explicit bad-input diagnostics,
  injects an actual nine-stage interruption, and proves resumed output matches
  uninterrupted output.

- `scenariolens run`, a one-command product workflow that expands native input
  directories, hashes source files, executes baseline-comparison,
  heading-aware lane-selection, and linked-lane continuation studies, and
  writes one versioned run manifest/report with stage timings and a stable
  analysis digest.
- `scenariolens run-verify`, a release gate that compares independent run
  bundles, verifies input and stage fingerprints, enforces matching analysis
  digests, and checks the 15-minute and 8 GB laptop budgets. Run manifests now
  record cross-platform peak process memory.
- Every `scenariolens run` bundle now generates `explorer/index.html`, a
  versioned `explorer/run.json`, ranked `explorer/scenarios.json`, and rendered
  trajectory assets. Explorer case IDs participate in the deterministic
  analysis digest, and the static frontend is included in built packages.
- The Scenario Explorer now reads `scenariolens.explorer_run.v1` provenance and
  stage metrics, uses a compact operational layout instead of a report-card
  wall, and shares the same frontend between the public demo and local runs.
  Three Playwright tests cover the public workflow, generated-run assets and
  report links, console errors, and desktop/mobile overflow in CI.
- `scenariolens demo --open` and `scenariolens run ... --open` now validate and
  serve generated run bundles through a loopback HTTP server, print the exact
  Explorer URL, launch the system browser, and stop cleanly on Ctrl+C. Host,
  port, ephemeral-port, and headless-browser controls are available without
  changing the existing non-interactive command behavior.
- `lane-continuation-study --scenario-offset` now selects deterministic
  per-input scenario windows before applying `--max-scenarios`, records the
  boundary in source and top-level manifests, and preserves original
  within-source indices for leakage-auditable holdout studies.
- `docs/reports/scenariolens_v1_run_validation.md`, generated from two complete
  1,193-scenario runs over four local Waymo Motion validation shards. All 7
  readiness, digest, input, stage, duration, and memory checks pass; the slower
  run completed in 459.495 seconds and peak memory remained at 1.915 GB.
- `docs/v1_acceptance.md`, freezing the one-command product contract, complete
  1,193-scenario local-corpus gate, separate 993-scenario frozen-policy
  validation cohort, clean-package and browser requirements, performance
  budget, honest non-goals, and terminal `v1.0.0` release criteria.
- `scenariolens evidence-index` workflow,
  `docs/reports/scenariolens_evidence_index.md`, and
  `docs/demo/evidence_index.json`, generating a v1 public evidence spine that
  verifies 16 demo/report/provenance/selector/CI artifacts and makes the
  project easier to review without publishing raw Waymo records.
- `scenariolens public-surface-check` workflow and
  `docs/reports/scenariolens_public_surface_check.md`, adding an offline v1
  release-readiness gate for public links, demo JSON contracts, SVG assets,
  raw-data boundaries, public-safety language, and CI smoke coverage.
- 200-scenario lane-continuation and terminal-selector scale-up reports across
  four local Waymo Motion validation shards:
  `docs/reports/waymo_lane_continuation_study_200.md`,
  `docs/reports/waymo_lane_continuation_replay_prototype_200.md`,
  `docs/reports/waymo_lane_continuation_topology_gap_audit_200.md`, and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md`.
  The pass scans 451 lane-continuation targets, replays/probes 45 queued
  cases, audits 15 topology blockers, and publishes 7 terminal-selector visual
  cards with 0 false promotions and 1 remaining false hold under the best
  zero-false-promotion calibration candidate.
- `scenariolens lane-continuation-terminal-neighborhood-selector-transfer`
  workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md`,
  applying the 6-case provisional selector calibration to the broader
  200-scenario replay queue. The transfer validation covers 7 cases, including
  4 novel validation cases, improves replay-gate matches from 4/7 to 5/7, and
  keeps 0 false promotions while leaving 2 false holds.
- `scenariolens lane-continuation-terminal-neighborhood-selector-error-audit`
  workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_error_audit_200.md`,
  explaining the transfer queue's remaining 2 false holds and testing 5
  counterfactual selector gates. The audit shows that relaxing heading to 0.70
  reduces false holds from 2 to 1 without false promotions on this small queue,
  while combining heading relaxation with a 25 m route-extension gate introduces
  a false promotion.
- `scenariolens lane-continuation-terminal-neighborhood-selector-route-context-audit`
  workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200.md`,
  joining the 2 transfer false holds back to derived replay diagnostics. The
  route/context audit separates 1 borderline heading-relaxation validation
  candidate from 1 severe selected-heading disagreement that should remain held
  for lane-direction, route-context, and coordinate-frame inspection.
- `scenariolens lane-continuation-terminal-neighborhood-selector-candidate-validation`
  workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md`,
  validating a narrow context-aware heading candidate on the 7-case transfer
  queue. The candidate improves replay-label agreement from 5/7 to 6/7,
  recovers 1 false hold, preserves 2/2 replay-held negative controls, keeps 0
  false promotions, and leaves the severe route/context case held.
- `scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas`
  workflow,
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md`,
  and `docs/demo/selector_decisions.json`, joining the 7 visual selector
  cards to candidate-validation labels. The static Explorer now shows the
  recovered false hold, 3 accepted recoveries, 2 negative controls, and 1
  retained route/context hold without publishing raw Waymo records or changing
  default selector behavior.
- `scenariolens lane-continuation-terminal-neighborhood-casebook` now supports
  `--asset-prefix` so multiple public casebooks can share
  `docs/reports/assets/` without overwriting SVG cards.
- `scenariolens lane-continuation-terminal-neighborhood-casebook` workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md`,
  publishing six derived SVG decision cards for the expanded terminal selector
  queue: 3 replay-accepted recoveries, 3 held negative controls, and 0 raw
  Waymo trajectories or map geometry.
- `scenariolens lane-continuation-terminal-neighborhood-selector-calibration`
  workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md`,
  sweeping 30 selector gate candidates and recommending a provisional 40 m
  route-extension gate that improves expanded replay-label agreement from 4/6
  to 6/6 with 0 false promotions on the current queue.
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
- Waymo Motion ingestion now preserves the first 240 map features and appends a
  bounded two-hop linked-lane closure set, cutting continuation topology gaps
  from 33 to 17 on an earlier 100-scenario local validation slice.
- Waymo Motion ingestion now extends that bounded linked-lane closure to seven
  hops and up to 240 closure features, raising the 100-scenario
  lane-continuation study to 223 candidates, 210 linked-lane rollouts, 143
  linked-lane improvements, and 13 remaining topology gaps.
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
- `scenariolens lane-continuation-route-context-guard` workflow and
  `docs/reports/waymo_lane_continuation_route_context_guard.md`, testing a
  stricter non-oracle route-context promotion guard against branch replay
  outcomes.
- `scenariolens lane-continuation-route-context-guard-calibration` workflow
  and `docs/reports/waymo_lane_continuation_route_context_guard_calibration.md`,
  sweeping endpoint-alignment gates and keeping the current -0.05 gate with
  0 false holds and 0 false promotions on the current branch replay queue.
- Expanded lane-continuation branch queue artifacts at
  `docs/reports/waymo_lane_continuation_branch_coverage_expanded.md` and
  `docs/reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md`,
  raising the queue to 30 candidates, 20 replay cases, 10 topology probes, 6
  branchable cases, and 1 replay-held route-context negative control.
- Expanded topology/terminal-neighborhood follow-up reports at
  `docs/reports/waymo_lane_continuation_topology_gap_audit_expanded.md`,
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md`,
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md`,
  and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md`,
  triaging 10 expanded topology blockers into 0 cap-recoverable linked-target
  gaps and 10 terminal/directional selected-lane cases, finding 6 nearby
  recovery candidates, replay-accepting 3/6 ready candidates, and
  selector-promoting 1 candidate with 0 false promotions.
- `scenariolens lane-continuation-branch-coverage` workflow and
  `docs/reports/waymo_lane_continuation_branch_coverage.md`, connecting the
  continuation candidate, replay, diagnostics, branch-selection, branch-replay,
  and route-context guard manifests into a public-safe expansion funnel.
- `scenariolens lane-continuation-topology-gap-audit` workflow and
  `docs/reports/waymo_lane_continuation_topology_gap_audit.md`, reloading the
  5 topology blockers from the replay manifest and showing that 0 blocker cases
  remain cap-recoverable while 5 lanes are terminal or directional-link cases
  after linked-lane closure materialization.
- `scenariolens lane-continuation-terminal-neighborhood-audit` workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_audit.md`,
  reloading the 5 terminal/directional blockers and finding 2 nearby
  alternate-lane recovery candidates plus 3 directional-link mismatches without
  changing the default scorer.
- `scenariolens lane-continuation-terminal-neighborhood-replay` workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_replay.md`,
  force-replaying the 2 nearby recovery candidates, accepting 1 alternate lane
  for a bounded selector experiment, and holding 1 regression case.
- `scenariolens lane-continuation-terminal-neighborhood-selector` workflow and
  `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector.md`,
  applying a bounded non-oracle selector policy that promotes 1 alternate lane,
  holds 1 low-heading case, and matches the replay gate on 2/2 decisions.
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
