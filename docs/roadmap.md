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

## Milestone 1A: Waymo-Aligned Stack Rationale

Goal: make the technology choices explicit and recruiter-readable.

- keep the default Python package dependency-free,
- document Waymo Motion `Scenario`-shaped records as the dataset boundary,
- explain the lightweight TFRecord/protobuf reader for local Motion slices,
- identify JAX/Waymax as the future simulation path,
- keep frontend/dashboard work secondary to the autonomy data stack.

Status: implemented in `docs/tech_stack.md`.

## Milestone 2: Small Real Data Slice

Goal: replace synthetic records with a small public dataset slice.

- document ingestion boundaries and Waymo Open Dataset access steps,
- support generic CSV ingestion for small external fixtures,
- parse a small motion dataset subset,
- generate a compact feature index,
- compare synthetic and real scenario distributions,
- create 3-5 curated scenario collections.

Status: initial downloaded Waymo Motion validation shard smoke run completed and
summarized in `docs/reports/waymo_motion_validation_summary.md` and
`docs/reports/waymo_motion_case_study.md`. Broader distribution comparison and
curated collections remain next work.

## Milestone 2A: Native Waymo Motion Mini-Slice

Goal: make the real-data adapter credible without making the repo heavy.

- ingest protobuf-shaped Waymo Motion JSON records without extra dependencies,
- read binary protobuf and TFRecord shard inputs without extra dependencies,
- map `sdc_track_index` to ScenarioLens ego tracks,
- skip invalid states and preserve timestamps, object types, and velocities,
- add a preflight command for local downloaded slices,
- document the exact field boundary and raw-data workflow.

Status: implemented for native JSON mini-slices, binary Scenario protos, and
sharded TFRecord slices. Local slice preflight, the downloaded-slice recipe, the
validation packet command, prediction-target metadata, object-of-interest
metadata, and coarse map-feature extraction are implemented. Richer
traffic-light feature extraction remains next work.

## Milestone 3: Searchable Demo

Goal: make the project immediately understandable.

- generate a portfolio report with top-ranked scenarios and SVG assets,
- generate a stable dashboard data contract,
- build a dashboard or lightweight web app,
- add scenario filtering and ranking views,
- visualize trajectories on a 2D map/canvas,
- show why each scenario was ranked highly.

Status: portfolio report implemented in `docs/reports/portfolio_report.md`.
Dashboard data contract implemented in `docs/demo/scenarios.json`. Static
Scenario Explorer UI implemented in `docs/demo/index.html`, with filtering,
sorting, trajectory previews, score components, and mobile-responsive layout.

## Milestone 3B: Interaction Metrics Upgrade

Goal: make ranking more interpretable and autonomy-specific.

- break final scores into named components,
- add VRU proximity and sampled path-conflict proximity,
- add max speed, ego max speed, and max deceleration features,
- add quality filtering and raw-vs-scored count reporting for real slices,
- expose component scores in JSON, Markdown, and portfolio reports.

Status: implemented for synthetic, Waymo-shaped fixtures, and small real Waymo
Motion validation slices.

## Milestone 3C: Dashboard Data Contract

Goal: make the future dashboard a thin presentation layer over a tested data
contract.

- combine synthetic, native Waymo-shaped JSON, and normalized Waymo-shaped CSV
  scenarios,
- export ranked scenario cards with score components, metrics, tags, reasons,
  sources, datasets, and SVG paths,
- generate matching SVG trajectory assets,
- document the static payload shape for future UI work.

Status: implemented in `docs/demo/scenarios.json` and `docs/demo/assets/`,
including baseline ADE/FDE and failure-score fields.

## Milestone 3D: Baseline Failure Mining

Goal: turn scenario ranking into measurable downstream evaluation.

- select prediction targets from Waymo Motion metadata when available,
- run a lightweight constant-velocity trajectory baseline,
- compute ADE, FDE, max FDE, miss rate, and baseline failure score,
- add baseline failure as an interpretable score component,
- render dashed forecast overlays in SVG previews,
- expose baseline metrics in Markdown/JSON reports, validation packets, and
  the Scenario Explorer.

Status: implemented for synthetic fixtures, Waymo-shaped JSON/CSV fixtures,
and local Waymo Motion validation slices. Broader real-slice distribution
analysis remains next work.

## Milestone 4: Portfolio Polish

Goal: make the repo recruiter- and engineer-readable.

- write a concise technical report,
- add screenshots/GIFs,
- add reproducible commands,
- add limitations and future work,
- prepare resume bullets and a project page.

Status: in progress. The repo has CI, a portfolio report, a local Scenario
Explorer demo, a `docs/` entrypoint ready for GitHub Pages publishing, a product
strategy, an architecture map, recruiting notes, and suggested GitHub metadata.

## Milestone 4A: Production-Grade Repo Story

Goal: make the end goal and system boundary obvious before a reviewer reads any
code.

- explain the target user and product strategy,
- document what the project is and is not claiming,
- map ingestion, scoring, reports, rendering, and dashboard modules,
- connect the live demo to data provenance and the real-data case study,
- keep the README focused on the engineering artifact.

Status: implemented in `docs/project_strategy.md`, `docs/architecture.md`, the
README, and the Scenario Explorer navigation/status panel.

## Milestone 5: Real-Slice Distribution Study

Goal: make the baseline failure analysis credible on more real data.

- select larger real-data scenario collections from downloaded validation
  shards,
- compare baseline errors by scenario tag and score component,
- report which ranked scenarios are hardest for the baseline,
- evaluate whether selected scenarios should be replayed or perturbed in
  Waymax/JAX.

Status: initial implementation complete for one local Waymo Motion validation
shard in `docs/reports/waymo_motion_failure_study.md`. Next work is to run the
same command across more shards, compare distribution stability, and use the
hardest scenario ids to motivate a stronger baseline or Waymax replay.

## Stretch Goals

- open-vocabulary scenario search,
- embedding-based retrieval,
- Waymax or sim-agent integration,
- city/ODD gap comparison for Seattle or Bellevue.
