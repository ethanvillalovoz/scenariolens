# Framework Concepts

ScenarioLens is organized as a small evaluation framework. Each layer has a
clear data boundary so the project can grow without becoming a one-off demo.

```text
Dataset Adapter
-> Scenario Schema
-> Metrics
-> Baseline Evaluator
-> Lane-Selection Study
-> Debug Casebook
-> Replay Candidate Plan
-> Open-Loop Replay Prototype
-> Map-Match Audit
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

The default evaluator is a constant-velocity prediction baseline. It computes
ADE, FDE, max FDE, miss rate, and a failure score on prediction targets. A
second lane-aware comparison baseline uses parsed lane polylines for
vehicle/cyclist targets when map context is available, then falls back to
constant velocity for pedestrians, missing maps, low-speed tracks, or distant
lane matches. This keeps the core baseline stable while showing how map context
can reduce forecast error on curved-road cases.

## Lane-Selection Study

The lane-selection study is an ablation for improving the map baseline without
changing the default scorer. It compares the existing nearest-lane selector
against a heading-aware selector that prefers lane tangents aligned with the
target's anchor velocity. The current real-data study shows a small FDE
improvement over nearest-lane selection while still trailing constant velocity
overall, so it is evidence for matcher iteration rather than a production
prediction claim.

## Debug Casebook

The debug casebook turns a baseline comparison or lane-selection study into
selected examples: improvements, regressions, and fallback-heavy cases. Local
artifacts include SVG overlays, per-track error timelines, lane-match distance,
heading-alignment diagnostics, and fallback reasons. Public copies keep the raw
trajectories and local debug manifests out of git while preserving the
interpretation.

## Replay Candidate Plan

The replay candidate plan is the bridge from scenario mining to simulation. It
reads a debug casebook, ranks cases by replay priority, and labels each one as
ready for improvement replay, ready for regression replay, or requiring a
map-match audit first. It is a planning artifact for future Waymax/JAX work,
not a claim that replay simulation is already complete.

## Open-Loop Replay Prototype

The replay prototype is the first executable step after planning. It reloads
the replay-ready local scenarios, reruns constant-velocity and lane-aware
rollouts from the same anchor state, and applies small deterministic
anchor-velocity perturbations. The output is a public-safe stability report:
which diagnostics preserve their expected improvement/regression sign, which
are sensitive to small state changes, and which cases should remain blocked on
map matching. It is still open-loop evaluation, not closed-loop simulation.

## Map-Match Audit

The map-match audit handles cases that are not ready to be treated as replay
evidence. It reloads fallback-heavy debug examples, sweeps lane-match
thresholds, and asks a narrow engineering question: would accepting farther
lanes improve the diagnostic, or would it make the forecast less trustworthy?
The current real-data audit shows that widening the radius can worsen FDE, so
the correct follow-up is coordinate-frame, lane-coverage, and lane-selection
work before changing the default matcher.

## Reports

Reports are public-safe artifacts. They summarize aggregate metrics, tag-level
failures, score components, stability across slices, and the hardest scenario
IDs without publishing raw gated dataset records.

## Explorer

The static explorer consumes deterministic JSON and SVG assets. It is the
portfolio front door for the framework: filters, rankings, trajectory previews,
score components, baseline failures, public-safe heading-aware case diagnostics,
and links to the public reports.

## Extension Points

- Add a dataset adapter for another public motion dataset.
- Add another prediction baseline or calibrate the lane-aware matcher on more
  public data.
- Add richer map-match diagnostics for lane coverage, heading alignment, and
  route/intent priors.
- Prototype nearest-lane vs heading-aware replay for the strongest candidate
  cases.
- Add map-aware features or traffic-light summaries.
- Graduate stable replay-prototype candidates into an optional Waymax/JAX path.
- Add additional public-safe report types.
