# Tech Stack

ScenarioLens is designed to be Waymo-public-stack aligned, not a guess at
Waymo's private internal stack. The core project stays lightweight enough to run
on a laptop, while optional paths connect to public Waymo tooling when the
environment supports it.

## Stack Summary

| Layer | Choice | Status | Why |
| --- | --- | --- | --- |
| Core language | Python 3.11+ | Current | Natural fit for data ingestion, metrics, ML-adjacent tooling, and autonomous-driving evaluation. |
| Core dependencies | Python standard library | Current | Keeps the default repo reproducible on Apple Silicon without heavy installs. |
| Data model | ScenarioLens dataclasses | Current | Small internal representation for ranking, reporting, and rendering. |
| Waymo data boundary | Waymo Motion `Scenario`-shaped JSON, protobuf, TFRecord | Current/optional | Mirrors public Waymo Motion fields while allowing dependency-free fixtures. |
| Native Waymo package | `waymo-open-dataset-tf-2-12-0` / `waymo_open_dataset` import | Optional | Public Waymo package for binary protobuf and TFRecord paths. Best handled in a separate compatible environment. |
| TensorFlow | TensorFlow | Optional | Needed for native TFRecord reading, not for ScenarioLens JSON or normalized CSV. |
| Simulation stretch | JAX + Waymax | Future | Waymax is a Waymo Research JAX simulator built around Waymo Open Motion data. |
| Data index stretch | Parquet / DuckDB | Future | Useful after local slices grow beyond small JSON artifacts. |
| Frontend demo | Static React + TypeScript + Vite | Future | Recruiter-facing presentation layer; not the core autonomy stack. |
| CI | Python unittest + GitHub Actions | Current | Simple, dependency-light verification. |

## Current Design Decision

The default install intentionally has no runtime dependencies:

```toml
dependencies = []
```

That is deliberate. ScenarioLens can ingest synthetic examples, normalized CSV,
and protobuf-shaped Waymo Motion JSON without installing TensorFlow or the Waymo
Open Dataset package. This keeps the project easy to review and run.

Native binary Waymo inputs are treated as optional:

- `.json`, `.jsonl`, `.ndjson`: dependency-free.
- `.pb`, `.bin`: require the public Waymo Open Dataset package.
- `.tfrecord`, `.tfrecords`: require the public Waymo Open Dataset package and
  TensorFlow.

Use preflight before ingesting local downloaded data:

```bash
PYTHONPATH=src python3 -m scenariolens.cli waymo-motion-preflight \
  --input data/raw/waymo/motion/validation
```

## Why Not Put Waymo Dependencies In `pyproject.toml` Yet?

The public Waymo Open Dataset package is a specialized binary distribution. The
current TensorFlow 2.12 Waymo Open Dataset package variant on PyPI is published
by Waymo Research, but its available wheel is Linux x86_64, while this project
is being developed on Apple Silicon. Pinning it as a normal project extra would
make the repo look less portable and could create a rough first-run experience.

Instead:

- keep ScenarioLens core dependency-free,
- document the optional Waymo/TensorFlow environment,
- use protobuf-shaped JSON fixtures in CI,
- run binary TFRecord experiments in a separate Linux or Colab-style
  environment when needed.

## Public Waymo Alignment

ScenarioLens already aligns with the public Waymo ecosystem in the places that
matter most for this portfolio project:

- it names the Waymo Motion `Scenario` proto as the external boundary,
- it maps public fields such as `scenario_id`, `timestamps_seconds`, `tracks`,
  `object_type`, `states`, and `sdc_track_index`,
- it treats TFRecord/protobuf ingestion as optional public-Waymo tooling,
- it keeps future simulation work pointed at JAX/Waymax.

## Why Not C++ Or Bazel Yet?

The public Waymo Open Dataset repository includes Python, C++, notebooks, and
Starlark/Bazel-related code. ScenarioLens is currently an evaluation and data
workflow project, so Python gives the strongest signal for the least setup
cost. C++ or Bazel should be added only if there is a clear reason:

- C++: if trajectory metrics or geometry kernels become real bottlenecks.
- Bazel: if native extensions or larger generated-protobuf workflows become
  part of the core project.

Until then, adding those tools would make the repo heavier without making the
project more convincing.

## Future Stack Milestones

1. Add a downloaded Waymo Motion validation-slice run in a separate compatible
   environment.
2. Add a compact feature index, likely JSON first and Parquet/DuckDB once the
   slice gets larger.
3. Add a static React/TypeScript/Vite Scenario Explorer dashboard.
4. Add a small JAX/Waymax experiment that replays or evaluates selected
   high-value scenarios.

## References

- Waymo Open Dataset: https://waymo.com/open/
- Waymo Open Dataset GitHub: https://github.com/waymo-research/waymo-open-dataset
- Waymo Motion `Scenario` proto: https://github.com/waymo-research/waymo-open-dataset/blob/master/src/waymo_open_dataset/protos/scenario.proto
- Waymo Open Dataset PyPI package: https://pypi.org/project/waymo-open-dataset-tf-2-12-0/
- Waymax: https://github.com/waymo-research/waymax
