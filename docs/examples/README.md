# Example Scenario Gallery

This directory contains small generated artifacts for quickly understanding what
ScenarioLens produces before connecting to real autonomous-driving data.

The top-ranked SVG gallery was generated with:

```bash
PYTHONPATH=src python3 -m scenariolens.cli render --top 3 --output-dir docs/examples/top_scenarios
```

The broader generated portfolio report lives at
[`docs/reports/portfolio_report.md`](../reports/portfolio_report.md).

## Included Scenarios

- `synthetic_dense_intersection_vru`: dense multi-agent intersection with both
  pedestrian and cyclist interaction.
- `synthetic_occluded_pedestrian`: pedestrian crossing from behind a stopped
  vehicle-like obstruction.
- `synthetic_unprotected_left_turn`: left-turn interaction with oncoming traffic
  and a pedestrian.
- `waymo_motion_normalized.csv`: tiny Waymo Motion-shaped normalized fixture
  for exercising the planned Waymo adapter path without downloading raw data.

These artifacts are intentionally tiny and synthetic. They exist to make the
evaluation pipeline visible in the GitHub repository while the project remains
lightweight and laptop-friendly.
