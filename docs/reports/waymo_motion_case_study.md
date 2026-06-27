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
| Score | min / median / mean / max | 7.48 / 32.57 / 29.67 / 42.74 |
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

## Top Ranked Scenarios

| Rank | Scenario | Score | Main Reason |
| ---: | --- | ---: | --- |
| 1 | `a651202aa8e79d45` | 42.741 | contains 22 vulnerable road user(s) |
| 2 | `5f5660d70a6f14f6` | 41.654 | contains 16 vulnerable road user(s) |
| 3 | `7e969997e3e0b772` | 39.427 | contains 9 vulnerable road user(s) |
| 4 | `706fecd25045c8d` | 39.325 | contains 7 vulnerable road user(s) |
| 5 | `d30709cd60e60395` | 38.926 | contains 14 vulnerable road user(s) |

## Interpretation

- The scores are screening heuristics for review prioritization, not certified safety metrics.
- The run demonstrates that ScenarioLens can ingest a real Motion TFRecord shard with a dependency-free reader.
- The aggregate section is safe to publish because it contains counts and summary statistics only.
- The next useful expansion is to compare these aggregate distributions across more validation shards.
