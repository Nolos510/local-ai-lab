"""Draft score review queue and human confirmation pages."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

from .. import model_roles, score_review
from ..components import (
    EVAL_RESULTS_DIR,
    _dashboard_run_ids,
    _pill,
    _safe_artifact_dir,
    _table,
    _text,
)
from ..filters import _query_value
from ..layout import _layout
from ..scoring import FINAL_LABELS, METRIC_FIELDS


def _score_value(record, field):
    scores = record.get("scores") if isinstance(record, dict) else None
    return scores.get(field) if isinstance(scores, dict) else None


def _display_number(value):
    if value in (None, ""):
        return "—"
    return f"{float(value):.1f}"


def _review_next_action(review):
    if review.get("status") == "draft":
        return "Await independent reviewer"
    flags = set(review.get("flags") or ())
    if "capture_errors_present" in flags or "capture_evidence_malformed" in flags:
        return "Rerun capture before scoring"
    if "capture_evidence_missing" in flags:
        return "Capture evidence before scoring"
    if {"primary_all_scores_zero", "reviewer_all_scores_zero"} & flags:
        return "Rescore or retire shared-zero evidence"
    if flags == {"label"}:
        return "Adjudicate the final label"
    if {"metric_delta", "total_delta"} & flags:
        return "Inspect metric deltas"
    if {"primary_output_incomplete", "reviewer_output_incomplete"} & flags:
        return "Rerun incomplete judge output"
    return "Inspect evidence and resolve"


def _review_entries(eval_results_dir):
    root = Path(eval_results_dir)
    if not root.is_dir():
        return []
    entries = []
    for path in sorted(root.iterdir(), key=lambda item: item.name, reverse=True):
        if not path.is_dir() or not (path / "draft-scores.json").is_file():
            continue
        try:
            artifact_dir = _safe_artifact_dir(path.name, root)
        except ValueError:
            continue
        if not model_roles.model_supports_generation(
            model_roles.artifact_model_role(artifact_dir)
        ):
            continue
        if (artifact_dir / "scores.json").is_file():
            continue
        if not score_review.has_raw_evidence(artifact_dir):
            continue
        primary = score_review.load_json_object(artifact_dir / "draft-scores.json")
        reviewer = score_review.load_json_object(artifact_dir / "review-scores.json")
        review = score_review.review_state(artifact_dir)
        if review.get("status") == "rejected":
            continue
        if score_review.automatic_disposition(artifact_dir):
            continue
        entries.append(
            {
                "run_id": path.name,
                "primary": primary,
                "reviewer": reviewer,
                "review": review,
            }
        )
    return entries


def _review_all_control(entries, enable_score_actions, action_token, reviewer_model):
    reviewable_ids = [
        entry["run_id"] for entry in entries if entry["review"].get("status") == "draft"
    ]
    count = len(reviewable_ids)
    if count <= 0:
        return '<p class="empty">No untouched drafts are awaiting independent review.</p>'
    if not enable_score_actions:
        return (
            '<div class="cell-stack"><button type="button" disabled>Review all drafts</button>'
            '<span class="empty">Restart with <code>--enable-score-actions</code>.</span></div>'
        )
    if not reviewer_model:
        return (
            '<div class="cell-stack"><button type="button" disabled>Review all drafts</button>'
            '<span class="empty">Restart with an exact <code>--reviewer-model</code>.</span></div>'
        )
    hidden_run_ids = "".join(
        f'<input type="hidden" name="benchmark_run_id" value="{_text(run_id)}">'
        for run_id in reviewable_ids
    )
    return f"""
    <form class="inline-form" method="post" action="/actions/review-all-drafts">
      <input type="hidden" name="token" value="{_text(action_token)}">
      {hidden_run_ids}
      <button type="submit">Review all drafts</button>
      <span class="empty">{count} untouched draft{'s' if count != 1 else ''} will be reviewed sequentially.</span>
    </form>
    """


def _confirm_agreements_control(entries, enable_score_actions, action_token):
    confirmable_ids = [
        entry["run_id"]
        for entry in entries
        if entry["review"].get("status") == "machine_reviewed"
    ]
    count = len(confirmable_ids)
    if count <= 0:
        return (
            '<p class="empty">No independently reviewed agreements are ready for '
            "batch confirmation.</p>"
        )
    if not enable_score_actions:
        return (
            '<div class="cell-stack"><button type="button" disabled>'
            'Confirm reviewed agreements</button><span class="empty">Restart with '
            '<code>--enable-score-actions</code>.</span></div>'
        )
    hidden_run_ids = "".join(
        f'<input type="hidden" name="benchmark_run_id" value="{_text(run_id)}">'
        for run_id in confirmable_ids
    )
    return f"""
    <form class="inline-form" method="post" action="/actions/confirm-reviewed-agreements">
      <input type="hidden" name="token" value="{_text(action_token)}">
      {hidden_run_ids}
      <label class="review-acknowledgement">
        <input type="checkbox" name="human_reviewed" value="yes" required>
        I reviewed these independent agreements and approve the displayed primary scores.
      </label>
      <button type="submit">Confirm {count} reviewed agreement{'s' if count != 1 else ''}</button>
      <span class="empty">Only machine-reviewed agreements are included. Disagreements remain in the queue for individual review.</span>
    </form>
    """


def _review_queue(
    eval_results_dir=EVAL_RESULTS_DIR,
    *,
    conn=None,
    query=None,
    enable_score_actions=False,
    action_token="",
    reviewer_model=None,
):
    all_entries = _review_entries(eval_results_dir)
    scope = _query_value(query or {}, "scope").lower()
    imported_ids = _dashboard_run_ids(conn) if conn is not None else set()
    if conn is not None and scope != "all":
        entries = [entry for entry in all_entries if entry["run_id"] in imported_ids]
        scope = "current"
    else:
        entries = all_entries
        scope = "all"
    current_count = sum(entry["run_id"] in imported_ids for entry in all_entries)
    archived_count = max(0, len(all_entries) - current_count)
    rows = []
    for entry in entries:
        primary = entry["primary"]
        review = entry["review"]
        status = review.get("status") or "draft"
        status_label = (
            "judge disagreement" if status == "disagreement" else status.replace("_", " ")
        )
        rows.append(
            [
                f'<a href="/reviews/{_text(entry["run_id"])}">{_text(entry["run_id"])}</a>',
                _pill(status_label),
                _text(primary.get("judge", {}).get("model") or "unknown"),
                _text(review.get("reviewer_judge") or "—"),
                _display_number(primary.get("total_score")),
                _text(primary.get("final_label") or "—"),
                _display_number(review.get("mean_metric_delta")),
                (
                    '<div class="cell-stack">'
                    f'<a href="/reviews/{_text(entry["run_id"])}">Review draft</a>'
                    f'<span class="empty">{_text(_review_next_action(review))}</span>'
                    "</div>"
                ),
            ]
        )
    body = """
    <section class="panel page-intro">
      <h2>Draft Review Queue</h2>
      <p>A second local model can independently score the same evidence. It never sees the primary draft and does not confirm the score.</p>
      <div class="section-note" aria-label="How to handle draft results">
        <p><strong>Your role is evidence owner, not another judge.</strong> The local judge models grade the responses; you decide whether the run is trustworthy enough to influence model decisions.</p>
        <p><strong>Confirm</strong> accepts a reviewed result. <strong>Edit and confirm</strong> is rare and should correct only a clearly unsupported label or metric. <strong>Reject</strong> removes invalid or irrelevant evidence from active rankings while preserving the artifact. <strong>Rerun</strong> is the safest choice for failed captures or material disagreement.</p>
      </div>
      <p class="empty"><strong>Machine reviewed</strong> means the two judges are within the configured thresholds. <strong>Judge disagreement</strong> means both score records are structurally valid but their labels or metrics differ beyond a configured threshold. Rejected, all-zero, role-mismatched, and capture-failed artifacts are quarantined automatically and do not appear in this active queue.</p>
      <div class="filter-actions" aria-label="Review queue scope">
        <a class="action-link{current_active}" href="/reviews">Current dashboard ({current_count})</a>
        <a class="action-link secondary{all_active}" href="/reviews?scope=all">All artifacts ({all_count})</a>
      </div>
      <p class="section-note">The default queue contains only generative draft artifacts imported into the active dashboard. {archived_count} archival or unimported artifact{archived_suffix} remain available in All Artifacts. Embedding and reranker artifacts are excluded because they require retrieval-specific evaluation.</p>
      {review_all_control}
      {confirm_agreements_control}
    </section>
    <section class="runs-section">
      {table}
    </section>
    """.format(
        current_active=" secondary" if scope != "current" else "",
        all_active="" if scope != "all" else " active",
        current_count=current_count,
        all_count=len(all_entries),
        archived_count=archived_count,
        archived_suffix="s" if archived_count != 1 else "",
        review_all_control=_review_all_control(
            entries,
            enable_score_actions,
            action_token,
            reviewer_model,
        ),
        confirm_agreements_control=_confirm_agreements_control(
            entries,
            enable_score_actions,
            action_token,
        ),
        table=_table(
            [
                "Artifact",
                "Review state",
                "Primary judge",
                "Independent reviewer",
                "Draft total",
                "Draft label",
                "Mean delta",
                "Action",
            ],
            rows,
            empty_message="No draft-scored artifacts are awaiting human disposition.",
            table_class="draft-review-table",
        ),
    )
    return _layout("Draft Review Queue", "/reviews", body)


def _metric_input_rows(primary, reviewer, review):
    deltas = review.get("metric_deltas") or {}
    rows = []
    for field in METRIC_FIELDS:
        primary_value = _score_value(primary, field)
        reviewer_value = _score_value(reviewer, field)
        rows.append(
            [
                _text(field.replace("_", " ").title()),
                _display_number(primary_value),
                _display_number(reviewer_value),
                _display_number(deltas.get(field)),
                (
                    f'<input aria-label="Edit { _text(field.replace("_", " ")) }" '
                    f'type="number" min="0" max="100" step="0.1" name="{_text(field)}" '
                    f'value="{_text(primary_value)}" required>'
                ),
            ]
        )
    return rows


def _review_action_control(run_id, status, enable_score_actions, action_token, reviewer_model):
    if status == "rejected":
        return (
            '<p class="empty">Rejected evidence is preserved for audit and cannot '
            "be confirmed. Follow its recorded remediation with a fresh capture or "
            "score attempt.</p>"
        )
    if not enable_score_actions or not reviewer_model:
        return (
            '<button type="button" disabled>Send for Second Review</button>'
            '<p class="empty">Score actions and a different local reviewer model are required.</p>'
        )
    label = "Rerun Independent Review" if status in ("machine_reviewed", "disagreement") else "Send for Second Review"
    return f"""
    <form class="inline-form" method="post" action="/actions/review-score">
      <input type="hidden" name="token" value="{_text(action_token)}">
      <input type="hidden" name="benchmark_run_id" value="{_text(run_id)}">
      <button type="submit">{_text(label)}</button>
    </form>
    """


def _confirmation_controls(primary, review_status):
    if review_status == "rejected":
        return (
            '<button type="button" disabled>Rejected evidence</button>'
            '<p class="empty">This artifact is preserved for audit but cannot be '
            "confirmed. Create a fresh capture or score attempt.</p>"
        )
    if review_status not in ("machine_reviewed", "disagreement"):
        return (
            '<button type="button" disabled>Confirm Draft Score</button>'
            '<p class="empty">Run an independent review before confirming this draft.</p>'
        )
    options = "".join(
        '<option value="{}"{}>{}</option>'.format(
            _text(label),
            " selected" if label == primary.get("final_label") else "",
            _text(label.replace("_", " ").title()),
        )
        for label in FINAL_LABELS
    )
    return f"""
    <div class="field">
      <label for="final-label">Final label</label>
      <select id="final-label" name="final_label">{options}</select>
    </div>
    <label class="review-acknowledgement">
      <input type="checkbox" name="human_reviewed" value="yes" required>
      I reviewed the benchmark evidence and score comparison.
    </label>
    <div class="filter-actions">
      <button type="submit" name="confirmation_mode" value="primary">Confirm Primary Score</button>
      <button type="submit" name="confirmation_mode" value="edited">Edit &amp; Confirm</button>
    </div>
    """


def _review_detail(
    benchmark_run_id,
    eval_results_dir=EVAL_RESULTS_DIR,
    *,
    enable_score_actions=False,
    action_token="",
    reviewer_model=None,
):
    artifact_dir = _safe_artifact_dir(benchmark_run_id, eval_results_dir)
    primary = score_review.load_json_object(artifact_dir / "draft-scores.json")
    if not primary:
        raise ValueError("Draft score artifact is missing or invalid.")
    reviewer = score_review.load_json_object(artifact_dir / "review-scores.json")
    review = score_review.review_state(artifact_dir)
    status = review.get("status") or "draft"
    status_label = (
        "judge disagreement" if status == "disagreement" else status.replace("_", " ")
    )
    flags = ", ".join(review.get("flags") or ()) or "none"
    if status == "rejected":
        rejection_section = """
        <section class="runs-section">
          <h2>Rejected Evidence</h2>
          <p class="section-note">This artifact remains available for audit, but it is excluded from active rankings and cannot be confirmed. Follow the recorded remediation with a fresh capture or score attempt.</p>
        </section>
        """
    else:
        rejection_section = f"""
        <section class="runs-section">
          <h2>Reject Draft</h2>
          <p class="section-note">Rejection preserves the raw evidence and both score records, but removes the imported draft score from active rankings.</p>
          <form class="inline-form" method="post" action="/actions/reject-score">
            <input type="hidden" name="token" value="{_text(action_token)}">
            <input type="hidden" name="benchmark_run_id" value="{_text(benchmark_run_id)}">
            <label class="review-acknowledgement">
              <input type="checkbox" name="human_reviewed" value="yes" required>
              I reviewed this draft and want to reject it.
            </label>
            <button class="danger-secondary" type="submit">Reject Draft</button>
          </form>
        </section>
        """
    body = """
    <section class="panel page-intro">
      <p><a href="/reviews">Back to Draft Review Queue</a></p>
      <h2>{run_id}</h2>
      <p><strong>Review state:</strong> {status}</p>
      <p><strong>Primary judge:</strong> {primary_judge} &middot; <strong>Independent reviewer:</strong> {reviewer_judge}</p>
      <p><strong>Primary label:</strong> {primary_label} &middot; <strong>Reviewer label:</strong> {reviewer_label}</p>
      <p><strong>Mean metric delta:</strong> {mean_delta} &middot; <strong>Total delta:</strong> {total_delta} &middot; <strong>Flags:</strong> {flags}</p>
      <p class="empty">Independent review is blind to the primary draft. A machine-reviewed result means agreement within thresholds; it does not confirm the score.</p>
      <p class="section-note"><strong>Choose by evidence quality:</strong> confirm when the capture is sound and the reviewed result is credible; edit only when the displayed evidence clearly supports the change; reject invalid or irrelevant evidence; rerun when capture quality or judge disagreement leaves doubt.</p>
      <p><a href="/artifacts/{run_id}">Inspect benchmark evidence</a></p>
      {review_control}
    </section>
    <section class="runs-section">
      <h2>Score Comparison</h2>
      <form class="inline-form" method="post" action="/actions/confirm-score">
        <input type="hidden" name="token" value="{token}">
        <input type="hidden" name="benchmark_run_id" value="{run_id}">
        {metric_table}
        {confirmation_controls}
      </form>
    </section>
    {rejection_section}
    """.format(
        run_id=_text(benchmark_run_id),
        status=_pill(status_label),
        primary_judge=_text(primary.get("judge", {}).get("model") or "unknown"),
        reviewer_judge=_text(review.get("reviewer_judge") or "not reviewed"),
        primary_label=_text(primary.get("final_label") or "—"),
        reviewer_label=_text(review.get("reviewer_label") or "—"),
        mean_delta=_display_number(review.get("mean_metric_delta")),
        total_delta=_display_number(review.get("total_delta")),
        flags=_text(flags),
        review_control=_review_action_control(
            benchmark_run_id,
            status,
            enable_score_actions,
            action_token,
            reviewer_model,
        ),
        token=_text(action_token),
        metric_table=_table(
            ["Metric", "Primary", "Reviewer", "Delta", "Final score"],
            _metric_input_rows(primary, reviewer, review),
            table_class="score-review-table",
        ),
        confirmation_controls=_confirmation_controls(primary, status),
        rejection_section=rejection_section,
    )
    return _layout(f"Review {benchmark_run_id}", "/reviews", body)


__all__ = ("_review_queue", "_review_detail")
