"""Dashboard reports page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db
from ..components import *
from ..filters import *
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS

def _reports(conn, database_path):
    report = generate_markdown_report(database_path)
    body = f"""
    <section class="panel" style="margin-bottom:16px">
      <h2>What This Means</h2>
      <p>Ranked models are imported benchmark results, not installed-model inventory.</p>
      <p>Radar candidates are possible models to evaluate, not scored models.</p>
      <p>My Models checks local LM Studio and Ollama inventory on demand.</p>
      <p>Scores are valid only after raw responses, confirmed scores, and decisions exist.</p>
      <p>Demo rows are examples only and are hidden from real dashboard views by default.</p>
    </section>
    <h2>Export Report</h2><pre class="report">{escape(report)}</pre>
    """
    return _layout("Export Report", "/reports", body)

__all__ = ('_reports',)
