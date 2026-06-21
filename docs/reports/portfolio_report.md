# ScenarioLens Portfolio Report

## Executive Summary

ScenarioLens is a laptop-friendly autonomous-driving evaluation project for discovering and explaining long-tail driving scenarios. It ranks scenarios using lightweight interaction metrics, ODD-relevant taxonomy tags, vulnerable-road-user counts, same-timestep proximity, path-conflict proximity, dynamics, and a simple constant-velocity time-to-collision proxy.

The current pipeline supports synthetic scenarios, ScenarioLens JSON, row-wise CSV ingestion, normalized Waymo Motion-shaped fixtures, and native protobuf-shaped Waymo Motion JSON mini-slices. Local slice preflight helps keep binary protobuf and TFRecord ingestion optional so the core project stays easy to run.

## Current Coverage

- Synthetic scenarios analyzed: 10
- Native Waymo-shaped JSON scenarios analyzed: 1
- Normalized Waymo-shaped scenarios analyzed: 2
- Unit tests cover schema I/O, ranking, taxonomy, ingestion, reporting, CLI flows, and SVG rendering.

## Top Synthetic Scenarios

| Rank | Scenario | Score | Tags |
| ---: | --- | ---: | --- |
| 1 | `synthetic_dense_intersection_vru` | 34.658 | vulnerable_road_user, pedestrian_crossing, cyclist_interaction, dense_multi_agent |
| 2 | `synthetic_occluded_pedestrian` | 32.728 | vulnerable_road_user, pedestrian_crossing, blocked_lane, close_interaction |
| 3 | `synthetic_unprotected_left_turn` | 27.851 | vulnerable_road_user, unprotected_turn, close_interaction |

### 1. `synthetic_dense_intersection_vru`

![synthetic_dense_intersection_vru](assets/synthetic_dense_intersection_vru.svg)

- Score: 34.658
- Agents: 4
- Vulnerable road users: 2
- Min distance: 0.632 m
- Min VRU distance: 0.632 m
- Min path distance: 0.632 m
- Min TTC proxy: 0.136 s
- Max speed: 5.000 m/s
- Ego max speed: 4.000 m/s
- Max deceleration: 0.000 m/s^2
- Component scores:
  - density: 1.000
  - vru: 3.000
  - taxonomy: 9.000
  - proximity: 7.368
  - ttc: 7.330
  - vru_proximity: 4.776
  - path_conflict: 2.184
  - dynamics: 0.000
- Why it matters:
  - contains 2 vulnerable road user(s)
  - minimum agent distance is 0.632 m
  - minimum constant-velocity TTC proxy is 0.136 s
  - closest vehicle-to-VRU distance is 0.632 m
  - agent paths come within 0.632 m
  - dense scene with 4 tracked agents
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Cyclist interaction

### 2. `synthetic_occluded_pedestrian`

![synthetic_occluded_pedestrian](assets/synthetic_occluded_pedestrian.svg)

- Score: 32.728
- Agents: 3
- Vulnerable road users: 1
- Min distance: 0.510 m
- Min VRU distance: 0.510 m
- Min path distance: 0.510 m
- Min TTC proxy: 0.500 s
- Max speed: 4.000 m/s
- Ego max speed: 4.000 m/s
- Max deceleration: 1.000 m/s^2
- Component scores:
  - density: 0.750
  - vru: 1.500
  - taxonomy: 9.000
  - proximity: 7.490
  - ttc: 6.875
  - vru_proximity: 4.868
  - path_conflict: 2.245
  - dynamics: 0.000
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 0.510 m
  - minimum constant-velocity TTC proxy is 0.500 s
  - closest vehicle-to-VRU distance is 0.510 m
  - agent paths come within 0.510 m
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Blocked lane, Close interaction

### 3. `synthetic_unprotected_left_turn`

![synthetic_unprotected_left_turn](assets/synthetic_unprotected_left_turn.svg)

- Score: 27.851
- Agents: 3
- Vulnerable road users: 1
- Min distance: 1.887 m
- Min VRU distance: 1.887 m
- Min path distance: 1.000 m
- Min TTC proxy: 0.277 s
- Max speed: 6.000 m/s
- Ego max speed: 3.606 m/s
- Max deceleration: 0.181 m/s^2
- Component scores:
  - density: 0.750
  - vru: 1.500
  - taxonomy: 6.500
  - proximity: 6.113
  - ttc: 7.153
  - vru_proximity: 3.835
  - path_conflict: 2.000
  - dynamics: 0.000
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 1.887 m
  - minimum constant-velocity TTC proxy is 0.277 s
  - closest vehicle-to-VRU distance is 1.887 m
  - agent paths come within 1.000 m
  - high-value taxonomy tags: Vulnerable road user, Unprotected turn, Close interaction

## Native Waymo Motion JSON Mini-Slice

This section uses a tiny checked-in JSON record shaped like the public Waymo Motion `Scenario` proto. It exercises native field mapping for timestamps, object types, valid states, velocities, and the SDC ego-track index without requiring a dataset download.

| Rank | Scenario | Score | Tags |
| ---: | --- | ---: | --- |
| 1 | `waymo_native_sample_interaction` | 31.542 | vulnerable_road_user, objects_of_interest, tracks_to_predict |

### 1. `waymo_native_sample_interaction`

![waymo_native_sample_interaction](assets/waymo_native_sample_interaction.svg)

- Score: 31.542
- Agents: 3
- Vulnerable road users: 1
- Min distance: 0.863 m
- Min VRU distance: 0.863 m
- Min path distance: 0.863 m
- Min TTC proxy: 0.012 s
- Max speed: 5.000 m/s
- Ego max speed: 5.000 m/s
- Max deceleration: 10.000 m/s^2
- Component scores:
  - density: 0.750
  - vru: 1.500
  - taxonomy: 2.000
  - proximity: 7.137
  - ttc: 7.485
  - vru_proximity: 4.602
  - path_conflict: 2.068
  - dynamics: 6.000
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 0.863 m
  - minimum constant-velocity TTC proxy is 0.012 s
  - closest vehicle-to-VRU distance is 0.863 m
  - agent paths come within 0.863 m
  - max deceleration is 10.000 m/s^2
  - high-value taxonomy tags: Vulnerable road user

## Normalized Waymo-Shaped Fixture Results

These examples use a tiny checked-in CSV shaped like a normalized Waymo Motion extraction. The data is synthetic, but the field boundary exercises row-wise extraction for real Motion slices.

| Rank | Scenario | Score | Tags |
| ---: | --- | ---: | --- |
| 1 | `waymo_like_unprotected_turn` | 28.851 | vulnerable_road_user, pedestrian_crossing, unprotected_turn |
| 2 | `waymo_like_cyclist` | 23.179 | vulnerable_road_user, cyclist_interaction, close_interaction |

### 1. `waymo_like_unprotected_turn`

![waymo_like_unprotected_turn](assets/waymo_like_unprotected_turn.svg)

- Score: 28.851
- Agents: 3
- Vulnerable road users: 1
- Min distance: 1.887 m
- Min VRU distance: 1.887 m
- Min path distance: 1.000 m
- Min TTC proxy: 0.277 s
- Max speed: 6.000 m/s
- Ego max speed: 3.606 m/s
- Max deceleration: 0.181 m/s^2
- Component scores:
  - density: 0.750
  - vru: 1.500
  - taxonomy: 7.500
  - proximity: 6.113
  - ttc: 7.153
  - vru_proximity: 3.835
  - path_conflict: 2.000
  - dynamics: 0.000
- Why it matters:
  - contains 1 vulnerable road user(s)
  - minimum agent distance is 1.887 m
  - minimum constant-velocity TTC proxy is 0.277 s
  - closest vehicle-to-VRU distance is 1.887 m
  - agent paths come within 1.000 m
  - high-value taxonomy tags: Vulnerable road user, Pedestrian crossing, Unprotected turn

### 2. `waymo_like_cyclist`

![waymo_like_cyclist](assets/waymo_like_cyclist.svg)

- Score: 23.179
- Agents: 2
- Vulnerable road users: 1
- Min distance: 2.915 m
- Min VRU distance: 2.915 m
- Min path distance: 2.625 m
- Min TTC proxy: 1.726 s
- Max speed: 6.000 m/s
- Ego max speed: 6.000 m/s
- Max deceleration: 0.000 m/s^2
- Component scores:
  - density: 0.500
  - vru: 1.500
  - taxonomy: 6.500
  - proximity: 5.085
  - ttc: 5.343
  - vru_proximity: 3.063
  - path_conflict: 1.188
  - dynamics: 0.000
- Why it matters:
  - contains 1 vulnerable road user(s)
  - closest vehicle-to-VRU distance is 2.915 m
  - high-value taxonomy tags: Vulnerable road user, Cyclist interaction, Close interaction

## Limitations

- Checked-in Waymo examples are synthetic mini fixtures, not downloaded real validation shards.
- Binary protobuf and TFRecord ingestion require optional packages and are not exercised in CI.
- The TTC value is a simple constant-velocity screening proxy, not a certified safety metric.
- The current renderer is 2D and focuses on agent trajectories, not parsed map lanes or traffic lights.

## Next Work

- Run the documented local-slice recipe on a small downloaded Waymo Motion validation shard.
- Add map/lane and traffic-light features from native Motion records.
- Compare synthetic, native mini-slice, and downloaded-slice score distributions.
- Create curated scenario collections for pedestrian, cyclist, merge, and unprotected-turn cases.
