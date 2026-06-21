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

- document ingestion boundaries and Waymo Open Dataset access steps,
- support generic CSV ingestion for small external fixtures,
- parse a small motion dataset subset,
- generate a compact feature index,
- compare synthetic and real scenario distributions,
- create 3-5 curated scenario collections.

Before downloading large data, use the renderer on the synthetic top-ranked
scenarios to keep the portfolio story visual and understandable.

## Milestone 2A: Native Waymo Motion Mini-Slice

Goal: make the real-data adapter credible without making the repo heavy.

- ingest protobuf-shaped Waymo Motion JSON records without extra dependencies,
- preserve the optional path for binary protobuf and TFRecord inputs,
- map `sdc_track_index` to ScenarioLens ego tracks,
- skip invalid states and preserve timestamps, object types, and velocities,
- add a preflight command for local downloaded slices,
- document the exact field boundary and raw-data workflow.

Status: implemented for native JSON mini-slices and optional binary hooks.
Local slice preflight and the downloaded-slice recipe are implemented. Full
downloaded-dataset validation, map geometry parsing, and traffic-light feature
extraction remain next steps.

## Milestone 3: Searchable Demo

Goal: make the project immediately understandable.

- generate a portfolio report with top-ranked scenarios and SVG assets,
- build a dashboard or lightweight web app,
- add scenario filtering and ranking views,
- visualize trajectories on a 2D map/canvas,
- show why each scenario was ranked highly.

Status: portfolio report implemented in `docs/reports/portfolio_report.md`.

## Milestone 3B: Interaction Metrics Upgrade

Goal: make ranking more interpretable and autonomy-specific.

- break final scores into named components,
- add VRU proximity and sampled path-conflict proximity,
- add max speed, ego max speed, and max deceleration features,
- expose component scores in JSON, Markdown, and portfolio reports.

Status: implemented for synthetic and normalized Waymo-shaped scenarios.

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
