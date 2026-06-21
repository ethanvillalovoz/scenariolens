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
- The format is intentionally compact and laptop-friendly.
- Raw dataset files should remain outside git; derived JSON slices can be
  regenerated from ingestion scripts.

