"""Dashboard shell layout, Midnight Neon CSS, sidebar, and inline script."""

# ruff: noqa: E501

from __future__ import annotations

from html import escape

from .icons import icon as render_icon

NAV_ITEMS = (
    ("/lab", "Lab Dashboard"),
    ("/capability", "Capability"),
    ("/", "Overview"),
    ("/runs", "Model Runs"),
    ("/compare", "Compare Models"),
    ("/inventory", "Installed Models"),
    ("/radar", "Radar Candidates"),
    ("/specialty", "Specialty Models"),
    ("/projects", "Project Radar"),
    ("/storage", "Storage / Install Status"),
    ("/reports", "Reports"),
)

NAV_ICONS = {
    "/lab": "ti-layout-dashboard",
    "/capability": "ti-server",
    "/": "ti-chart-bar",
    "/runs": "ti-player-play",
    "/compare": "ti-git-compare",
    "/inventory": "ti-device-desktop-analytics",
    "/radar": "ti-radar",
    "/specialty": "ti-sparkles",
    "/projects": "ti-brand-github",
    "/storage": "ti-database",
    "/reports": "ti-file-analytics",
}

def _layout(title, current_path, body):
    nav = []
    for path, label in NAV_ITEMS:
        active = " active" if current_path == path else ""
        icon_name = NAV_ICONS.get(path, "ti-circle")
        nav.append(
            f'<a class="nav{active}" href="{path}" data-label="{escape(label)}" title="{escape(label)}">'
            f"{render_icon(icon_name)}"
            f"<span>{escape(label)}</span></a>"
        )
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Local Model Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0a0b12;
      --header: rgba(13, 15, 26, 0.72);
      --panel: rgba(22, 24, 40, 0.55);
      --panel-soft: rgba(255, 255, 255, 0.04);
      --control: #12141f;
      --ink: #e7e9f5;
      --muted: #9498b5;
      --line: rgba(255, 255, 255, 0.09);
      --line-soft: rgba(255, 255, 255, 0.05);
      --accent: #8b7bff;
      --accent-ink: #0a0b12;
      --accent-soft: rgba(139, 123, 255, 0.16);
      --accent-soft-ink: #b9b0ff;
      --accent-2: #2ad4ee;
      --table-head: rgba(255, 255, 255, 0.035);
      --pill-bg: rgba(139, 123, 255, 0.15);
      --pill-ink: #c4bcff;
      --status-confirmed-bg: rgba(52, 211, 153, 0.15);
      --status-confirmed-ink: #6ee7b7;
      --status-draft-bg: rgba(251, 191, 36, 0.15);
      --status-draft-ink: #fcd34d;
      --danger: #fb7185;
      --danger-bg: rgba(251, 113, 133, 0.14);
      --danger-border: rgba(251, 113, 133, 0.45);
      --code-bg: #0d0f1a;
      --code-ink: #e7e9f5;
      --shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
      --accent-grad: linear-gradient(135deg, #8b7bff 0%, #2ad4ee 100%);
      --glow: 0 0 0 1px rgba(139, 123, 255, 0.30), 0 10px 34px rgba(139, 123, 255, 0.22);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.5;
      font-weight: 400;
    }}
    strong {{ font-weight: 500; }}
    header {{
      border-bottom: 0.5px solid var(--line);
      background: var(--header);
    }}
    .topbar {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 22px 20px 16px;
    }}
    h1 {{
      margin: 0 0 16px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
      font-weight: 500;
    }}
    nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .nav {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      color: var(--muted);
      border: 0.5px solid var(--line);
      border-radius: 8px;
      padding: 8px 11px;
      text-decoration: none;
      background: var(--panel-soft);
      font-weight: 500;
      transition: background 150ms ease, color 150ms ease, border-color 150ms ease;
    }}
    .nav .ti {{
      color: var(--accent);
      width: 1em;
      height: 1em;
      display: inline-block;
      vertical-align: -0.125em;
      fill: none;
      stroke: currentColor;
      flex: 0 0 auto;
    }}
    .nav.active {{
      border-color: transparent;
      color: var(--accent-soft-ink);
      background: var(--accent-soft);
    }}
    .nav.active .ti {{
      color: var(--accent-soft-ink);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px 20px 32px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .stat, .panel {{
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
      margin: 0 0 22px;
    }}
    .chart-panel {{
      overflow: hidden;
    }}
    .capability-chart-grid {{
      grid-template-columns: 1fr;
    }}
    .chart-panel-large {{
      display: grid;
      gap: 12px;
      min-height: 250px;
      overflow: visible;
    }}
    .chart-panel-head, .chart-dialog-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .chart-panel-head h2, .chart-dialog-head h2 {{
      margin: 0;
    }}
    .chart-expand {{
      min-height: 34px;
      padding: 6px 10px;
      border-color: var(--line);
      background: var(--panel-soft);
      color: var(--ink);
    }}
    .chart-summary {{
      display: grid;
      gap: 9px;
      min-width: 0;
    }}
    .chart-summary-row {{
      display: grid;
      grid-template-columns: minmax(90px, max-content) minmax(0, 1fr);
      gap: 12px;
      align-items: baseline;
      min-width: 0;
    }}
    .chart-summary-value {{
      color: var(--ink);
      font-size: 24px;
      line-height: 1.1;
      font-weight: 650;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}
    .chart-summary-row span {{
      color: var(--muted);
      min-width: 0;
      overflow-wrap: anywhere;
    }}
    .chart-preview {{
      min-height: 78px;
      overflow-x: auto;
      padding-bottom: 2px;
    }}
    .chart {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .chart-preview .chart {{
      min-width: 860px;
    }}
    .chart-dialog {{
      width: min(980px, calc(100vw - 48px));
      max-height: min(720px, calc(100vh - 48px));
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--control);
      color: var(--ink);
      box-shadow: var(--shadow);
      overflow: auto;
    }}
    .chart-dialog::backdrop {{
      background: rgba(0, 0, 0, 0.64);
      -webkit-backdrop-filter: blur(4px);
      backdrop-filter: blur(4px);
    }}
    .chart-dialog-body {{
      margin: 18px 0;
      overflow-x: auto;
    }}
    .chart-dialog .chart {{
      min-width: 900px;
    }}
    .chart-bar {{
      fill: url(#chart-bar-gradient);
      filter: drop-shadow(0 0 7px rgba(42, 212, 238, 0.25));
    }}
    .chart-label, .chart-value, .chart-empty-text {{
      fill: var(--muted);
      font-size: 14px;
    }}
    .chart-value {{
      fill: var(--ink);
      font-weight: 500;
    }}
    .chart-gridline {{
      stroke: var(--line);
      stroke-width: 1;
    }}
    .stat {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 12px;
      align-items: start;
    }}
    .stat .ti {{
      color: var(--accent);
      width: 1.25em;
      height: 1.25em;
      display: inline-block;
      vertical-align: -0.125em;
      fill: none;
      stroke: currentColor;
      margin-top: 3px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 5px;
    }}
    .stat .value {{
      font-size: 26px;
      font-weight: 500;
      line-height: 1.1;
    }}
    .stat-breakdown {{
      grid-column: span 2;
      min-width: 0;
    }}
    .stat-breakdown > div {{
      min-width: 0;
    }}
    .stat-metrics {{
      display: grid;
      grid-template-columns: repeat(2, minmax(74px, 1fr));
      gap: 10px;
      align-items: stretch;
    }}
    .stat-metrics span {{
      display: grid;
      gap: 3px;
      min-width: 0;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel-soft);
    }}
    .stat-metrics strong {{
      color: var(--ink);
      font-size: 24px;
      line-height: 1;
      font-weight: 650;
      font-variant-numeric: tabular-nums;
    }}
    .stat-metrics em {{
      color: var(--muted);
      font-size: 11px;
      line-height: 1.1;
      font-style: normal;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      white-space: nowrap;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(140px, 1fr)) auto;
      gap: 12px;
      align-items: end;
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      margin: 0 0 18px;
      box-shadow: var(--shadow);
    }}
    .filters-compact {{
      grid-template-columns: minmax(220px, 2fr) repeat(2, minmax(140px, 1fr)) auto;
    }}
    .filters-wide {{
      grid-template-columns: minmax(220px, 2fr) repeat(4, minmax(140px, 1fr)) auto;
    }}
    .field label {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
      margin: 0 0 6px;
    }}
    input, select {{
      width: 100%;
      min-height: 38px;
      border: 0.5px solid var(--line);
      border-radius: 8px;
      background: var(--control);
      color: var(--ink);
      font: inherit;
      padding: 8px 10px;
    }}
    button {{
      min-height: 38px;
      border: 0.5px solid var(--accent);
      border-radius: 8px;
      background: var(--accent);
      color: var(--accent-ink);
      font: inherit;
      font-weight: 500;
      padding: 8px 13px;
      cursor: pointer;
    }}
    button:disabled {{
      border-color: var(--line);
      background: var(--panel-soft);
      color: var(--muted);
      cursor: not-allowed;
    }}
    button.danger {{
      border-color: var(--danger-border);
      background: var(--danger-bg);
      color: var(--danger);
    }}
    button.danger-secondary {{
      border-color: var(--danger-border);
      background: transparent;
      color: var(--danger);
    }}
    button.danger:hover, button.danger-secondary:hover {{
      box-shadow: 0 0 0 1px var(--danger-border), 0 10px 26px rgba(251, 113, 133, 0.15);
    }}
    .inline-form {{
      display: grid;
      gap: 8px;
      align-items: start;
    }}
    .filter-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .clear-link {{
      color: var(--muted);
      font-size: 13px;
      text-decoration: none;
    }}
    h2 {{
      font-size: 20px;
      margin: 0 0 14px;
      letter-spacing: 0;
      font-weight: 500;
    }}
    table {{
      width: 100%;
      min-width: 760px;
      border-collapse: separate;
      border-spacing: 0;
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    th, td {{
      border-bottom: 0.5px solid var(--line-soft);
      padding: 13px 12px;
      text-align: left;
      vertical-align: top;
      white-space: normal;
      overflow-wrap: anywhere;
    }}
    th {{
      background: var(--table-head);
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .cell-scroll {{
      max-height: 220px;
      min-width: 0;
      overflow: auto;
      overscroll-behavior: contain;
      scrollbar-gutter: stable;
      padding-right: 2px;
    }}
    .table-wrap {{
      width: 100%;
      overflow-x: auto;
      border-radius: 12px;
    }}
    .table-scroll-shell {{
      display: grid;
      gap: 8px;
    }}
    .table-scroll-toolbar {{
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }}
    .table-scroll-toolbar button {{
      min-height: 34px;
      padding: 6px 10px;
    }}
    .icon-button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 38px;
      min-width: 38px;
      height: 38px;
      padding: 0;
    }}
    .icon-button .ti {{
      width: 18px;
      height: 18px;
      stroke: currentColor;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    a {{ color: var(--accent); }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 9px;
      background: var(--pill-bg);
      color: var(--pill-ink);
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }}
    .score-status {{
      background: var(--status-confirmed-bg);
      color: var(--status-confirmed-ink);
      text-transform: uppercase;
    }}
    .score-status.draft {{
      background: var(--status-draft-bg);
      color: var(--status-draft-ink);
    }}
    .empty {{ color: var(--muted); }}
    .report {{
      background: var(--code-bg);
      color: var(--code-ink);
      border-radius: 12px;
      padding: 18px;
      overflow-x: auto;
      white-space: pre-wrap;
    }}
    .command {{
      margin: 0;
      background: var(--code-bg);
      color: var(--code-ink);
      border-radius: 12px;
      padding: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 13px;
    }}
    .workflow-table td:nth-child(1) {{
      width: 150px;
      font-weight: 500;
    }}
    .lab-queue {{
      min-width: 980px;
    }}
    .lab-queue th:nth-child(1),
    .lab-queue td:nth-child(1) {{
      width: 250px;
    }}
    .lab-queue th:nth-child(2),
    .lab-queue td:nth-child(2),
    .lab-queue th:nth-child(3),
    .lab-queue td:nth-child(3),
    .lab-queue th:nth-child(4),
    .lab-queue td:nth-child(4) {{
      width: 120px;
    }}
    .lab-artifacts-table {{
      table-layout: fixed;
      min-width: 1560px;
    }}
    .lab-artifacts-table th:nth-child(1),
    .lab-artifacts-table td:nth-child(1) {{
      width: 280px;
    }}
    .lab-artifacts-table th:nth-child(2),
    .lab-artifacts-table td:nth-child(2),
    .lab-artifacts-table th:nth-child(3),
    .lab-artifacts-table td:nth-child(3),
    .lab-artifacts-table th:nth-child(4),
    .lab-artifacts-table td:nth-child(4),
    .lab-artifacts-table th:nth-child(5),
    .lab-artifacts-table td:nth-child(5),
    .lab-artifacts-table th:nth-child(6),
    .lab-artifacts-table td:nth-child(6) {{
      width: 96px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .lab-artifacts-table th:nth-child(7),
    .lab-artifacts-table td:nth-child(7) {{
      width: 150px;
    }}
    .lab-artifacts-table th:nth-child(8),
    .lab-artifacts-table td:nth-child(8) {{
      width: 190px;
    }}
    .lab-artifacts-table th:nth-child(9),
    .lab-artifacts-table td:nth-child(9) {{
      width: 460px;
    }}
    .capability-ready-table {{
      table-layout: fixed;
      min-width: 1280px;
    }}
    .capability-ready-table th:nth-child(1),
    .capability-ready-table td:nth-child(1) {{
      width: 300px;
    }}
    .capability-ready-table th:nth-child(2),
    .capability-ready-table td:nth-child(2) {{
      width: 110px;
    }}
    .capability-ready-table th:nth-child(3),
    .capability-ready-table td:nth-child(3) {{
      width: 150px;
    }}
    .capability-ready-table th:nth-child(4),
    .capability-ready-table td:nth-child(4) {{
      width: 240px;
    }}
    .capability-ready-table th:nth-child(5),
    .capability-ready-table td:nth-child(5) {{
      width: 280px;
    }}
    .capability-ready-table th:nth-child(6),
    .capability-ready-table td:nth-child(6) {{
      width: 200px;
    }}
    .capability-quant-table {{
      table-layout: fixed;
      min-width: 1520px;
    }}
    .capability-quant-table th:nth-child(1),
    .capability-quant-table td:nth-child(1) {{
      width: 280px;
    }}
    .capability-quant-table th:nth-child(2),
    .capability-quant-table td:nth-child(2) {{
      width: 300px;
    }}
    .capability-quant-table th:nth-child(3),
    .capability-quant-table td:nth-child(3) {{
      width: 110px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .capability-quant-table th:nth-child(4),
    .capability-quant-table td:nth-child(4) {{
      width: 180px;
    }}
    .capability-quant-table th:nth-child(5),
    .capability-quant-table td:nth-child(5) {{
      width: 160px;
    }}
    .capability-quant-table th:nth-child(6),
    .capability-quant-table td:nth-child(6) {{
      width: 260px;
    }}
    .capability-quant-table th:nth-child(7),
    .capability-quant-table td:nth-child(7) {{
      width: 230px;
    }}
    .runs-table {{
      table-layout: fixed;
      min-width: 1640px;
    }}
    .runs-table th:nth-child(1),
    .runs-table td:nth-child(1) {{
      width: 110px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .runs-table th:nth-child(2),
    .runs-table td:nth-child(2) {{
      width: 210px;
    }}
    .runs-table th:nth-child(2),
    .runs-table td:nth-child(2),
    .compare-table th:nth-child(1),
    .compare-table td:nth-child(1),
    .radar-table th:nth-child(1),
    .radar-table td:nth-child(1),
    .project-table th:nth-child(1),
    .project-table td:nth-child(1) {{
      position: sticky;
      left: 0;
      z-index: 3;
      background: var(--control);
      box-shadow: 1px 0 0 var(--line), 10px 0 18px rgba(0, 0, 0, 0.18);
    }}
    .runs-table th:nth-child(2),
    .compare-table th:nth-child(1),
    .radar-table th:nth-child(1),
    .project-table th:nth-child(1) {{
      z-index: 4;
      background: #181a29;
    }}
    .overview-table {{
      table-layout: fixed;
      min-width: 1240px;
    }}
    .overview-table th:nth-child(1),
    .overview-table td:nth-child(1) {{
      width: 260px;
    }}
    .overview-table th:nth-child(2),
    .overview-table td:nth-child(2) {{
      width: 170px;
    }}
    .overview-table th:nth-child(3),
    .overview-table td:nth-child(3),
    .overview-table th:nth-child(5),
    .overview-table td:nth-child(5),
    .overview-table th:nth-child(6),
    .overview-table td:nth-child(6),
    .overview-table th:nth-child(7),
    .overview-table td:nth-child(7) {{
      width: 96px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .overview-table th:nth-child(4),
    .overview-table td:nth-child(4),
    .overview-table th:nth-child(8),
    .overview-table td:nth-child(8),
    .overview-table th:nth-child(9),
    .overview-table td:nth-child(9),
    .overview-table th:nth-child(10),
    .overview-table td:nth-child(10) {{
      width: 130px;
    }}
    .runs-table th:nth-child(3),
    .runs-table td:nth-child(3) {{
      width: 135px;
    }}
    .runs-table th:nth-child(4),
    .runs-table td:nth-child(4),
    .runs-table th:nth-child(5),
    .runs-table td:nth-child(5),
    .runs-table th:nth-child(6),
    .runs-table td:nth-child(6),
    .runs-table th:nth-child(7),
    .runs-table td:nth-child(7),
    .runs-table th:nth-child(8),
    .runs-table td:nth-child(8),
    .runs-table th:nth-child(9),
    .runs-table td:nth-child(9) {{
      width: 86px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .runs-table th:nth-child(10),
    .runs-table td:nth-child(10),
    .runs-table th:nth-child(11),
    .runs-table td:nth-child(11) {{
      width: 120px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .runs-table th:nth-child(12),
    .runs-table td:nth-child(12) {{
      width: 190px;
    }}
    .runs-table th:nth-child(13),
    .runs-table td:nth-child(13) {{
      width: 240px;
    }}
    .compare-table {{
      table-layout: fixed;
      min-width: 2960px;
    }}
    .compare-table th:nth-child(1),
    .compare-table td:nth-child(1) {{
      width: 260px;
    }}
    .compare-table th:nth-child(2),
    .compare-table td:nth-child(2) {{
      width: 90px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .compare-table th:nth-child(3),
    .compare-table td:nth-child(3) {{
      width: 130px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .compare-table th:nth-child(4),
    .compare-table td:nth-child(4) {{
      width: 170px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .compare-table th:nth-child(n+5),
    .compare-table td:nth-child(n+5) {{
      width: 210px;
    }}
    .inventory-models-table {{
      table-layout: fixed;
      min-width: 1760px;
    }}
    .inventory-models-table th:nth-child(1),
    .inventory-models-table td:nth-child(1) {{
      width: 130px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .inventory-models-table th:nth-child(2),
    .inventory-models-table td:nth-child(2) {{
      width: 300px;
    }}
    .inventory-models-table th:nth-child(3),
    .inventory-models-table td:nth-child(3) {{
      width: 260px;
    }}
    .inventory-models-table th:nth-child(4),
    .inventory-models-table td:nth-child(4) {{
      width: 140px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .inventory-models-table th:nth-child(5),
    .inventory-models-table td:nth-child(5) {{
      width: 460px;
    }}
    .inventory-models-table th:nth-child(6),
    .inventory-models-table td:nth-child(6) {{
      width: 230px;
    }}
    .inventory-models-table th:nth-child(7),
    .inventory-models-table td:nth-child(7) {{
      width: 240px;
    }}
    .inventory-checks-table {{
      table-layout: fixed;
      min-width: 1360px;
    }}
    .inventory-checks-table th:nth-child(1),
    .inventory-checks-table td:nth-child(1) {{
      width: 180px;
    }}
    .inventory-checks-table th:nth-child(2),
    .inventory-checks-table td:nth-child(2),
    .inventory-checks-table th:nth-child(3),
    .inventory-checks-table td:nth-child(3) {{
      width: 100px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .inventory-checks-table th:nth-child(4),
    .inventory-checks-table td:nth-child(4) {{
      width: 360px;
    }}
    .inventory-checks-table th:nth-child(5),
    .inventory-checks-table td:nth-child(5) {{
      width: 620px;
    }}
    .model-detail-results-scroll {{
      width: 100%;
      overflow-x: auto;
      overflow-y: visible;
      overscroll-behavior-x: contain;
      scrollbar-gutter: stable;
      padding-bottom: 8px;
    }}
    .model-detail-results-toolbar {{
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin: 16px 0 8px;
    }}
    .model-detail-results-toolbar button {{
      min-height: 34px;
      border-color: var(--line);
      background: var(--panel-soft);
      color: var(--ink);
    }}
    .model-detail-section {{
      min-width: 1320px;
    }}
    .model-detail-section + .model-detail-section {{
      margin-top: 16px;
    }}
    .model-detail-results-scroll .table-wrap {{
      overflow-x: visible;
    }}
    .model-detail-runs-table {{
      table-layout: fixed;
      min-width: 1320px;
    }}
    .model-detail-runs-table th:nth-child(1),
    .model-detail-runs-table td:nth-child(1) {{
      width: 115px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-runs-table td:nth-child(1) .cell-scroll,
    .model-detail-runs-table td:nth-child(3) .cell-scroll,
    .model-detail-runs-table td:nth-child(4) .cell-scroll,
    .model-detail-runs-table td:nth-child(5) .cell-scroll,
    .model-detail-runs-table td:nth-child(6) .cell-scroll,
    .model-detail-runs-table td:nth-child(7) .cell-scroll,
    .model-detail-runs-table td:nth-child(8) .cell-scroll,
    .model-detail-runs-table td:nth-child(9) .cell-scroll,
    .model-detail-runs-table td:nth-child(10) .cell-scroll {{
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-runs-table th:nth-child(2),
    .model-detail-runs-table td:nth-child(2) {{
      width: 125px;
    }}
    .model-detail-runs-table th:nth-child(3),
    .model-detail-runs-table td:nth-child(3),
    .model-detail-runs-table th:nth-child(4),
    .model-detail-runs-table td:nth-child(4),
    .model-detail-runs-table th:nth-child(5),
    .model-detail-runs-table td:nth-child(5),
    .model-detail-runs-table th:nth-child(6),
    .model-detail-runs-table td:nth-child(6),
    .model-detail-runs-table th:nth-child(7),
    .model-detail-runs-table td:nth-child(7),
    .model-detail-runs-table th:nth-child(8),
    .model-detail-runs-table td:nth-child(8) {{
      width: 84px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-runs-table th:nth-child(9),
    .model-detail-runs-table td:nth-child(9),
    .model-detail-runs-table th:nth-child(10),
    .model-detail-runs-table td:nth-child(10) {{
      width: 118px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-runs-table th:nth-child(11),
    .model-detail-runs-table td:nth-child(11) {{
      width: 200px;
    }}
    .model-detail-runs-table th:nth-child(12),
    .model-detail-runs-table td:nth-child(12) {{
      width: 260px;
    }}
    .model-detail-decisions-table {{
      table-layout: fixed;
      min-width: 1320px;
    }}
    .model-detail-decisions-table th:nth-child(1),
    .model-detail-decisions-table td:nth-child(1) {{
      width: 180px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-decisions-table td:nth-child(1) .cell-scroll,
    .model-detail-decisions-table td:nth-child(2) .cell-scroll,
    .model-detail-decisions-table td:nth-child(3) .cell-scroll {{
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-decisions-table th:nth-child(2),
    .model-detail-decisions-table td:nth-child(2),
    .model-detail-decisions-table th:nth-child(3),
    .model-detail-decisions-table td:nth-child(3) {{
      width: 100px;
      white-space: nowrap;
      overflow-wrap: normal;
    }}
    .model-detail-decisions-table th:nth-child(4),
    .model-detail-decisions-table td:nth-child(4),
    .model-detail-decisions-table th:nth-child(5),
    .model-detail-decisions-table td:nth-child(5),
    .model-detail-decisions-table th:nth-child(6),
    .model-detail-decisions-table td:nth-child(6) {{
      width: 300px;
    }}
    .split {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
      gap: 18px;
    }}
    .cell-stack {{
      display: grid;
      gap: 7px;
    }}
    .cell-stack strong {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
    }}
    .radar-table {{
      min-width: 1520px;
    }}
    .radar-table th:nth-child(1),
    .radar-table td:nth-child(1) {{
      width: 180px;
    }}
    .radar-table th:nth-child(2),
    .radar-table td:nth-child(2) {{
      width: 112px;
    }}
    .radar-table th:nth-child(3),
    .radar-table td:nth-child(3) {{
      width: 132px;
    }}
    .radar-table th:nth-child(4),
    .radar-table td:nth-child(4) {{
      width: 220px;
    }}
    .radar-table th:nth-child(5),
    .radar-table td:nth-child(5) {{
      width: 230px;
    }}
    .radar-table th:nth-child(6),
    .radar-table td:nth-child(6) {{
      width: 260px;
    }}
    .radar-table th:nth-child(7),
    .radar-table td:nth-child(7) {{
      width: 190px;
    }}
    .radar-table th:nth-child(8),
    .radar-table td:nth-child(8) {{
      width: 190px;
    }}
    .project-table {{
      min-width: 980px;
    }}
    .project-table th:nth-child(1),
    .project-table td:nth-child(1) {{
      width: 190px;
    }}
    .project-table th:nth-child(2),
    .project-table td:nth-child(2) {{
      width: 150px;
    }}
    .project-table th:nth-child(4),
    .project-table td:nth-child(4) {{
      width: 220px;
    }}
    @media (max-width: 780px) {{
      .filters {{ grid-template-columns: 1fr; }}
      .filter-actions {{ justify-content: flex-start; }}
      .split {{ grid-template-columns: 1fr; }}
      .stat-breakdown {{ grid-column: auto; }}
      .chart-grid {{ gap: 10px; margin-bottom: 14px; }}
      .chart-panel {{ padding: 14px; }}
      .chart-panel h2 {{ font-size: 18px; margin: 0 0 8px; }}
      .chart-panel .chart-empty {{ max-height: 44px; }}
      .chart-summary-row {{ grid-template-columns: 1fr; gap: 4px; }}
      h1 {{ font-size: 24px; }}
      th, td {{ padding: 11px 9px; }}
    }}
    body {{
      background:
        radial-gradient(1100px 600px at 12% -8%, rgba(139, 123, 255, 0.20), transparent 60%),
        radial-gradient(900px 520px at 96% 2%, rgba(42, 212, 238, 0.14), transparent 58%),
        var(--bg);
      background-attachment: fixed;
      -webkit-font-smoothing: antialiased;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      letter-spacing: 0.1px;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: var(--header);
      -webkit-backdrop-filter: saturate(160%) blur(16px);
      backdrop-filter: saturate(160%) blur(16px);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      font-weight: 600;
      letter-spacing: -0.4px;
      background: var(--accent-grad);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      width: fit-content;
    }}
    h2 {{
      font-weight: 600;
      letter-spacing: -0.2px;
    }}
    .nav {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel-soft);
      -webkit-backdrop-filter: blur(8px);
      backdrop-filter: blur(8px);
      transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, box-shadow 160ms ease, color 160ms ease;
    }}
    .nav:hover {{
      color: var(--ink);
      border-color: rgba(139, 123, 255, 0.45);
      transform: translateY(-1px);
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
    }}
    .nav:hover .ti {{ color: var(--accent-2); }}
    .nav.active {{
      color: #ffffff;
      background: var(--accent-grad);
      border-color: transparent;
      box-shadow: var(--glow);
    }}
    .nav.active .ti {{ color: #ffffff; }}
    .stat, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      -webkit-backdrop-filter: blur(14px);
      backdrop-filter: blur(14px);
      box-shadow: var(--shadow);
      transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }}
    .stat {{
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 16px 18px;
    }}
    .stat:hover, .panel:hover {{
      transform: translateY(-2px);
      border-color: rgba(139, 123, 255, 0.40);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(139, 123, 255, 0.18);
    }}
    .stat .ti {{
      color: var(--accent);
      font-size: 22px;
      width: 40px;
      height: 40px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
      background: var(--accent-soft);
      flex: 0 0 auto;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }}
    .stat .value {{
      font-size: 26px;
      font-weight: 600;
      line-height: 1.1;
      font-variant-numeric: tabular-nums;
      background: var(--accent-grad);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }}
    .stat-metrics strong {{
      background: var(--accent-grad);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }}
    .pill {{
      background: var(--pill-bg);
      color: var(--pill-ink);
      border: 1px solid rgba(139, 123, 255, 0.28);
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.3px;
    }}
    .pill.score-status {{
      background: var(--status-confirmed-bg);
      color: var(--status-confirmed-ink);
      border-color: rgba(52, 211, 153, 0.35);
    }}
    .pill.score-status.draft {{
      background: var(--status-draft-bg);
      color: var(--status-draft-ink);
      border-color: rgba(251, 191, 36, 0.38);
    }}
    .table-wrap {{
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow-x: auto;
      overflow-y: hidden;
      background: var(--panel);
      -webkit-backdrop-filter: blur(14px);
      backdrop-filter: blur(14px);
      box-shadow: var(--shadow);
    }}
    .table-scroll-toolbar {{
      margin-bottom: 2px;
    }}
    .table-scroll-toolbar button {{
      border-color: var(--line);
      background: var(--panel-soft);
      color: var(--ink);
    }}
    table {{ border-collapse: separate; border-spacing: 0; }}
    th {{
      background: var(--table-head);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      font-size: 11.5px;
      font-weight: 600;
      border-bottom: 1px solid var(--line);
    }}
    td {{ border-bottom: 1px solid var(--line-soft); }}
    tbody tr {{ transition: background 140ms ease; }}
    tbody tr:hover {{ background: rgba(139, 123, 255, 0.07); }}
    tbody tr:last-child td {{ border-bottom: none; }}
    a {{ color: var(--accent-2); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code, pre {{
      background: var(--code-bg);
      color: var(--code-ink);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .app {{ display: flex; align-items: stretch; min-height: 100vh; }}
    .sidebar {{
      position: sticky;
      top: 0;
      align-self: flex-start;
      height: 100vh;
      width: 256px;
      flex: 0 0 256px;
      display: flex;
      flex-direction: column;
      padding: 18px 14px;
      background: var(--header);
      -webkit-backdrop-filter: saturate(160%) blur(16px);
      backdrop-filter: saturate(160%) blur(16px);
      border-right: 1px solid var(--line);
      overflow-y: auto;
      transition: width 200ms ease, flex-basis 200ms ease, padding 200ms ease;
    }}
    .brand {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 16px;
      padding: 4px 6px;
    }}
    .brand h1 {{ margin: 0; font-size: 18px; line-height: 1.25; }}
    .collapse-btn {{
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 30px;
      height: 30px;
      border-radius: 9px;
      border: 1px solid var(--line);
      background: var(--panel-soft);
      color: var(--muted);
      cursor: pointer;
      transition: color 150ms ease, border-color 150ms ease;
    }}
    .collapse-btn:hover {{ color: var(--accent-2); border-color: rgba(139, 123, 255, 0.45); }}
    .collapse-btn .ti {{ width: 18px; height: 18px; stroke: currentColor; transition: transform 200ms ease; }}
    .sidebar nav {{ flex-direction: column; flex-wrap: nowrap; gap: 4px; }}
    .sidebar .nav {{ width: 100%; justify-content: flex-start; padding: 9px 12px; white-space: nowrap; overflow: hidden; position: relative; }}
    .app main {{ flex: 1 1 auto; min-width: 0; max-width: none; margin: 0; padding: 28px 32px 40px; }}
    .app.collapsed .sidebar {{ width: 72px; flex-basis: 72px; padding: 18px 10px; }}
    .app.collapsed .brand {{ justify-content: center; }}
    .app.collapsed .brand h1 {{ display: none; }}
    .app.collapsed .sidebar .nav span {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
      border: 0;
    }}
    .app.collapsed .sidebar .nav {{ justify-content: center; padding: 9px 0; overflow: visible; }}
    .app.collapsed .sidebar .nav::after {{
      content: attr(data-label);
      position: absolute;
      left: calc(100% + 10px);
      top: 50%;
      transform: translateY(-50%);
      min-width: max-content;
      max-width: 240px;
      padding: 7px 10px;
      border-radius: 9px;
      border: 1px solid rgba(139, 123, 255, 0.38);
      background: rgba(13, 15, 26, 0.96);
      color: var(--ink);
      box-shadow: var(--shadow);
      opacity: 0;
      pointer-events: none;
      transition: opacity 140ms ease, transform 140ms ease;
      z-index: 40;
    }}
    .app.collapsed .sidebar .nav:hover::after,
    .app.collapsed .sidebar .nav:focus-visible::after {{
      opacity: 1;
      transform: translate(3px, -50%);
    }}
    .app.collapsed .collapse-btn .ti {{ transform: rotate(180deg); }}
    @media (max-width: 760px) {{
      .app {{ flex-direction: column; }}
      .sidebar {{ position: static; height: auto; width: 100%; flex-basis: auto; flex-direction: column; border-right: none; border-bottom: 1px solid var(--line); }}
      .sidebar nav {{ flex-direction: row; flex-wrap: wrap; }}
      .sidebar .nav {{ width: auto; }}
      .app main {{ padding: 20px; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <h1>Local Model Performance Dashboard</h1>
        <button class="collapse-btn" type="button" aria-label="Toggle sidebar"><svg class="ti" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 7l-5 5 5 5M18 7l-5 5 5 5"/></svg></button>
      </div>
      <nav>{nav}</nav>
    </aside>
    <main>{body}</main>
  </div>
  <script>
  (function() {{
    var app = document.querySelector('.app');
    var btn = document.querySelector('.collapse-btn');
    if (!app || !btn) {{ return; }}
    try {{ if (localStorage.getItem('dash-sidebar') === 'collapsed') {{ app.classList.add('collapsed'); }} }} catch (e) {{}}
    btn.addEventListener('click', function() {{
      app.classList.toggle('collapsed');
      try {{ localStorage.setItem('dash-sidebar', app.classList.contains('collapsed') ? 'collapsed' : 'open'); }} catch (e) {{}}
    }});
    document.querySelectorAll('[data-chart-dialog]').forEach(function(trigger) {{
      trigger.addEventListener('click', function() {{
        var dialog = document.getElementById(trigger.getAttribute('data-chart-dialog'));
        if (!dialog) {{ return; }}
        if (typeof dialog.showModal === 'function') {{
          dialog.showModal();
        }} else {{
          dialog.setAttribute('open', 'open');
        }}
      }});
    }});
    document.querySelectorAll('.chart-dialog').forEach(function(dialog) {{
      dialog.addEventListener('click', function(event) {{
        if (event.target === dialog && typeof dialog.close === 'function') {{
          dialog.close();
        }}
      }});
    }});
    document.addEventListener('click', function(event) {{
      var trigger = event.target.closest('[data-scroll-target]');
      if (!trigger) {{ return; }}
      var target = document.getElementById(trigger.getAttribute('data-scroll-target'));
      var amount = parseInt(trigger.getAttribute('data-scroll-by') || '0', 10);
      if (!target || !amount) {{ return; }}
      event.preventDefault();
      var before = target.scrollLeft;
      if (typeof target.scrollBy === 'function') {{
        target.scrollBy({{ left: amount, top: 0, behavior: 'auto' }});
      }}
      if (target.scrollLeft === before) {{
        target.scrollLeft = before + amount;
      }}
    }});
  }})();
  </script>
</body>
</html>""".format(title=escape(title), nav="".join(nav), body=body)

__all__ = ("NAV_ITEMS", "NAV_ICONS", "_layout")
