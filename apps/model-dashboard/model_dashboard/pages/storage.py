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


def _storage_decision_rows(decisions):
    rows = []
    for row in decisions:
        model = '<div class="cell-stack storage-model-identity"><div class="storage-model-name"><a href="/models/{id}">{name}</a></div></div>'.format(
            id=row["model_id"],
            name=_text(row["model_name"]),
        )
        rows.append(
            [
                model,
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    return rows


def _storage_decision_table(
    decisions,
    empty_message="No real storage/install decisions match these filters.",
    table_class="storage-decisions-table",
    scroll_id="storage-decisions-table-scroll",
    scroll_label="Decision log table",
):
    return _table(
        ["Model", "Decision", "Keep installed", "Best use case", "Weakness", "Retest"],
        _storage_decision_rows(decisions),
        empty_message=empty_message,
        table_class=table_class,
        scroll_controls=True,
        scroll_id=scroll_id,
        scroll_label=scroll_label,
    )


def _storage(conn, query=None):
    all_decisions = db.list_decisions(conn)
    decisions = _real_rows(all_decisions)
    filters = _storage_filter_values(query or {})
    filtered_decisions = _filter_storage_decisions(decisions, filters)
    body = """
    {notice}
    <section class="panel storage-intro-panel">
      <h2>Storage / Install Status</h2>
      <p>This is a benchmark decision log. It is not an installed-model inventory scanner.</p>
      <p>Use <a href="/inventory">My Models</a> to check local LM Studio and Ollama inventory.</p>
    </section>
    <section class="storage-decisions-section">
      {filters}
      <h2>Decision Log{filtered_count}</h2>
      {table}
    </section>
    """.format(
        notice=_real_data_notice(len(_demo_rows(all_decisions))),
        filters=_storage_filters(decisions, filters),
        filtered_count=(
            f" ({len(filtered_decisions)} of {len(decisions)})" if any(filters.values()) else ""
        ),
        table=_storage_decision_table(filtered_decisions),
    )
    return _layout("Storage / Install Status", "/storage", body)

__all__ = ('_storage', '_storage_decision_rows', '_storage_decision_table')
