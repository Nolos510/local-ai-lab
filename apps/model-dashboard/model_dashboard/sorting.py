"""Shared server-side table sorting and sortable-header links."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from urllib.parse import urlencode

SortGetter = Callable[[object], object]
SortColumns = Mapping[str, tuple[SortGetter, str]]


def _query_value(query, key):
    value = (query or {}).get(key, "")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _sort_state(query, columns):
    column = _query_value(query, "sort")
    if column not in columns:
        return "", "asc"
    direction = "desc" if _query_value(query, "dir").lower() == "desc" else "asc"
    return column, direction


def _numeric_sort_value(value):
    if value is None or str(value).strip() in ("", "—"):
        return None
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _text_sort_value(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "—":
        return None
    return text.casefold()


def _sort_rows(rows: Sequence, query, columns: SortColumns):
    """Sort recognized columns while keeping missing values last in either direction."""

    column, direction = _sort_state(query, columns)
    if not column:
        return list(rows)
    getter, value_type = columns[column]
    normalize = _numeric_sort_value if value_type == "number" else _text_sort_value
    present = []
    missing = []
    for row in rows:
        value = normalize(getter(row))
        (missing if value is None else present).append((value, row))
    present.sort(key=lambda item: item[0], reverse=direction == "desc")
    return [row for _, row in present] + [row for _, row in missing]


def _query_pairs(query):
    pairs = []
    for key, value in (query or {}).items():
        if key in ("sort", "dir"):
            continue
        values = value if isinstance(value, (list, tuple)) else (value,)
        for item in values:
            pairs.append((str(key), str(item)))
    return pairs


def _sortable_headers(path, query, headers: Mapping[str, str], fragment=""):
    """Build safe header-link metadata while retaining unrelated query parameters."""

    current_column = _query_value(query, "sort")
    current_direction = (
        "desc" if _query_value(query, "dir").lower() == "desc" else "asc"
    )
    valid_columns = set(headers.values())
    if current_column not in valid_columns:
        current_column = ""
    result = {}
    for label, column in headers.items():
        active = column == current_column
        next_direction = "desc" if active and current_direction == "asc" else "asc"
        query_string = urlencode(
            _query_pairs(query) + [("sort", column), ("dir", next_direction)]
        )
        result[label] = {
            "href": f"{path}?{query_string}{fragment}",
            "direction": current_direction if active else "",
            "next_direction": next_direction,
        }
    return result


__all__ = ("_sort_rows", "_sortable_headers")
