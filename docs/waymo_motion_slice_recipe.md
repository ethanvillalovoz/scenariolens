# Waymo Motion Slice Recipe

This recipe shows the intended local workflow for a small downloaded Waymo
Motion slice:

```text
Waymo Motion file or folder -> validate -> ScenarioLens JSON + report + SVG gallery
```

The goal is to prove that ScenarioLens can move from toy fixtures toward a real
autonomous-driving dataset without downloading or committing a full dataset.

## 1. Get A Tiny Motion Slice

Use the official Waymo Open Dataset access flow:

- Open https://waymo.com/open/.
- Sign in and follow Waymo's dataset access requirements.
- Choose Motion data.
- Download only one small validation or training shard at first.
- Keep raw files under `data/raw/waymo/motion/`.

Suggested local layout:

```text
data/raw/waymo/motion/
  validation/
    shard-00000.tfrecord
```

Raw dataset files are intentionally ignored by git. Do not commit downloaded
Waymo files or derived outputs unless their license and terms allow it.

If the browser downloads the shard somewhere else, run doctor before moving
files by hand:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-doctor \
  --input data/raw/waymo/motion/validation \
  --output data/processed/waymo_motion_readiness.json
```

Doctor reports:

- whether the configured input path is ingestable,
- whether `gcloud` or `gsutil` are installed,
- whether optional Waymo/TensorFlow packages are importable,
- whether likely raw Motion files exist in Downloads or Desktop,
- the next action needed before validation can run.

## 2. Validate The Local Slice

Run the one-command validation workflow first:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-validate \
  --input data/raw/waymo/motion/validation \
  --output-dir data/processed/waymo_motion_validation_run \
  --max-scenarios 25 \
  --top 5
```

The validation command writes:

- `preflight.json`: file counts, supported suffixes, local size, and optional
  dependency readiness,
- `manifest.json`: machine-readable run summary,
- `README.md`: human-readable run summary,
- `scenarios.json`: normalized ScenarioLens records,
- `report.md`: ranked scenario report,
- `assets/*.svg`: top-scenario trajectory previews.

Expected behavior:

- `.json`, `.jsonl`, and `.ndjson` are dependency-free.
- `.pb` and `.bin` require the optional Waymo Open Dataset package.
- `.tfrecord` and `.tfrecords` require optional Waymo and TensorFlow packages.

If the command says the slice is not ready, inspect
`data/processed/waymo_motion_validation_run/preflight.json`, fix the path or
optional dependency setup, and rerun the same command.

## 3. Optional Manual Steps

The validation command wraps the manual preflight, ingest, report, and render
flow. If you want to debug those steps separately, use the commands below.

### Preflight Only

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-preflight \
  --input data/raw/waymo/motion/validation
```

### Convert To ScenarioLens JSON

Once preflight passes, ingest a very small number of scenarios first:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format native \
  --input data/raw/waymo/motion/validation \
  --output data/processed/waymo_motion_validation_sample.json \
  --max-scenarios 25
```

For a protobuf-shaped JSON export or fixture, the same command works without
optional packages:

```bash
PYTHONPATH=src python3 -m scenariolens.cli ingest-waymo-motion \
  --format native \
  --input docs/examples/waymo_motion_native_sample.json \
  --output data/processed/waymo_motion_native_sample.json
```

### Generate A Ranked Report

```bash
PYTHONPATH=src python3 -m scenariolens.cli report \
  --input data/processed/waymo_motion_validation_sample.json \
  --format markdown \
  --limit 10 \
  --output /tmp/scenariolens_waymo_motion_report.md
```

Look for scenarios with:

- vulnerable road users,
- low same-timestep distance,
- low path distance,
- low constant-velocity TTC proxy,
- high deceleration,
- useful Waymo fields such as objects of interest or tracks to predict.

### Render A Small Gallery

```bash
PYTHONPATH=src python3 -m scenariolens.cli render \
  --input data/processed/waymo_motion_validation_sample.json \
  --top 5 \
  --output-dir /tmp/scenariolens_waymo_motion_gallery
```

The SVGs give a quick visual sanity check before any heavier dashboard work.

## 4. Portfolio Use

For a public GitHub repo, keep this distinction clear:

- checked-in examples are synthetic mini fixtures,
- local downloaded Waymo files remain untracked,
- reports from local Waymo slices should be summarized carefully,
- do not imply benchmark results unless the slice and process are documented.

This lets the project demonstrate real dataset readiness while staying
laptop-friendly and license-conscious.

## References

- Waymo Open Dataset: https://waymo.com/open/
- Waymo Open Dataset Challenges: https://waymo.com/open/challenges/
- Waymo Motion Scenario proto: https://github.com/waymo-research/waymo-open-dataset/blob/master/src/waymo_open_dataset/protos/scenario.proto
