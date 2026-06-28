# ScenarioLens v0.2.0 Release Checklist

Use this checklist before tagging the first public product-quality release.

## Public Surface

- README first viewport has live demo, screenshot, quick start, feature grid,
  dataset support, and real-data report links.
- GitHub sidebar metadata matches `docs/github_metadata.md`.
- `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CITATION.cff`, issue
  templates, and PR template are present.
- Demo screenshot is current and readable on GitHub.

## Technical Proof

- `failure-study` report is regenerated from the local Waymo Motion shard.
- `failure-study-stability` report is regenerated.
- If authenticated Waymo access is available, shards `00008`, `00009`, and
  `00010` are downloaded locally and a cross-shard stability report is added.
- If access remains blocked, `docs/reports/waymo_motion_shard_plan.md` remains
  the public fallback.

## Verification

```bash
python -m pip install -e ".[dev]"
scenariolens --help
PYTHONPATH=src python -m unittest discover
node --check docs/demo/app.js
python -m json.tool docs/demo/scenarios.json >/tmp/scenariolens-dashboard.json
git diff --check
```

Also browser-smoke-test the live explorer route:

- page loads without framework/runtime errors,
- filters update the result table,
- scenario detail image renders,
- baseline failure card updates,
- report links resolve.

## Release

- Create tag `v0.2.0`.
- Draft GitHub Release using `docs/releases/v0.2.0.md`.
- Verify CI passes on the tag.
