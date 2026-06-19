"""Inline SVG chart helpers for the dependency-free dashboard."""

from __future__ import annotations

from html import escape

BAR_HEIGHT = 22
BAR_GAP = 10
LABEL_WIDTH = 270
VALUE_WIDTH = 110
PLOT_WIDTH = 600
PADDING_X = 16
PADDING_Y = 16
PLACEHOLDER_HEIGHT = 72
BAR_GRADIENT_ID = "chart-bar-gradient"


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
    title: str = "Chart",
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
        return placeholder()

    row_height = BAR_HEIGHT + BAR_GAP
    height = PADDING_Y * 2 + len(values) * row_height - BAR_GAP
    width = PADDING_X * 2 + LABEL_WIDTH + PLOT_WIDTH + VALUE_WIDTH
    plot_x = PADDING_X + LABEL_WIDTH
    value_x = plot_x + PLOT_WIDTH + 16
    parts = [
        (
            f'<svg class="chart chart-bars" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{escape(title)}">'
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
        bar_width = round((value / scale_max) * PLOT_WIDTH, 2)
        parts.append(
            f'<text class="chart-label" x="{PADDING_X}" y="{y + 15}">{escape(str(label))}</text>'
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
