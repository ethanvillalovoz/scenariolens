# ScenarioLens Portfolio Report

## Executive Summary

ScenarioLens is a laptop-friendly autonomous-driving evaluation project for discovering and explaining long-tail driving scenarios. It ranks scenarios using lightweight interaction metrics, ODD-relevant taxonomy tags, vulnerable-road-user counts, closest-agent distance, and a simple constant-velocity time-to-collision proxy.

The current pipeline supports synthetic scenarios, ScenarioLens JSON, row-wise CSV ingestion, and a normalized Waymo Motion-shaped fixture. The native Waymo Motion parser is intentionally left as an optional future adapter so the core project stays dependency-free and easy to run.

## Current Coverage

- Synthetic scenarios analyzed: 10
- Normalized Waymo-shaped scenarios analyzed: 2
- Unit tests cover schema I/O, ranking, taxonomy, ingestion, reporting, CLI flows, and SVG rendering.

## Top Synthetic Scenarios

| Rank | Scenario | Score | Tags |
| ---: | --- | ---: | --- |
| 1 | `synthetic_dense_intersection_vru` | 27.698 | vulnerable_road_user, pedestrian_crossing, cyclist_interaction, dense_multi_agent |
| 2 | `synthetic_occluded_pedestrian` | 25.615 | vulnerable_road_user, pedestrian_crossing, blocked_lane, close_interaction |
| 3 | `synthetic_unprotected_left_turn` | 22.017 | vulnerable_road_user, unprotected_turn, close_interaction |

### 1. `synthetic_dense_intersection_vru`

![synthetic_dense_intersection_vru](assets/synthetic_dense_intersection_vru.svg)

- Score: 27.698
- Agents: 4
- Vulnerable road users: 2
- Min distance: 0.632 m
- Min TTC proxy: 0.136 s
- Why it matters:
  - contains 2 vulnerable road user(s)
  - minimum agent distance is 0.632 m
  - minimum constant-velocity TTC proxy is 0.136 s
  - dense scene with 4 tracked agents
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Cyclist interaction

### 2. `synthetic_occluded_pedestrian`

![synthetic_occluded_pedestrian](assets/synthetic_occluded_pedestrian.svg)

- Score: 25.615
- Agents: 3
- Vulnerable road users: 1
- Min distance: 0.510 m
- Min TTC proxy: 0.500 s
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 0.510 m
  - minimum constant-velocity TTC proxy is 0.500 s
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Blocked lane, Close interaction

### 3. `synthetic_unprotected_left_turn`

![synthetic_unprotected_left_turn](assets/synthetic_unprotected_left_turn.svg)

- Score: 22.017
- Agents: 3
- Vulnerable road users: 1
- Min distance: 1.887 m
- Min TTC proxy: 0.277 s
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 1.887 m
  - minimum constant-velocity TTC proxy is 0.277 s
  - high-value taxonomy tags: Vulnerable road user, Unprotected turn, Close interaction

## Normalized Waymo-Shaped Fixture Results

These examples use a tiny checked-in CSV shaped like a normalized Waymo Motion extraction. The data is synthetic, but the field boundary exercises the adapter path planned for real Motion slices.

| Rank | Scenario | Score | Tags |
| ---: | --- | ---: | --- |
| 1 | `waymo_like_unprotected_turn` | 23.017 | vulnerable_road_user, pedestrian_crossing, unprotected_turn |
| 2 | `waymo_like_cyclist` | 18.927 | vulnerable_road_user, cyclist_interaction, close_interaction |

### 1. `waymo_like_unprotected_turn`

![waymo_like_unprotected_turn](assets/waymo_like_unprotected_turn.svg)

- Score: 23.017
- Agents: 3
- Vulnerable road users: 1
- Min distance: 1.887 m
- Min TTC proxy: 0.277 s
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 1.887 m
  - minimum constant-velocity TTC proxy is 0.277 s
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Unprotected turn

### 2. `waymo_like_cyclist`

![waymo_like_cyclist](assets/waymo_like_cyclist.svg)

- Score: 18.927
- Agents: 2
- Vulnerable road users: 1
- Min distance: 2.915 m
- Min TTC proxy: 1.726 s
- Why it matters:
  - contains 1 vulnerable road user(s)
  - high-value taxonomy tags: Vulnerable road user, Cyclist interaction, Close interaction

## Limitations

- Current scenario data is synthetic or normalized-fixture data, not a native Waymo slice.
- Native Waymo Motion TFRecord/protobuf parsing is not implemented yet.
- The TTC value is a simple constant-velocity screening proxy, not a certified safety metric.
- The current renderer is 2D and focuses on agent trajectories, not map lanes or traffic lights.

## Next Work

- Add native Waymo Motion mini-slice ingestion behind the existing adapter boundary.
- Add map/lane context once real Motion records are available.
- Add richer interaction metrics such as deceleration, crossing conflict, and trajectory overlap.
- Create curated scenario collections for pedestrian, cyclist, merge, and unprotected-turn cases.
