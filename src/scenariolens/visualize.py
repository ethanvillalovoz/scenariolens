from __future__ import annotations

from html import escape
from math import inf

from scenariolens.metrics import score_scenario
from scenariolens.schema import AgentTrack, Scenario, State
from scenariolens.taxonomy import infer_tags

AGENT_COLORS = {
    "vehicle": "#2563eb",
    "pedestrian": "#dc2626",
    "cyclist": "#16a34a",
    "unknown": "#6b7280",
}

BACKGROUND = "#f8fafc"
GRID = "#dbe3ee"
INK = "#0f172a"


def scenario_bounds(scenario: Scenario) -> tuple[float, float, float, float]:
    """Return min_x, min_y, max_x, max_y for all states in a scenario."""

    min_x = inf
    min_y = inf
    max_x = -inf
    max_y = -inf

    for track in scenario.tracks:
        for state in track.states:
            min_x = min(min_x, state.x)
            min_y = min(min_y, state.y)
            max_x = max(max_x, state.x)
            max_y = max(max_y, state.y)

    if min_x == inf:
        return (0.0, 0.0, 1.0, 1.0)

    if min_x == max_x:
        min_x -= 1.0
        max_x += 1.0
    if min_y == max_y:
        min_y -= 1.0
        max_y += 1.0

    return (min_x, min_y, max_x, max_y)


def scenario_svg(
    scenario: Scenario,
    width: int = 920,
    height: int = 640,
    padding: int = 56,
) -> str:
    """Render a scenario as a standalone SVG string."""

    min_x, min_y, max_x, max_y = scenario_bounds(scenario)
    world_width = max_x - min_x
    world_height = max_y - min_y
    plot_width = width - (padding * 2)
    plot_height = height - (padding * 2)
    scale = min(plot_width / world_width, plot_height / world_height)
    x_offset = (width - (world_width * scale)) / 2
    y_offset = (height - (world_height * scale)) / 2

    def project(state: State) -> tuple[float, float]:
        x = x_offset + ((state.x - min_x) * scale)
        y = height - (y_offset + ((state.y - min_y) * scale))
        return (x, y)

    score = score_scenario(scenario)
    tags = infer_tags(scenario)
    elements = [
        _svg_header(width, height),
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{BACKGROUND}" />',
        _grid(width, height, padding),
        _title(scenario.scenario_id, score.interaction_score, tags),
        _legend(scenario),
    ]

    for track in scenario.tracks:
        elements.append(_track_path(track, project, scenario.ego_track_id))

    elements.append("</svg>")
    return "\n".join(elements) + "\n"


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img">'
    )


def _grid(width: int, height: int, padding: int) -> str:
    lines: list[str] = []
    for x in range(padding, width - padding + 1, 80):
        lines.append(
            f'<line x1="{x}" y1="{padding}" x2="{x}" y2="{height - padding}" '
            f'stroke="{GRID}" stroke-width="1" />'
        )
    for y in range(padding, height - padding + 1, 80):
        lines.append(
            f'<line x1="{padding}" y1="{y}" x2="{width - padding}" y2="{y}" '
            f'stroke="{GRID}" stroke-width="1" />'
        )
    return "\n".join(lines)


def _title(scenario_id: str, score: float, tags: tuple[str, ...]) -> str:
    tag_text = ", ".join(tags) if tags else "untagged"
    return "\n".join(
        [
            f'<text x="56" y="34" fill="{INK}" font-size="20" '
            f'font-family="Arial, sans-serif" font-weight="700">{escape(scenario_id)}</text>',
            f'<text x="56" y="56" fill="#475569" font-size="13" '
            f'font-family="Arial, sans-serif">score {score:.3f} | {escape(tag_text)}</text>',
        ]
    )


def _legend(scenario: Scenario) -> str:
    present_types = tuple(
        agent_type
        for agent_type in ("vehicle", "pedestrian", "cyclist", "unknown")
        if any(track.agent_type == agent_type for track in scenario.tracks)
    )
    x = 56
    y = 608
    pieces = []
    for index, agent_type in enumerate(present_types):
        item_x = x + (index * 138)
        color = AGENT_COLORS[agent_type]
        pieces.extend(
            [
                f'<circle cx="{item_x}" cy="{y}" r="6" fill="{color}" />',
                f'<text x="{item_x + 12}" y="{y + 4}" fill="#334155" font-size="12" '
                f'font-family="Arial, sans-serif">{agent_type}</text>',
            ]
        )
    return "\n".join(pieces)


def _track_path(
    track: AgentTrack,
    project,
    ego_track_id: str | None,
) -> str:
    points = [project(state) for state in track.states]
    color = AGENT_COLORS.get(track.agent_type, AGENT_COLORS["unknown"])
    stroke_width = 4 if track.agent_id == ego_track_id else 3
    opacity = "1.0" if track.agent_id == ego_track_id else "0.86"
    point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    label_x = end_x + 8
    label_y = end_y - 8
    label = escape(track.agent_id)

    return "\n".join(
        [
            f'<polyline points="{point_text}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke_width}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{opacity}" />',
            f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="4" fill="{color}" opacity="0.45" />',
            f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="6" fill="{color}" />',
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" fill="{INK}" font-size="12" '
            f'font-family="Arial, sans-serif">{label}</text>',
        ]
    )

