# ScenarioLens V1 Release Check

**Status: PASS.**

This packet builds ScenarioLens from the repository, installs the wheel into a clean virtual environment, and exercises the installed entrypoint from outside the checkout.

It uses checked-in synthetic fixtures for packaging and failure-path validation. Real-data claims remain in the separate full-corpus and frozen selector holdout reports.

## Summary

- ScenarioLens version: `1.0.0`
- Checks passed: 15 / 15
- Duration: 4.110 s
- Release-check digest: `517b0e830a58871bda3db34bd064d36c381947cfc20f692ba3fc07c4b7d8c9a6`
- Wheel: `scenariolens-1.0.0-py3-none-any.whl`
- Wheel SHA-256: `b09911f6aab3f310fa505931d52f924c9cfe528a3c4eec453130311397067e2c`
- Product-run digest: `b7d46bc602b8b7df7c31a61c8519be790ae22e4722e0f5620072372d87f71f6f`
- Resume digest: `4676bca8d60bf5f1377ee196b5ad3ff164c9c9668e0f6a353fced9f8dc124171`

## Checks

| Check | Result | Observed | Expected |
| --- | --- | --- | --- |
| Wheel build | pass | exit 0; 1 wheel(s) | exit 0; exactly 1 wheel |
| Reproducible wheel rebuild | pass | exit 0; name match True; hash match True | exit 0; wheel names and SHA-256 hashes match |
| Clean wheel installation | pass | venv exit 0; install exit 0 | both exit 0; console script present |
| Installed import provenance | pass | version 1.0.0; outside checkout True | version 1.0.0; outside checkout true |
| Installed console entrypoint | pass | exit 0; command list present True | exit 0; ScenarioLens commands listed |
| Installed synthetic fixture export | pass | exit 0; file present True | exit 0; fixture present |
| Installed one-command product run | pass | exit 0; ready True; scenarios 11 | exit 0; ready true; 11 scenarios; 3 stages |
| Installed run-bundle contract | pass | 8/8 required artifacts | 8/8 required artifacts |
| Missing map-context fallback | pass | run ready True; no-map fallbacks 13 | run ready true; no-map fallbacks > 0 |
| Empty input rejection | pass | exit 2; diagnostic present True | exit 2; expected diagnostic present |
| Missing input rejection | pass | exit 2; diagnostic present True | exit 2; expected diagnostic present |
| Unsupported input rejection | pass | exit 2; diagnostic present True | exit 2; expected diagnostic present |
| Truncated TFRecord rejection | pass | exit 2; diagnostic present True | exit 2; expected diagnostic present |
| Interrupted output diagnostics | pass | exit 0; status interrupted; completed 3 | exit 0; interrupted; 3 completed stages |
| Verified interruption resume | pass | status complete; reused 3; executed 6; digest match True | complete; 3 reused; 6 executed; digest match true |

## Diagnostics

### Wheel build

- Result: pass
- Command output: `... dependencies: finished with status 'done' / Getting requirements to build wheel: started / Getting requirements to build wheel: finished with status 'done' / Preparing metadata (pyproject.toml): started / Preparing metadata (pyproject.toml): finished with status 'done' / Building wheels for collected packages: scenariolens / Building wheel for scenariolens (pyproject.toml): started / Building wheel for scenariolens (pyproject.toml): finished with status 'done' / Created wheel for scenariolens: filename=scenariolens-1.0.0-py3-none-any.whl size=384699 sha256=b09911f6aab3f310fa505931d52f924c9cfe528a3c4eec453130311397067e2c / Stored in directory: <system-temp>/pip-ephem-wheel-cache-zfw0o86m/wheels/72/c5/d1/3648a127c49d116380ae790a07196c84b2abd9685f88625594 / Successfully built scenariolens`

### Reproducible wheel rebuild

- Result: pass
- Command output: `... dependencies: finished with status 'done' / Getting requirements to build wheel: started / Getting requirements to build wheel: finished with status 'done' / Preparing metadata (pyproject.toml): started / Preparing metadata (pyproject.toml): finished with status 'done' / Building wheels for collected packages: scenariolens / Building wheel for scenariolens (pyproject.toml): started / Building wheel for scenariolens (pyproject.toml): finished with status 'done' / Created wheel for scenariolens: filename=scenariolens-1.0.0-py3-none-any.whl size=384699 sha256=b09911f6aab3f310fa505931d52f924c9cfe528a3c4eec453130311397067e2c / Stored in directory: <system-temp>/pip-ephem-wheel-cache-7_2orkmg/wheels/72/c5/d1/3648a127c49d116380ae790a07196c84b2abd9685f88625594 / Successfully built scenariolens`

### Clean wheel installation

- Result: pass
- No command output.
- Command output: `Processing <repo>/data/processed/scenariolens_v1_release_check_final/dist/scenariolens-1.0.0-py3-none-any.whl / Installing collected packages: scenariolens / Successfully installed scenariolens-1.0.0`

### Installed import provenance

- Result: pass
- Command output: `{"version": "1.0.0", "path": "<temp>/venv/lib/python3.14/site-packages/scenariolens/__init__.py"}`

### Installed console entrypoint

- Result: pass
- Command output: `...ntext-failure-study / Join map/signal context summaries with baseline / failure metrics for public-safe real-data diagnostics. / context-eval-set    Turn a context-failure-study manifest into a curated / public-safe evaluation set. / portfolio-report    Generate the checked-in ScenarioLens portfolio report. / dashboard-data      Generate static JSON and SVG assets for the Scenario / Explorer dashboard. / evidence-index      Generate a v1 public evidence index that verifies the / demo, reports, provenance docs, and CI artifacts / exist. / public-surface-check / Verify public README/demo/report links, JSON / contracts, raw-data boundary, and CI smoke coverage. / render              Render scenarios as SVG trajectory views. / options: / -h, --help            show this help message and exit`

### Installed synthetic fixture export

- Result: pass
- Command output: `Exported 11 scenario(s) to <temp>/synthetic.json`

### Installed one-command product run

- Result: pass
- Command output: `Wrote ScenarioLens run manifest to <temp>/product-run/manifest.json / Wrote ScenarioLens run report to <temp>/product-run/report.md / ScenarioLens run ready: 1 source(s), 11 scenario(s), 3 stage(s), digest b7d46bc602b8, peak memory 35.77 MB.`

### Installed run-bundle contract

- Result: pass
- All top-level, study, and Explorer artifacts are present.

### Missing map-context fallback

- Result: pass
- Targets without lane geometry retained the documented constant-velocity fallback.

### Empty input rejection

- Result: pass
- Command output: `usage: scenariolens run [-h] --input INPUT / [--format {native,scenariolens-json}] / [--output OUTPUT] [--max-scenarios MAX_SCENARIOS] / [--top TOP] [--no-input-hash] [--open] [--host HOST] / [--port PORT] [--no-browser] / scenariolens run: error: the following arguments are required: --input`

### Missing input rejection

- Result: pass
- Command output: `ScenarioLens run input does not exist: <temp>/missing.tfrecord`

### Unsupported input rejection

- Result: pass
- Command output: `Unsupported Waymo Motion input suffix: .txt. Supported suffixes: .bin, .json, .jsonl, .ndjson, .pb, .tfrecord, .tfrecord-*-of-*, .tfrecords`

### Truncated TFRecord rejection

- Result: pass
- Command output: `<temp>/truncated.tfrecord: truncated TFRecord header at record 0`

### Interrupted output diagnostics

- Result: pass
- Command output: `SCENARIOLENS_RELEASE_PROBE={"analysis_digest": "4676bca8d60bf5f1377ee196b5ad3ff164c9c9668e0f6a353fced9f8dc124171", "digest_match": true, "executed_stage_count": 6, "failure_type": "KeyboardInterrupt", "final_status": "complete", "interrupted_active_stage": "topology_gap_audit", "interrupted_stage_count": 3, "interrupted_status": "interrupted", "reused_stage_count": 3, "stage_count": 9}`

### Verified interruption resume

- Result: pass
- Command output: `SCENARIOLENS_RELEASE_PROBE={"analysis_digest": "4676bca8d60bf5f1377ee196b5ad3ff164c9c9668e0f6a353fced9f8dc124171", "digest_match": true, "executed_stage_count": 6, "failure_type": "KeyboardInterrupt", "final_status": "complete", "interrupted_active_stage": "topology_gap_audit", "interrupted_stage_count": 3, "interrupted_status": "interrupted", "reused_stage_count": 3, "stage_count": 9}`

## Boundaries

- The installed product run uses public synthetic scenarios.
- The no-map check validates explicit constant-velocity fallback, not map-aware accuracy.
- The interruption probe runs the actual installed nine-stage pipeline and injects one `KeyboardInterrupt` at the topology stage.
- This packet does not publish or inspect raw Waymo records.
- Passing this packet is necessary for v1 release readiness, but it does not establish production autonomy safety.
