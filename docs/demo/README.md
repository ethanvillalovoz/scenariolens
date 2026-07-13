# Scenario Explorer Demo

This directory contains the static ScenarioLens Explorer and the checked-in
public payloads used by GitHub Pages and the portfolio route.

Run it locally:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000/demo/`.

The public demo joins two deliberately separate evidence layers:

- `run.json` contains aggregate metrics from two reproducible 1,193-scenario
  local runs over four Waymo Motion validation shards.
- `scenarios.json` contains 14 checked-in synthetic and Waymo-shaped fixture
  cases whose trajectories are safe to publish and inspect in a browser.

The interface labels that boundary directly. Raw Waymo TFRecords and local
per-scenario packets remain outside git. See
[`docs/data_provenance.md`](../data_provenance.md) for the complete trust model.

## Files

- `index.html`: compact operational shell shared by public and generated runs.
- `styles.css`: responsive Explorer visual system.
- `app.js`: run summary, filtering, sorting, diagnostics, and case inspection.
- `run.json`: `scenariolens.explorer_run.v1` aggregate run contract.
- `scenarios.json`: `scenariolens.dashboard.v1` ranked case contract.
- `selector_decisions.json`: public-safe terminal-selector decision atlas.
- `evidence_index.json`: generated v1 public evidence catalog.
- `assets/*.svg`: trajectory and selector-decision visuals.

`scenariolens run` copies the same HTML, CSS, and JavaScript into
`<output>/explorer/`, writes a run-specific `run.json` and `scenarios.json`, and
renders selected trajectories under `<output>/assets/`. The public demo and a
local run therefore use the same versioned payload contracts and interaction
code.

## Regeneration

```bash
scenariolens dashboard-data \
  --output docs/demo/scenarios.json \
  --assets-dir docs/demo/assets \
  --lane-selection-manifest data/processed/waymo_lane_selection_study/manifest.json

scenariolens evidence-index \
  --output-dir data/processed/scenariolens_evidence_index \
  --public-report docs/reports/scenariolens_evidence_index.md \
  --demo-json docs/demo/evidence_index.json \
  --repo-root .

scenariolens public-surface-check \
  --output-dir data/processed/scenariolens_public_surface_check \
  --public-report docs/reports/scenariolens_public_surface_check.md \
  --repo-root .
```

The hand-curated public `run.json` mirrors fields from the checked-in
full-corpus reproducibility report. Update it only when a new public-safe run
validation packet is published.

## Browser Contract

The Explorer must load without relevant console errors and support:

- run readiness, digest, timing, memory, and stage summaries,
- report navigation using portable relative paths,
- dataset, tag, score, and component filters,
- sorting and keyboard-selectable scenario rows,
- trajectory rendering and previous/next case navigation,
- baseline comparison cards and public-safe diagnostics,
- mobile layouts without page-level horizontal overflow.

The payloads are deterministic and contain no generated timestamps, so changes
remain reviewable in pull requests.
