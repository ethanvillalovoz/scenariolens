## Summary

<!-- Summarize the change and why it belongs in ScenarioLens. -->

## Type

- [ ] Scenario metric or baseline
- [ ] Ingestion or data workflow
- [ ] Dashboard or visualization
- [ ] Documentation or repo polish
- [ ] Test/CI improvement

## Validation

- [ ] `PYTHONPATH=src python3 -m unittest discover`
- [ ] `node --check docs/demo/app.js`
- [ ] `python3 -m json.tool docs/demo/scenarios.json`
- [ ] `git diff --check`

## Data Safety

- [ ] No raw Waymo or gated dataset files are committed.
- [ ] Public reports contain only aggregate statistics, commands, scenario IDs,
      or license-safe artifacts.

## Notes For Reviewers

<!-- Add reviewer context, screenshots, or known follow-ups here. -->
