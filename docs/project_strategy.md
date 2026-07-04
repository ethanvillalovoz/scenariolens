# ScenarioLens Product Strategy

## North Star

ScenarioLens is a local-first autonomy evaluation tool that turns motion
scenario data into ranked, explainable long-tail evaluation candidates where
simple prediction baselines struggle.

The project is built to answer one practical question:

> If an autonomous-driving team is preparing for a new operating domain, which
> recorded scenarios should engineers inspect, replay, perturb, or add to an
> evaluation set first, especially when a lightweight predictor fails?

## End Goal

The finished repo should feel like a small production evaluation system, not a
toy model. A reviewer should be able to clone it, run tests, inspect the data
boundary, generate reports, open the explorer, and understand how each scenario
was ranked.

The strongest portfolio signal is not that ScenarioLens replaces a self-driving
stack. It is that the repo demonstrates the kind of judgment autonomy teams
need around data quality, scenario selection, metric design, validation, and
honest communication of limitations.

## Target User

ScenarioLens is aimed at an autonomy evaluation engineer, prediction/planning
engineer, simulation engineer, or technical recruiter reviewing evidence of
interest in Waymo-style problems.

That user wants to know:

- whether a dataset adapter is real or only mocked,
- which fields are trusted and which are ignored,
- why a scenario is considered high value,
- where a baseline predictor fails,
- how rankings can be reproduced,
- where raw data lives,
- what the next engineering milestone would be.

## Product Surface

ScenarioLens currently has four connected surfaces:

1. **Dataset boundary**: synthetic records, normalized CSV, Waymo
   Motion-shaped JSON, binary Scenario protos, and small Waymo Motion TFRecord
   slices.
2. **Evaluation core**: a compact schema, quality filtering, taxonomy tags,
   constant-velocity baseline ADE/FDE, lane-aware baseline comparison, and
   heading-aware lane-selection ablation, plus interpretable score components
   for density, VRUs, proximity, TTC, path conflict, dynamics, baseline failure,
   and scenario category.
3. **Artifacts**: Markdown/JSON reports, SVG trajectory previews, validation
   packets, baseline-debug casebooks, replay-candidate plans, open-loop replay
   prototype packets, heading-aware replay packets, map-match audits,
   lane-selection studies, and public-safe real-data case studies.
4. **Explorer**: a static dashboard for filtering, sorting, inspecting scenario
   evidence, and reviewing public-safe heading-aware case diagnostics and replay
   planning links without requiring a backend.

## Why It Is Waymo-Aligned

Waymo's public ecosystem emphasizes datasets, motion prediction, simulation,
scenario generation, and safety evaluation. ScenarioLens fits that public
boundary by focusing on scenario triage: finding and explaining the interactions
where a simple trajectory baseline struggles and that deserve more targeted
evaluation.

The repo intentionally uses public Waymo Motion `Scenario`-shaped records and a
downloaded validation-shard smoke test, while keeping raw data outside git.
That makes the project credible without implying access to Waymo's private
stack or internal metrics.

## What This Is Not

ScenarioLens is not:

- a production autonomy stack,
- a motion forecasting benchmark submission,
- a claim about Waymo production performance,
- a replacement for the official Waymo Open Dataset tooling,
- a visual perception or LiDAR project.

It is a focused scenario evaluation and data-product project.

## Work Tracks

### 1. Recruiter Polish

Make the first two minutes strong: README, screenshot, live explorer, concise
project brief, recruiting packet, honest data provenance, and a public-safe
real-data case study.

### 2. Engineering Depth

Keep the core runnable and tested: deterministic fixtures, dependency-light
Waymo Motion parsing, validation packets, CI, documented schemas, and clear
failure modes for missing or malformed data.

### 3. ML and Simulation Path

Use the ranking output as the bridge into ML: select high-value scenarios,
compare lightweight trajectory-baseline errors by scenario type, and reserve
JAX/Waymax for replay or perturbation once the data contract is stable.

### 4. Dashboard and Product Experience

Treat the explorer as an engineering tool, not a landing page: ranked cases,
filters, score explanations, baseline ADE/FDE, map context, real-data status,
and links back to reports and provenance.

## Current Proof

- Static explorer: [`docs/demo`](demo)
- Data provenance: [`docs/data_provenance.md`](data_provenance.md)
- Architecture: [`docs/architecture.md`](architecture.md)
- Framework concepts: [`docs/framework_concepts.md`](framework_concepts.md)
- CLI workflows: [`docs/cli_workflows.md`](cli_workflows.md)
- Tech stack rationale: [`docs/tech_stack.md`](tech_stack.md)
- Technical case study:
  [`docs/case_studies/waymo_baseline_failures.md`](case_studies/waymo_baseline_failures.md)
- Real-data case study:
  [`docs/reports/waymo_motion_case_study.md`](reports/waymo_motion_case_study.md)
- Validation summary:
  [`docs/reports/waymo_motion_validation_summary.md`](reports/waymo_motion_validation_summary.md)
- Failure study:
  [`docs/reports/waymo_motion_failure_study.md`](reports/waymo_motion_failure_study.md)
- Failure stability study:
  [`docs/reports/waymo_motion_failure_stability.md`](reports/waymo_motion_failure_stability.md)
- Lane-aware baseline comparison:
  [`docs/reports/lane_aware_baseline_study.md`](reports/lane_aware_baseline_study.md)
- Real lane-aware cross-shard diagnostic:
  [`docs/reports/waymo_lane_aware_baseline_cross_shard.md`](reports/waymo_lane_aware_baseline_cross_shard.md)
- Lane-aware baseline debug casebook:
  [`docs/reports/waymo_lane_aware_debug_casebook.md`](reports/waymo_lane_aware_debug_casebook.md)
- Replay candidate plan:
  [`docs/reports/waymo_replay_candidate_plan.md`](reports/waymo_replay_candidate_plan.md)
- Open-loop replay prototype:
  [`docs/reports/waymo_open_loop_replay_prototype.md`](reports/waymo_open_loop_replay_prototype.md)
- Map-match threshold audit:
  [`docs/reports/waymo_map_match_audit.md`](reports/waymo_map_match_audit.md)
- Heading-aware lane-selection study:
  [`docs/reports/waymo_heading_aware_lane_selection_study.md`](reports/waymo_heading_aware_lane_selection_study.md)
- Heading-aware debug casebook:
  [`docs/reports/waymo_heading_aware_debug_casebook.md`](reports/waymo_heading_aware_debug_casebook.md)
- Heading-aware replay candidate plan:
  [`docs/reports/waymo_heading_aware_replay_candidate_plan.md`](reports/waymo_heading_aware_replay_candidate_plan.md)
- Heading-aware replay prototype:
  [`docs/reports/waymo_heading_aware_replay_prototype.md`](reports/waymo_heading_aware_replay_prototype.md)
- Lane-continuation candidate plan:
  [`docs/reports/waymo_lane_continuation_candidate_plan.md`](reports/waymo_lane_continuation_candidate_plan.md)
- Lane-continuation replay prototype:
  [`docs/reports/waymo_lane_continuation_replay_prototype.md`](reports/waymo_lane_continuation_replay_prototype.md)
- Lane-continuation route diagnostics:
  [`docs/reports/waymo_lane_continuation_route_diagnostics.md`](reports/waymo_lane_continuation_route_diagnostics.md)
- Lane-continuation branch selection:
  [`docs/reports/waymo_lane_continuation_branch_selection.md`](reports/waymo_lane_continuation_branch_selection.md)
- Motion-context branch replay:
  [`docs/reports/waymo_lane_continuation_branch_replay.md`](reports/waymo_lane_continuation_branch_replay.md)
- Branch rollout gate:
  [`docs/reports/waymo_lane_continuation_branch_rollout_gate.md`](reports/waymo_lane_continuation_branch_rollout_gate.md)
- Route-context guard study:
  [`docs/reports/waymo_lane_continuation_route_context_guard.md`](reports/waymo_lane_continuation_route_context_guard.md)
- Route-context guard calibration:
  [`docs/reports/waymo_lane_continuation_route_context_guard_calibration.md`](reports/waymo_lane_continuation_route_context_guard_calibration.md)
- Branch coverage audit:
  [`docs/reports/waymo_lane_continuation_branch_coverage.md`](reports/waymo_lane_continuation_branch_coverage.md)
- Expanded branch coverage audit:
  [`docs/reports/waymo_lane_continuation_branch_coverage_expanded.md`](reports/waymo_lane_continuation_branch_coverage_expanded.md)
- Expanded route-context guard calibration:
  [`docs/reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md`](reports/waymo_lane_continuation_route_context_guard_calibration_expanded.md)
- Expanded topology gap audit:
  [`docs/reports/waymo_lane_continuation_topology_gap_audit_expanded.md`](reports/waymo_lane_continuation_topology_gap_audit_expanded.md)
- Expanded terminal neighborhood audit:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_audit_expanded.md)
- Expanded terminal neighborhood replay gate:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_replay_expanded.md)
- Expanded terminal neighborhood selector experiment:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_expanded.md)
- Expanded terminal neighborhood selector calibration:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_expanded.md)
- Expanded terminal selector visual casebook:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md`](reports/waymo_lane_continuation_terminal_neighborhood_casebook_expanded.md)
- 200-scenario lane-continuation study:
  [`docs/reports/waymo_lane_continuation_study_200.md`](reports/waymo_lane_continuation_study_200.md)
- 200-scenario terminal selector transfer validation:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md)
- 200-scenario terminal selector error audit:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_error_audit_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_error_audit_200.md)
- 200-scenario terminal selector route/context audit:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector_route_context_audit_200.md)
- 200-scenario terminal selector visual casebook:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md`](reports/waymo_lane_continuation_terminal_neighborhood_casebook_200.md)
- Topology gap audit:
  [`docs/reports/waymo_lane_continuation_topology_gap_audit.md`](reports/waymo_lane_continuation_topology_gap_audit.md)
- Terminal neighborhood audit:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_audit.md`](reports/waymo_lane_continuation_terminal_neighborhood_audit.md)
- Terminal neighborhood replay gate:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_replay.md`](reports/waymo_lane_continuation_terminal_neighborhood_replay.md)
- Terminal neighborhood selector experiment:
  [`docs/reports/waymo_lane_continuation_terminal_neighborhood_selector.md`](reports/waymo_lane_continuation_terminal_neighborhood_selector.md)
- No-auth baseline ablation:
  [`docs/reports/baseline_ablation_study.md`](reports/baseline_ablation_study.md)
- Shard expansion plan:
  [`docs/reports/waymo_motion_shard_plan.md`](reports/waymo_motion_shard_plan.md)
- Roadmap: [`docs/roadmap.md`](roadmap.md)
