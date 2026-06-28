# Waymo Motion Real-Data Case Study

This case study summarizes one local ScenarioLens smoke run against a downloaded Waymo Open Dataset Motion validation shard. It is designed to be public-safe: raw Waymo files, normalized scenario JSON, and SVGs from the shard remain local ignored artifacts.

## Run Scope

- Dataset path: `data/raw/waymo/motion/validation`
- Supported files: 1
- Supported bytes scanned: 246,887,249
- Scenarios analyzed: 25
- Top scenarios reported: 5
- Raw dataset files committed: no

## Aggregate Findings

| Category | Metric | Value |
| --- | --- | ---: |
| Score | min / median / mean / max | 19.48 / 41.06 / 39.29 / 51.43 |
| Tracks | avg raw agents | 59.40 |
| Tracks | avg scored agents | 58.72 |
| Tracks | avg excluded tracks | 0.68 |
| Tracks | low-quality track rate | 1.14% |
| VRUs | scenarios with VRUs | 19 |
| VRUs | avg raw VRUs | 4.84 |
| Waymo metadata | scenarios with SDC track | 25 |
| Waymo metadata | total prediction targets | 101 |
| Waymo metadata | total objects of interest | 18 |
| Waymo metadata | scenarios with parsed map features | 25 |
| Prediction baseline | evaluated targets | 101 |
| Prediction baseline | mean ADE / FDE | 10.49 m / 27.55 m |
| Prediction baseline | max FDE | 69.32 m |
| Prediction baseline | weighted miss rate | 96.04% |

## Top Ranked Scenarios

| Rank | Scenario | Score | Main Reason |
| ---: | --- | ---: | --- |
| 1 | `7e969997e3e0b772` | 51.427 | contains 9 vulnerable road user(s) |
| 2 | `706fecd25045c8d` | 51.325 | contains 7 vulnerable road user(s) |
| 3 | `770fec53ec3e0395` | 50.890 | contains 4 vulnerable road user(s) |
| 4 | `d30709cd60e60395` | 50.759 | contains 14 vulnerable road user(s) |
| 5 | `67fff4d5bb3acf8d` | 50.543 | contains 9 vulnerable road user(s) |

## Interpretation

- The scores are screening heuristics for review prioritization, not certified safety metrics.
- The run demonstrates that ScenarioLens can ingest a real Motion TFRecord shard with a dependency-free reader.
- The aggregate section is safe to publish because it contains counts and summary statistics only.
- The companion [Real-Slice Failure Study](waymo_motion_failure_study.md) breaks baseline ADE/FDE and miss rate down by tag and score component.
- The next useful expansion is to compare these interaction and baseline-failure distributions across more validation shards.
