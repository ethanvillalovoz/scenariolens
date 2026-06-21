# Roadmap

## Milestone 1: Local Scenario Core

Goal: a complete local prototype with synthetic scenarios.

- define scenario schema,
- implement interaction/risk metrics,
- implement scenario tags,
- rank scenarios by evaluation value,
- add unit tests,
- export a Markdown or JSON report,
- render scenarios as dependency-free SVG trajectory views.

Status: implemented for the first synthetic corpus. ScenarioLens now includes
taxonomy scoring, ranked Markdown/JSON reports, and dependency-free SVG
trajectory rendering. Scenario JSON export/load and GitHub Actions CI are now
part of the bridge toward real data.

## Milestone 2: Small Real Data Slice

Goal: replace synthetic records with a small public dataset slice.

- document Waymo Open Dataset access steps,
- parse a small motion dataset subset,
- generate a compact feature index,
- compare synthetic and real scenario distributions,
- create 3-5 curated scenario collections.

Before downloading large data, use the renderer on the synthetic top-ranked
scenarios to keep the portfolio story visual and understandable.

## Milestone 3: Searchable Demo

Goal: make the project immediately understandable.

- build a dashboard or lightweight web app,
- add scenario filtering and ranking views,
- visualize trajectories on a 2D map/canvas,
- show why each scenario was ranked highly.

## Milestone 4: Portfolio Polish

Goal: make the repo recruiter- and engineer-readable.

- write a concise technical report,
- add screenshots/GIFs,
- add reproducible commands,
- add limitations and future work,
- prepare resume bullets and a project page.

## Stretch Goals

- open-vocabulary scenario search,
- embedding-based retrieval,
- Waymax or sim-agent integration,
- baseline trajectory-prediction evaluation,
- city/ODD gap comparison for Seattle or Bellevue.
