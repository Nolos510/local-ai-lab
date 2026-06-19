"""Dashboard storage page."""

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

def _storage(conn, query=None):
    rows = []
    all_decisions = db.list_decisions(conn)
    decisions = _real_rows(all_decisions)
    filters = _storage_filter_values(query or {})
    filtered_decisions = _filter_storage_decisions(decisions, filters)
    for row in filtered_decisions:
        rows.append(
            [
                '<a href="/models/{id}">{name}</a>'.format(
                    id=row["model_id"], name=_text(row["model_name"])
                ),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = """
    {notice}
    <section class="panel" style="margin-bottom:16px">
      <h2>Storage / Install Status</h2>
      <p>This is a benchmark decision log. It is not an installed-model inventory scanner.</p>
      <p>Use <a href="/inventory">Installed Models</a> to check local LM Studio and Ollama inventory.</p>
    </section>
    {filters}
    <h2>Decision Log{filtered_count}</h2>
    {table}
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_decisions))),
        filters=_storage_filters(decisions, filters),
        filtered_count=(
            f" ({len(filtered_decisions)} of {len(decisions)})" if any(filters.values()) else ""
        ),
        table=_table(
            ["Model", "Decision", "Keep installed", "Best use case", "Weakness", "Retest"],
            rows,
            empty_message="No real storage/install decisions match these filters.",
        ),
    )
    return _layout("Storage / Install Status", "/storage", body)

__all__ = ('_storage',)
