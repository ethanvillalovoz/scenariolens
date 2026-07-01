# ScenarioLens Context Replay Candidate Plan

This report turns the context eval debug casebook into a small, honest replay/debug queue. It keeps context-rich failures, signal and route/topology cases, lane-aware regressions, and fallback-stress cases visible while separating replay-ready scenarios from map-match audits. It is not a completed simulation integration or benchmark claim.

## Scope

- Source debug manifest: `data/processed/waymo_context_eval_debug_casebook/manifest.json`
- Source kind: `context_eval_set`
- Ready for planning: True
- Debug cases read: 5
- Replay candidates produced: 5
- Raw Waymo files committed: no
- Local SVG overlays and per-track debug manifests committed: no

## Queue Summary

| Metric | Count |
| --- | ---: |
| Replay-ready candidates | 2 |
| Regression-focused candidates | 1 |
| Improvement-focused candidates | 1 |
| Fallback-audit candidates | 3 |
| Local overlay artifacts present | 5 |

## Ranked Candidates

| Rank | Scenario | Case | Readiness | Priority | FDE delta | Map used | Fallbacks | Main next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `ef4c5d0e40fdea48` | Context eval seed 5 | `ready_for_regression_replay` | 15.20 | -63.578 m | 1 | 0 | Replay the scenario with constant-velocity and lane-aware rollouts from the same anchor state. |
| 2 | `7fc449ae179c29ac` | Context eval seed 2 | `ready_for_improvement_replay` | 6.09 | +1.682 m | 3 | 5 | Replay the scenario to confirm the map-conditioned advantage under the same initial state. |
| 3 | `5c8f9e7af4b0248a` | Context eval seed 1 | `needs_map_match_audit` | 3.33 | 0.000 m | 0 | 4 | Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay. |
| 4 | `479404468f0a7548` | Context eval seed 4 | `needs_map_match_audit` | 2.85 | 0.000 m | 0 | 4 | Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay. |
| 5 | `1f18831dfad32caa` | Context eval seed 3 | `needs_map_match_audit` | 2.67 | 0.000 m | 0 | 3 | Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay. |

## `ef4c5d0e40fdea48`

- Case type: Context eval seed 5
- Readiness: `ready_for_regression_replay`
- Priority score: 15.20
- Why it matters: A map-used lane-aware forecast regressed sharply, making this a high-value replay/debug target.
- Constant-velocity FDE: 46.688 m
- Lane-aware FDE: 110.266 m
- FDE delta: -63.578 m
- Worst track delta: -63.578 m
- Max lane distance: 0.038 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario with constant-velocity and lane-aware rollouts from the same anchor state.
- Visualize nearest-lane choice, lane direction, and candidate alternative lanes before changing the baseline.
- Use replay output to decide whether a route/intent prior or richer map matching is needed.

Blockers / cautions:
- No blocking issue identified from the debug manifest.

## `7fc449ae179c29ac`

- Case type: Context eval seed 2
- Readiness: `ready_for_improvement_replay`
- Priority score: 6.09
- Why it matters: A map-used lane-aware forecast improved final displacement error, making this a positive replay control.
- Constant-velocity FDE: 46.985 m
- Lane-aware FDE: 45.303 m
- FDE delta: +1.682 m
- Worst track delta: +24.030 m
- Max lane distance: 33.663 m
- Local overlay available: True

Recommended next actions:
- Replay the scenario to confirm the map-conditioned advantage under the same initial state.
- Compare final displacement and miss status against the debug casebook metrics.
- Use the result as a positive control before tuning lane-aware behavior on harder regressions.

Blockers / cautions:
- Some targets still require fallback-reason audit.
- At least one target is far from its nearest lane polyline.

## `5c8f9e7af4b0248a`

- Case type: Context eval seed 1
- Readiness: `needs_map_match_audit`
- Priority score: 3.33
- Why it matters: The case exposes map-match coverage or coordinate-frame limits before replay should be trusted.
- Constant-velocity FDE: 69.320 m
- Lane-aware FDE: 69.320 m
- FDE delta: 0.000 m
- Worst track delta: 0.000 m
- Max lane distance: 33.055 m
- Local overlay available: True

Recommended next actions:
- Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay.
- Confirm targets are eligible vehicle/cyclist tracks and are near usable lane polylines.
- Rerun baseline-debug after map matching is corrected, then reconsider replay.

Blockers / cautions:
- Lane-aware fallback was used for every evaluated target.
- No target used lane-map context in the lane-aware baseline.
- At least one target is far from its nearest lane polyline.

## `479404468f0a7548`

- Case type: Context eval seed 4
- Readiness: `needs_map_match_audit`
- Priority score: 2.85
- Why it matters: The case exposes map-match coverage or coordinate-frame limits before replay should be trusted.
- Constant-velocity FDE: 50.184 m
- Lane-aware FDE: 50.184 m
- FDE delta: 0.000 m
- Worst track delta: 0.000 m
- Max lane distance: 257.531 m
- Local overlay available: True

Recommended next actions:
- Audit map coordinate frame, nearest-lane distance, and lane-match threshold before replay.
- Confirm targets are eligible vehicle/cyclist tracks and are near usable lane polylines.
- Rerun baseline-debug after map matching is corrected, then reconsider replay.

Blockers / cautions:
- Lane-aware fallback was used for every evaluated target.
- No target used lane-map context in the lane-aware baseline.
- At least one target is far from its nearest lane polyline.

## `1f18831dfad32caa`

- Case type: Context eval seed 3
- Readiness: `needs_map_match_audit`
- Priority score: 2.67
- Why it matters: The case exposes map-match coverage or coordinate-frame limits before replay should be trusted.
- Constant-velocity FDE: 48.806 m
- Lane-aware FDE: 48.806 m
- FDE delta: 0.000 m
- Worst track delta: 0.000 m
- Max lane distance: 26.611 m
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
- Context-derived candidates should preserve their eval-set group labels during follow-up so signal, topology, regression, and fallback behavior are not collapsed into one score.
- Fallback-audit candidates should not be replayed as model evidence until map matching, coordinate frames, and target eligibility are checked.
- This is a planning artifact for the next experiment, not a completed Waymax/JAX integration.
