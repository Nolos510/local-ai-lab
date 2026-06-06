"""Markdown report generation for local model evaluation results."""

from datetime import datetime
from pathlib import Path

from . import db


def _value(value, fallback=""):
    return fallback if value is None else str(value)


def _score(value):
    return "" if value is None else f"{float(value):.2f}"


def _is_demo_row(row):
    keys = row.keys()
    provider = str(row["provider"] if "provider" in keys else "")
    source_url = str(row["source_url"] if "source_url" in keys else "")
    return provider == "Local Fixture" or source_url.startswith("local-registry://")


def _real_rows(rows):
    return [row for row in rows if not _is_demo_row(row)]


def _demo_rows(rows):
    return [row for row in rows if _is_demo_row(row)]


def generate_markdown_report(db_path, include_demo=False):
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Local Model Performance Report",
        "",
        f"Generated: {generated_at}",
        "",
    ]

    with db.connect(db_path) as conn:
        db.create_schema(conn)
        all_summaries = db.list_model_summaries(conn)
        all_runs = db.list_runs(conn)
        all_scores = db.list_score_details(conn)
        all_decisions = db.list_decisions(conn)
        summaries = all_summaries if include_demo else _real_rows(all_summaries)
        decisions = all_decisions if include_demo else _real_rows(all_decisions)
        demo_count = len(_demo_rows(all_summaries))
        counts = {
            "models": len(summaries),
            "model_runs": len(all_runs if include_demo else _real_rows(all_runs)),
            "eval_scores": len(all_scores if include_demo else _real_rows(all_scores)),
            "decisions": len(decisions),
        }

        lines.extend(
            [
                "## What this means",
                "",
                "- Ranked models are imported benchmark results, not installed-model inventory.",
                "- Radar candidates are possible models to evaluate, not scored models.",
                "- Installed Models is the source of truth for what the dashboard detects locally.",
                "- Scores are only valid after raw responses, confirmed scores, "
                "and decisions exist.",
                "- Demo rows are examples only and are hidden from this report by default.",
                "",
                "## Summary",
                "",
                "- Models tracked: {}".format(counts["models"]),
                "- Runs tracked: {}".format(counts["model_runs"]),
                "- Eval score rows: {}".format(counts["eval_scores"]),
                "- Decisions logged: {}".format(counts["decisions"]),
                f"- Demo fixture models hidden: {0 if include_demo else demo_count}",
                "",
                "## Ranked Models",
                "",
                "| Model | Backend | Quant | Score | Status | Label | Decision | Best use case |",
                "| --- | --- | --- | ---: | --- | --- | --- | --- |",
            ]
        )
        if not summaries:
            lines.append("| No real benchmark imports yet. |  |  |  |  |  |  |  |")
        for row in summaries:
            table_row = (
                "| {model} | {backend} | {quant} | {score} | {status} | "
                "{label} | {decision} | {use} |"
            )
            lines.append(
                table_row.format(
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
        if not decisions:
            lines.append("| No real install/storage decisions yet. |  |  |  |")
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


def write_report(db_path, output_path, include_demo=False):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = generate_markdown_report(db_path, include_demo=include_demo)
    output_path.write_text(report, encoding="utf-8")
    return output_path
