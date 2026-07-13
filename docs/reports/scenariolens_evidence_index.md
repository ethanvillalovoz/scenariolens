# ScenarioLens V1 Evidence Index

This generated index is the public evidence spine for ScenarioLens. It collects the product demo, data boundary, real-data diagnostics, replay bridges, selector validation reports, and CI surface that make the repo reviewable without publishing raw Waymo records.

It is intentionally honest: this is a scenario-mining and evaluation framework, not a production autonomy stack, not a closed-loop simulator, and not a Waymo benchmark submission.

## Readiness

- Ready: yes
- Required artifacts present: 17 / 17
- Missing required artifacts: 0
- Evidence stages: 8
- Public-safe artifacts indexed: 17
- Local real-data/Waymo-derived artifacts indexed: 14

## Stage Summary

| Stage | Present | Artifacts | Why it matters |
| --- | ---: | ---: | --- |
| Product surface | 2 | 2 | Makes the repo understandable quickly through static public artifacts. |
| Data boundary | 1 | 1 | Documents what data is trusted, derived, local, and excluded from git. |
| Scenario mining | 2 | 2 | Shows ScenarioLens can rank and explain real motion scenarios. |
| Baseline models | 2 | 2 | Compares lightweight prediction baselines with honest wins and regressions. |
| Replay bridge | 1 | 1 | Connects mined cases to laptop-safe open-loop replay diagnostics. |
| Lane continuation | 2 | 2 | Audits map-link and lane-continuation failure modes at larger scale. |
| Selector validation | 4 | 4 | Validates conservative selector gates before changing default behavior. |
| Release readiness | 3 | 3 | Keeps the public repo tested and contribution-ready. |

## Evidence Artifacts

| Artifact | Stage | Scope | Key metrics | Present |
| --- | --- | --- | --- | ---: |
| [Static Scenario Explorer](../demo/index.html) | Product surface | 14 public demo scenarios plus real-data evidence links | Explorer scenarios: 14; Live route: GitHub Pages/portfolio friendly | yes |
| [Data Provenance Boundary](../data_provenance.md) | Data boundary | Public-safe data handling and raw-data exclusion policy | Raw TFRecords in git: 0 | yes |
| [Cross-Shard Failure Stability](waymo_motion_failure_stability_cross_shard.md) | Scenario mining | 100 scenarios across 4 local Waymo Motion validation shards | Scenarios: 100; Validation shards: 4 | yes |
| [Context-Joined Failure Study](waymo_context_failure_study_cross_shard.md) | Scenario mining | Map, route, signal, and failure metrics over the 100-scenario slice | Scenarios: 100 | yes |
| [Lane-Aware Baseline Diagnostic](waymo_lane_aware_baseline_cross_shard.md) | Baseline models | Constant-velocity vs lane-aware estimates on 100 real scenarios | Scenarios: 100; Published regressions: yes | yes |
| [Heading-Aware Lane Selection Study](waymo_heading_aware_lane_selection_study.md) | Baseline models | 418 evaluated prediction targets from the 100-scenario slice | Evaluated targets: 418; FDE vs nearest lane: +0.489 m improvement | yes |
| [Heading-Aware Replay Prototype](waymo_heading_aware_replay_prototype.md) | Replay bridge | Selected heading-aware cases with deterministic perturbations | Perturbation mode: deterministic | yes |
| [200-Scenario Lane-Continuation Study](waymo_lane_continuation_study_200.md) | Lane continuation | 451 lane-continuation targets across four local validation shards | Scenarios: 200; Continuation targets: 451 | yes |
| [200-Scenario Continuation Replay](waymo_lane_continuation_replay_prototype_200.md) | Lane continuation | Replay/probe queue derived from the 200-scenario continuation study | Queued cases: 45; Raw trajectories committed: 0 | yes |
| [200-Scenario Terminal Selector Calibration](waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md) | Selector validation | Zero-false-promotion gate sweep over terminal-neighborhood cases | False promotions: 0; Default selector changed: no | yes |
| [Terminal Selector Transfer Validation](waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md) | Selector validation | 7-case validation queue, including 4 novel transfer cases | Validation cases: 7; Novel cases: 4 | yes |
| [Context-Aware Selector Candidate Validation](waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md) | Selector validation | Candidate policy joined to transfer and route/context audits | Agreement: 6/7; False promotions: 0 | yes |
| [Terminal Selector Decision Atlas](waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md) | Selector validation | 7 derived selector cards joined to candidate-validation labels | Visual cards: 7; Candidate agreement: 6/7 | yes |
| [Selector Atlas Demo Payload](../demo/selector_decisions.json) | Product surface | Public-safe selector decision cards loaded by the static Explorer | Cards: 7 | yes |
| [Full-Corpus Run Reproducibility](scenariolens_v1_run_validation.md) | Release readiness | Two complete analysis runs over 1,193 scenarios from four local validation shards | Scenarios per run: 1,193; Reproducibility checks: 7/7; Maximum duration: 459.495 s; Maximum peak memory: 1.915 GB | yes |
| [CI Validation Workflow](../../.github/workflows/ci.yml) | Release readiness | Unit tests plus deterministic run-bundle integration on every push | CI raw Waymo dependency: none | yes |
| [Public Surface Check](scenariolens_public_surface_check.md) | Release readiness | Offline check for public links, payload contracts, raw-data boundary, and CI smoke coverage | Offline checks: 7; Raw-data guard: yes | yes |

## Artifact Notes

### Static Scenario Explorer

- Path: `docs/demo/index.html`
- Proof type: interactive demo
- Command: `scenariolens dashboard-data --output docs/demo/scenarios.json`
- Data status: public fixtures plus aggregate/derived real-data links
- Why it matters: Gives a reviewer a zero-install first look at ranking, filtering, trajectory previews, failure cards, and selector diagnostics.
- Limitation: The explorer is static and does not expose raw Waymo data.

### Data Provenance Boundary

- Path: `docs/data_provenance.md`
- Proof type: provenance
- Command: `documented local Waymo Motion workflow`
- Data status: raw Waymo files ignored; public artifacts are derived
- Why it matters: Makes the project credible without implying private-data access or publishing restricted raw records.
- Limitation: External users need their own Waymo Open Dataset access.

### Cross-Shard Failure Stability

- Path: `docs/reports/waymo_motion_failure_stability_cross_shard.md`
- Proof type: real-data aggregate study
- Command: `scenariolens failure-study-stability --input ...`
- Data status: aggregate public report from local validation shards
- Why it matters: Shows that the ranking and baseline-failure workflow runs beyond one toy fixture or hand-picked scene.
- Limitation: This is a local diagnostic slice, not a Waymo benchmark.

### Context-Joined Failure Study

- Path: `docs/reports/waymo_context_failure_study_cross_shard.md`
- Proof type: context diagnostic
- Command: `scenariolens context-failure-study --input ...`
- Data status: public scenario IDs and aggregate context counts
- Why it matters: Connects scenario mining to map/signal context so failures are actionable, not just high numeric scores.
- Limitation: Context fields are derived from the lightweight parser boundary.

### Lane-Aware Baseline Diagnostic

- Path: `docs/reports/waymo_lane_aware_baseline_cross_shard.md`
- Proof type: baseline comparison
- Command: `scenariolens baseline-compare-study --input ...`
- Data status: aggregate public report with wins and regressions
- Why it matters: Demonstrates honest model evaluation: the map-aware baseline helps some cases and regresses others.
- Limitation: The lane-aware baseline is diagnostic, not a production predictor.

### Heading-Aware Lane Selection Study

- Path: `docs/reports/waymo_heading_aware_lane_selection_study.md`
- Proof type: map-matching ablation
- Command: `scenariolens lane-selection-study --input ...`
- Data status: aggregate target-level comparison
- Why it matters: Turns a failed naive map baseline into a specific matcher ablation with measured improvement over nearest-lane selection.
- Limitation: Heading-aware selection still trails constant velocity overall.

### Heading-Aware Replay Prototype

- Path: `docs/reports/waymo_heading_aware_replay_prototype.md`
- Proof type: open-loop replay
- Command: `scenariolens heading-replay-prototype --candidate-manifest ...`
- Data status: public-safe replay summary; local packets ignored
- Why it matters: Shows the path from mined cases to replay-style validation while staying laptop-safe.
- Limitation: Open-loop diagnostic only; no closed-loop Waymax/JAX claim.

### 200-Scenario Lane-Continuation Study

- Path: `docs/reports/waymo_lane_continuation_study_200.md`
- Proof type: real-data map diagnostic
- Command: `scenariolens lane-continuation-study --input ...`
- Data status: aggregate public report from local shards
- Why it matters: Scales the lane-continuation diagnosis from isolated examples to a larger real-data target set.
- Limitation: Still bounded to four local validation shards.

### 200-Scenario Continuation Replay

- Path: `docs/reports/waymo_lane_continuation_replay_prototype_200.md`
- Proof type: open-loop replay
- Command: `scenariolens lane-continuation-replay-prototype --candidate-manifest ...`
- Data status: public-safe replay summary; local trajectories ignored
- Why it matters: Checks whether continuation candidates survive bounded replay and topology probes.
- Limitation: Open-loop rollouts only, with local per-case artifacts ignored.

### 200-Scenario Terminal Selector Calibration

- Path: `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_calibration_200.md`
- Proof type: policy calibration
- Command: `scenariolens lane-continuation-terminal-neighborhood-selector-calibration ...`
- Data status: derived candidate labels and aggregate counts
- Why it matters: Makes selector promotion conservative and measurable instead of silently changing behavior.
- Limitation: The selected gate is provisional and queue-bounded.

### Terminal Selector Transfer Validation

- Path: `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_transfer_200.md`
- Proof type: transfer validation
- Command: `scenariolens lane-continuation-terminal-neighborhood-selector-transfer ...`
- Data status: derived replay labels and selector outcomes
- Why it matters: Tests whether the selector gate transfers beyond the calibration queue without false promotions.
- Limitation: The transfer queue is intentionally small and diagnostic.

### Context-Aware Selector Candidate Validation

- Path: `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_candidate_validation_200.md`
- Proof type: candidate validation
- Command: `scenariolens lane-continuation-terminal-neighborhood-selector-candidate-validation ...`
- Data status: public-safe candidate labels and rationale
- Why it matters: Shows one narrow improvement path: recover a false hold while preserving negative controls.
- Limitation: The default selector remains unchanged pending broader validation.

### Terminal Selector Decision Atlas

- Path: `docs/reports/waymo_lane_continuation_terminal_neighborhood_selector_decision_atlas_200.md`
- Proof type: visual decision atlas
- Command: `scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas ...`
- Data status: SVG decision cards plus public-safe JSON payload
- Why it matters: Turns the selector validation into visual evidence a reviewer can inspect quickly.
- Limitation: No raw Waymo trajectories or map geometry are published.

### Selector Atlas Demo Payload

- Path: `docs/demo/selector_decisions.json`
- Proof type: static data contract
- Command: `scenariolens lane-continuation-terminal-neighborhood-selector-decision-atlas --demo-json ...`
- Data status: derived public JSON, no raw trajectories
- Why it matters: Keeps the Explorer a thin presentation layer over generated, tested artifacts.
- Limitation: The payload mirrors selected public report fields only.

### Full-Corpus Run Reproducibility

- Path: `docs/reports/scenariolens_v1_run_validation.md`
- Proof type: real-data execution validation
- Command: `scenariolens run; scenariolens run-verify ...`
- Data status: aggregate digest, timing, memory, and readiness checks only
- Why it matters: Proves the one-command product path completes deterministically on the full local corpus within the declared laptop budgets.
- Limitation: The local corpus is not a Waymo benchmark and raw records remain outside git.

### CI Validation Workflow

- Path: `.github/workflows/ci.yml`
- Proof type: automation
- Command: `python -m unittest discover; scenariolens run; scenariolens run-verify`
- Data status: CI-safe fixtures only
- Why it matters: Shows the framework is maintained as software, not just a set of static reports.
- Limitation: Live Waymo shards remain local and are not required in CI.

### Public Surface Check

- Path: `docs/reports/scenariolens_public_surface_check.md`
- Proof type: readiness gate
- Command: `scenariolens public-surface-check --repo-root .`
- Data status: CI-safe repository metadata and derived public artifacts only
- Why it matters: Turns the public repo surface into a testable release gate instead of relying on manual README/demo inspection.
- Limitation: External links are counted but not fetched to keep CI deterministic.

## Public-Safety Boundary

- Raw Waymo TFRecords and per-case local replay/debug packets remain outside git.
- Public reports use aggregate counts, scenario IDs, derived SVG cards, and documented limitations.
- The selector evidence is diagnostic; the default selector remains unchanged until broader validation.
- This index verifies repository artifacts, not local raw-data availability.
