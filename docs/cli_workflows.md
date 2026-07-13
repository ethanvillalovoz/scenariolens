# ScenarioLens CLI Workflows

This page collects the copy-paste workflows that make ScenarioLens feel like a
real framework instead of a one-off script.

## Install Locally

```bash
python -m pip install -e .
scenariolens --help
```

If your system Python is externally managed, create a virtualenv first:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m unittest discover
```

## One-Command Analysis Bundle

Run the complete core analysis path on the built-in synthetic corpus:

```bash
scenariolens export-synthetic --output /tmp/scenariolens-synthetic.json
scenariolens run \
  --input /tmp/scenariolens-synthetic.json \
  --format scenariolens-json \
  --output runs/synthetic \
  --max-scenarios 11 \
  --top 10
```

Run the same product path over every supported native file in a local Waymo
Motion directory:

```bash
scenariolens run \
  --input data/raw/waymo/motion/validation \
  --format native \
  --output runs/waymo-validation \
  --max-scenarios 400 \
  --top 50
```

Native directories expand into deterministic per-file sources, so
`--max-scenarios` applies to each shard. The command hashes every input and
runs the baseline-comparison, heading-aware lane-selection, and linked-lane
continuation studies. It writes a top-level `manifest.json`, concise
`report.md`, stage timings, aggregate metrics, stable analysis digest, and all
specialist artifacts under `studies/`. It also ranks the input cases, renders
trajectory SVGs under `assets/`, and writes a self-contained static Explorer
under `explorer/`. The Explorer payload records run provenance, stage metrics,
case IDs, and portable report links. Use `--no-input-hash` only for a local
iteration where provenance is not required.

Validate two independent runs against the v1 determinism and laptop budgets:

```bash
scenariolens run-verify \
  --manifest runs/waymo-validation-01/manifest.json \
  --manifest runs/waymo-validation-02/manifest.json \
  --output-dir data/processed/scenariolens_v1_run_validation \
  --max-duration-seconds 900 \
  --max-peak-memory-gb 8 \
  --public-report docs/reports/scenariolens_v1_run_validation.md
```

The validator requires every run and stage to be ready, identical input and
stage fingerprints, one shared analysis digest, matching source/scenario
scope, and compliance with both execution budgets. Timestamps, output paths,
and timings are intentionally excluded from the analysis digest; source
hashes, configuration, stage formats, counts, and aggregate metrics are not.

Browser-test both the public demo and a newly generated local run:

```bash
npm ci
npx playwright install chromium
npm run test:browser
```

The suite exercises run metadata, stage summaries, filtering, sorting, case
selection, trajectory loading, report links, desktop layout, and mobile
overflow while failing on browser console errors.

## Synthetic Demo

```bash
scenariolens demo
scenariolens report --format markdown --limit 5
scenariolens render --top 3 --output-dir /tmp/scenariolens-gallery
```

## V1 Evidence Index

```bash
scenariolens evidence-index \
  --output-dir data/processed/scenariolens_evidence_index \
  --public-report docs/reports/scenariolens_evidence_index.md \
  --demo-json docs/demo/evidence_index.json \
  --repo-root .
```

This verifies the curated public evidence spine: live demo assets, provenance,
real-data reports, selector-validation artifacts, static demo payloads, and CI.
The output is a local ignored run packet plus checked-in Markdown/JSON copies.

## Public Surface Check

```bash
scenariolens public-surface-check \
  --output-dir data/processed/scenariolens_public_surface_check \
  --public-report docs/reports/scenariolens_public_surface_check.md \
  --repo-root .
```

This is the v1 release-readiness gate for the public repo surface. It checks the
evidence index, static demo JSON contracts, local README/demo/report links,
referenced SVG assets, raw-data boundary, public-safety language, and CI smoke
coverage without reading local Waymo shards or fetching external URLs.

## Waymo-Shaped Fixtures

```bash
scenariolens ingest-waymo-motion \
  --format native \
  --input docs/examples/waymo_motion_native_sample.json \
  --output /tmp/scenariolens-waymo-native.json

scenariolens report \
  --input /tmp/scenariolens-waymo-native.json \
  --format markdown \
  --limit 5
```

## Local Waymo Motion Slice

Raw Waymo files stay outside git under `data/raw/`.

```bash
scenariolens waymo-motion-doctor \
  --input data/raw/waymo/motion/validation \
  --output data/processed/waymo_motion_readiness.json

scenariolens waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

## Failure Study

```bash
scenariolens failure-study \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_failure_study \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_motion_failure_study.md
```

## Baseline Comparison

```bash
scenariolens baseline-compare \
  --format markdown \
  --limit 8 \
  --output docs/reports/lane_aware_baseline_study.md
```

This compares the default constant-velocity baseline against the lane-aware
baseline. Vehicles and cyclists use parsed lane polylines when map context is
available; pedestrians, missing maps, low-speed tracks, and distant lane matches
fall back to constant velocity.

## Real Lane-Aware Baseline Study

```bash
scenariolens baseline-compare-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --output-dir data/processed/waymo_lane_aware_baseline_cross_shard \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_lane_aware_baseline_cross_shard.md
```

This writes an ignored local manifest/report packet and a public-safe Markdown
copy. Use it to compare constant-velocity and lane-aware ADE/FDE/miss-rate
estimates across repeated Waymo Motion inputs, including top improvements,
top regressions, map-used counts, and fallback reasons. Negative improvement is
valid diagnostic evidence: it shows where naive nearest-lane following needs a
richer map, intent, or replay model.

## Baseline Debug Casebook

```bash
scenariolens baseline-debug \
  --study-manifest data/processed/waymo_lane_aware_baseline_cross_shard/manifest.json \
  --output-dir data/processed/waymo_lane_aware_debug_casebook \
  --case-count 3 \
  --public-report docs/reports/waymo_lane_aware_debug_casebook.md
```

This selects a lane-aware improvement, regression, and fallback-heavy case from
a `baseline-compare-study` manifest. It writes local SVG overlays and per-track
debug manifests under ignored `data/processed/` paths, plus a public-safe
casebook with scenario IDs, metric summaries, fallback reasons, and
interpretation.

## Replay Candidate Plan

```bash
scenariolens replay-candidates \
  --debug-manifest data/processed/waymo_lane_aware_debug_casebook/manifest.json \
  --output-dir data/processed/waymo_replay_candidates \
  --public-report docs/reports/waymo_replay_candidate_plan.md
```

This turns a `baseline-debug` manifest into a small Waymax/JAX replay candidate
queue. It ranks the improvement, regression, and fallback-heavy examples by
priority, records readiness labels, and separates replay-ready cases from
map-match audits. It is a planning artifact for the next experiment, not a
claim that ScenarioLens already runs replay simulation.

## Open-Loop Replay Prototype

```bash
scenariolens replay-prototype \
  --candidate-manifest data/processed/waymo_replay_candidates/manifest.json \
  --output-dir data/processed/waymo_replay_prototype \
  --top 2 \
  --public-report docs/reports/waymo_open_loop_replay_prototype.md
```

This reloads the top replay-ready local scenarios, replays the
constant-velocity and lane-aware open-loop rollouts from the same anchor state,
and applies small deterministic anchor-velocity perturbations. The checked-in
report publishes aggregate metrics only: the real run covers two Waymo Motion
scenarios, four prediction targets, and eight perturbation trials. It is not a
closed-loop simulator, not Waymax/JAX execution, and not a Waymo benchmark
claim.

## Map-Match Audit

```bash
scenariolens map-match-audit \
  --debug-manifest data/processed/waymo_lane_aware_debug_casebook/manifest.json \
  --output-dir data/processed/waymo_map_match_audit \
  --case-count 1 \
  --public-report docs/reports/waymo_map_match_audit.md
```

This reads a `baseline-debug` manifest, reloads selected fallback-heavy local
scenarios, sweeps lane-match thresholds, and checks whether accepting farther
lane matches helps or hurts FDE. The checked-in real-data report shows why the
current threshold is a guardrail: widening the radius on the fallback-heavy case
made the lane-aware baseline worse, so the right next step is lane-set,
coordinate-frame, and lane-selection auditing rather than a larger default
radius.

## Heading-Aware Lane Selection Study

```bash
scenariolens lane-selection-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --output-dir data/processed/waymo_lane_selection_study \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_heading_aware_lane_selection_study.md
```

This compares the existing nearest-lane selector with a heading-aware selector
that prefers lane tangents aligned with the target's anchor velocity. It keeps
the default ScenarioLens scorer unchanged. The current real-data report shows a
small FDE improvement over nearest-lane selection while still trailing constant
velocity overall, which makes it useful as an honest map-matching ablation
rather than a production prediction claim.

## Heading-Aware Debug Casebook

```bash
scenariolens baseline-debug \
  --study-manifest data/processed/waymo_lane_selection_study/manifest.json \
  --output-dir data/processed/waymo_heading_aware_debug_casebook \
  --case-count 6 \
  --public-report docs/reports/waymo_heading_aware_debug_casebook.md
```

When the study manifest comes from `lane-selection-study`, `baseline-debug`
switches into a heading-aware casebook mode. It writes ignored local SVG
overlays and per-case manifests comparing constant velocity, nearest-lane, and
heading-aware forecasts, while the public report keeps only scenario IDs,
metrics, fallback reasons, and interpretation.

## Heading-Aware Replay Candidate Plan

```bash
scenariolens replay-candidates \
  --debug-manifest data/processed/waymo_heading_aware_debug_casebook/manifest.json \
  --output-dir data/processed/waymo_heading_aware_replay_candidates \
  --public-report docs/reports/waymo_heading_aware_replay_candidate_plan.md
```

When the debug manifest comes from the heading-aware casebook, `replay-candidates`
switches into a nearest-lane vs heading-aware planning mode. It ranks selector
wins, regressions, and fallback-heavy cases, keeps constant velocity as context,
and labels which cases are ready for the heading-aware replay prototype
versus which still need map-match or coordinate-frame audit.

## Heading-Aware Replay Prototype

```bash
scenariolens heading-replay-prototype \
  --candidate-manifest data/processed/waymo_heading_aware_replay_candidates/manifest.json \
  --output-dir data/processed/waymo_heading_aware_replay_prototype \
  --top 5 \
  --public-report docs/reports/waymo_heading_aware_replay_prototype.md
```

This reloads the selected local scenarios from the heading-aware replay
candidate queue, reruns nearest-lane and heading-aware open-loop rollouts from
the same anchor state, and applies deterministic speed/heading perturbations.
The checked-in real-data run covers all five heading-ready cases from the
current queue. The public report keeps only scenario IDs, aggregate stability
counts, metric deltas, and local artifact pointers; raw Waymo files and replay
packets stay ignored under `data/processed/`.

## Map And Signal Context Study

```bash
scenariolens context-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --output-dir data/processed/waymo_context_study_cross_shard \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_context_study_cross_shard.md
```

This summarizes public-safe map, traffic-signal, stop-point, and lane-topology
coverage from local Waymo Motion records. The checked-in report covers the
same 100-scenario, four-shard local slice as the other real-data diagnostics
and publishes aggregate counts plus scenario IDs only.

## Context-Joined Failure Study

```bash
scenariolens context-failure-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --output-dir data/processed/waymo_context_failure_study_cross_shard \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_context_failure_study_cross_shard.md
```

This joins ScenarioLens scores and prediction-baseline errors with the parsed
map/signal context summaries. The checked-in report highlights context-rich
constant-velocity failures, signal-heavy failures, route-topology failures, and
lane-aware regressions with rich context.

## Context Evaluation Set

```bash
scenariolens context-eval-set \
  --context-failure-manifest data/processed/waymo_context_failure_study_cross_shard/manifest.json \
  --output-dir data/processed/waymo_context_eval_set \
  --top-per-group 5 \
  --public-report docs/reports/waymo_context_eval_set.md
```

This turns the context-joined failure manifest into a public-safe evaluation
set with grouped scenario IDs, acceptance checks, and follow-up experiment
hooks. The checked-in report contains 14 unique scenario IDs across signal,
route/topology, lane-regression, and fallback-stress groups. It is not an
official benchmark and does not include raw Waymo data.

## Context Eval Debug Casebook

```bash
scenariolens baseline-debug \
  --study-manifest data/processed/waymo_context_eval_set/manifest.json \
  --output-dir data/processed/waymo_context_eval_debug_casebook \
  --case-count 5 \
  --public-report docs/reports/waymo_context_eval_debug_casebook.md
```

When the study manifest comes from `context-eval-set`, `baseline-debug` reloads
the selected local scenarios, writes ignored SVG overlays and per-case
manifests, and publishes a public-safe casebook. The checked-in report covers
five context-eval seeds: context-rich failure, signal/topology cases,
fallback-stress cases, and a lane-aware regression.

## Context Replay Candidate Plan

```bash
scenariolens replay-candidates \
  --debug-manifest data/processed/waymo_context_eval_debug_casebook/manifest.json \
  --output-dir data/processed/waymo_context_replay_candidates \
  --public-report docs/reports/waymo_context_replay_candidate_plan.md
```

This turns the context eval debug casebook into a replay/debug queue. The
checked-in report identifies two replay-ready candidates and three map-match
audits while preserving the context-eval grouping instead of collapsing every
case into one aggregate score.

## Context Open-Loop Replay Prototype

```bash
scenariolens replay-prototype \
  --candidate-manifest data/processed/waymo_context_replay_candidates/manifest.json \
  --output-dir data/processed/waymo_context_replay_prototype \
  --top 2 \
  --public-report docs/reports/waymo_context_open_loop_replay_prototype.md
```

This executes the replay-ready portion of the context queue. The checked-in
report reloads two context eval seeds from local Waymo shards, compares
constant-velocity and lane-aware open-loop rollouts, and runs four deterministic
anchor perturbations per case. It publishes only public-safe stability metrics;
local replay packets, SVG overlays, and raw Waymo records stay ignored.

## Context Route/Intent Audit

```bash
scenariolens route-intent-audit \
  --replay-manifest data/processed/waymo_context_replay_prototype/manifest.json \
  --output-dir data/processed/waymo_context_route_intent_audit \
  --case-count 3 \
  --public-report docs/reports/waymo_context_route_intent_audit.md
```

This follows stable context replay regressions one diagnostic step deeper. The
current checked-in report reloads the stable warning case, compares
constant-velocity, nearest-lane, and heading-aware rollouts, and identifies a
lane-continuity or route-link follow-up before changing the matcher or making a
closed-loop simulation claim.

## Lane-Link Continuation Prototype

```bash
scenariolens lane-continuation-prototype \
  --audit-manifest data/processed/waymo_context_route_intent_audit/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_prototype \
  --case-count 3 \
  --public-report docs/reports/waymo_lane_continuation_prototype.md
```

This tests the route/intent audit's lane-continuity hypothesis without changing
the default scorer. A deterministic fixture proves the prototype can follow
parsed `exit_lanes`; the current real Waymo case resolves lane chain
`144 -> 190 -> 193` and reduces the clamped nearest-lane FDE by 63.578 m while
leaving the default scorer unchanged.

## Lane-Continuation Validation Study

```bash
scenariolens lane-continuation-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --format native \
  --output-dir data/processed/waymo_lane_continuation_study \
  --max-scenarios 25 \
  --top 10 \
  --public-report docs/reports/waymo_lane_continuation_study.md
```

This scans the same 100-scenario local Waymo slice for targets whose
nearest-lane rollout would clamp at the end of a selected lane. The checked-in
report keeps both sides of the diagnostic after linked-lane closure
materialization: 143 linked-lane improvements, 63 regressions, and 13 topology
gaps.

## Lane-Continuation Candidate Plan

```bash
scenariolens lane-continuation-candidates \
  --study-manifest data/processed/waymo_lane_continuation_study/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_candidates \
  --top-per-bucket 5 \
  --public-report docs/reports/waymo_lane_continuation_candidate_plan.md
```

This turns the validation study into a queue for follow-up work: positive
replay controls, regression replay/debug targets, and topology-audit blockers.
It is still a planning artifact, not a completed Waymax/JAX integration.

## Lane-Continuation Replay Prototype

```bash
scenariolens lane-continuation-replay-prototype \
  --candidate-manifest data/processed/waymo_lane_continuation_candidates/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_replay_prototype \
  --top-per-bucket 5 \
  --format native \
  --max-scenarios-per-source 25 \
  --public-report docs/reports/waymo_lane_continuation_replay_prototype.md
```

This executes the queued continuation controls and regressions in a lightweight
open-loop replay pass, then re-probes topology-audit rows as blockers. The
checked-in report covers 10 target-track replays, 40 deterministic
perturbation trials, and 5 topology probes while keeping raw Waymo data and
local replay packets ignored.

## Lane-Continuation Route Diagnostics

```bash
scenariolens lane-continuation-route-diagnostics \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_route_diagnostics \
  --top 10 \
  --public-report docs/reports/waymo_lane_continuation_route_diagnostics.md
```

This turns replay results into a route/topology casebook: stable linked-lane
regressions, horizon-limit cases, link-worse-than-constant-velocity cases, and
parser/topology blockers. It is still diagnostic evidence, not route planning.

## Lane-Continuation Branch Selection

```bash
scenariolens lane-continuation-branch-selection \
  --diagnostics-manifest data/processed/waymo_lane_continuation_route_diagnostics/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_branch_selection \
  --top 5 \
  --max-hops 2 \
  --public-report docs/reports/waymo_lane_continuation_branch_selection.md
```

This follows the route-diagnostics casebook by enumerating parsed branch
alternatives for continuation regressions. The `anchor_heading` selector uses
only anchor velocity and route geometry; the `motion_context` selector adds a
non-oracle prior from recent speed, known forecast horizon, route-chain length,
and downstream lane speed limits; the `oracle_upper_bound` selector uses
observed future motion only to measure recoverable branch-choice error. Treat
it as diagnostic evidence, not a route planner or benchmark claim.

## Lane-Continuation Branch Replay

```bash
scenariolens lane-continuation-branch-replay \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_branch_replay \
  --top 5 \
  --public-report docs/reports/waymo_lane_continuation_branch_replay.md
```

This replays motion-context branch choices under deterministic anchor-velocity
perturbations. The checked-in report covers 2 branchable real-data cases and 8
perturbation trials. The acceptance gate requires branch preservation and at
least 1.0 m recoverable FDE in every valid perturbation: 1 branch passes that
gate for broader selector evaluation while 1 speed-sensitive route-context
margin case remains held. The report also evaluates an experimental
history-speed-prior replay score; it preserves the accepted case while keeping
the route-context margin case held. Treat this as open-loop selector evidence,
not as route planning or a benchmark claim.

## Lane-Continuation Branch Rollout Gate

```bash
scenariolens lane-continuation-branch-rollout-gate \
  --branch-replay-manifest data/processed/waymo_lane_continuation_branch_replay/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_branch_rollout_gate \
  --public-report docs/reports/waymo_lane_continuation_branch_rollout_gate.md
```

This converts branch replay diagnostics into a conservative promote/hold
packet. The current real-data report promotes 1 branch for broader selector
evaluation and holds 1 route-context margin case. It is release-style evidence
triage, not a production release process, route planner, or benchmark claim.

## Lane-Continuation Route-Context Guard

```bash
scenariolens lane-continuation-route-context-guard \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection/manifest.json \
  --branch-replay-manifest data/processed/waymo_lane_continuation_branch_replay/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_route_context_guard \
  --public-report docs/reports/waymo_lane_continuation_route_context_guard.md
```

This evaluates a stricter non-oracle promotion guard over the two current
motion-context branch candidates. The guard uses route-fit, endpoint-alignment,
and downstream speed-limit context from branch selection, then checks whether
its promote/hold decision agrees with the replay gate. The current real-data
report promotes 1 robust branch, holds 1 route-context margin case for
route-feature follow-up, and records 2/2 replay-gate matches with 0 false holds.
Treat it as a candidate policy for larger branchable queues, not as a route
planner or benchmark.

## Lane-Continuation Route-Context Guard Calibration

```bash
scenariolens lane-continuation-route-context-guard-calibration \
  --route-context-guard-manifest data/processed/waymo_lane_continuation_route_context_guard/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_route_context_guard_calibration \
  --public-report docs/reports/waymo_lane_continuation_route_context_guard_calibration.md
```

This sweeps a small endpoint-alignment gate grid over the current guard
decisions and compares each candidate policy with branch-replay labels. The
current real-data report keeps the existing -0.05 endpoint gate with 0 false
holds and 0 false promotions on the 2-case queue. Treat it as calibration
evidence for a larger branchable queue, not as a default policy change.

## Lane-Continuation Branch Coverage Audit

```bash
scenariolens lane-continuation-branch-coverage \
  --candidate-manifest data/processed/waymo_lane_continuation_candidates/manifest.json \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype/manifest.json \
  --diagnostics-manifest data/processed/waymo_lane_continuation_route_diagnostics/manifest.json \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection/manifest.json \
  --branch-replay-manifest data/processed/waymo_lane_continuation_branch_replay/manifest.json \
  --route-context-guard-manifest data/processed/waymo_lane_continuation_route_context_guard/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_branch_coverage \
  --public-report docs/reports/waymo_lane_continuation_branch_coverage.md
```

This manifest-only audit connects the continuation candidate plan, replay
prototype, route diagnostics, branch selection, branch replay, and
route-context guard into one coverage funnel. The current real-data report
shows 15 continuation candidates, 10 replay-ready candidates, 5 branch-selection
cases, 3 branchable cases, 1 route-guard promotion, 5 topology blockers, and
8 expansion queue items. Treat it as a planning and coverage artifact, not as a
benchmark or proof that the selector is ready across the full dataset.

## Expanded Lane-Continuation Branch Queue

```bash
scenariolens lane-continuation-candidates \
  --study-manifest data/processed/waymo_lane_continuation_study/manifest.json \
  --top-per-bucket 10 \
  --output-dir data/processed/waymo_lane_continuation_candidates_expanded

scenariolens lane-continuation-replay-prototype \
  --candidate-manifest data/processed/waymo_lane_continuation_candidates_expanded/manifest.json \
  --top-per-bucket 10 \
  --output-dir data/processed/waymo_lane_continuation_replay_prototype_expanded \
  --format native \
  --max-scenarios-per-source 25

scenariolens lane-continuation-route-diagnostics \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json \
  --top 20 \
  --output-dir data/processed/waymo_lane_continuation_route_diagnostics_expanded

scenariolens lane-continuation-branch-selection \
  --diagnostics-manifest data/processed/waymo_lane_continuation_route_diagnostics_expanded/manifest.json \
  --top 10 \
  --max-hops 2 \
  --output-dir data/processed/waymo_lane_continuation_branch_selection_expanded

scenariolens lane-continuation-branch-replay \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection_expanded/manifest.json \
  --top 10 \
  --output-dir data/processed/waymo_lane_continuation_branch_replay_expanded

scenariolens lane-continuation-route-context-guard \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection_expanded/manifest.json \
  --branch-replay-manifest data/processed/waymo_lane_continuation_branch_replay_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_route_context_guard_expanded

scenariolens lane-continuation-route-context-guard-calibration \
  --route-context-guard-manifest data/processed/waymo_lane_continuation_route_context_guard_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_route_context_guard_calibration_expanded \
  --public-report docs/reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md

scenariolens lane-continuation-branch-coverage \
  --candidate-manifest data/processed/waymo_lane_continuation_candidates_expanded/manifest.json \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json \
  --diagnostics-manifest data/processed/waymo_lane_continuation_route_diagnostics_expanded/manifest.json \
  --branch-selection-manifest data/processed/waymo_lane_continuation_branch_selection_expanded/manifest.json \
  --branch-replay-manifest data/processed/waymo_lane_continuation_branch_replay_expanded/manifest.json \
  --route-context-guard-manifest data/processed/waymo_lane_continuation_route_context_guard_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_branch_coverage_expanded \
  --public-report docs/reports/waymo_lane_continuation_branch_coverage_expanded.md
```

This raises the current local branch queue from 15 to 30 continuation
candidates without changing the default scorer. The current expanded reports
produce 20 replay cases, 10 topology probes, 10 branch-selection cases, 6
branchable cases, 1 accepted branch replay, and 1 replay-held route-context
margin negative. The expanded guard calibration keeps the current -0.05
endpoint gate with 0 false holds and 0 false promotions on the expanded replay
queue. Treat this as a larger real-slice diagnostic, not full-dataset coverage.

## Expanded Lane-Continuation Topology Follow-Up

```bash
scenariolens lane-continuation-topology-gap-audit \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_topology_gap_audit_expanded \
  --public-report docs/reports/waymo_lane_continuation_topology_gap_audit_expanded.md

scenariolens lane-continuation-terminal-neighborhood-audit \
  --topology-manifest data/processed/waymo_lane_continuation_topology_gap_audit_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_audit_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md

scenariolens lane-continuation-terminal-neighborhood-replay \
  --terminal-neighborhood-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_audit_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded \
  --top 6 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md

scenariolens lane-continuation-terminal-neighborhood-selector \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md

scenariolens lane-continuation-terminal-neighborhood-selector-calibration \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md

scenariolens lane-continuation-terminal-neighborhood-casebook \
  --selector-calibration-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_casebook_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md
```

This follows the expanded branch queue's 10 topology blockers. The checked-in
public reports classify 0 cap-recoverable linked-target gaps and 10
terminal/directional selected-lane cases, find 6 nearby recovery candidates,
accept 3/6 ready candidates under deterministic replay perturbations, and
promote 1 candidate under the bounded non-oracle selector with 0 false
promotions. The calibration reaches 6/6 replay-label agreement, and the visual
casebook turns those six decisions into derived SVG cards for quick review.
Treat these as diagnostic selector inputs, not default routing behavior.

## Lane-Continuation Topology Gap Audit

```bash
scenariolens lane-continuation-topology-gap-audit \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_topology_gap_audit \
  --public-report docs/reports/waymo_lane_continuation_topology_gap_audit.md
```

This audit reloads the topology blocker cases named by the replay manifest and
compares capped ScenarioLens map features with raw parsed map-feature IDs. The
current real-data report audits 5 topology blockers, finds 0 blocker cases that
remain cap-recoverable after linked-lane closure materialization, and confirms
5 terminal or directional-link cases. Treat it as an ingestion/topology
expansion target, not as route-planning evidence.

## Lane-Continuation Terminal Neighborhood Audit

```bash
scenariolens lane-continuation-terminal-neighborhood-audit \
  --topology-manifest data/processed/waymo_lane_continuation_topology_gap_audit/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_audit \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_audit.md
```

This audit reloads the terminal/directional blockers from the topology-gap
manifest and inspects a bounded selected-lane neighborhood. The current
real-data report audits 5 cases, finds 2 nearby aligned lane recovery
candidates and 3 directional-link mismatches, and keeps the result framed as
replay/gating input rather than selector behavior.

## Lane-Continuation Terminal Neighborhood Replay

```bash
scenariolens lane-continuation-terminal-neighborhood-replay \
  --terminal-neighborhood-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_audit/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_replay \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_replay.md
```

This gate force-replays the nearby-lane recovery candidates from the
terminal-neighborhood audit against their selected terminal lanes. The current
real-data report evaluates 2 cases, accepts 1 alternate lane for a bounded
selector experiment, holds 1 regression case, and keeps the result framed as
diagnostic evidence rather than default selector behavior.

## Lane-Continuation Terminal Neighborhood Selector

```bash
scenariolens lane-continuation-terminal-neighborhood-selector \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector.md
```

This experiment applies a bounded, non-oracle selector policy to the
terminal-neighborhood replay candidates. The current real-data report promotes
1 heading-aligned alternate lane, holds 1 low-heading case, and matches the
replay gate on 2/2 decisions without changing default scorer behavior.

## Lane-Continuation Terminal Neighborhood Selector Calibration

```bash
scenariolens lane-continuation-terminal-neighborhood-selector-calibration \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md
```

This sweep keeps the default selector unchanged while evaluating 30
distance/heading/route-extension gate candidates against the expanded
terminal-neighborhood replay labels. The checked-in report recommends a
provisional 40 m route-extension gate, improving replay-label agreement from
4/6 to 6/6 with 0 false promotions on the current queue. Treat it as a
calibration target for broader evidence, not a production route selector.

## Lane-Continuation Terminal Neighborhood Casebook

```bash
scenariolens lane-continuation-terminal-neighborhood-casebook \
  --selector-calibration-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_casebook_expanded \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md
```

This converts the expanded selector calibration into a public-safe visual
casebook. The checked-in report publishes six derived SVG cards: 3
replay-accepted recoveries, 3 held negative controls, the current versus
recommended selector decision, and the gate evidence behind each choice. The
cards are metric diagrams, not trajectory or raw map overlays.

## 200-Scenario Terminal Selector Scale-Up

```bash
scenariolens lane-continuation-study \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150 \
  --input data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150 \
  --max-scenarios 50 \
  --top 20 \
  --output-dir data/processed/waymo_lane_continuation_study_200 \
  --public-report docs/reports/waymo_lane_continuation_study_200.md

scenariolens lane-continuation-candidates \
  --study-manifest data/processed/waymo_lane_continuation_study_200/manifest.json \
  --top-per-bucket 15 \
  --output-dir data/processed/waymo_lane_continuation_candidates_200 \
  --public-report docs/reports/waymo_lane_continuation_candidate_plan_200.md

scenariolens lane-continuation-replay-prototype \
  --candidate-manifest data/processed/waymo_lane_continuation_candidates_200/manifest.json \
  --top-per-bucket 15 \
  --max-scenarios-per-source 50 \
  --output-dir data/processed/waymo_lane_continuation_replay_prototype_200 \
  --public-report docs/reports/waymo_lane_continuation_replay_prototype_200.md

scenariolens lane-continuation-topology-gap-audit \
  --replay-manifest data/processed/waymo_lane_continuation_replay_prototype_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_topology_gap_audit_200 \
  --public-report docs/reports/waymo_lane_continuation_topology_gap_audit_200.md

scenariolens lane-continuation-terminal-neighborhood-audit \
  --topology-manifest data/processed/waymo_lane_continuation_topology_gap_audit_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_audit_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_audit_200.md

scenariolens lane-continuation-terminal-neighborhood-replay \
  --terminal-neighborhood-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_audit_200/manifest.json \
  --top 7 \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_200.md

scenariolens lane-continuation-terminal-neighborhood-selector \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-calibration \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-transfer \
  --selector-calibration-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded/manifest.json \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-error-audit \
  --selector-transfer-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_error_audit_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_error_audit_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-route-context-audit \
  --selector-transfer-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json \
  --terminal-neighborhood-replay-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_replay_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-candidate-validation \
  --selector-transfer-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200/manifest.json \
  --selector-route-context-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md

scenariolens lane-continuation-terminal-neighborhood-casebook \
  --selector-calibration-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200/manifest.json \
  --asset-prefix terminal_selector_casebook_200 \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_casebook_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md

scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas \
  --casebook-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_casebook_200/manifest.json \
  --candidate-validation-manifest data/processed/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200/manifest.json \
  --output-dir data/processed/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200 \
  --public-report docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md \
  --demo-json docs/demo/selector_decisions.json \
  --demo-assets-dir docs/demo/assets
```

This doubles the local shard window to 200 scenarios while staying laptop-safe.
The checked-in reports scan 451 lane-continuation targets, queue 45
replay/audit cases, replay 30 target tracks with 120 perturbation trials, audit
15 topology blockers, and replay 7 terminal-neighborhood candidates. The
selector calibration improves replay agreement from 4/7 to 6/7 with 0 false
promotions, but leaves 1 false hold; the report frames that as a remaining
selector limitation rather than a solved policy. The transfer-validation step
applies the 6-case provisional calibration to the broader 7-case replay queue:
it sees 3 overlap cases and 4 novel cases, improves default replay-gate
agreement from 4/7 to 5/7, keeps 0 false promotions, and leaves 2 false holds.
The error-audit step explains those false holds: both are novel heading-gate
misses, one is recoverable by a heading-relaxed diagnostic candidate, and a
combined heading/route relaxation would introduce a false promotion.
The route/context audit then joins both false holds back to derived replay
diagnostics: one becomes a borderline heading-relaxation validation candidate,
while the severe selected-heading disagreement stays held for lane-direction,
route-context, and coordinate-frame inspection.
The candidate-validation step applies only that context-aware heading candidate
on top of the transferred selector: replay agreement improves from 5/7 to 6/7,
false promotions remain 0, 2/2 replay-held negative controls stay held, and
the severe route/context case remains a false hold instead of becoming a broad
gate relaxation. The decision-atlas step joins those labels back to the 7
derived SVG cards so the Explorer can show 1 recovered false hold, 3 accepted
recoveries, 2 negative controls, and 1 retained route/context hold without
publishing raw Waymo records.

## Baseline Ablation

```bash
scenariolens baseline-ablation \
  --format markdown \
  --output docs/reports/baseline_ablation_study.md
```

This no-auth study compares constant velocity, the default lane-aware matcher,
and a stricter lane-aware matcher over the checked-in fixture corpus. Use it
when Waymo shard auth is blocked but you still want a reproducible technical
proof point.

## Stability Study

```bash
scenariolens failure-study-stability \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_failure_stability \
  --max-scenarios 75 \
  --window-size 25 \
  --top-tags 10 \
  --min-tag-slices 2 \
  --public-report docs/reports/waymo_motion_failure_stability.md
```

## Shard Expansion Plan

```bash
scenariolens waymo-motion-shard-plan \
  --input data/raw/waymo/motion/validation \
  --output docs/reports/waymo_motion_shard_plan.md \
  --json-output data/processed/waymo_motion_shard_plan.json \
  --next-count 3
```

## Dashboard Assets

```bash
scenariolens dashboard-data \
  --output docs/demo/scenarios.json \
  --assets-dir docs/demo/assets \
  --lane-selection-manifest data/processed/waymo_lane_selection_study/manifest.json
```

If the lane-selection manifest is present, the dashboard payload includes
public-safe heading-aware improvement, regression, and fallback-heavy cases for
the Explorer diagnostics panel. If the manifest is absent, the dashboard still
regenerates with the small fixture scenarios only.

Then preview:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000/demo/`.
