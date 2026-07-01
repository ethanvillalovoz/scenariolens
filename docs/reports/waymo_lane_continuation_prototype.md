# ScenarioLens Lane-Link Continuation Prototype

This report follows the route/intent audit's lane-continuity warning with a small executable prototype. It reloads the audited local scenario, compares constant-velocity, nearest-lane, heading-aware, and lane-link continuation rollouts, then reports whether parsed entry/exit lane links reduce the stable regression.

It is intentionally scoped: this is not route planning, not a default scorer change, not closed-loop simulation, and not a Waymo benchmark claim. Raw Waymo files and local per-case packets stay out of git.

## Scope

- Route/intent audit manifest: `data/processed/waymo_context_route_intent_audit/manifest.json`
- Ready for prototype: True
- Cases evaluated: 1
- Max lane-link hops: 2
- Lane-match threshold: 3.500 m
- Waymo map feature cap: 240
- Raw Waymo files committed: no
- Local lane-link packets committed: no

## Prototype Summary

| Metric | Value |
| --- | ---: |
| Evaluated cases | 1 |
| Evaluated tracks | 1 |
| Tracks using linked lanes | 1 |
| Tracks improved over nearest lane | 1 |
| Tracks still clamped after links | 0 |
| Mean nearest FDE | 110.266 m |
| Mean lane-link FDE | 46.688 m |
| Mean lane-link improvement over nearest | +63.578 m |

## Case Summary

| Rank | Scenario | Tracks | CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link improvement | Main result |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `ef4c5d0e40fdea48` | 1 | 46.688 m | 110.266 m | 110.266 m | 46.688 m | +63.578 m | `lane_link_improvement` |

## `ef4c5d0e40fdea48`

- Case: Context eval seed 5
- Source: `validation.tfrecord-00008-of-00150`
- Primary result: **lane_link_improvement**
- Why: Following parsed lane links reduced FDE versus the clamped nearest-lane rollout.
- Recommended next action: Promote this case into a lane-continuation validation set.
- Local prototype packet: `data/processed/waymo_lane_continuation_prototype/cases/1-context-eval-seed-5-ef4c5d0e40fdea48/lane_continuation_prototype.json`

Track results:

| Track | CV FDE | Nearest FDE | Heading FDE | Lane-link FDE | Link improvement | Feature chain | Before/after remaining | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `755` | 46.688 m | 110.266 m | 110.266 m | 46.688 m | +63.578 m | 144 -> 190 -> 193 | 16.691 m / 115.539 m | `lane_link_improvement` |

Case metrics:

- Constant-velocity FDE: 46.688 m
- Nearest-lane FDE: 110.266 m
- Heading-aware FDE: 110.266 m
- Lane-link FDE: 46.688 m

## Interpretation

- A lane-link improvement supports the audit finding: the nearest-lane failure was partly a lane-continuity artifact.
- A remaining regression does not invalidate the framework; it points to route choice, map topology quality, speed modeling, or richer prediction logic.
- This prototype keeps the default scoring baseline unchanged and treats linked-lane following as a follow-up experiment.
- Public artifacts stay aggregate and diagnostic; local per-case packets and raw Waymo TFRecords remain ignored.
