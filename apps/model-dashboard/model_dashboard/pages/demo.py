"""Dashboard demo page."""

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

def _demo(conn):
    summaries = _demo_rows(db.list_model_summaries(conn))
    rows = []
    for row in summaries:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["id"], name=_text(row["model_name"])
                ),
                _text(row["provider"]),
                _text(row["backend"]),
                _number(row["total_score"], 2),
                _pill(row["final_label"]),
                _text(row["decision"]),
            ]
        )
    body = """
    <section class="panel" style="margin-bottom:16px">
      <h2>Demo Data</h2>
      <p>These fixture rows are bundled examples for dashboard QA. They are not installed on this machine and are hidden from real dashboard views.</p>
    </section>
    {table}
    """.format(
        table=_table(
            ["Model", "Provider", "Backend", "Score", "Label", "Decision"],
            rows,
            empty_message="No demo fixture rows found.",
        )
    )
    return _layout("Demo Data", "", body)

__all__ = ('_demo',)
