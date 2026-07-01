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

## Synthetic Demo

```bash
scenariolens demo
scenariolens report --format markdown --limit 5
scenariolens render --top 3 --output-dir /tmp/scenariolens-gallery
```

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
report keeps both sides of the diagnostic: 96 linked-lane improvements, 47
regressions, and 33 topology gaps.

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
