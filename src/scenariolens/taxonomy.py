from __future__ import annotations

from dataclasses import dataclass

from scenariolens.schema import Scenario


@dataclass(frozen=True)
class TagDefinition:
    """Human-readable meaning for a scenario category."""

    tag: str
    label: str
    description: str
    weight: float


TAG_DEFINITIONS: tuple[TagDefinition, ...] = (
    TagDefinition(
        tag="vulnerable_road_user",
        label="Vulnerable road user",
        description="Scenario contains a pedestrian or cyclist.",
        weight=2.0,
    ),
    TagDefinition(
        tag="pedestrian_crossing",
        label="Pedestrian crossing",
        description="Pedestrian trajectory intersects or approaches vehicle flow.",
        weight=3.0,
    ),
    TagDefinition(
        tag="cyclist_interaction",
        label="Cyclist interaction",
        description="Scenario includes a cyclist near vehicle traffic.",
        weight=2.5,
    ),
    TagDefinition(
        tag="merge_conflict",
        label="Merge conflict",
        description="Vehicles negotiate lane merge or lane-change pressure.",
        weight=2.0,
    ),
    TagDefinition(
        tag="unprotected_turn",
        label="Unprotected turn",
        description="A turning vehicle must reason about cross traffic or VRUs.",
        weight=2.5,
    ),
    TagDefinition(
        tag="blocked_lane",
        label="Blocked lane",
        description="A lane obstruction creates rerouting or yielding pressure.",
        weight=2.0,
    ),
    TagDefinition(
        tag="stopped_vehicle",
        label="Stopped vehicle",
        description="A stopped or very slow vehicle affects scene behavior.",
        weight=1.5,
    ),
    TagDefinition(
        tag="hard_braking",
        label="Hard braking",
        description="An agent decelerates sharply or must respond quickly.",
        weight=2.0,
    ),
    TagDefinition(
        tag="close_interaction",
        label="Close interaction",
        description="Two or more agents pass within a small spatial margin.",
        weight=2.0,
    ),
    TagDefinition(
        tag="dense_multi_agent",
        label="Dense multi-agent scene",
        description="Several agents interact in the same local scene.",
        weight=1.5,
    ),
    TagDefinition(
        tag="low_interaction",
        label="Low interaction",
        description="Scenario is useful as an easier baseline comparison.",
        weight=0.0,
    ),
)

TAG_ORDER = tuple(definition.tag for definition in TAG_DEFINITIONS)
TAG_BY_NAME = {definition.tag: definition for definition in TAG_DEFINITIONS}

TAG_ALIASES = {
    "bike": "cyclist_interaction",
    "bicycle": "cyclist_interaction",
    "cyclist": "cyclist_interaction",
    "crossing": "pedestrian_crossing",
    "merge": "merge_conflict",
    "multi_agent": "dense_multi_agent",
    "pedestrian": "vulnerable_road_user",
    "vru": "vulnerable_road_user",
}


def canonical_tag(tag: str) -> str:
    normalized = tag.strip().lower().replace(" ", "_").replace("-", "_")
    return TAG_ALIASES.get(normalized, normalized)


def normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    """Return unique canonical tags in taxonomy order, preserving unknowns last."""

    canonical = {canonical_tag(tag) for tag in tags if tag.strip()}
    ordered = [tag for tag in TAG_ORDER if tag in canonical]
    unknown = sorted(tag for tag in canonical if tag not in TAG_BY_NAME)
    return tuple(ordered + unknown)


def infer_tags(scenario: Scenario) -> tuple[str, ...]:
    """Infer taxonomy tags from lightweight scenario metadata.

    This first milestone keeps inference intentionally conservative. Richer tags
    can be added once real dataset fields are available.
    """

    tags = set(normalize_tags(scenario.tags))
    agent_types = {track.agent_type for track in scenario.tracks}

    if "pedestrian" in agent_types or "cyclist" in agent_types:
        tags.add("vulnerable_road_user")

    if "cyclist" in agent_types:
        tags.add("cyclist_interaction")

    if len(scenario.tracks) >= 4:
        tags.add("dense_multi_agent")

    return normalize_tags(tuple(tags))


def tag_weight(tags: tuple[str, ...]) -> float:
    return round(sum(TAG_BY_NAME[tag].weight for tag in tags if tag in TAG_BY_NAME), 3)

