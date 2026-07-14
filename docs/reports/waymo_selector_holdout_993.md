# ScenarioLens Frozen Selector Holdout

**Release-gate status: PASS.**

This report evaluates the terminal-neighborhood selector candidate on a scenario window that was excluded from policy calibration. The policy was frozen at commit `ba0b37e` before this holdout run. No selector threshold is tuned here.

This is same-shard scenario-window validation, not an independent-shard benchmark. It is useful evidence of out-of-window transfer, but it does not establish production autonomy safety or Waymo benchmark performance.

## Cohort And Policy

- Sources: 4
- Holdout scenarios evaluated: 993
- Excluded prefix per source: 50
- Expected holdout scenarios: 993
- Frozen maximum alternate distance: 5.000 m
- Frozen minimum heading alignment: 0.950
- Frozen minimum route extension: 40.000 m
- Frozen diagnostic heading gate: 0.700
- Analysis digest: `48f3161d4c44f9720a26baa6db987963f7fe69b7ffdadc01aaca43a866852b41`
- Runtime: 783.537 s
- Peak process memory: 3.614 GB
- Raw Waymo records committed: no

## Release Gates

| Check | Result | Observed | Expected |
| --- | --- | ---: | ---: |
| All pipeline stages ready | pass | 9 | 9 |
| Expected holdout scenarios evaluated | pass | 993 | 993 |
| No development-window scenario indices | pass | 51 | > 50 |
| Selector decisions trace to holdout tracks | pass | 78 | 78 |
| No selector cases overlap calibration | pass | 0 | 0 |
| All surfaced topology gaps queued | pass | 124 | 124 |
| All nearby recoveries replayed | pass | 78 | 78 |
| Minimum selector decisions reached | pass | 78 | >= 30 |

## Evidence Funnel

| Stage | Count |
| --- | ---: |
| Candidate targets | 2321 |
| Topology gaps | 124 |
| Topology cases audited | 124 |
| Terminal-neighborhood cases | 110 |
| Nearby recovery candidates | 78 |
| Perturbation-replayed selector decisions | 78 |
| Replay-accepted recoveries | 55 |
| Replay-held controls | 23 |

## Selector Outcomes

| Metric | Frozen transfer policy | Context-aware candidate |
| --- | ---: | ---: |
| Replay-label matches | 33 | 52 |
| False promotions | 12 | 12 |
| False holds | 33 | 14 |
| Promotions | 34 | 53 |
| Holds | 44 | 25 |
| False holds recovered by frozen context rule | n/a | 19 |

The replay labels come from deterministic nominal and perturbation tests. They are validation labels for this bounded diagnostic, not ground-truth driving-policy labels.

## Stage Artifacts

| Stage | Ready | Duration | Report |
| --- | --- | ---: | --- |
| Holdout lane-continuation study | True | 165.134 s | local run bundle |
| Replay and topology candidate plan | True | 0.016 s | local run bundle |
| Deterministic continuation replay | True | 278.650 s | local run bundle |
| Topology gap audit | True | 152.979 s | local run bundle |
| Terminal-neighborhood alternatives | True | 92.145 s | local run bundle |
| Terminal-neighborhood perturbation replay | True | 94.186 s | local run bundle |
| Frozen selector transfer | True | 0.003 s | local run bundle |
| Frozen false-hold route/context audit | True | 0.002 s | local run bundle |
| Frozen context-aware candidate validation | True | 0.001 s | local run bundle |

## Input Provenance

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `validation.tfrecord-00007-of-00150` | 246887249 | `c017ab0a5f0f8d03...` |
| `validation.tfrecord-00008-of-00150` | 291303216 | `2d42c0751ba13fc6...` |
| `validation.tfrecord-00009-of-00150` | 291553780 | `09ac3a742f0a5230...` |
| `validation.tfrecord-00010-of-00150` | 288993386 | `1948e64f336ab0a5...` |

## Interpretation And Uncertainty

The context-aware candidate created 12 false promotion(s) against the perturbation-replay labels. Keep the default selector unchanged and inspect these holdout failures; do not tune against this validation cohort.

- Passing this packet means the evaluation is complete and leakage/coverage gates passed; it does not automatically mean the candidate should replace the default selector.
- The cohort shares shards with development data, so geographic and collection correlations may remain.
- The selector only sees terminal-neighborhood cases surfaced by the preceding lane-continuation diagnostic; it is not evaluated on every possible autonomy failure mode.
- A stronger post-v1 result would preserve this frozen policy and repeat the packet on untouched shards.
