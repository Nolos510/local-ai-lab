"""Inline SVG chart helpers for the dependency-free dashboard."""

from __future__ import annotations

from html import escape
from math import isfinite

BAR_HEIGHT = 22
BAR_GAP = 10
LABEL_WIDTH = 270
VALUE_WIDTH = 110
PLOT_WIDTH = 600
PADDING_X = 16
PADDING_Y = 16
PLACEHOLDER_HEIGHT = 72
BAR_GRADIENT_ID = "chart-bar-gradient"
AVG_LABEL_CHAR_WIDTH = 8.8
LABEL_PADDING = 24
SCATTER_PLOT_LEFT = 84
SCATTER_PLOT_TOP = 24
SCATTER_PLOT_RIGHT = 744
SCATTER_PLOT_BOTTOM = 384
SCATTER_LEGEND_X = 780
SCATTER_MIN_RADIUS = 6
SCATTER_MAX_RADIUS = 22
SCATTER_LEGEND_ROW_HEIGHT = 30


def _coerce_value(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return max(0.0, number)


def _format_value(value: float, value_format: str) -> str:
    try:
        return value_format.format(value)
    except (IndexError, KeyError, ValueError):
        return str(value)


def _resolved_label_width(labels: list[str], minimum_width: int) -> int:
    if not labels:
        return minimum_width
    natural_width = int(max(len(label) for label in labels) * AVG_LABEL_CHAR_WIDTH) + LABEL_PADDING
    return max(minimum_width, natural_width)


def _finite_number(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def efficiency(tokens_per_sec: object, ram_usage_gb: object) -> float | None:
    """Return throughput per GB of peak RAM when both inputs are usable."""

    throughput = _finite_number(tokens_per_sec)
    peak_ram = _finite_number(ram_usage_gb)
    if throughput is None or throughput < 0 or peak_ram is None or peak_ram <= 0:
        return None
    return throughput / peak_ram


def placeholder(message: str = "No data yet") -> str:
    """Return a small, valid SVG placeholder."""

    return (
        f'<svg class="chart chart-empty" viewBox="0 0 1000 {PLACEHOLDER_HEIGHT}" '
        'role="img" aria-label="No chart data available">'
        '<text class="chart-empty-text" x="500" y="40" text-anchor="middle">'
        f"{escape(message)}</text>"
        "</svg>"
    )


def horizontal_bars(
    items: list[tuple[str, object]],
    *,
    value_format: str = "{:.1f}",
    max_value: float | None = None,
    label_width: int = LABEL_WIDTH,
    title: str = "Chart",
    empty_message: str = "No data yet",
) -> str:
    """Render labeled horizontal bars as an inline SVG string."""

    values: list[tuple[str, float]] = []
    for label, value in items:
        number = _coerce_value(value)
        if number is not None:
            values.append((label, number))

    computed_max = _coerce_value(max_value) if max_value is not None else None
    scale_max = computed_max or (max((value for _, value in values), default=0.0))
    if not values or scale_max <= 0:
        return placeholder(empty_message)

    labels = [str(label) for label, _ in values]
    resolved_label_width = _resolved_label_width(labels, label_width)
    row_height = BAR_HEIGHT + BAR_GAP
    height = PADDING_Y * 2 + len(values) * row_height - BAR_GAP
    width = PADDING_X * 2 + resolved_label_width + PLOT_WIDTH + VALUE_WIDTH
    plot_x = PADDING_X + resolved_label_width
    value_x = plot_x + PLOT_WIDTH + 16
    parts = [
        (
            f'<svg class="chart chart-bars" viewBox="0 0 {width} {height}" '
            f'style="min-width:{width}px" role="img" aria-label="{escape(title)}">'
        ),
        "<defs>"
        f'<linearGradient id="{BAR_GRADIENT_ID}" x1="0%" y1="0%" x2="100%" y2="0%">'
        '<stop offset="0%" stop-color="#8b7bff"></stop>'
        '<stop offset="100%" stop-color="#2ad4ee"></stop>'
        "</linearGradient>"
        "</defs>",
    ]

    for index, (label, value) in enumerate(values):
        y = PADDING_Y + index * row_height
        bar_width = round((min(value, scale_max) / scale_max) * PLOT_WIDTH, 2)
        label_text = str(label)
        parts.append(
            f'<text class="chart-label" x="{PADDING_X}" y="{y + 15}">'
            f"{escape(label_text)}</text>"
        )
        parts.append(
            f'<line class="chart-gridline" x1="{plot_x}" y1="{y + BAR_HEIGHT}" '
            f'x2="{plot_x + PLOT_WIDTH}" y2="{y + BAR_HEIGHT}"></line>'
        )
        parts.append(
            f'<rect class="chart-bar" x="{plot_x}" y="{y}" width="{bar_width}" '
            f'height="{BAR_HEIGHT}" rx="4" fill="url(#{BAR_GRADIENT_ID})"></rect>'
        )
        parts.append(
            f'<text class="chart-value" x="{value_x}" y="{y + 15}">'
            f"{escape(_format_value(value, value_format))}</text>"
        )

    parts.append("</svg>")
    return "".join(parts)


def scatter(
    items: list[tuple[str, object, object, object]],
    *,
    title: str = "Scatter chart",
    empty_message: str = "No data yet",
) -> str:
    """Render a bounded scatter where each item is label, x, y, and bubble value."""

    values: list[tuple[str, float, float, float]] = []
    for label, x_value, y_value, bubble_value in items:
        x_number = _finite_number(x_value)
        y_number = _finite_number(y_value)
        bubble_number = _finite_number(bubble_value)
        if (
            x_number is None
            or x_number < 0
            or y_number is None
            or y_number < 0
            or bubble_number is None
            or bubble_number <= 0
        ):
            continue
        values.append((str(label), x_number, y_number, bubble_number))

    if not values:
        return placeholder(empty_message)

    max_x = max(1.0, max(value[1] for value in values))
    max_y = max(100.0, max(value[2] for value in values))
    max_bubble = max(value[3] for value in values)
    plot_width = SCATTER_PLOT_RIGHT - SCATTER_PLOT_LEFT
    plot_height = SCATTER_PLOT_BOTTOM - SCATTER_PLOT_TOP
    center_width = plot_width - 2 * SCATTER_MAX_RADIUS
    center_height = plot_height - 2 * SCATTER_MAX_RADIUS
    legend_width = max(
        320,
        int(max(len(label) for label, _, _, _ in values) * AVG_LABEL_CHAR_WIDTH) + 190,
    )
    width = SCATTER_LEGEND_X + legend_width + PADDING_X
    height = max(
        SCATTER_PLOT_BOTTOM + 68,
        SCATTER_PLOT_TOP + len(values) * SCATTER_LEGEND_ROW_HEIGHT + 38,
    )
    parts = [
        (
            f'<svg class="chart chart-scatter" viewBox="0 0 {width} {height}" '
            f'style="min-width:{width}px" role="img" aria-label="{escape(title)}">'
        )
    ]

    for tick in range(5):
        fraction = tick / 4
        x = round(SCATTER_PLOT_LEFT + fraction * plot_width, 2)
        y = round(SCATTER_PLOT_BOTTOM - fraction * plot_height, 2)
        parts.append(
            f'<line class="chart-gridline" x1="{x}" y1="{SCATTER_PLOT_TOP}" '
            f'x2="{x}" y2="{SCATTER_PLOT_BOTTOM}"></line>'
        )
        parts.append(
            f'<line class="chart-gridline" x1="{SCATTER_PLOT_LEFT}" y1="{y}" '
            f'x2="{SCATTER_PLOT_RIGHT}" y2="{y}"></line>'
        )
        parts.append(
            f'<text class="chart-tick" x="{x}" y="{SCATTER_PLOT_BOTTOM + 22}" '
            f'text-anchor="middle">{max_x * fraction:.1f}</text>'
        )
        parts.append(
            f'<text class="chart-tick" x="{SCATTER_PLOT_LEFT - 12}" y="{y + 5}" '
            f'text-anchor="end">{max_y * fraction:.1f}</text>'
        )

    parts.append(
        f'<text class="chart-axis-label" x="{(SCATTER_PLOT_LEFT + SCATTER_PLOT_RIGHT) / 2}" '
        f'y="{SCATTER_PLOT_BOTTOM + 48}" text-anchor="middle">Tokens / sec</text>'
    )
    y_center = (SCATTER_PLOT_TOP + SCATTER_PLOT_BOTTOM) / 2
    parts.append(
        f'<text class="chart-axis-label" x="18" y="{y_center}" text-anchor="middle" '
        f'transform="rotate(-90 18 {y_center})">Confirmed total score</text>'
    )
    parts.append(
        f'<text class="chart-axis-label" x="{SCATTER_LEGEND_X}" y="{SCATTER_PLOT_TOP}" '
        'dominant-baseline="hanging">Models · bubble radius encodes peak RAM GB</text>'
    )

    for index, (label, x_value, y_value, bubble_value) in enumerate(values):
        radius = SCATTER_MIN_RADIUS + (
            bubble_value / max_bubble * (SCATTER_MAX_RADIUS - SCATTER_MIN_RADIUS)
        )
        cx = SCATTER_PLOT_LEFT + SCATTER_MAX_RADIUS + (x_value / max_x) * center_width
        cy = SCATTER_PLOT_BOTTOM - SCATTER_MAX_RADIUS - (y_value / max_y) * center_height
        cx = round(cx, 2)
        cy = round(cy, 2)
        radius = round(radius, 2)
        safe_label = escape(label)
        tooltip = escape(
            f"{label}: {x_value:.1f} tokens/sec, {y_value:.2f} confirmed score, "
            f"{bubble_value:.1f} GB peak RAM"
        )
        legend_y = SCATTER_PLOT_TOP + 34 + index * SCATTER_LEGEND_ROW_HEIGHT
        parts.append(
            f'<circle class="chart-point" cx="{cx}" cy="{cy}" r="{radius}">'
            f"<title>{tooltip}</title></circle>"
        )
        parts.append(
            f'<text class="chart-legend-label" x="{SCATTER_LEGEND_X}" y="{legend_y}">'
            f"{safe_label}</text>"
        )
        parts.append(
            f'<text class="chart-legend-value" x="{width - PADDING_X}" y="{legend_y}" '
            f'text-anchor="end">{x_value:.1f} tok/s · {y_value:.2f} score · '
            f"{bubble_value:.1f} GB</text>"
        )

    parts.append("</svg>")
    return "".join(parts)
