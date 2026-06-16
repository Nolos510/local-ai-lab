"""Inline SVG icons for the dependency-free dashboard.

Icon paths are from Tabler Icons v3.26.0, MIT licensed:
https://github.com/tabler/tabler-icons
"""

from __future__ import annotations

from html import escape


def _path(d: str) -> str:
    return f'<path d="{d}" />'


ICONS: dict[str, tuple[str, ...]] = {
    "ti-archive": (
        _path("M3 4m0 2a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v0a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2z"),
        _path("M5 8v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-10"),
        _path("M10 12l4 0"),
    ),
    "ti-brand-github": (
        _path(
            "M9 19c-4.3 1.4 -4.3 -2.5 -6 -3m12 5v-3.5c0 -1 .1 -1.4 "
            "-.5 -2c2.8 -.3 5.5 -1.4 5.5 -6a4.6 4.6 0 0 0 -1.3 -3.2a4.2 "
            "4.2 0 0 0 -.1 -3.2s-1.1 -.3 -3.5 1.3a12.3 12.3 0 0 0 -6.2 "
            "0c-2.4 -1.6 -3.5 -1.3 -3.5 -1.3a4.2 4.2 0 0 0 -.1 3.2a4.6 "
            "4.6 0 0 0 -1.3 3.2c0 4.6 2.7 5.7 5.5 6c-.6 .6 -.6 1.2 "
            "-.5 2v3.5"
        ),
    ),
    "ti-chart-bar": (
        _path("M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z"),
        _path("M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z"),
        _path("M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z"),
        _path("M4 20h14"),
    ),
    "ti-chart-line": (_path("M4 19l16 0"), _path("M4 15l4 -6l4 2l4 -5l4 4")),
    "ti-checkup-list": (
        _path("M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2"),
        _path("M9 3m0 2a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v0a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2z"),
        _path("M9 14h.01"),
        _path("M9 17h.01"),
        _path("M12 16l1 1l3 -3"),
    ),
    "ti-circle": (_path("M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"),),
    "ti-circle-check": (
        _path("M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"),
        _path("M9 12l2 2l4 -4"),
    ),
    "ti-cube": (
        _path(
            "M21 16.008v-8.018a1.98 1.98 0 0 0 -1 -1.717l-7 -4.008a2.016 "
            "2.016 0 0 0 -2 0l-7 4.008c-.619 .355 -1 1.01 -1 1.718v8.018c0 "
            ".709 .381 1.363 1 1.717l7 4.008a2.016 2.016 0 0 0 2 0l7 "
            "-4.008c.619 -.355 1 -1.01 1 -1.718z"
        ),
        _path("M12 22v-10"),
        _path("M12 12l8.73 -5.04"),
        _path("M3.27 6.96l8.73 5.04"),
    ),
    "ti-database": (
        _path("M12 6m-8 0a8 3 0 1 0 16 0a8 3 0 1 0 -16 0"),
        _path("M4 6v6a8 3 0 0 0 16 0v-6"),
        _path("M4 12v6a8 3 0 0 0 16 0v-6"),
    ),
    "ti-device-desktop-analytics": (
        _path("M3 4m0 1a1 1 0 0 1 1 -1h16a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-16a1 1 0 0 1 -1 -1z"),
        _path("M7 20h10"),
        _path("M9 16v4"),
        _path("M15 16v4"),
        _path("M9 12v-4"),
        _path("M12 12v-1"),
        _path("M15 12v-2"),
        _path("M12 12v-1"),
    ),
    "ti-edit": (
        _path("M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1"),
        _path("M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z"),
        _path("M16 5l3 3"),
    ),
    "ti-eye": (
        _path("M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0"),
        _path("M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6"),
    ),
    "ti-file-analytics": (
        _path("M14 3v4a1 1 0 0 0 1 1h4"),
        _path("M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z"),
        _path("M9 17l0 -5"),
        _path("M12 17l0 -1"),
        _path("M15 17l0 -3"),
    ),
    "ti-flame": (
        _path(
            "M12 10.941c2.333 -3.308 .167 -7.823 -1 -8.941c0 3.395 "
            "-2.235 5.299 -3.667 6.706c-1.43 1.408 -2.333 3.621 -2.333 "
            "5.588c0 3.704 3.134 6.706 7 6.706s7 -3.002 7 -6.706c0 "
            "-1.712 -1.232 -4.403 -2.333 -5.588c-2.084 3.353 -3.257 "
            "3.353 -4.667 2.235"
        ),
    ),
    "ti-git-compare": (
        _path("M6 6m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"),
        _path("M18 18m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"),
        _path("M11 6h5a2 2 0 0 1 2 2v8"),
        _path("M14 9l-3 -3l3 -3"),
        _path("M13 18h-5a2 2 0 0 1 -2 -2v-8"),
        _path("M10 15l3 3l-3 3"),
    ),
    "ti-layout-dashboard": (
        _path("M5 4h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1"),
        _path("M5 16h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1"),
        _path("M15 12h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1"),
        _path("M15 4h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1"),
    ),
    "ti-link": (
        _path("M9 15l6 -6"),
        _path("M11 6l.463 -.536a5 5 0 0 1 7.071 7.072l-.534 .464"),
        _path("M13 18l-.397 .534a5.068 5.068 0 0 1 -7.127 0a4.972 4.972 0 0 1 0 -7.071l.524 -.463"),
    ),
    "ti-list-check": (
        _path("M3.5 5.5l1.5 1.5l2.5 -2.5"),
        _path("M3.5 11.5l1.5 1.5l2.5 -2.5"),
        _path("M3.5 17.5l1.5 1.5l2.5 -2.5"),
        _path("M11 6l9 0"),
        _path("M11 12l9 0"),
        _path("M11 18l9 0"),
    ),
    "ti-player-play": (_path("M7 4v16l13 -8z"),),
    "ti-radar": (
        _path("M21 12h-8a1 1 0 1 0 -1 1v8a9 9 0 0 0 9 -9"),
        _path("M16 9a5 5 0 1 0 -7 7"),
        _path("M20.486 9a9 9 0 1 0 -11.482 11.495"),
    ),
    "ti-server": (
        _path("M3 4m0 3a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v2a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3z"),
        _path("M3 12m0 3a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v2a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3z"),
        _path("M7 8l0 .01"),
        _path("M7 16l0 .01"),
    ),
    "ti-shield": (
        _path(
            "M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 "
            "0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3"
        ),
    ),
    "ti-sparkles": (
        _path(
            "M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 "
            "2 0 0 1 -2 2zm0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 "
            "1 -2 -2a2 2 0 0 1 -2 2zm-7 12a6 6 0 0 1 6 -6a6 6 0 0 1 "
            "-6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6z"
        ),
    ),
}


def icon(name: str, *, cls: str = "ti") -> str:
    """Return an inline SVG icon, falling back to a neutral circle."""

    icon_name = name if name in ICONS else "ti-circle"
    classes = f"{cls} {icon_name}".strip()
    body = "".join(ICONS[icon_name])
    return (
        f'<svg class="{escape(classes)}" viewBox="0 0 24 24" aria-hidden="true" '
        'focusable="false" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )
