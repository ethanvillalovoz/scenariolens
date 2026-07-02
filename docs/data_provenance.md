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
publishes aggregate/ranked diagnostics only: 178 candidate tracks, 145 linked
lane rollouts, 96 improvements, 47 regressions, and 33 topology gaps. Raw
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
2 branchable parsed-topology cases, 3 single-chain cases, and 2 oracle
upper-bound improvements. The oracle branch uses observed future motion only
as a diagnostic upper bound; it is not a deployed route selector. Local branch
manifests remain ignored under `data/processed/`.

## Interpretation Rules

- Checked-in metrics demonstrate the ScenarioLens pipeline, not Waymo benchmark
  performance.
- Synthetic scenarios are useful for testing expected long-tail patterns before
  spending time on large downloads.
- Waymo-shaped fixtures prove field mapping and ingestion behavior, not dataset
  scale.
- The checked-in validation and stability reports document small local
  real-data runs, not full Waymo benchmark submissions.
