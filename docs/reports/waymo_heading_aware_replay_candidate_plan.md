# ScenarioLens Heading-Aware Replay Candidate Plan

This report turns the heading-aware debug casebook into a small, honest candidate queue for the next replay/simulation or matcher experiment. It does not claim that ScenarioLens already performs heading-aware simulation replay. It identifies which nearest-lane vs heading-aware cases should be replayed first, why they matter, and what must be checked before treating replay results as evidence.

## Scope

- Source debug manifest: `data/processed/waymo_heading_aware_debug_casebook/manifest.json`
- Source kind: `lane_selection_study`
- Ready for planning: True
- Debug cases read: 6
- Replay candidates produced: 6
- Raw Waymo files committed: no
- Local SVG overlays and per-track debug manifests committed: no

## Queue Summary

| Metric | Count |
| --- | ---: |
| Replay-ready candidates | 5 |
| Regression-focused candidates | 1 |
| Improvement-focused candidates | 4 |
| Fallback-audit candidates | 1 |
| Local overlay artifacts present | 6 |
| Heading-aware lane-selection candidates | 6 |

## Ranked Candidates

| Rank | Scenario | Case | Readiness | Priority | Heading vs nearest | Heading vs CV | Heading map used | Heading fallbacks | Main next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `d30e6448f14e4c75` | Largest heading improvement | `ready_for_heading_improvement_replay` | 9.99 | +12.156 m | -8.934 m | 3 | 5 | Replay the scenario as a positive control for heading-aware lane selection. |
| 2 | `706fecd25045c8d` | Largest heading regression | `ready_for_heading_regression_replay` | 7.08 | -4.373 m | -3.058 m | 4 | 3 | Replay nearest-lane and heading-aware rollouts from the same anchor state. |
| 3 | `7912ee9523cb6fd` | Additional heading improvement | `ready_for_heading_improvement_replay` | 6.88 | +7.924 m | -7.270 m | 2 | 2 | Replay the scenario as a positive control for heading-aware lane selection. |
| 4 | `e3f6a29b59e42c1` | Additional heading improvement | `ready_for_heading_improvement_replay` | 6.74 | +5.008 m | +1.308 m | 4 | 1 | Replay the scenario as a positive control for heading-aware lane selection. |
| 5 | `46c1c1fbe5ef29d1` | Additional heading improvement | `ready_for_heading_improvement_replay` | 6.53 | +5.488 m | -15.482 m | 3 | 3 | Replay the scenario as a positive control for heading-aware lane selection. |
| 6 | `2f035a284480e981` | Heading fallback-heavy case | `needs_heading_map_match_audit` | 3.00 | 0.000 m | 0.000 m | 0 | 8 | Audit heading alignment, lane distance, lane direction, and coordinate frame before replay. |

## `d30e6448f14e4c75`

- Case type: Largest heading improvement
- Readiness: `ready_for_heading_improvement_replay`
- Priority score: 9.99
- Why it matters: A heading-aware lane choice improved over nearest-lane selection, making this a positive replay control for heading alignment.
- Constant-velocity FDE: 27.509 m
- Nearest-lane FDE: 48.599 m
- Heading-aware FDE: 36.443 m
- Heading improvement vs nearest-lane: +12.156 m
- Heading improvement vs constant velocity: -8.934 m
- Worst track heading delta: +49.114 m
- Max lane distance: 24.345 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario as a positive control for heading-aware lane selection.
- Compare nearest-lane and heading-aware final displacement under the same anchor state.
- Use the result to confirm the selector helps for the right reason before tuning harder regressions.

Blockers / cautions:
- Some targets still require fallback-reason audit.

## `706fecd25045c8d`

- Case type: Largest heading regression
- Readiness: `ready_for_heading_regression_replay`
- Priority score: 7.08
- Why it matters: A heading-aware lane choice regressed against nearest-lane selection, making this a high-value selector replay/debug target.
- Constant-velocity FDE: 32.547 m
- Nearest-lane FDE: 31.232 m
- Heading-aware FDE: 35.605 m
- Heading improvement vs nearest-lane: -4.373 m
- Heading improvement vs constant velocity: -3.058 m
- Worst track heading delta: -30.608 m
- Max lane distance: 6.124 m
- Local overlay available: True

Recommended next actions:
- Replay nearest-lane and heading-aware rollouts from the same anchor state.
- Visualize selected lane direction, target heading, and nearby alternative lanes before changing thresholds.
- Use replay output to decide whether route, intent, or lane-direction priors are needed.

Blockers / cautions:
- Some targets still require fallback-reason audit.

## `7912ee9523cb6fd`

- Case type: Additional heading improvement
- Readiness: `ready_for_heading_improvement_replay`
- Priority score: 6.88
- Why it matters: A heading-aware lane choice improved over nearest-lane selection, making this a positive replay control for heading alignment.
- Constant-velocity FDE: 26.353 m
- Nearest-lane FDE: 41.547 m
- Heading-aware FDE: 33.623 m
- Heading improvement vs nearest-lane: +7.924 m
- Heading improvement vs constant velocity: -7.270 m
- Worst track heading delta: +31.699 m
- Max lane distance: 3.764 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario as a positive control for heading-aware lane selection.
- Compare nearest-lane and heading-aware final displacement under the same anchor state.
- Use the result to confirm the selector helps for the right reason before tuning harder regressions.

Blockers / cautions:
- Some targets still require fallback-reason audit.

## `e3f6a29b59e42c1`

- Case type: Additional heading improvement
- Readiness: `ready_for_heading_improvement_replay`
- Priority score: 6.74
- Why it matters: A heading-aware lane choice improved over nearest-lane selection, making this a positive replay control for heading alignment.
- Constant-velocity FDE: 50.124 m
- Nearest-lane FDE: 53.824 m
- Heading-aware FDE: 48.816 m
- Heading improvement vs nearest-lane: +5.008 m
- Heading improvement vs constant velocity: +1.308 m
- Worst track heading delta: +25.038 m
- Max lane distance: 5.394 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario as a positive control for heading-aware lane selection.
- Compare nearest-lane and heading-aware final displacement under the same anchor state.
- Use the result to confirm the selector helps for the right reason before tuning harder regressions.

Blockers / cautions:
- Some targets still require fallback-reason audit.

## `46c1c1fbe5ef29d1`

- Case type: Additional heading improvement
- Readiness: `ready_for_heading_improvement_replay`
- Priority score: 6.53
- Why it matters: A heading-aware lane choice improved over nearest-lane selection, making this a positive replay control for heading alignment.
- Constant-velocity FDE: 20.759 m
- Nearest-lane FDE: 41.729 m
- Heading-aware FDE: 36.241 m
- Heading improvement vs nearest-lane: +5.488 m
- Heading improvement vs constant velocity: -15.482 m
- Worst track heading delta: +17.229 m
- Max lane distance: 6.386 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario as a positive control for heading-aware lane selection.
- Compare nearest-lane and heading-aware final displacement under the same anchor state.
- Use the result to confirm the selector helps for the right reason before tuning harder regressions.

Blockers / cautions:
- Some targets still require fallback-reason audit.

## `2f035a284480e981`

- Case type: Heading fallback-heavy case
- Readiness: `needs_heading_map_match_audit`
- Priority score: 3.00
- Why it matters: The case exposes heading-aware map-match coverage, alignment, or coordinate-frame limits before replay should be trusted.
- Constant-velocity FDE: 31.995 m
- Nearest-lane FDE: 31.995 m
- Heading-aware FDE: 31.995 m
- Heading improvement vs nearest-lane: 0.000 m
- Heading improvement vs constant velocity: 0.000 m
- Worst track heading delta: 0.000 m
- Max lane distance: 138.703 m
- Local overlay available: True

Recommended next actions:
- Audit heading alignment, lane distance, lane direction, and coordinate frame before replay.
- Confirm vehicle/cyclist targets are near usable lane polylines with valid anchor velocity.
- Rerun heading-aware baseline-debug after map matching is corrected, then reconsider replay.

Blockers / cautions:
- Heading-aware fallback was used for every evaluated target.
- No target used heading-aware lane-map context in the selector.
- At least one target is far from its nearest lane polyline.

## Interpretation

- Heading-improvement candidates test whether heading-aware lane selection preserves its nearest-lane advantage under replay.
- Heading-regression candidates are high-value debugging targets because they expose heading alignment, lane direction, route, or intent assumptions.
- Fallback-audit candidates should not be replayed as model evidence until map matching, coordinate frames, target eligibility, and heading thresholds are checked.
- This is a planning artifact for the next experiment, not a completed Waymax/JAX integration.
