"""Markdown report generation for local model evaluation results."""

from datetime import datetime
from pathlib import Path

from . import db


def _value(value, fallback=""):
    return fallback if value is None else str(value)


def _score(value):
    return "" if value is None else "{:.2f}".format(float(value))


def generate_markdown_report(db_path):
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Local Model Performance Report",
        "",
        "Generated: {}".format(generated_at),
        "",
    ]

    with db.connect(db_path) as conn:
        db.create_schema(conn)
        counts = {table: db.table_count(conn, table) for table in db.TABLES}
        summaries = db.list_model_summaries(conn)
        decisions = db.list_decisions(conn)

        lines.extend(
            [
                "## Summary",
                "",
                "- Models tracked: {}".format(counts["models"]),
                "- Runs tracked: {}".format(counts["model_runs"]),
                "- Eval score rows: {}".format(counts["eval_scores"]),
                "- Decisions logged: {}".format(counts["decisions"]),
                "",
                "## Ranked Models",
                "",
                "| Model | Backend | Quant | Score | Status | Label | Decision | Best use case |",
                "| --- | --- | --- | ---: | --- | --- | --- | --- |",
            ]
        )
        for row in summaries:
            lines.append(
                "| {model} | {backend} | {quant} | {score} | {status} | {label} | {decision} | {use} |".format(
                    model=_value(row["model_name"]),
                    backend=_value(row["backend"]),
                    quant=_value(row["quantization"]),
                    score=_score(row["total_score"]),
                    status=_value(row["score_status"]),
                    label=_value(row["final_label"]),
                    decision=_value(row["decision"]),
                    use=_value(row["best_use_case"]),
                )
            )

        lines.extend(["", "## Install Decisions", ""])
        lines.extend(
            [
                "| Model | Keep installed | Weakness | Retest condition |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in decisions:
            lines.append(
                "| {model} | {keep} | {weakness} | {retest} |".format(
                    model=_value(row["model_name"]),
                    keep="yes" if row["keep_installed"] else "no",
                    weakness=_value(row["weakness"]),
                    retest=_value(row["retest_condition"]),
                )
            )

    lines.append("")
    return "\n".join(lines)


def write_report(db_path, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = generate_markdown_report(db_path)
    output_path.write_text(report, encoding="utf-8")
    return output_path
