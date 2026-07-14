# ScenarioLens Run Reproducibility Validation

This generated report validates independent executions of the ScenarioLens one-command analysis bundle.

## Summary

- Ready: yes
- Runs compared: 2
- Sources per run: 4
- Scenarios per run: 1193
- Analysis digest: `875060cf4e8fb9fca13e433f7581bb10026a05017769c62110a1b7ecc87cfa93`
- Maximum duration: 601.447 seconds
- Maximum peak memory: 3.642 GB
- Duration budget: 900.000 seconds
- Peak-memory budget: 8.00 GB

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| Every run and stage is ready | pass | 2/2 top-level runs ready. |
| Analysis digests match | pass | Observed 1 unique digest(s). |
| Input fingerprints match | pass | Observed 1 unique input fingerprint(s). |
| Source and scenario counts match | pass | Scenario counts: [1193, 1193]; source counts: [4, 4]. |
| Stable stage outputs match | pass | Observed 1 stable stage fingerprint(s). |
| Every run meets the duration budget | pass | Maximum 601.447 s; budget 900.000 s. |
| Every run reports and meets the peak-memory budget | pass | Maximum 3.642 GB; budget 8.00 GB. |

## Runs

| Run | Ready | Sources | Scenarios | Stages | Duration | Peak memory | Digest |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | yes | 4 | 1193 | 3 | 594.359 s | 3.640 GB | `875060cf4e8f` |
| 2 | yes | 4 | 1193 | 3 | 601.447 s | 3.642 GB | `875060cf4e8f` |

## Interpretation Boundary

- This validation compares generated ScenarioLens analysis bundles. It verifies deterministic aggregate evidence and laptop execution budgets, not closed-loop autonomy safety or Waymo benchmark status.
- Volatile timestamps, output paths, and timings are excluded from the analysis digest; input identities, configuration, stage formats, counts, and aggregate metrics are included.
- Raw Waymo records and per-scenario trajectories remain local and are not embedded in this report.
