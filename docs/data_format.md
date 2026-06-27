# Scenario JSON Format

ScenarioLens uses a small JSON format as the bridge between synthetic examples
and future dataset-derived scenarios.

## Export Example

```bash
PYTHONPATH=src python3 -m scenariolens.cli export-synthetic --output data/processed/synthetic_scenarios.json
```

## Use Exported Data

```bash
PYTHONPATH=src python3 -m scenariolens.cli report \
  --input data/processed/synthetic_scenarios.json \
  --format markdown \
  --limit 5

PYTHONPATH=src python3 -m scenariolens.cli render \
  --input data/processed/synthetic_scenarios.json \
  --top 3 \
  --output-dir /tmp/scenariolens-gallery
```

## Shape

```json
{
  "format": "scenariolens.scenarios",
  "version": 1,
  "scenarios": [
    {
      "scenario_id": "synthetic_pedestrian_crossing",
      "source": "synthetic",
      "ego_track_id": "ego",
      "tags": ["pedestrian_crossing", "close_interaction"],
      "metadata": {
        "waymo_tracks_to_predict_track_ids": ["ped_1"],
        "waymo_objects_of_interest_track_ids": ["ped_1"]
      },
      "tracks": [
        {
          "agent_id": "ego",
          "agent_type": "vehicle",
          "states": [
            {"t": 0.0, "x": 0.0, "y": 0.0, "vx": 5.0, "vy": 0.0}
          ]
        }
      ]
    }
  ]
}
```

## Notes

- `agent_type` currently supports `vehicle`, `pedestrian`, `cyclist`, and
  `unknown`.
- Coordinates are local 2D scene coordinates in meters.
- `metadata` is optional and stores dataset-specific context that should survive
  ingest, such as Waymo SDC indices, current time indices, tracks to predict, and
  objects of interest. When available, `waymo_map_features` stores simplified
  lane, road-line, road-edge, crosswalk, speed-bump, and driveway geometry for
  SVG rendering.
- The format is intentionally compact and laptop-friendly.
- Raw dataset files should remain outside git; derived JSON slices can be
  regenerated from ingestion scripts.

## Scoring Contract

Reports and dashboard payloads include both raw scene counts and the calibrated
scoring view used for ranking:

- `agent_count`: all tracks in the ScenarioLens record.
- `scoring_agent_count`: tracks that passed quality filtering and local context
  selection.
- `excluded_track_count`: tracks not used by the scorer because they were
  low-quality or outside the ego/Waymo-interest context.
- `low_quality_track_count`: tracks with too few states, non-finite values,
  impossible speeds, or invalid time ordering.
- `scoring_vulnerable_road_user_count`: pedestrians/cyclists inside the scored
  context.
- `sdc_track_present`, `prediction_target_count`, and
  `object_of_interest_count`: credibility fields preserved from Waymo-shaped
  inputs when available.
