# ScenarioLens Replay Candidate Plan

This report turns the baseline-debug casebook into a small, honest candidate queue for the next Waymax/JAX replay experiment. It does not claim that ScenarioLens already performs simulation replay. It identifies which cases should be replayed first, why they matter, and what must be checked before treating replay results as evidence.

## Scope

- Source debug manifest: `data/processed/waymo_lane_aware_debug_casebook/manifest.json`
- Ready for planning: True
- Debug cases read: 3
- Replay candidates produced: 3
- Raw Waymo files committed: no
- Local SVG overlays and per-track debug manifests committed: no

## Queue Summary

| Metric | Count |
| --- | ---: |
| Replay-ready candidates | 2 |
| Regression-focused candidates | 1 |
| Improvement-focused candidates | 1 |
| Fallback-audit candidates | 1 |
| Local overlay artifacts present | 3 |

## Ranked Candidates

| Rank | Scenario | Case | Readiness | Priority | FDE delta | Map used | Fallbacks | Main next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `fc8c647623f81bb4` | Largest regression | `ready_for_regression_replay` | 15.50 | -141.362 m | 1 | 0 | Replay the scenario with constant-velocity and lane-aware rollouts from the same anchor state. |
| 2 | `b2b7c2ad7bcd134b` | Largest improvement | `ready_for_improvement_replay` | 6.98 | +14.151 m | 3 | 0 | Replay the scenario to confirm the map-conditioned advantage under the same initial state. |
| 3 | `2f035a284480e981` | Fallback-heavy case | `needs_map_match_audit` | 3.00 | 0.000 m | 0 | 8 | Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay. |

## `fc8c647623f81bb4`

- Case type: Largest regression
- Readiness: `ready_for_regression_replay`
- Priority score: 15.50
- Why it matters: A map-used lane-aware forecast regressed sharply, making this a high-value replay/debug target.
- Constant-velocity FDE: 3.152 m
- Lane-aware FDE: 144.514 m
- FDE delta: -141.362 m
- Worst track delta: -141.362 m
- Max lane distance: 0.031 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario with constant-velocity and lane-aware rollouts from the same anchor state.
- Visualize nearest-lane choice, lane direction, and candidate alternative lanes before changing the baseline.
- Use replay output to decide whether a route/intent prior or richer map matching is needed.

Blockers / cautions:
- No blocking issue identified from the debug manifest.

## `b2b7c2ad7bcd134b`

- Case type: Largest improvement
- Readiness: `ready_for_improvement_replay`
- Priority score: 6.98
- Why it matters: A map-used lane-aware forecast improved final displacement error, making this a positive replay control.
- Constant-velocity FDE: 55.051 m
- Lane-aware FDE: 40.900 m
- FDE delta: +14.151 m
- Worst track delta: +27.974 m
- Max lane distance: 0.815 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario to confirm the map-conditioned advantage under the same initial state.
- Compare final displacement and miss status against the debug casebook metrics.
- Use the result as a positive control before tuning lane-aware behavior on harder regressions.

Blockers / cautions:
- No blocking issue identified from the debug manifest.

## `2f035a284480e981`

- Case type: Fallback-heavy case
- Readiness: `needs_map_match_audit`
- Priority score: 3.00
- Why it matters: The case exposes map-match coverage or coordinate-frame limits before replay should be trusted.
- Constant-velocity FDE: 31.995 m
- Lane-aware FDE: 31.995 m
- FDE delta: 0.000 m
- Worst track delta: 0.000 m
- Max lane distance: 138.703 m
- Local overlay available: True

Recommended next actions:
- Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay.
- Confirm targets are eligible vehicle/cyclist tracks and are near usable lane polylines.
- Rerun baseline-debug after map matching is corrected, then reconsider replay.

Blockers / cautions:
- Lane-aware fallback was used for every evaluated target.
- No target used lane-map context in the lane-aware baseline.
- At least one target is far from its nearest lane polyline.

## Interpretation

- Improvement candidates test whether map-conditioned rollouts preserve the observed lane-aware advantage under replay.
- Regression candidates are higher-value debugging targets because they expose lane choice, direction, route, or intent assumptions.
- Fallback-audit candidates should not be replayed as model evidence until map matching, coordinate frames, and target eligibility are checked.
- This is a planning artifact for the next experiment, not a completed Waymax/JAX integration.
