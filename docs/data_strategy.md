# Data Strategy

## Phase 0: Synthetic Scenarios

Begin with small synthetic scenario records. This lets us validate schema,
metrics, ranking logic, tests, and reporting without waiting on large downloads
or dataset access.

The synthetic corpus can now be exported to ScenarioLens JSON:

```bash
PYTHONPATH=src python3 -m scenariolens.cli export-synthetic --output data/processed/synthetic_scenarios.json
```

## Phase 1: Curated Public Data Slice

Move to a small subset of public autonomous-driving data. The most relevant
target is the Waymo Open Dataset, especially motion/scenario data because it is
directly connected to interaction prediction, sim agents, and scenario
generation.

Before adding Waymo-specific parsing, ScenarioLens supports a generic row-wise
CSV track importer. This keeps the ingestion boundary testable with tiny files:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-csv \
  --input data/raw/example_tracks.csv \
  --output data/processed/example_scenarios.json
```

The repo also includes a tiny Waymo Motion-shaped normalized fixture:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format normalized-csv \
  --input docs/examples/waymo_motion_normalized.csv \
  --output data/processed/waymo_motion_normalized.json
```

The repo should support a `data/raw/` drop-in workflow:

```text
data/raw/
  waymo/
    motion/
      training/
      validation/
```

Raw files stay untracked.

## Phase 2: Scenario Feature Index

Convert raw records into compact rows such as:

- scenario id,
- city/domain metadata when available,
- number of vehicles,
- number of pedestrians/cyclists,
- minimum distance between agents,
- minimum time-to-collision proxy,
- ego speed and acceleration summaries,
- map/traffic-light features when available,
- derived scenario tags,
- ranking score.

Store derived outputs under `data/processed/`.

## Phase 3: Search And Retrieval

Once the structured index works, add retrieval:

- filter by scenario tags,
- text search over generated descriptions,
- optional embedding search,
- optional visual retrieval if a small perception slice is added.

## Phase 4: Evaluation Sets

The final artifact should export small scenario sets for downstream use:

- `pedestrian_occlusion_top_50`,
- `high_interaction_merge_top_50`,
- `cyclist_close_pass_top_50`,
- `unprotected_turn_conflict_top_50`,
- `low_visibility_when_available`.

Each set should include the ranking rationale and summary statistics.
