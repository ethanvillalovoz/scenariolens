# ScenarioLens v1 Acceptance Contract

Status: frozen for the `v1.0.0` release track on 2026-07-13.

## Product Contract

ScenarioLens v1 is a local-first autonomy evaluation product. Given one or
more ScenarioLens JSON files or local Waymo Motion inputs, a user must be able
to run one command and receive a reproducible analysis bundle containing:

- input readiness and provenance,
- scenario and prediction-baseline summaries,
- ranked baseline failures and map-aware regressions,
- lane-selection and lane-continuation diagnostics,
- a concise Markdown report,
- a versioned machine-readable manifest,
- rendered case assets and an interactive local Explorer.

The intended commands are:

```bash
scenariolens demo --open
scenariolens run --input <path> --output runs/<name> --open
```

Existing specialist commands remain supported for research and debugging, but
they are not the primary v1 user journey.

## Required Run Bundle

Every successful `scenariolens run` execution must produce a self-contained
directory with stable relative links:

```text
manifest.json             Versioned run contract and deterministic digest
report.md                 Concise findings and limitations
studies/                  Generated study manifests and reports
explorer/                 Local static Explorer payload and page
assets/                   Rendered public-safe case assets
```

The top-level manifest must record the ScenarioLens version, input identities,
configuration, completed stages, aggregate metrics, stage timings, readiness,
and a digest that excludes volatile paths and timestamps.

## Real-Data Evaluation Contract

The current local corpus contains four Waymo Motion validation shards:

- `validation.tfrecord-00007-of-00150`: 276 scenarios
- `validation.tfrecord-00008-of-00150`: 314 scenarios
- `validation.tfrecord-00009-of-00150`: 301 scenarios
- `validation.tfrecord-00010-of-00150`: 302 scenarios

The complete local corpus contains 1,193 scenarios. The first 50 scenarios per
shard form the 200-scenario development cohort used by existing reports. The
remaining 993 scenarios form a frozen-policy scenario-window validation cohort
for the terminal selector candidate. This is same-shard window validation, not
an independent-shard benchmark.

The selector candidate and thresholds present at commit `ba0b37e` are frozen
before validation. A full-corpus lane-continuation aggregate was run only to
measure capacity and establish the release workload; it was not used to retune
the selector. If the validation cohort yields fewer than 30 selector decisions,
new untouched shards may be added only after preserving the frozen policy and
documenting the new-shard boundary.

Validation result: the frozen run evaluated all 993 holdout scenarios and 78
selector decisions, with zero overlap against the calibration identities and
8/8 release-integrity checks passing. It completed in 783.537 seconds with
3.614 GB peak process memory. The context-aware candidate improved agreement
from 33/78 to 52/78 but produced 12 false promotions, so the evaluation packet
passes while the candidate remains disabled. See
[`docs/reports/waymo_selector_holdout_993.md`](reports/waymo_selector_holdout_993.md).

## Release Gates

### Functional

- `scenariolens demo --open` completes without gated data.
- `scenariolens run` completes from a clean installation.
- A successful run generates every required bundle artifact.
- Existing specialist CLI commands and payload formats remain compatible.

### Full Real-Data

- The complete 1,193-scenario corpus runs without an unhandled exception.
- The frozen selector is evaluated separately on the 993-scenario validation
  cohort without threshold tuning.
- Reports include improvements, regressions, fallback counts, and uncertainty.
- Raw Waymo records and per-case local packets remain outside git.

### Determinism And Performance

- Two equivalent full-corpus runs produce the same canonical analysis digest.
- The end-to-end local run completes in at most 15 minutes on the target M5
  MacBook Air.
- Peak resident memory remains below 8 GB.
- Stage timings and peak-memory measurements are captured in the release
  validation packet.

The initial capacity baseline is 1,193 scenarios and 2,772 continuation targets
in 182.55 seconds with approximately 1.91 GB maximum resident memory.

### Installation And Failure Paths

- A built wheel installs into clean supported Python environments.
- Two builds under the release environment produce byte-identical wheels.
- The installed console entrypoint runs outside the repository checkout.
- Empty input, missing input, unsupported input, truncated TFRecord, missing
  map context, interrupted output, and resumed output paths are tested.
- Failures return non-zero exit codes and preserve useful diagnostics.

Interruption/resume status: implemented for the nine-stage frozen selector
holdout. The atomic `state.json` records input/policy/configuration fingerprints,
completed-artifact hashes, the active stage, and failure history. `--resume`
reuses only a verified contiguous stage prefix; changed inputs and tampered
artifacts are rejected. Unit coverage simulates interruption after three stages,
and an integration run executes and then reuses the actual nine-stage pipeline
with an identical analysis digest.

Clean-package status: implemented as `scenariolens release-check`. The gate
builds the package twice, compares wheel SHA-256 hashes, installs the artifact
into an isolated virtual environment, executes the product outside the source
checkout, and probes every required failure path. The current implementation
passes 15/15 checks locally; CI reruns the same command from a fresh checkout.

### Explorer

- The generated Explorer loads the run bundle rather than hard-coded metrics.
- Filtering, sorting, case selection, baseline comparison, trajectory assets,
  provenance, and report navigation work in a real browser.
- Desktop and mobile checks have no relevant console errors, broken assets, or
  horizontal overflow.
- The deployed demo and a locally generated run use the same versioned payload
  contract.

### Public Surface And Release

- The README presents one product loop, three flagship proof points, one live
  demo, and one quick start without exposing the full research ledger inline.
- Detailed reports remain available through an evidence index.
- CI validates unit, integration, package, static-asset, and public-surface
  contracts without requiring gated Waymo data.
- `v1.0.0-rc.1` passes the complete release validation packet before the final
  `v1.0.0` tag and GitHub Release are published.
- The exact release commit passes GitHub Actions and the live portfolio route.

## Non-Goals

ScenarioLens v1 is not a production autonomous-driving stack, a Waymo benchmark
submission, a closed-loop safety certification, an LLM product, or a GPU model
training project. Waymax/JAX integration and additional model families are
post-v1 work unless they are required to fix a release-blocking defect.

## Definition Of Done

The v1 track is complete only when the one-command workflow, full local corpus,
separate frozen-policy validation, clean package installation, failure paths,
interactive Explorer, public documentation, release candidate, and final
`v1.0.0` release all pass. Additional disconnected experiments do not move the
project closer to this terminal condition.
