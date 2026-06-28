# ScenarioLens Project Brief

## One-Line Pitch

ScenarioLens is a local-first autonomy evaluation tool that mines motion
scenarios for rare, interactive, and safety-relevant cases, then ranks them into
candidate evaluation sets for prediction, planning, simulation, safety review,
and ODD expansion, with baseline ADE/FDE evidence showing where simple motion
forecasts fail.

## Why This Is the Right Project

Waymo publicly emphasizes large and diverse autonomous-driving datasets, and the
Waymo Open Dataset challenge history includes tracks for interaction prediction,
sim agents, scenario generation, and vision-based end-to-end driving. That makes
scenario discovery and evaluation a strong portfolio target: it sits near the
technical core of autonomy without requiring a full robotaxi stack.

The project is also a good personal fit for Ethan's background:

- software engineering: build a reproducible data/evaluation tool,
- AI/ML: scenario retrieval, ranking, and optional embeddings,
- robotics: interaction reasoning, ODDs, prediction/planning evaluation,
- research judgment: metrics, baselines, ablations, and defensible claims.

## Primary Audience

This project should read well for:

- autonomous-driving software engineering internships,
- behavior prediction and planning internships,
- simulation/evaluation internships,
- perception internships if visual scene tags are added later,
- safety research or autonomy data roles.

## What We Are Not Building

ScenarioLens is not trying to train a complete autonomous-driving model or clone
Waymo's internal stack. The strongest signal is thoughtful evaluation tooling:
finding the scenarios that matter, explaining why they matter, and showing how
they stress a downstream prediction baseline, model, or planner.

## Core Product

The finished portfolio artifact should read like a small production evaluation
system. It should include:

- a clean GitHub repo,
- a reproducible pipeline,
- a small curated scenario corpus plus a real-data validation path,
- a scenario taxonomy,
- ranking metrics,
- public-safe reports,
- a dashboard/explorer,
- a short project write-up with results, limitations, and next work.

The current prototype already includes the reproducible pipeline, synthetic
corpus, native Waymo Motion JSON/proto/TFRecord ingestion, taxonomy,
interaction component scoring, constant-velocity baseline ADE/FDE and miss-rate
analysis, public-safe tag-level failure studies, tests, Markdown/JSON reports,
a local real-data validation packet workflow, static dashboard data, and 2D SVG
trajectory rendering with forecast overlays.

The stack is intentionally aligned with the public Waymo/autonomy ecosystem:
Python for data and evaluation tooling, Waymo Motion `Scenario`-shaped records
as the dataset boundary, a lightweight built-in reader for downloaded Motion
TFRecord slices, and JAX/Waymax as the future simulation path. See
`docs/tech_stack.md` for the detailed rationale.

See `docs/project_strategy.md` for the product strategy and
`docs/architecture.md` for the module/data-flow map.

## Representative Scenario Categories

- high-interaction merges,
- unprotected left turns,
- pedestrian crossings with occlusion,
- cyclist interactions,
- stopped or slow lead vehicles,
- blocked lane / lane change pressure,
- ambiguous right-of-way,
- dense multi-agent intersections,
- night/rain/low-visibility conditions when supported by data,
- map or traffic-light uncertainty when supported by data.

## Success Criteria

The project is successful if a recruiter or engineer can understand, in under
two minutes, that Ethan:

- understands a real autonomous-driving evaluation problem,
- can build a clean data pipeline,
- can validate against a real public dataset slice without overclaiming,
- can define meaningful metrics,
- can compare simple baseline failures across scenario types,
- can reason about long-tail autonomy risk,
- can communicate tradeoffs without overclaiming.

## Public References

- Waymo Open Dataset: https://waymo.com/open/
- Waymo Open Dataset Challenges: https://waymo.com/open/challenges/
- Waymo Research: https://waymo.com/research/
