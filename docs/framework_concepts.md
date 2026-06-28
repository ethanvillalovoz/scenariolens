# Framework Concepts

ScenarioLens is organized as a small evaluation framework. Each layer has a
clear data boundary so the project can grow without becoming a one-off demo.

```text
Dataset Adapter
-> Scenario Schema
-> Metrics
-> Baseline Evaluator
-> Reports
-> Explorer
```

## Dataset Adapter

Adapters convert raw or fixture data into the ScenarioLens schema. Current
inputs include synthetic scenarios, row-wise CSV, Waymo Motion-shaped JSON/CSV,
binary Scenario protos, and small Motion TFRecord shards.

## Scenario Schema

The schema is intentionally compact: scenario metadata, agent tracks, typed
states, tags, and evaluation metadata such as Waymo prediction targets. This is
the stable boundary between ingestion, metrics, reports, and the dashboard.

## Metrics

Metrics are interpretable by design: vulnerable road users, density, proximity,
path conflict, screened TTC, dynamics, taxonomy tags, and baseline failure
evidence. ScenarioLens ranks scenarios by review value, not by a certified
safety score.

## Baseline Evaluator

The current evaluator is a constant-velocity prediction baseline. It computes
ADE, FDE, max FDE, miss rate, and a failure score on prediction targets. This is
simple on purpose: the baseline creates a measurable reference point for future
lane-aware or simulation-backed comparisons.

## Reports

Reports are public-safe artifacts. They summarize aggregate metrics, tag-level
failures, score components, stability across slices, and the hardest scenario
IDs without publishing raw gated dataset records.

## Explorer

The static explorer consumes deterministic JSON and SVG assets. It is the
portfolio front door for the framework: filters, rankings, trajectory previews,
score components, baseline failures, and links to the public reports.

## Extension Points

- Add a dataset adapter for another public motion dataset.
- Add a stronger prediction baseline.
- Add map-aware features or traffic-light summaries.
- Add a Waymax/JAX replay path for selected hard scenarios.
- Add additional public-safe report types.
