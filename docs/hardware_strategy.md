# Hardware Strategy

Development machine:

- Apple Silicon MacBook Air
- 32 GB RAM
- 1 TB storage

## Constraints

The machine is capable, but the project should avoid assuming:

- local GPU training,
- full-dataset image/LiDAR processing,
- repeated scans of large TFRecord or parquet files,
- hundreds of gigabytes of active working data,
- heavyweight model training as the core deliverable.

## Strategy

1. Start with motion/scenario metadata.
   Motion data is a better first target than full perception data because it is
   closer to planning/evaluation and can be processed with lighter compute.

2. Build metadata indexes.
   Parse scenario records once, then store compact derived features in
   `data/processed/`.

3. Use curated slices.
   Keep the active dataset small enough to move quickly: first synthetic records,
   then dozens to hundreds of real scenarios, then thousands if the pipeline is
   efficient.

4. Make heavy modules optional.
   Visual embeddings, open-vocabulary retrieval, and model training can be later
   extensions. The core project should still be impressive without them.

5. Keep raw data out of git.
   `data/raw/` and `data/processed/` are ignored. Only small samples, schemas,
   and reproducible scripts should be committed.

## Practical Storage Budget

Recommended local budget:

- 0.5 GB: synthetic and tiny sample scenarios,
- 5-20 GB: first real dataset slice,
- 50-150 GB: optional larger local experiment,
- 200+ GB: avoid unless there is a very specific reason.

## Compute Budget

Default target:

- feature extraction on CPU,
- batch jobs that run in minutes, not hours,
- no required cloud bill,
- no required GPU,
- optional acceleration later with PyTorch/MPS if useful.

