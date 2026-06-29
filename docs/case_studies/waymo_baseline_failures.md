# Case Study: Finding Baseline Motion-Prediction Failures

This case study is the recruiter-facing technical story for ScenarioLens.

## Question

Which Waymo Motion scenarios are most useful for evaluating a simple
motion-prediction baseline?

## Method

ScenarioLens loads a local Waymo Motion validation shard, extracts the fields
needed for motion analysis, evaluates a constant-velocity baseline on prediction
targets, and groups the results by scenario tags and score components.

The public report avoids raw gated data. It publishes aggregate statistics,
scenario IDs, tags, and reproducible commands.

## Current Evidence

- Real-slice failure study:
  [`docs/reports/waymo_motion_failure_study.md`](../reports/waymo_motion_failure_study.md)
- Failure distribution stability study:
  [`docs/reports/waymo_motion_failure_stability.md`](../reports/waymo_motion_failure_stability.md)
- Cross-shard failure stability study:
  [`docs/reports/waymo_motion_failure_stability_cross_shard.md`](../reports/waymo_motion_failure_stability_cross_shard.md)
- Shard expansion plan:
  [`docs/reports/waymo_motion_shard_plan.md`](../reports/waymo_motion_shard_plan.md)
- Map-match threshold audit:
  [`docs/reports/waymo_map_match_audit.md`](../reports/waymo_map_match_audit.md)

The current local evidence includes the original 75-scenario windowed study and
a true cross-shard run over four validation shards, covering 100 real scenarios
and 418 evaluated prediction targets. The cross-shard report shows mean FDE
varying from 21.20 m to 28.89 m across sampled shards, with cyclist interaction
the most variable shared tag. The follow-up map-match audit shows that simply
widening the lane-match threshold on a fallback-heavy case makes FDE worse, so
the next matcher work should focus on lane coverage, coordinate frames, heading,
and route/intent priors.

## Why It Matters

Autonomy teams need tooling that finds where average-case performance hides
long-tail weaknesses. ScenarioLens demonstrates that workflow on public-data
boundaries: ingest a slice, score the scenario, evaluate a baseline, group the
failures, and produce reviewable evidence.

## Next Step

Expand beyond shards `00007` through `00010`, improve map matching with
heading-aware lane selection and coordinate-frame checks, and graduate stable
open-loop replay candidates from
`docs/reports/waymo_open_loop_replay_prototype.md` into an optional Waymax/JAX
path.
