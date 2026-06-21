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

The Waymo Motion adapter keeps raw dataset parsing separate from the rest of
ScenarioLens. The status command documents the active boundary:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-status
```

ScenarioLens supports a dependency-free native JSON path for small records that
mirror the public Waymo Motion `Scenario` proto:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format native \
  --input docs/examples/waymo_motion_native_sample.json \
  --output data/processed/waymo_motion_native_sample.json \
  --max-scenarios 50
```

The native JSON reader accepts either protobuf JSON camelCase names such as
`scenarioId`, `timestampsSeconds`, `sdcTrackIndex`, `objectType`, `centerX`,
and `velocityX`, or Python/proto-style snake_case names such as `scenario_id`,
`timestamps_seconds`, `sdc_track_index`, `object_type`, `center_x`, and
`velocity_x`.

The same `--format native` command can read `.pb` and `.tfrecord` files when
optional Waymo/TensorFlow packages are installed. Those dependencies are not
required for the core project or tests.

ScenarioLens also supports a lightweight normalized CSV shape that mirrors key
fields from a Motion extraction:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format normalized-csv \
  --input docs/examples/waymo_motion_normalized.csv \
  --output data/processed/waymo_motion_normalized.json \
  --max-scenarios 50
```

Then run the normal report/render flow:

```bash
PYTHONPATH=src python3 -m scenariolens.cli report \
  --input data/processed/waymo_motion_normalized.json \
  --limit 5
```

For a local downloaded dataset slice, keep raw files outside git and point the
native command at a file or directory:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format native \
  --input data/raw/waymo/motion \
  --output data/processed/waymo_motion_slice.json \
  --max-scenarios 50
```

### Native Waymo Motion JSON Fields

Required fields:

| Field | Meaning |
| --- | --- |
| `scenarioId` / `scenario_id` | Waymo scenario id. |
| `tracks` | Array of tracked agents. |
| `tracks[].id` | Track id. |
| `tracks[].objectType` / `tracks[].object_type` | Waymo object type enum. |
| `tracks[].states` | Object states over time. |
| `tracks[].states[].centerX` / `center_x` | Local x position in meters. |
| `tracks[].states[].centerY` / `center_y` | Local y position in meters. |

Optional fields:

| Field | Meaning |
| --- | --- |
| `timestampsSeconds` / `timestamps_seconds` | Timestamps for state indices. Defaults to frame index if missing. |
| `sdcTrackIndex` / `sdc_track_index` | Index of the self-driving-car track, mapped to `ego_track_id`. |
| `tracks[].states[].velocityX` / `velocity_x` | x velocity. Defaults to `0`. |
| `tracks[].states[].velocityY` / `velocity_y` | y velocity. Defaults to `0`. |
| `tracks[].states[].valid` | Invalid states are skipped. Defaults to valid for small JSON fixtures. |
| `objectsOfInterest` / `objects_of_interest` | Adds an explanatory `objects_of_interest` tag. |
| `tracksToPredict` / `tracks_to_predict` | Adds an explanatory `tracks_to_predict` tag. |
| `mapFeatures` / `map_features` | Adds an explanatory `map_context` tag. |
| `dynamicMapStates` / `dynamic_map_states` | Adds an explanatory `traffic_signal_context` tag. |

### Normalized Waymo Motion CSV Columns

Required:

| Column | Meaning |
| --- | --- |
| `scenario_id` | Waymo scenario id or derived scenario id. |
| `track_id` | Waymo track id or stable extracted object id. |
| `object_type` | `TYPE_VEHICLE`, `TYPE_PEDESTRIAN`, `TYPE_CYCLIST`, or other mapped type. |
| `timestep` | Waymo timestep/frame index or timestamp. |
| `center_x` | Local x position in meters. |
| `center_y` | Local y position in meters. |

Optional:

| Column | Meaning |
| --- | --- |
| `velocity_x` | x velocity. Defaults to `0`. |
| `velocity_y` | y velocity. Defaults to `0`. |
| `is_sdc` | `true`/`1` marks the self-driving-car track as ego. |
| `ego_track_id` | Explicit ego track id. Overrides `is_sdc` inference. |
| `tags` | `;`, `|`, or comma-separated ScenarioLens tags. |
| `source` | Source label stored in ScenarioLens JSON. |

Waymo's public Open Dataset site lists Motion data and challenge tracks such as
Scenario Generation, Sim Agents, and Interaction Prediction. ScenarioLens is
being shaped around that evaluation surface while keeping the heavy dataset
parser outside the dependency-free core.

References:

- https://waymo.com/open/
- https://waymo.com/open/challenges/
- https://github.com/waymo-research/waymo-open-dataset/blob/master/src/waymo_open_dataset/protos/scenario.proto
