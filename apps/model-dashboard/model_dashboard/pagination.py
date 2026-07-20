"""Shared server-side pagination for dashboard list surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import ceil
from urllib.parse import urlencode

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Page:
    items: tuple
    number: int
    page_size: int
    total_items: int
    total_pages: int
    first_item: int
    last_item: int

    @property
    def has_previous(self):
        return self.number > 1

    @property
    def has_next(self):
        return self.number < self.total_pages


def _positive_int(value, fallback):
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _paginate(
    rows,
    query=None,
    *,
    default_page_size=DEFAULT_PAGE_SIZE,
    max_page_size=MAX_PAGE_SIZE,
):
    """Return a bounded, clamped page after callers finish filtering and sorting."""

    page_size = min(
        _positive_int((query or {}).get("page_size", ""), default_page_size),
        max_page_size,
    )
    total_items = len(rows)
    total_pages = max(1, ceil(total_items / page_size))
    number = min(
        _positive_int((query or {}).get("page", ""), 1),
        total_pages,
    )
    start = (number - 1) * page_size
    stop = min(start + page_size, total_items)
    first_item = start + 1 if total_items else 0
    return Page(
        items=tuple(rows[start:stop]),
        number=number,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        first_item=first_item,
        last_item=stop,
    )


def _page_href(path, query, number, page_size):
    pairs = []
    for key, value in (query or {}).items():
        if key in ("page", "page_size"):
            continue
        values = value if isinstance(value, (list, tuple)) else (value,)
        for item in values:
            pairs.append((str(key), str(item)))
    pairs.extend((('page', str(number)), ('page_size', str(page_size))))
    return f"{path}?{urlencode(pairs)}"


def _pagination_controls(path, query, page, *, label):
    """Render prev/next navigation while retaining sort and filter state."""

    previous = (
        '<a class="pagination-link" rel="prev" href="{}">Previous</a>'.format(
            escape(
                _page_href(path, query, page.number - 1, page.page_size),
                quote=True,
            )
        )
        if page.has_previous
        else '<span class="pagination-link disabled" aria-disabled="true">Previous</span>'
    )
    next_link = (
        '<a class="pagination-link" rel="next" href="{}">Next</a>'.format(
            escape(
                _page_href(path, query, page.number + 1, page.page_size),
                quote=True,
            )
        )
        if page.has_next
        else '<span class="pagination-link disabled" aria-disabled="true">Next</span>'
    )
    return (
        f'<nav class="pagination" aria-label="{escape(label, quote=True)}">'
        f'<p class="pagination-status">showing {page.first_item}-{page.last_item} '
        f"of {page.total_items}</p>"
        '<div class="pagination-links">'
        f"{previous}{next_link}"
        "</div></nav>"
    )


__all__ = (
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "Page",
    "_paginate",
    "_page_href",
    "_pagination_controls",
)
