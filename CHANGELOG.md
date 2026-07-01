# Changelog

All notable changes to ScenarioLens are documented here.

## [Unreleased]

### Added

- Baseline ablation CLI/report comparing constant velocity, default lane-aware,
  and strict lane-aware variants without gated Waymo downloads.
- `scenariolens baseline-compare-study` for repeated Waymo Motion or
  ScenarioLens JSON inputs, with public-safe manifest/report outputs.
- 100-scenario real Waymo lane-aware baseline diagnostic across four local
  validation shards, including top improvements, top regressions, map-used
  counts, and fallback reasons.
- `scenariolens baseline-debug` casebook workflow that selects improvement,
  regression, and fallback-heavy cases from a comparison study, writes local SVG
  overlays, and publishes a public-safe summary.
- `scenariolens replay-candidates` workflow that converts a baseline-debug
  manifest into a public-safe Waymax/JAX replay candidate queue.
- `scenariolens replay-prototype` workflow that reloads replay-ready local
  scenarios, reruns open-loop baseline rollouts, and applies deterministic
  anchor-velocity perturbations before publishing a public-safe stability
  report.
- `scenariolens map-match-audit` workflow that reloads fallback-heavy debug
  cases, sweeps lane-match thresholds, and publishes a public-safe diagnostic
  before changing matcher behavior.
- `scenariolens lane-selection-study` workflow and heading-aware lane-selection
  baseline variant comparing nearest-lane and heading-aware map matching across
  the 100-scenario local Waymo slice.
- Lane-aware fallback reason summaries in Markdown/JSON reports and the static
  Scenario Explorer dashboard payload.
- Short animated demo GIF for the README public surface.

## [0.2.0] - 2026-06-28

### Added

- Product-quality public README surface with live demo, evidence links, and
  quick-start workflows.
- Contributor, citation, release, and issue/PR metadata for an open-source
  baseline release.
- Scenario Explorer evidence band and baseline-failure summary card.
- CLI workflow documentation and framework concepts guide.
- Lane-aware prediction baseline comparison using parsed lane polylines when
  map context is available.
- `scenariolens baseline-compare` Markdown/JSON reports, a curved-lane fixture,
  dashboard comparison metrics, and the checked-in lane-aware study report.

### Deferred

- True cross-shard Waymo Motion failure stability report after authenticated
  shard downloads are available.
- Small Waymax/JAX replay or perturbation path for selected high-value
  scenarios.

## [0.1.0] - 2026-06-28

### Added

- Scenario schema, synthetic corpus, CSV ingestion, Waymo Motion-shaped JSON/CSV
  ingestion, and lightweight native Motion TFRecord/proto reader.
- Interpretable scenario ranking metrics for VRUs, proximity, TTC proxy, path
  conflict, density, dynamics, and taxonomy.
- Constant-velocity prediction baseline with ADE/FDE, miss rate, and failure
  score.
- Public-safe real-slice failure and stability studies.
- Static Scenario Explorer with deterministic dashboard JSON and SVG assets.
- GitHub Actions CI for unit tests and static JavaScript syntax checks.
