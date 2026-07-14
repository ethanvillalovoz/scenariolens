# ScenarioLens v1.0.0 Release Checklist

Use this checklist for `v1.0.0-rc.1` and the final `v1.0.0` promotion.

## Version And Package

- [x] `pyproject.toml`, `scenariolens.__version__`, `CITATION.cff`, changelog,
      and release notes agree on the release version.
- [x] Two clean builds produce byte-identical wheels.
- [x] The wheel installs without project dependencies into Python 3.11 and the
      target laptop runtime.
- [x] The installed `scenariolens` entrypoint runs outside the checkout.

## Product And Real Data

- [x] Two exact-RC `scenariolens run` executions process all 1,193 local
      scenarios with the same digest.
- [x] `run-verify` passes every readiness, scope, digest, duration, and memory
      gate.
- [x] The frozen 993-scenario selector report remains unchanged and the
      rejected candidate remains disabled.
- [x] Raw Waymo records and local per-case packets remain untracked.

## Failure And Recovery

- [x] `scenariolens release-check` passes 15/15 checks.
- [x] Empty, missing, unsupported, and truncated inputs return exit code 2 with
      useful diagnostics.
- [x] Missing map context uses the documented constant-velocity fallback.
- [x] Interrupted holdout state is atomic and a verified resume matches the
      uninterrupted digest.

## Public Surface

- [x] The evidence index and public-surface check are ready with no missing
      required artifacts.
- [x] Unit, compile, static JSON/JavaScript, and Playwright checks pass.
- [x] The portfolio route is synced from `docs/demo/` and verified on desktop
      and mobile without relevant console errors or horizontal overflow.
- [x] README, release notes, reports, and local demo links resolve.

## Publish

- [x] The exact release-candidate commit passes GitHub Actions on Python 3.11.
- [x] Merge the reviewed release candidate to `main`.
- [x] Create annotated tag `v1.0.0-rc.1` and a GitHub prerelease from
      `docs/releases/v1.0.0-rc.1.md`.
- [x] Verify tag CI and the public release assets.
- [x] Promote the validated code to `v1.0.0` and rerun the clean-package packet.
- [x] Publish the annotated `v1.0.0` tag, final wheel, and GitHub Release.
