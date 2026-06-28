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
- Shard expansion plan:
  [`docs/reports/waymo_motion_shard_plan.md`](../reports/waymo_motion_shard_plan.md)

The current local run covers 75 real scenarios and 309 evaluated prediction
targets across three contiguous windows. It shows that overall mean FDE is
fairly stable across the local windows, while tags such as cyclist interaction
and objects of interest vary more.

## Why It Matters

Autonomy teams need tooling that finds where average-case performance hides
long-tail weaknesses. ScenarioLens demonstrates that workflow on public-data
boundaries: ingest a slice, score the scenario, evaluate a baseline, group the
failures, and produce reviewable evidence.

## Next Step

After authenticated Waymo access is available, download shards `00008`,
`00009`, and `00010`, then rerun the stability workflow as a true cross-shard
study.
