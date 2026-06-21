# Scenario Taxonomy

ScenarioLens uses a small taxonomy to make ranking explainable. The taxonomy is
not meant to be final or safety-certified; it is a compact vocabulary for
finding high-value scenarios in early experiments.

## Tags

| Tag | Meaning | Why It Matters |
| --- | --- | --- |
| `vulnerable_road_user` | A pedestrian or cyclist is present. | VRU behavior is central to urban autonomy safety. |
| `pedestrian_crossing` | A pedestrian crosses or approaches vehicle flow. | Tests yielding, occlusion reasoning, and prediction under uncertainty. |
| `cyclist_interaction` | A cyclist appears near vehicle traffic. | Cyclists can move faster and less predictably than pedestrians. |
| `merge_conflict` | Vehicles negotiate a merge or lane-change pressure. | Requires interaction-aware prediction and planning. |
| `unprotected_turn` | A turn depends on cross traffic or VRU behavior. | Common source of complex right-of-way decisions. |
| `blocked_lane` | A stopped object or obstruction changes the route. | Tests rerouting, yielding, and lane-change pressure. |
| `stopped_vehicle` | A stopped or slow vehicle affects behavior. | Useful for hard-braking and occlusion-adjacent cases. |
| `hard_braking` | An agent slows sharply or must respond quickly. | Highlights reactive planning and following-distance behavior. |
| `close_interaction` | Agents pass within a small spatial margin. | Useful proxy for scenarios worth human review. |
| `dense_multi_agent` | Several agents interact in one local scene. | Tests joint reasoning instead of single-agent prediction. |
| `low_interaction` | Easier baseline scene. | Keeps evaluation sets from only containing extreme cases. |

## Scoring Role

ScenarioLens combines taxonomy weights with lightweight interaction features:

- number of tracked agents,
- number of vulnerable road users,
- minimum same-timestep pairwise distance,
- minimum constant-velocity time-to-collision proxy,
- taxonomy tag weights.

The score is a review-prioritization heuristic. It is useful for ranking and
explaining scenarios, but it should not be interpreted as a certified risk
model.
