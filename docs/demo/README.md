# Scenario Explorer Demo Data

This directory contains the static data contract for the future Scenario
Explorer dashboard.

Generated files:

- `scenarios.json`: ranked dashboard payload.
- `assets/*.svg`: trajectory views referenced by `scenarios.json`.

Regenerate with:

```bash
PYTHONPATH=src python3 -m scenariolens.cli dashboard-data \
  --output docs/demo/scenarios.json \
  --assets-dir docs/demo/assets
```

## Payload Shape

`scenarios.json` uses format `scenariolens.dashboard.v1` and includes:

- dataset summaries,
- available filter values,
- ranked scenarios,
- score totals and component scores,
- metrics used in ranking,
- taxonomy tags,
- explanation reasons,
- SVG asset paths,
- basic track metadata.

The payload is deterministic and does not include timestamps, so it can be
checked into git and reviewed in pull requests.
