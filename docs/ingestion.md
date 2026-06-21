# Ingestion

ScenarioLens ingestion follows one boundary:

```text
raw or external dataset file -> ScenarioLens JSON -> report/render/rank
```

This keeps dataset-specific parsing separate from scoring, reporting, and
visualization.

## Generic CSV Tracks

Use `ingest-csv` for small external examples and hand-built fixtures.

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-csv \
  --input data/raw/example_tracks.csv \
  --output data/processed/example_scenarios.json
```

Then run the normal pipeline:

```bash
PYTHONPATH=src python3 -m scenariolens.cli report \
  --input data/processed/example_scenarios.json \
  --limit 5

PYTHONPATH=src python3 -m scenariolens.cli render \
  --input data/processed/example_scenarios.json \
  --top 3 \
  --output-dir /tmp/scenariolens-gallery
```

### CSV Columns

Required:

| Column | Meaning |
| --- | --- |
| `scenario_id` | Scenario/group identifier. |
| `agent_id` | Track identifier within a scenario. |
| `agent_type` | `vehicle`, `pedestrian`, `cyclist`, or `unknown`. |
| `t` | Timestamp or frame index. |
| `x` | Local x position in meters. |
| `y` | Local y position in meters. |

Optional:

| Column | Meaning |
| --- | --- |
| `vx` | x velocity. Defaults to `0`. |
| `vy` | y velocity. Defaults to `0`. |
| `ego_track_id` | Ego track id for visualization emphasis. |
| `tags` | `;`, `|`, or comma-separated scenario tags. |
| `source` | Source label stored in ScenarioLens JSON. |

## Waymo Motion Adapter

The Waymo Motion adapter is intentionally a planned optional adapter right now.
The command exists to document the boundary:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-status
```

The future command shape is:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --input data/raw/waymo/motion \
  --output data/processed/waymo_motion_slice.json \
  --max-scenarios 50
```

Waymo's public Open Dataset site lists Motion data and challenge tracks such as
Scenario Generation, Sim Agents, and Interaction Prediction. ScenarioLens is
being shaped around that evaluation surface while keeping the heavy dataset
parser outside the dependency-free core.

References:

- https://waymo.com/open/
- https://waymo.com/open/challenges/

