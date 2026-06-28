# ScenarioLens Failure Distribution Stability Study

This report compares public-safe aggregate baseline-failure statistics across real-data slices. Raw Waymo files and per-scenario derived outputs remain outside git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation`
- Input format: `native`
- Comparison mode: single-input windowed comparison
- Ready for analysis: True
- Slices compared: 3
- Scenarios analyzed: 75
- Evaluated baseline targets: 309
- Max scenarios per input: 75
- Window size: 25
- Raw scenario data committed: no

## Executive Findings

| Metric | Value |
| --- | ---: |
| Mean FDE min / max / range | 25.77 m / 26.66 m / 0.89 m |
| Miss-rate min / max / range | 94.18% / 96.19% / 2.01% |
| Highest mean-FDE slice | `input_01_window_001_025` |
| Lowest mean-FDE slice | `input_01_window_051_075` |
| Most variable tag | `cyclist_interaction` (21.07 m FDE range) |

## Slice Distribution

| Slice | Scenarios | Targets | Mean ADE | Mean FDE | Miss Rate | Top FDE Tag | Hardest Scenario |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `input_01_window_001_025` | 25 | 101 | 10.17 m | 26.66 m | 96.04% | `objects_of_interest` | `5c8f9e7af4b0248a` |
| `input_01_window_026_050` | 25 | 105 | 9.43 m | 26.02 m | 96.19% | `objects_of_interest` | `f8194e7b4026784b` |
| `input_01_window_051_075` | 25 | 103 | 9.40 m | 25.77 m | 94.18% | `vulnerable_road_user` | `42e1f8772178733e` |

## Tag Stability

| Tag | Slices | Scenarios | Targets | Mean FDE | FDE Range | Miss-Rate Range | Highest FDE Slice |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `cyclist_interaction` | 3 | 7 | 40 | 19.70 m | 21.07 m | 10.00% | `input_01_window_026_050` |
| `objects_of_interest` | 3 | 24 | 122 | 25.81 m | 12.10 m | 2.38% | `input_01_window_026_050` |
| `vulnerable_road_user` | 3 | 59 | 256 | 24.68 m | 2.47 m | 1.67% | `input_01_window_051_075` |
| `map_context` | 3 | 75 | 309 | 26.15 m | 0.89 m | 2.01% | `input_01_window_001_025` |
| `tracks_to_predict` | 3 | 75 | 309 | 26.15 m | 0.89 m | 2.01% | `input_01_window_001_025` |
| `traffic_signal_context` | 3 | 75 | 309 | 26.15 m | 0.89 m | 2.01% | `input_01_window_001_025` |
| `dense_multi_agent` | 3 | 74 | 308 | 26.11 m | 0.75 m | 2.01% | `input_01_window_001_025` |

## Hardest Slice Representatives

| Slice | Scenario | FDE | Miss Rate | Tags |
| --- | --- | ---: | ---: | --- |
| `input_01_window_001_025` | `5c8f9e7af4b0248a` | 69.32 m | 100.00% | `dense_multi_agent`, `map_context`, `objects_of_interest`, `tracks_to_predict`, `traffic_signal_context` |
| `input_01_window_026_050` | `f8194e7b4026784b` | 64.14 m | 100.00% | `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` |
| `input_01_window_051_075` | `42e1f8772178733e` | 56.47 m | 100.00% | `vulnerable_road_user`, `dense_multi_agent`, `map_context`, `tracks_to_predict`, `traffic_signal_context` |

## Interpretation

- This is a distribution screen, not a benchmark claim.
- Large FDE range across slices means the constant-velocity baseline fails unevenly across sampled scenario families.
- With one local shard, the current report compares contiguous scenario windows; with more downloaded shards, rerun the same command with multiple `--input` values for true cross-shard stability.
