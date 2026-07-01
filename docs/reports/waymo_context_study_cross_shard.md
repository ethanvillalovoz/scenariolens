# ScenarioLens Waymo Map and Signal Context Study

This report summarizes public-safe map, traffic-signal, and lane-topology context parsed from local Waymo Motion slices. It exists to answer a recruiter-facing question that pure ADE/FDE reports cannot answer: what contextual evidence is available when a scenario looks hard?

Raw Waymo TFRecords and per-scenario derived packets remain outside git.

## Run Scope

- Inputs: `data/raw/waymo/motion/validation/validation.tfrecord-00007-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00008-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00009-of-00150`, `data/raw/waymo/motion/validation/validation.tfrecord-00010-of-00150`
- Input format: `native`
- Ready for analysis: True
- Sources analyzed: 4
- Scenarios analyzed: 100
- Max scenarios per input: 25
- Raw scenario data committed: no
- Public artifact contains scenario IDs plus aggregate counts only

## Executive Summary

| Context family | Scenarios | Coverage | Count |
| --- | ---: | ---: | ---: |
| Static map features | 100 | 100.0% | 15453 features |
| Traffic signal lane states | 76 | 76.0% | 60583 lane states |
| Lane topology / route hints | 99 | 99.0% | 27065 links |
| Signal stop points | n/a | n/a | 60583 stop points |

## Static Map Summary

| Metric | Value |
| --- | ---: |
| Total map features | 15453 |
| Lane features | 6605 |
| Lane speed limits parsed | 6605 |
| Mean parsed lane speed limit | 27.0 mph |
| Entry-lane links | 6729 |
| Exit-lane links | 6803 |
| Neighbor-lane links | 13533 |

Map feature kinds:

- `crosswalk`: 120
- `driveway`: 552
- `lane`: 6605
- `road_edge`: 4236
- `road_line`: 3902
- `speed_bump`: 38

Lane types:

- `TYPE_BIKE_LANE`: 355
- `TYPE_FREEWAY`: 115
- `TYPE_SURFACE_STREET`: 6028
- `TYPE_UNDEFINED`: 107

## Traffic Signal Summary

| Metric | Value |
| --- | ---: |
| Dynamic-map timesteps | 9100 |
| Timesteps with observed lane states | 6289 |
| Signal-controlled lane references | 869 |
| Stop-state observations | 33880 |
| Caution-state observations | 1320 |
| Go-state observations | 13106 |
| Unknown-state observations | 12277 |

Signal state distribution:

- `LANE_STATE_ARROW_CAUTION`: 294
- `LANE_STATE_ARROW_GO`: 1059
- `LANE_STATE_ARROW_STOP`: 7611
- `LANE_STATE_CAUTION`: 1026
- `LANE_STATE_FLASHING_STOP`: 180
- `LANE_STATE_GO`: 12047
- `LANE_STATE_STOP`: 26089
- `LANE_STATE_UNKNOWN`: 12277

## Per-Source Summary

| Source | Scenarios | Map ctx | Signal ctx | Route ctx | Features | Lane states | Route links |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation.tfrecord-00007-of-00150` | 25 | 25 | 18 | 25 | 3978 | 15588 | 7568 |
| `validation.tfrecord-00008-of-00150` | 25 | 25 | 19 | 25 | 3711 | 13740 | 7003 |
| `validation.tfrecord-00009-of-00150` | 25 | 25 | 18 | 24 | 3868 | 11781 | 6119 |
| `validation.tfrecord-00010-of-00150` | 25 | 25 | 21 | 25 | 3896 | 19474 | 6375 |

## Map-Dense Scenarios

| Rank | Source | Scenario | Features | Lanes | Crosswalks | Route links | Signal states |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 160 | 73 | 0 | 220 | 2047 |
| 2 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 160 | 67 | 0 | 240 | 1890 |
| 3 | `validation.tfrecord-00010-of-00150` | `d8dde10f514a501c` | 160 | 93 | 0 | 376 | 1890 |
| 4 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 160 | 95 | 0 | 471 | 1800 |
| 5 | `validation.tfrecord-00007-of-00150` | `67fff4d5bb3acf8d` | 160 | 68 | 0 | 353 | 1542 |
| 6 | `validation.tfrecord-00007-of-00150` | `7e969997e3e0b772` | 160 | 39 | 0 | 131 | 1530 |
| 7 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 160 | 87 | 0 | 364 | 1440 |
| 8 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | 160 | 86 | 0 | 372 | 1440 |
| 9 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 160 | 59 | 0 | 388 | 1359 |
| 10 | `validation.tfrecord-00008-of-00150` | `6bfab54b46fe8f78` | 160 | 27 | 0 | 92 | 1350 |

## Signal-Dense Scenarios

| Rank | Source | Scenario | Signal states | Controlled lanes | Stop points | Top state | Map features |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | `validation.tfrecord-00010-of-00150` | `7c8b1da44fecf0ba` | 2047 | 23 | 2047 | `LANE_STATE_STOP (703)` | 160 |
| 2 | `validation.tfrecord-00010-of-00150` | `1f18831dfad32caa` | 1890 | 21 | 1890 | `LANE_STATE_GO (801)` | 160 |
| 3 | `validation.tfrecord-00010-of-00150` | `d8dde10f514a501c` | 1890 | 21 | 1890 | `LANE_STATE_STOP (1116)` | 160 |
| 4 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 1800 | 20 | 1800 | `LANE_STATE_STOP (900)` | 160 |
| 5 | `validation.tfrecord-00007-of-00150` | `67fff4d5bb3acf8d` | 1542 | 18 | 1542 | `LANE_STATE_ARROW_STOP (528)` | 160 |
| 6 | `validation.tfrecord-00007-of-00150` | `7e969997e3e0b772` | 1530 | 17 | 1530 | `LANE_STATE_STOP (1195)` | 160 |
| 7 | `validation.tfrecord-00009-of-00150` | `b2b7c2ad7bcd134b` | 1440 | 16 | 1440 | `LANE_STATE_STOP (720)` | 160 |
| 8 | `validation.tfrecord-00010-of-00150` | `fe4a6425278fbd5b` | 1440 | 16 | 1440 | `LANE_STATE_STOP (977)` | 160 |
| 9 | `validation.tfrecord-00008-of-00150` | `a56ce9f1cb56c196` | 1359 | 16 | 1359 | `LANE_STATE_UNKNOWN (639)` | 160 |
| 10 | `validation.tfrecord-00008-of-00150` | `6bfab54b46fe8f78` | 1350 | 15 | 1350 | `LANE_STATE_UNKNOWN (720)` | 160 |

## Route-Context Scenarios

| Rank | Source | Scenario | Route links | Entry | Exit | Neighbors | Lane speed limits |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `validation.tfrecord-00009-of-00150` | `e5d86b1e27302416` | 572 | 117 | 121 | 334 | 111 |
| 2 | `validation.tfrecord-00010-of-00150` | `5483901d3b74e2ba` | 536 | 140 | 135 | 261 | 121 |
| 3 | `validation.tfrecord-00007-of-00150` | `706fecd25045c8d` | 476 | 93 | 90 | 293 | 84 |
| 4 | `validation.tfrecord-00008-of-00150` | `7912ee9523cb6fd` | 472 | 115 | 115 | 242 | 103 |
| 5 | `validation.tfrecord-00007-of-00150` | `7fc449ae179c29ac` | 471 | 88 | 103 | 280 | 95 |
| 6 | `validation.tfrecord-00007-of-00150` | `8cad75133febe930` | 453 | 105 | 103 | 245 | 98 |
| 7 | `validation.tfrecord-00009-of-00150` | `48b920063c9f98cc` | 441 | 117 | 115 | 209 | 102 |
| 8 | `validation.tfrecord-00008-of-00150` | `8d4ff03a0b364739` | 440 | 100 | 100 | 240 | 99 |
| 9 | `validation.tfrecord-00010-of-00150` | `5c49e681a66c720` | 435 | 110 | 98 | 227 | 95 |
| 10 | `validation.tfrecord-00009-of-00150` | `69d3a2bd18586899` | 435 | 94 | 102 | 239 | 87 |

## Interpretation

- Map and signal context are coverage signals for evaluation design, not proof that a baseline understands right-of-way.
- Route-context counts are lane-graph hints from entry, exit, and neighbor relationships; ScenarioLens does not infer a route plan yet.
- Traffic-signal counts are parsed from public Waymo Motion dynamic-map lane states. This report does not validate signal label quality.
- The useful next step is to join these context summaries back to baseline failures so hard scenarios can be grouped by map, signal, and route evidence.
