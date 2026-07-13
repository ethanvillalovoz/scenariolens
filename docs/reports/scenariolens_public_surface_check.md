# ScenarioLens Public Surface Check

This generated report is the v1 release-readiness gate for the public ScenarioLens surface. It verifies that the demo payloads, report links, public evidence index, raw-data boundary, and CI smoke commands are internally consistent without requiring local Waymo shards.

It is intentionally scoped to repository health. It is not a Waymo benchmark claim, not a production autonomy validation, and not a closed-loop simulation result.

## Summary

- Ready: yes
- Checks passed: 7 / 7
- Failed checks: 0
- Warnings: 0
- Files checked: 17

## Checks

| Check | Status | Summary |
| --- | --- | --- |
| Evidence index readiness | pass | Evidence index is ready with no missing required artifacts. |
| Demo payload contracts | pass | Static demo JSON payloads parse and expose expected format versions. |
| Local link integrity | pass | All checked local links resolve to files in the repository. |
| Demo asset integrity | pass | All checked SVG assets referenced by demo JSON exist. |
| Raw-data boundary | pass | No raw Waymo or TFRecord-like files are tracked. |
| CI surface | pass | CI covers unit tests, deterministic run integration, clean-package release validation, static demo syntax, evidence JSON, and public-surface checks. |
| Public-safety language | pass | Core provenance/evidence docs state the non-benchmark and raw-data boundaries. |

## Details

### Evidence index readiness

- Status: pass
- Files: `docs/demo/evidence_index.json`
- Summary: Evidence index is ready with no missing required artifacts.
- Format: `scenariolens.evidence_index.v1`
- Ready flag: True
- Artifact count: 19
- Missing required artifacts: 0

### Demo payload contracts

- Status: pass
- Files: `docs/demo/scenarios.json`, `docs/demo/run.json`, `docs/demo/selector_decisions.json`, `docs/demo/evidence_index.json`
- Summary: Static demo JSON payloads parse and expose expected format versions.
- `docs/demo/scenarios.json` format `scenariolens.dashboard.v1`
- `docs/demo/run.json` format `scenariolens.explorer_run.v1`
- `docs/demo/selector_decisions.json` format `scenariolens.lane_continuation_terminal_neighborhood_selector_decision_atlas.v1`
- `docs/demo/evidence_index.json` format `scenariolens.evidence_index.v1`

### Local link integrity

- Status: pass
- Files: `README.md`, `docs/demo/index.html`, `docs/demo/README.md`, `docs/reports/scenariolens_evidence_index.md`, `docs/reports/scenariolens_public_surface_check.md`
- Summary: All checked local links resolve to files in the repository.
- `README.md` links scanned: 114
- `docs/demo/index.html` links scanned: 11
- `docs/demo/README.md` links scanned: 1
- `docs/reports/scenariolens_evidence_index.md` links scanned: 19
- `docs/reports/scenariolens_public_surface_check.md` links scanned: 0
- Local links checked: 137
- External links skipped: 6

### Demo asset integrity

- Status: pass
- Files: `docs/demo/scenarios.json`, `docs/demo/selector_decisions.json`
- Summary: All checked SVG assets referenced by demo JSON exist.
- Referenced demo assets checked: 7

### Raw-data boundary

- Status: pass
- Files: `.gitignore`, `docs/data_provenance.md`
- Summary: No raw Waymo or TFRecord-like files are tracked.
- Tracked files inspected: 285
- Tracked raw Waymo/TFRecord-like files: 0

### CI surface

- Status: pass
- Files: `.github/workflows/ci.yml`
- Summary: CI covers unit tests, deterministic run integration, clean-package release validation, static demo syntax, evidence JSON, and public-surface checks.
- `python -m unittest discover` present: True
- `node --check docs/demo/app.js` present: True
- `python -m json.tool docs/demo/run.json` present: True
- `python -m json.tool docs/demo/evidence_index.json` present: True
- `npm run test:browser` present: True
- `scenariolens run` present: True
- `scenariolens run-verify` present: True
- `scenariolens release-check` present: True
- `scenariolens evidence-index` present: True
- `scenariolens public-surface-check` present: True

### Public-safety language

- Status: pass
- Files: `docs/reports/scenariolens_evidence_index.md`, `docs/data_provenance.md`
- Summary: Core provenance/evidence docs state the non-benchmark and raw-data boundaries.
- `docs/reports/scenariolens_evidence_index.md` contains `not a Waymo benchmark`: True
- `docs/reports/scenariolens_evidence_index.md` contains `Raw Waymo TFRecords`: True
- `docs/reports/scenariolens_evidence_index.md` contains `default selector remains unchanged`: True
- `docs/data_provenance.md` contains `Raw Waymo`: True
- `docs/data_provenance.md` contains `outside git`: True

## Public-Safety Boundary

- The check reads checked-in derived reports and demo payloads only.
- Raw Waymo TFRecords, local replay packets, and per-case debug artifacts stay outside git.
- External links are counted but not fetched, so CI remains deterministic and offline-safe.
