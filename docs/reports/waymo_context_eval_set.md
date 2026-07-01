# ScenarioLens Context Evaluation Set

This report turns the context-joined failure study into a reusable, public-safe evaluation set. The goal is to make the next experiment obvious: which scenario IDs should be kept together, what context must be preserved, and what would count as a useful follow-up check.

It is not an official Waymo benchmark and does not include raw Waymo scenario data.

## Scope

- Source manifest: `data/processed/waymo_context_failure_study_cross_shard/manifest.json`
- Source format: `scenariolens.context_failure_study.v1`
- Source scenarios analyzed: 100
- Source prediction targets: 418
- Ready for eval-set use: True
- Eval groups: 5
- Unique scenario IDs: 14
- Raw scenario data committed: no
- Public artifact contains scenario IDs, group labels, metrics, and checks only

## Summary

| Metric | Value |
| --- | ---: |
| Group memberships | 25 |
| Unique scenarios | 14 |
| Signal-focused cases | 5 |
| Route/topology cases | 5 |
| Lane-regression cases | 5 |
| Fallback-stress cases | 5 |
| Mean priority score | 8.545 |

## Eval Groups

| Group | Cases | Unique scenarios | Purpose | Next experiment |
| --- | ---: | ---: | --- | --- |
| Context-rich failures | 5 | 5 | Stress the baseline on high-FDE scenes that preserve map, signal, or route context. | Use as broad smoke cases for baseline-debug and replay triage. |
| Signal-context failures | 5 | 5 | Preserve dynamic traffic-signal evidence while checking whether simple motion baselines miss long-tail behavior. | Add signal-state features or replay these cases with signal annotations visible. |
| Route/topology failures | 5 | 5 | Focus on lane-entry, exit, neighbor, and route-link context that a naive baseline does not reason about. | Compare nearest-lane, heading-aware, and route-aware lane selection. |
| Lane-aware regressions | 5 | 5 | Expose cases where naive lane following is worse than constant velocity even though map context is present. | Run map-match and intent-prior audits before tuning lane-following behavior. |
| Fallback-stress cases | 5 | 5 | Audit scenarios where map-conditioned baselines could not use map context for one or more evaluated targets. | Separate supported targets from fallback targets before replay. |

## Deduplicated Seed Set

| Rank | Source | Scenario | Priority | Groups | CV FDE | Lane delta | Signal states | Route links | Fallbacks |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 10.947 | Context-rich failures, Signal-context failures, Route/topology failures, Fallback-stress cases | 69.320 m | 0.000 m | 338 | 110 | 4 |
| 2 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 10.578 | Fallback-stress cases | 46.985 m | +1.682 m | 1800 | 471 | 5 |
| 3 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 10.304 | Fallback-stress cases | 48.806 m | 0.000 m | 1890 | 240 | 3 |
| 4 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 9.605 | Fallback-stress cases | 50.184 m | 0.000 m | 1052 | 14 | 4 |
| 5 | `validation.tfrecord-00008-of-00150` | `ef4c5d0e40fdea48` | 9.432 | Lane-aware regressions | 46.688 m | -63.578 m | 698 | 230 | 0 |
| 6 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 9.311 | Fallback-stress cases | 27.509 m | -21.090 m | 1008 | 270 | 3 |
| 7 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 8.667 | Lane-aware regressions | 22.523 m | -42.484 m | 1359 | 388 | 1 |
| 8 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | 8.170 | Lane-aware regressions | 11.285 m | -34.386 m | 990 | 382 | 2 |
| 9 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 8.122 | Context-rich failures, Signal-context failures, Route/topology failures | 55.051 m | +14.151 m | 1440 | 364 | 0 |
| 10 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 7.892 | Context-rich failures, Signal-context failures, Route/topology failures | 63.745 m | 0.000 m | 2047 | 220 | 2 |
| 11 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 7.817 | Context-rich failures, Signal-context failures, Route/topology failures | 59.535 m | 0.000 m | 364 | 440 | 1 |
| 12 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 7.037 | Context-rich failures, Signal-context failures, Route/topology failures | 57.623 m | +6.592 m | 536 | 208 | 0 |
| 13 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | 6.317 | Lane-aware regressions | 3.152 m | -141.362 m | 249 | 245 | 0 |
| 14 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | 5.429 | Lane-aware regressions | 7.576 m | -133.532 m | 0 | 383 | 0 |

## Context-rich failures

Purpose: Stress the baseline on high-FDE scenes that preserve map, signal, or route context.

Acceptance checks:
- At least one map, signal, or route context count is nonzero.
- The case remains in the high-FDE context-failure ranking.
- Scenario ID and source shard remain stable across reruns.
- Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.
- No raw Waymo trajectory or map packet is committed.

| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 8.947 | High baseline error with map, signal, or route context. | 69.320 m | 100.0% | 0.000 m | 338 | 110 |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 7.892 | High baseline error with map, signal, or route context. | 63.745 m | 100.0% | 0.000 m | 2047 | 220 |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 7.817 | High baseline error with map, signal, or route context. | 59.535 m | 100.0% | 0.000 m | 364 | 440 |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 7.037 | High baseline error with map, signal, or route context. | 57.623 m | 100.0% | +6.592 m | 536 | 208 |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 8.122 | High baseline error with map, signal, or route context. | 55.051 m | 100.0% | +14.151 m | 1440 | 364 |

## Signal-context failures

Purpose: Preserve dynamic traffic-signal evidence while checking whether simple motion baselines miss long-tail behavior.

Acceptance checks:
- Traffic-signal lane-state counts are present in the context manifest.
- Stop/go/unknown signal buckets remain visible in the public report.
- Scenario ID and source shard remain stable across reruns.
- Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.
- No raw Waymo trajectory or map packet is committed.

| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 8.947 | High baseline error with parsed traffic-signal state context. | 69.320 m | 100.0% | 0.000 m | 338 | 110 |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 7.892 | High baseline error with parsed traffic-signal state context. | 63.745 m | 100.0% | 0.000 m | 2047 | 220 |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 7.817 | High baseline error with parsed traffic-signal state context. | 59.535 m | 100.0% | 0.000 m | 364 | 440 |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 7.037 | High baseline error with parsed traffic-signal state context. | 57.623 m | 100.0% | +6.592 m | 536 | 208 |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 8.122 | High baseline error with parsed traffic-signal state context. | 55.051 m | 100.0% | +14.151 m | 1440 | 364 |

## Route/topology failures

Purpose: Focus on lane-entry, exit, neighbor, and route-link context that a naive baseline does not reason about.

Acceptance checks:
- Route, entry, exit, or neighbor link counts are present.
- Lane-topology context is preserved before comparing map-aware baselines.
- Scenario ID and source shard remain stable across reruns.
- Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.
- No raw Waymo trajectory or map packet is committed.

| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 8.947 | High baseline error with lane topology or route-link context. | 69.320 m | 100.0% | 0.000 m | 338 | 110 |
| 2 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 7.892 | High baseline error with lane topology or route-link context. | 63.745 m | 100.0% | 0.000 m | 2047 | 220 |
| 3 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 7.817 | High baseline error with lane topology or route-link context. | 59.535 m | 100.0% | 0.000 m | 364 | 440 |
| 4 | `validation.tfrecord-00008-of-00150` | `68e353cdd0fb176b` | 7.037 | High baseline error with lane topology or route-link context. | 57.623 m | 100.0% | +6.592 m | 536 | 208 |
| 5 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 8.122 | High baseline error with lane topology or route-link context. | 55.051 m | 100.0% | +14.151 m | 1440 | 364 |

## Lane-aware regressions

Purpose: Expose cases where naive lane following is worse than constant velocity even though map context is present.

Acceptance checks:
- The lane-aware FDE delta remains negative or is explicitly explained.
- Map-used and fallback counts are reported with the regression.
- Scenario ID and source shard remain stable across reruns.
- Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.
- No raw Waymo trajectory or map packet is committed.

| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00009-of-00150` | `fc8c647623f81bb4` | 6.317 | Lane-aware baseline regressed despite context being available. | 3.152 m | 100.0% | -141.362 m | 249 | 245 |
| 2 | `validation.tfrecord-00007-of-00150` | `2f366a31ab03f8b` | 5.429 | Lane-aware baseline regressed despite context being available. | 7.576 m | 100.0% | -133.532 m | 0 | 383 |
| 3 | `validation.tfrecord-00008-of-00150` | `ef4c5d0e40fdea48` | 9.432 | Lane-aware baseline regressed despite context being available. | 46.688 m | 100.0% | -63.578 m | 698 | 230 |
| 4 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 8.667 | Lane-aware baseline regressed despite context being available. | 22.523 m | 100.0% | -42.484 m | 1359 | 388 |
| 5 | `validation.tfrecord-00007-of-00150` | `77c44d1768793143` | 8.170 | Lane-aware baseline regressed despite context being available. | 11.285 m | 87.5% | -34.386 m | 990 | 382 |

## Fallback-stress cases

Purpose: Audit scenarios where map-conditioned baselines could not use map context for one or more evaluated targets.

Acceptance checks:
- Fallback count is nonzero and kept separate from map-used targets.
- Replay follow-up does not treat fallback targets as map-conditioned evidence.
- Scenario ID and source shard remain stable across reruns.
- Constant-velocity FDE and miss-rate metrics are regenerated, not hand-edited.
- No raw Waymo trajectory or map packet is committed.

| Rank | Source | Scenario | Priority | Reason | CV FDE | CV miss | Lane delta | Signal states | Route links |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 10.578 | One or more evaluated targets required lane-aware fallback. | 46.985 m | 100.0% | +1.682 m | 1800 | 471 |
| 2 | `validation.tfrecord-00007-of-00150` | `5c8f9e7af4b0248a` | 10.947 | One or more evaluated targets required lane-aware fallback. | 69.320 m | 100.0% | 0.000 m | 338 | 110 |
| 3 | `validation.tfrecord-00008-of-00150` | `479404468f0a7548` | 9.605 | One or more evaluated targets required lane-aware fallback. | 50.184 m | 100.0% | 0.000 m | 1052 | 14 |
| 4 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 10.304 | One or more evaluated targets required lane-aware fallback. | 48.806 m | 100.0% | 0.000 m | 1890 | 240 |
| 5 | `validation.tfrecord-00010-of-00150` | `d30e6448f14e4c75` | 9.311 | One or more evaluated targets required lane-aware fallback. | 27.509 m | 100.0% | -21.090 m | 1008 | 270 |

## How To Use This

- Treat this as a deterministic candidate set for the next ScenarioLens experiment, not as a benchmark leaderboard.
- Keep scenario IDs grouped by their selection reason so improvements do not hide regressions in signal, route, or fallback-heavy cases.
- For local debugging, feed selected source files and scenario IDs into `scenariolens baseline-debug`, then rerun replay-candidate and open-loop replay reports.
- Regenerate this eval set whenever the context-failure study inputs or selection thresholds change.
