# ScenarioLens Route/Intent Audit

This report follows the stable context replay regression one step deeper. It reloads replayed local scenarios, compares constant-velocity, nearest-lane, and heading-aware open-loop rollouts, and asks whether the lane-aware failure looks like route/intent ambiguity rather than a simple threshold issue.

It is intentionally scoped: this is not a route planner, not a matcher change, not closed-loop simulation, and not a Waymo benchmark claim. Raw Waymo files and local per-case packets stay out of git.

## Scope

- Replay manifest: `data/processed/waymo_context_replay_prototype/manifest.json`
- Source kind: `context_eval_set`
- Ready for audit: True
- Cases audited: 1
- Default lane-match threshold: 3.500 m
- Raw Waymo files committed: no
- Local route/intent packets committed: no

## Audit Summary

| Metric | Value |
| --- | ---: |
| Audited cases | 1 |
| Audited tracks | 1 |
| Stable replay regression cases | 1 |
| Nearest-lane regression tracks | 1 |
| Heading-fix candidate tracks | 0 |
| Route/intent diagnostic tracks | 0 |
| Lane-continuity risk tracks | 1 |

## Case Summary

| Rank | Scenario | Case | Tracks | CV FDE | Nearest FDE | Heading FDE | Worst delta | Main diagnosis |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `ef4c5d0e40fdea48` | Context eval seed 5 | 1 | 46.688 m | 110.266 m | 110.266 m | -63.578 m | `lane_continuity_or_route_link_needed` |

## `ef4c5d0e40fdea48`

- Case: Context eval seed 5
- Source: `validation.tfrecord-00008-of-00150`
- Replay stability: `stable_regression_warning`
- Primary diagnosis: **lane_continuity_or_route_link_needed**
- Why: The target would run beyond the selected lane polyline during the forecast horizon.
- Recommended next action: Inspect lane continuation links before trusting a lane-following rollout.
- Scenario route links: 634 (entry 152, exit 143, neighbors 339)
- Local audit packet: `data/processed/waymo_context_route_intent_audit/cases/1-context-eval-seed-5-ef4c5d0e40fdea48/route_intent_audit.json`

Track diagnostics:

| Track | CV FDE | Nearest FDE | Heading FDE | Nearest delta | Heading vs nearest | Lane dist | Future dist to lane | Future-lane align | Route hints | Diagnosis |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `755` | 46.688 m | 110.266 m | 110.266 m | -63.578 m | 0.000 m | 0.038 m | 110.266 m | 1.000 | 7 | `lane_continuity_or_route_link_needed` |

Case metrics:

- Constant-velocity FDE: 46.688 m
- Nearest-lane FDE: 110.266 m
- Heading-aware FDE: 110.266 m
- Stable replay sign: True

## Interpretation

- A stable replay regression means the warning persisted under small anchor-state perturbations; it does not prove the map baseline is generally bad.
- If heading-aware selection fixes the nearest-lane regression, lane selection should be improved before heavier simulation work.
- If both nearest-lane and heading-aware rollouts fail while route/topology hints exist, the likely next step is route or intent conditioning rather than a wider lane-match radius.
- Lane-continuity and curvature warnings identify cases where following the selected lane centerline through the horizon can diverge from the target's actual future motion.
- This audit keeps the public artifact honest: it explains a replayed failure mode without changing the default scoring baseline.
