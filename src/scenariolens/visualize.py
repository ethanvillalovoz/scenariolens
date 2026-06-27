from __future__ import annotations

from html import escape
from math import hypot, inf

from scenariolens.metrics import score_scenario, scoring_context
from scenariolens.schema import AgentTrack, Scenario, ScenarioScore, State
from scenariolens.taxonomy import infer_tags

AGENT_COLORS = {
    "vehicle": "#2563eb",
    "pedestrian": "#dc2626",
    "cyclist": "#16a34a",
    "unknown": "#6b7280",
}
AGENT_LABELS = {
    "vehicle": "Vehicle",
    "pedestrian": "Pedestrian",
    "cyclist": "Cyclist",
    "unknown": "Unknown",
}

BACKGROUND = "#f8fafc"
CANVAS = "#f9fbfd"
GRID = "#d7e1ee"
INK = "#0f172a"
MUTED = "#64748b"
ROAD = "#e4eaf2"
ROAD_EDGE = "#c7d3e1"
LANE_MARK = "#ffffff"
CONFLICT = "#f59e0b"
MAP_LANE = "#94a3b8"
MAP_EDGE = "#64748b"
MAP_POLYGON = "#e0f2fe"
MAX_TRACK_LABELS = 10

PlotRect = tuple[float, float, float, float]


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
    for x, y in _scenario_map_points(scenario):
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

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

    score = score_scenario(scenario)
    display_scenario = _display_scenario(scenario)
    raw_min_x, raw_min_y, raw_max_x, raw_max_y = scenario_bounds(display_scenario)
    raw_world_width = raw_max_x - raw_min_x
    raw_world_height = raw_max_y - raw_min_y
    context_pad = max(max(raw_world_width, raw_world_height) * 0.16, 3.0)
    min_x = raw_min_x - context_pad
    min_y = raw_min_y - context_pad
    max_x = raw_max_x + context_pad
    max_y = raw_max_y + context_pad
    world_width = max_x - min_x
    world_height = max_y - min_y
    plot: PlotRect = (
        float(padding),
        84.0,
        float(width - (padding * 2)),
        float(height - 166),
    )
    plot_x, plot_y, plot_width, plot_height = plot
    scale = min(plot_width / world_width, plot_height / world_height)
    x_offset = plot_x + ((plot_width - (world_width * scale)) / 2)
    y_offset = plot_y + ((plot_height - (world_height * scale)) / 2)

    def project_xy(x_value: float, y_value: float) -> tuple[float, float]:
        x = x_offset + ((x_value - min_x) * scale)
        y = plot_y + plot_height - ((y_value - min_y) * scale) - (y_offset - plot_y)
        return (x, y)

    def project(state: State) -> tuple[float, float]:
        return project_xy(state.x, state.y)

    tags = infer_tags(scenario)
    label_ids = _label_track_ids(display_scenario)
    elements = [
        _svg_header(width, height),
        _accessibility_metadata(scenario, score, tags),
        _defs(plot),
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{BACKGROUND}" />',
        _title(scenario, score, tags, width),
        _plot_background(plot),
        f'<g clip-path="url(#scenario-plot-clip)">',
        _grid(plot),
        _context_layer(
            display_scenario,
            raw_bounds=(raw_min_x, raw_min_y, raw_max_x, raw_max_y),
            world_bounds=(min_x, min_y, max_x, max_y),
            project_xy=project_xy,
            tags=tags,
        ),
        _closest_interaction_marker(display_scenario, project_xy),
    ]

    for track in display_scenario.tracks:
        elements.append(
            _track_path(
                track,
                project,
                scenario.ego_track_id,
                plot,
                show_label=track.agent_id in label_ids,
            )
        )

    elements.extend(
        [
            "</g>",
            _legend(display_scenario, height),
            "</svg>",
        ]
    )
    return "\n".join(elements) + "\n"


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img">'
    )


def _accessibility_metadata(
    scenario: Scenario,
    score: ScenarioScore,
    tags: tuple[str, ...],
) -> str:
    tag_text = ", ".join(tags) if tags else "untagged"
    agent_text = _agent_count_text(score)
    return "\n".join(
        [
            f"<title>{escape(scenario.scenario_id)} trajectory preview</title>",
            (
                "<desc>"
                f"Scenario {escape(scenario.scenario_id)} from {escape(scenario.source)}. "
                f"Score {score.interaction_score:.3f}. {escape(agent_text)}. "
                f"Tags: {escape(tag_text)}."
                "</desc>"
            ),
        ]
    )


def _defs(plot: PlotRect) -> str:
    plot_x, plot_y, plot_width, plot_height = plot
    return "\n".join(
        [
            "<defs>",
            f'<clipPath id="scenario-plot-clip"><rect x="{plot_x:.0f}" y="{plot_y:.0f}" '
            f'width="{plot_width:.0f}" height="{plot_height:.0f}" rx="10" /></clipPath>',
            "</defs>",
        ]
    )


def _plot_background(plot: PlotRect) -> str:
    plot_x, plot_y, plot_width, plot_height = plot
    return (
        f'<rect x="{plot_x:.0f}" y="{plot_y:.0f}" width="{plot_width:.0f}" '
        f'height="{plot_height:.0f}" rx="10" fill="{CANVAS}" '
        f'stroke="#d8e2ee" stroke-width="1.2" />'
    )


def _grid(plot: PlotRect) -> str:
    plot_x, plot_y, plot_width, plot_height = plot
    lines: list[str] = []
    left = int(plot_x)
    top = int(plot_y)
    right = int(plot_x + plot_width)
    bottom = int(plot_y + plot_height)
    for x in range(left + 64, right, 64):
        lines.append(
            f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" '
            f'stroke="{GRID}" stroke-width="1" opacity="0.52" />'
        )
    for y in range(top + 64, bottom, 64):
        lines.append(
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" '
            f'stroke="{GRID}" stroke-width="1" opacity="0.52" />'
        )
    return "\n".join(lines)


def _title(
    scenario: Scenario,
    score: ScenarioScore,
    tags: tuple[str, ...],
    width: int,
) -> str:
    visible_tags = tuple(_humanize_label(tag) for tag in tags[:3])
    if len(tags) > 3:
        visible_tags = (*visible_tags, f"+{len(tags) - 3} tags")
    tag_text = " / ".join(visible_tags) if visible_tags else "Untagged"
    label = _humanize_label(scenario.scenario_id)
    source_label = _compact_label(scenario.source, max_length=34)
    subtitle = f"score {score.interaction_score:.2f} / {_agent_count_text(score)} / {tag_text}"
    return "\n".join(
        [
            f'<text x="56" y="36" fill="{INK}" font-size="22" '
            f'font-family="Inter, Arial, sans-serif" font-weight="800">{escape(label)}</text>',
            f'<text x="56" y="60" fill="{MUTED}" font-size="13" '
            f'font-family="Inter, Arial, sans-serif" font-weight="650">{escape(subtitle)}</text>',
            f'<text x="{width - 56}" y="38" fill="{MUTED}" font-size="12" '
            f'font-family="Inter, Arial, sans-serif" text-anchor="end">'
            f'{escape(source_label)}</text>',
        ]
    )


def _legend(scenario: Scenario, height: int) -> str:
    present_types = tuple(
        agent_type
        for agent_type in ("vehicle", "pedestrian", "cyclist", "unknown")
        if any(track.agent_type == agent_type for track in scenario.tracks)
    )
    x = 56
    y = height - 40
    pieces = []
    for agent_type in present_types:
        color = AGENT_COLORS[agent_type]
        label = AGENT_LABELS[agent_type]
        item_width = 92 + (len(label) * 4)
        pieces.extend(
            [
                f'<rect x="{x}" y="{y - 15}" width="{item_width}" height="30" rx="15" '
                f'fill="#ffffff" stroke="#d8e2ee" />',
                f'<circle cx="{x + 18}" cy="{y}" r="6" fill="{color}" />',
                f'<text x="{x + 32}" y="{y + 4}" fill="#334155" font-size="12" '
                f'font-family="Inter, Arial, sans-serif" font-weight="700">{label}</text>',
            ]
        )
        x += item_width + 10
    pieces.extend(
        [
            f'<circle cx="{x + 18}" cy="{y}" r="5" fill="#ffffff" '
            f'stroke="{INK}" stroke-width="2" />',
            f'<circle cx="{x + 84}" cy="{y}" r="6" fill="{INK}" />',
            f'<text x="{x + 30}" y="{y + 4}" fill="{MUTED}" font-size="12" '
            f'font-family="Inter, Arial, sans-serif" font-weight="700">start</text>',
            f'<text x="{x + 96}" y="{y + 4}" fill="{MUTED}" font-size="12" '
            f'font-family="Inter, Arial, sans-serif" font-weight="700">latest</text>',
        ]
    )
    return "\n".join(pieces)


def _track_path(
    track: AgentTrack,
    project,
    ego_track_id: str | None,
    plot: PlotRect,
    show_label: bool = True,
) -> str:
    if not track.states:
        return ""

    points = [project(state) for state in track.states]
    color = AGENT_COLORS.get(track.agent_type, AGENT_COLORS["unknown"])
    is_ego = track.agent_id == ego_track_id
    stroke_width = 6 if is_ego else 4
    opacity = "1.0" if is_ego else "0.92"
    point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    label = "ego" if is_ego else track.agent_id

    elements = [
        f'<g class="track track-{track.agent_type}">',
        f'<polyline points="{point_text}" fill="none" stroke="#ffffff" '
        f'stroke-width="{stroke_width + 5}" stroke-linecap="round" '
        f'stroke-linejoin="round" opacity="0.78" />',
        f'<polyline points="{point_text}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round" opacity="{opacity}" />',
        f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="6" fill="#ffffff" '
        f'stroke="{color}" stroke-width="2.5" />',
        f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="8" fill="{color}" '
        f'stroke="#ffffff" stroke-width="2.5" />',
    ]
    if show_label:
        elements.append(_label_group(label, end_x, end_y, color, plot))
    elements.append("</g>")
    return "\n".join(elements)


def _road_context(
    raw_bounds: tuple[float, float, float, float],
    world_bounds: tuple[float, float, float, float],
    project_xy,
    tags: tuple[str, ...],
) -> str:
    raw_min_x, raw_min_y, raw_max_x, raw_max_y = raw_bounds
    min_x, min_y, max_x, max_y = world_bounds
    center_x = _axis_anchor(raw_min_x, raw_max_x)
    center_y = _axis_anchor(raw_min_y, raw_max_y)
    raw_extent = max(raw_max_x - raw_min_x, raw_max_y - raw_min_y, 1.0)
    road_half_width = min(max(raw_extent * 0.10, 3.6), 6.4)

    horizontal = _world_rect(
        min_x,
        center_y - road_half_width,
        max_x,
        center_y + road_half_width,
        project_xy,
    )
    vertical = _world_rect(
        center_x - road_half_width,
        min_y,
        center_x + road_half_width,
        max_y,
        project_xy,
    )
    center_screen = project_xy(center_x, center_y)
    road_edge_y = project_xy(center_x, center_y + road_half_width)[1]
    edge_offset = abs(road_edge_y - center_screen[1])
    lane_offset = edge_offset / 2

    elements = [
        _rect(horizontal, ROAD, ROAD_EDGE, opacity=0.92),
        _rect(vertical, ROAD, ROAD_EDGE, opacity=0.92),
        _lane_line(
            x1=horizontal[0],
            y1=center_screen[1],
            x2=horizontal[0] + horizontal[2],
            y2=center_screen[1],
        ),
        _lane_line(
            x1=center_screen[0],
            y1=vertical[1],
            x2=center_screen[0],
            y2=vertical[1] + vertical[3],
        ),
        _road_edge_line(
            horizontal[0],
            center_screen[1] - edge_offset,
            horizontal[0] + horizontal[2],
            center_screen[1] - edge_offset,
        ),
        _road_edge_line(
            horizontal[0],
            center_screen[1] + edge_offset,
            horizontal[0] + horizontal[2],
            center_screen[1] + edge_offset,
        ),
        _road_edge_line(
            center_screen[0] - edge_offset,
            vertical[1],
            center_screen[0] - edge_offset,
            vertical[1] + vertical[3],
        ),
        _road_edge_line(
            center_screen[0] + edge_offset,
            vertical[1],
            center_screen[0] + edge_offset,
            vertical[1] + vertical[3],
        ),
        _lane_line(
            x1=horizontal[0],
            y1=center_screen[1] - lane_offset,
            x2=horizontal[0] + horizontal[2],
            y2=center_screen[1] - lane_offset,
            opacity=0.35,
        ),
        _lane_line(
            x1=horizontal[0],
            y1=center_screen[1] + lane_offset,
            x2=horizontal[0] + horizontal[2],
            y2=center_screen[1] + lane_offset,
            opacity=0.35,
        ),
    ]
    if _has_crosswalk(tags):
        elements.append(_crosswalk(center_x, center_y, road_half_width, project_xy))
    return "\n".join(elements)


def _context_layer(
    scenario: Scenario,
    raw_bounds: tuple[float, float, float, float],
    world_bounds: tuple[float, float, float, float],
    project_xy,
    tags: tuple[str, ...],
) -> str:
    map_layer = _waymo_map_layer(scenario, project_xy)
    if map_layer:
        return map_layer
    return _road_context(
        raw_bounds=raw_bounds,
        world_bounds=world_bounds,
        project_xy=project_xy,
        tags=tags,
    )


def _waymo_map_layer(scenario: Scenario, project_xy) -> str:
    features = _map_features(scenario)
    if not features:
        return ""
    polygons: list[str] = []
    polylines: list[str] = []
    for feature in features:
        kind = str(feature.get("kind", ""))
        points = _feature_points(feature)
        if len(points) < 2:
            continue
        if kind in {"crosswalk", "speed_bump", "driveway"} and len(points) >= 3:
            polygons.append(_map_polygon(kind, points, project_xy))
        else:
            polylines.append(_map_polyline(kind, points, project_xy))
    return "\n".join((*polygons, *polylines))


def _map_polygon(kind: str, points: tuple[tuple[float, float], ...], project_xy) -> str:
    screen_points = " ".join(
        f"{x:.2f},{y:.2f}" for x, y in (project_xy(px, py) for px, py in points)
    )
    fill = "#ffffff" if kind == "crosswalk" else MAP_POLYGON
    opacity = "0.78" if kind == "crosswalk" else "0.42"
    return (
        f'<polygon class="map-feature map-{kind}" points="{screen_points}" '
        f'fill="{fill}" stroke="#bae6fd" stroke-width="1.2" opacity="{opacity}" />'
    )


def _map_polyline(kind: str, points: tuple[tuple[float, float], ...], project_xy) -> str:
    screen_points = " ".join(
        f"{x:.2f},{y:.2f}" for x, y in (project_xy(px, py) for px, py in points)
    )
    if kind == "lane":
        stroke = MAP_LANE
        width = "1.4"
        dash = ' stroke-dasharray="10 10"'
        opacity = "0.64"
    elif kind == "road_line":
        stroke = LANE_MARK
        width = "2.2"
        dash = ' stroke-dasharray="18 14"'
        opacity = "0.82"
    else:
        stroke = MAP_EDGE
        width = "2.2"
        dash = ""
        opacity = "0.74"
    return (
        f'<polyline class="map-feature map-{kind}" points="{screen_points}" '
        f'fill="none" stroke="{stroke}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round"{dash} opacity="{opacity}" />'
    )


def _closest_interaction_marker(scenario: Scenario, project_xy) -> str:
    closest = _closest_interaction(scenario)
    if closest is None:
        return ""
    distance, x_value, y_value = closest
    if distance > 8.0:
        return ""
    x, y = project_xy(x_value, y_value)
    radius = max(24.0, min(50.0, 54.0 - (distance * 3.0)))
    return "\n".join(
        [
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
            f'fill="{CONFLICT}" opacity="0.13" />',
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
            f'fill="none" stroke="{CONFLICT}" stroke-width="2" opacity="0.38" />',
        ]
    )


def _closest_interaction(scenario: Scenario) -> tuple[float, float, float] | None:
    states_by_time: dict[float, list[State]] = {}
    for track in scenario.tracks:
        for state in track.states:
            states_by_time.setdefault(round(state.t, 3), []).append(state)

    best: tuple[float, float, float] | None = None
    for states in states_by_time.values():
        for left_index, left in enumerate(states):
            for right in states[left_index + 1 :]:
                distance = hypot(left.x - right.x, left.y - right.y)
                if best is None or distance < best[0]:
                    best = (
                        distance,
                        (left.x + right.x) / 2,
                        (left.y + right.y) / 2,
                    )
    return best


def _world_rect(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    project_xy,
) -> tuple[float, float, float, float]:
    sx1, sy1 = project_xy(x1, y1)
    sx2, sy2 = project_xy(x2, y2)
    left = min(sx1, sx2)
    top = min(sy1, sy2)
    return (left, top, abs(sx2 - sx1), abs(sy2 - sy1))


def _rect(
    rect: tuple[float, float, float, float],
    fill: str,
    stroke: str,
    opacity: float = 1.0,
) -> str:
    x, y, width, height = rect
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="{opacity:.2f}" />'
    )


def _lane_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    opacity: float = 0.88,
) -> str:
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{LANE_MARK}" stroke-width="3" stroke-linecap="round" '
        f'stroke-dasharray="22 18" opacity="{opacity:.2f}" />'
    )


def _road_edge_line(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{ROAD_EDGE}" stroke-width="1.5" opacity="0.72" />'
    )


def _crosswalk(center_x: float, center_y: float, road_half_width: float, project_xy) -> str:
    stripe_width = 0.32
    stripe_gap = 0.74
    x_start = center_x + road_half_width + 0.7
    stripes: list[str] = []
    for index in range(7):
        x = x_start + (index * stripe_gap)
        rect = _world_rect(
            x - stripe_width,
            center_y - road_half_width + 0.35,
            x + stripe_width,
            center_y + road_half_width - 0.35,
            project_xy,
        )
        stripes.append(_rect(rect, "#ffffff", "#ffffff", opacity=0.78))
    return "\n".join(stripes)


def _label_group(
    label: str,
    anchor_x: float,
    anchor_y: float,
    color: str,
    plot: PlotRect,
) -> str:
    plot_x, plot_y, plot_width, plot_height = plot
    safe_label = escape(label)
    width = max(42.0, (len(label) * 7.4) + 22.0)
    height = 24.0
    x = anchor_x + 12.0
    if x + width > plot_x + plot_width - 8:
        x = anchor_x - width - 12.0
    y = anchor_y - height - 10.0
    if y < plot_y + 8:
        y = anchor_y + 12.0

    x = _clamp(x, plot_x + 8, plot_x + plot_width - width - 8)
    y = _clamp(y, plot_y + 8, plot_y + plot_height - height - 8)
    return "\n".join(
        [
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" '
            f'rx="12" fill="#ffffff" stroke="#d8e2ee" opacity="0.96" />',
            f'<rect x="{x + 7:.2f}" y="{y + 7:.2f}" width="4" height="10" '
            f'rx="2" fill="{color}" />',
            f'<text x="{x + 17:.2f}" y="{y + 16.5:.2f}" fill="{INK}" font-size="12" '
            f'font-family="Inter, Arial, sans-serif" font-weight="750">{safe_label}</text>',
        ]
    )


def _axis_anchor(min_value: float, max_value: float) -> float:
    if min_value <= 0 <= max_value:
        return 0.0
    return (min_value + max_value) / 2


def _has_crosswalk(tags: tuple[str, ...]) -> bool:
    return bool(
        {"pedestrian_crossing", "vulnerable_road_user", "cyclist_interaction"}
        .intersection(tags)
    )


def _scenario_map_points(scenario: Scenario) -> tuple[tuple[float, float], ...]:
    return tuple(
        point
        for feature in _map_features(scenario)
        for point in _feature_points(feature)
    )


def _map_features(scenario: Scenario) -> tuple[dict[str, object], ...]:
    value = scenario.metadata.get("waymo_map_features", ())
    if not isinstance(value, list):
        return ()
    return tuple(feature for feature in value if isinstance(feature, dict))


def _feature_points(feature: dict[str, object]) -> tuple[tuple[float, float], ...]:
    raw_points = feature.get("points", ())
    if not isinstance(raw_points, list):
        return ()
    points: list[tuple[float, float]] = []
    for point in raw_points:
        if not isinstance(point, list) or len(point) < 2:
            continue
        try:
            points.append((float(point[0]), float(point[1])))
        except (TypeError, ValueError):
            continue
    return tuple(points)


def _display_scenario(scenario: Scenario) -> Scenario:
    context = scoring_context(scenario)
    tracks = context.tracks if context.tracks else scenario.tracks
    return Scenario(
        scenario_id=scenario.scenario_id,
        tracks=tracks,
        ego_track_id=scenario.ego_track_id,
        tags=scenario.tags,
        source=scenario.source,
        metadata=scenario.metadata,
    )


def _label_track_ids(scenario: Scenario) -> set[str]:
    track_ids = {track.agent_id for track in scenario.tracks}
    priority: list[str] = []
    if scenario.ego_track_id and scenario.ego_track_id in track_ids:
        priority.append(scenario.ego_track_id)
    for key in (
        "waymo_tracks_to_predict_track_ids",
        "waymo_objects_of_interest_track_ids",
    ):
        value = scenario.metadata.get(key, ())
        if isinstance(value, list):
            priority.extend(
                str(track_id) for track_id in value if str(track_id) in track_ids
            )
    priority.extend(
        track.agent_id
        for track in scenario.tracks
        if track.agent_type in {"pedestrian", "cyclist"}
    )
    priority.extend(track.agent_id for track in scenario.tracks)
    return set(dict.fromkeys(priority[:MAX_TRACK_LABELS]))


def _agent_count_text(score: ScenarioScore) -> str:
    if score.scoring_agent_count == score.agent_count:
        return f"{score.agent_count} agents"
    return f"{score.scoring_agent_count} scored of {score.agent_count} agents"


def _humanize_label(value: str) -> str:
    acronyms = {"vru": "VRU", "sdc": "SDC", "ttc": "TTC", "json": "JSON", "csv": "CSV"}
    words = []
    for part in value.replace("-", "_").split("_"):
        words.append(acronyms.get(part.lower(), part.capitalize()))
    return " ".join(words)


def _compact_label(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
