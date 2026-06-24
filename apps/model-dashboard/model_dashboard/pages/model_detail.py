"""Dashboard model detail page."""

# ruff: noqa: E501,F401,F403,F405,I001
from __future__ import annotations

from html import escape
from pathlib import Path

from .. import capability, charts, db
from ..components import *
from ..filters import *
from ..icons import icon as render_icon
from ..layout import _layout
from ..reports import generate_markdown_report
from ..scoring import METRIC_FIELDS

def _model_detail(conn, model_id):
    detail = db.get_model_detail(conn, model_id)
    if detail is None:
        return _layout("Model Detail", "", "<h2>Model not found</h2>")
    model = detail["model"]
    if _is_demo_row(model):
        return _layout(
            "Demo Model Detail",
            "",
            """
            <section class="panel">
              <h2>Demo Fixture Model</h2>
              <p><strong>{name}</strong> is bundled demo data for dashboard testing, not an installed model.</p>
              <p><a href="/demo">View demo data</a> or return to <a href="/">real benchmark results</a>.</p>
            </section>
            """.format(name=_text(model["model_name"])),
        )
    run_rows = []
    for row in detail["runs"]:
        run_rows.append(
            [
                _text(row["date_tested"]),
                _text(row["backend"]),
                _text(row["format"]),
                _text(row["quantization"]),
                _text(row["context_window"]),
                _number(row["tokens_per_sec"]),
                _number(row["ram_usage_gb"]),
                _number(row["total_score"], 2),
                _status_pill(row["score_status"]),
                _pill(row["final_label"]),
                _artifact_link_from_notes(row["run_notes"]),
                _text(row["run_notes"]),
            ]
        )
    decision_rows = []
    for row in detail["decisions"]:
        decision_rows.append(
            [
                _text(row["created_at"]),
                _text(row["decision"]),
                "yes" if row["keep_installed"] else "no",
                _text(row["best_use_case"]),
                _text(row["weakness"]),
                _text(row["retest_condition"]),
            ]
        )
    body = """
    <div class="split">
      <section class="panel">
        <h2>{name}</h2>
        <p><strong>Family:</strong> {family}</p>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Parameters:</strong> {params}B</p>
        <p><strong>License:</strong> {license}</p>
        <p><strong>Source:</strong> {source}</p>
        <p>{notes}</p>
      </section>
      <section class="panel">
        <h2>Current Read</h2>
        <p>{summary}</p>
      </section>
    </div>
    <div class="model-detail-results-toolbar" aria-label="Model detail results controls">
      <button class="icon-button" type="button" data-scroll-target="model-detail-results" data-scroll-by="-360" aria-label="Scroll model detail results left" title="Scroll model detail results left">{left_icon}</button>
      <button class="icon-button" type="button" data-scroll-target="model-detail-results" data-scroll-by="360" aria-label="Scroll model detail results right" title="Scroll model detail results right">{right_icon}</button>
    </div>
    <div id="model-detail-results" class="model-detail-results-scroll" aria-label="Model detail runs and decisions">
      <section class="model-detail-section"><h2>Runs</h2>{runs}</section>
      <section class="model-detail-section"><h2>Decisions</h2>{decisions}</section>
    </div>
    """.format(
        name=_text(model["model_name"]),
        family=_text(model["model_family"]),
        provider=_text(model["provider"]),
        params=_number(model["params_b"], 1),
        license=_text(model["license"]),
        source=_external_link_or_text(model["source_url"], model["source_url"]),
        notes=_text(model["notes"]),
        summary=_text(detail["decisions"][0]["best_use_case"] if detail["decisions"] else ""),
        left_icon=render_icon("ti-chevron-left"),
        right_icon=render_icon("ti-chevron-right"),
        runs=_table(
            [
                "Date",
                "Backend",
                "Format",
                "Quant",
                "Context",
                "Tok/s",
                "RAM GB",
                "Score",
                "Status",
                "Label",
                "Artifact",
                "Notes",
            ],
            run_rows,
            table_class="model-detail-runs-table",
            header_tip_keys=RESULT_TABLE_HEADER_TIPS,
        ),
        decisions=_table(
            ["Created", "Decision", "Keep", "Best use case", "Weakness", "Retest"],
            decision_rows,
            table_class="model-detail-decisions-table",
            header_tip_keys=RESULT_TABLE_HEADER_TIPS,
        ),
    )
    return _layout("Model Detail", "", body)

__all__ = ('_model_detail',)
