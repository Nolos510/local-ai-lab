"""Markdown report generation for local model evaluation results."""

from datetime import datetime
from pathlib import Path

from . import db, model_roles, recommend, score_review

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVAL_RESULTS_DIR = REPO_ROOT / "data" / "eval_results"


def _value(value, fallback=""):
    return fallback if value is None else _markdown_cell(value)


def _markdown_cell(value):
    text = str(value).replace("\n", " ").replace("\r", " ")
    replacements = {
        "\\": "\\\\",
        "|": "\\|",
        "[": "\\[",
        "]": "\\]",
        "(": "\\(",
        ")": "\\)",
        "<": "&lt;",
        ">": "&gt;",
        "!": "\\!",
    }
    return "".join(replacements.get(char, char) for char in text)


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


def _benchmark_run_id(notes):
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith("benchmark_run_id="):
            return part.split("=", 1)[1].strip()
    return ""


def _run_role(row):
    return model_roles.infer_model_role(
        row["model_name"],
        row["model_family"],
        row["provider"],
        row["format"],
    )


def _artifact_review(row, eval_results_dir):
    run_id = _benchmark_run_id(row["run_notes"])
    if not run_id:
        return {"status": "unscored"}
    return score_review.review_state(Path(eval_results_dir) / run_id)


def _evidence_counts(runs, decisions, eval_results_dir):
    counts = {
        "confirmed": 0,
        "draft": 0,
        "quarantined": 0,
        "unscored": 0,
        "non_generation": 0,
        "frontier_ready": 0,
        "confirmed_missing_metrics": 0,
        "missing_run_config": 0,
    }
    confirmed_models = set()
    for row in runs:
        if not model_roles.model_supports_generation(_run_role(row)):
            counts["non_generation"] += 1
            continue
        if any(
            row[field] in (None, "")
            for field in ("quantization", "context_window", "temperature", "top_p")
        ):
            counts["missing_run_config"] += 1
        if row["score_status"] == "confirmed":
            counts["confirmed"] += 1
            confirmed_models.add(row["model_id"])
            if row["tokens_per_sec"] is None or row["ram_usage_gb"] is None:
                counts["confirmed_missing_metrics"] += 1
            else:
                counts["frontier_ready"] += 1
            continue
        if row["score_status"] == "draft":
            counts["draft"] += 1
            continue
        artifact_state = _artifact_review(row, eval_results_dir).get("status")
        if artifact_state == "rejected":
            counts["quarantined"] += 1
        elif artifact_state in ("draft", "machine_reviewed", "disagreement"):
            counts["draft"] += 1
        else:
            counts["unscored"] += 1
    counts["confirmed_models"] = len(confirmed_models)
    counts["decision_models"] = len({row["model_id"] for row in decisions})
    return counts


def generate_markdown_report(
    db_path,
    include_demo=False,
    eval_results_dir=DEFAULT_EVAL_RESULTS_DIR,
):
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
        runs = all_runs if include_demo else _real_rows(all_runs)
        scores = all_scores if include_demo else _real_rows(all_scores)
        decisions = all_decisions if include_demo else _real_rows(all_decisions)
        demo_count = len(_demo_rows(all_summaries))
        counts = {
            "models": len(summaries),
            "model_runs": len(runs),
            "eval_scores": len(scores),
            "decisions": len(decisions),
        }
        evidence = _evidence_counts(runs, decisions, eval_results_dir)
        recommendations = recommend.task_recommendations(scores)
        confirmed = evidence["confirmed"]
        confirmed_models = evidence["confirmed_models"]
        draft = evidence["draft"]
        quarantined = evidence["quarantined"]
        unscored = evidence["unscored"]
        non_generation = evidence["non_generation"]
        decision_models = evidence["decision_models"]
        frontier_ready = evidence["frontier_ready"]
        missing_metrics = evidence["confirmed_missing_metrics"]
        missing_config = evidence["missing_run_config"]

        lines.extend(
            [
                "## What this means",
                "",
                "- Ranked models are imported benchmark results, not installed-model inventory.",
                "- Radar candidates are possible models to evaluate, not scored models.",
                "- My Models is the source of truth for what the dashboard detects locally.",
                "- A confirmed score is authoritative benchmark evidence; a separate "
                "portfolio decision records whether to keep, watch, retest, or remove the model.",
                "- Drafts are pending independent review. Rejected or quarantined runs "
                "remain audit evidence but do not influence rankings.",
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
                "## Evidence Authority",
                "",
                f"- Confirmed score runs: {confirmed} across {confirmed_models} models",
                f"- Valid draft or independent-review-pending runs: {draft}",
                f"- Rejected or automatically quarantined runs: {quarantined}",
                f"- Truly unscored runs: {unscored}",
                f"- Non-generative runs routed outside the LLM rubric: {non_generation}",
                (
                    "- Models with an explicit portfolio decision: "
                    f"{decision_models} of {confirmed_models} confirmed models"
                ),
                "",
                "## Workload Leaders",
                "",
                (
                    "These recommendations use confirmed score evidence only. They "
                    "identify the best measured model per workload, not an install decision."
                ),
                "",
                "| Workload | Recommended model | Confirmed workload score | Why |",
                "| --- | --- | ---: | --- |",
            ]
        )
        if not recommendations.tasks:
            lines.append("| No confirmed workload evidence yet. |  |  |  |")
        for task in recommendations.tasks:
            names = ", ".join(leader.model_name for leader in task.leaders)
            lines.append(
                f"| {_value(task.task)} | {_value(names)} | {task.score:.2f} | "
                "Highest confirmed score for this workload's rubric dimensions. |"
            )
        lines.extend(
            [
                "",
                "## Efficiency Eligibility",
                "",
                (
                    "- Frontier-ready confirmed runs with both tokens/sec and peak RAM: "
                    f"{frontier_ready}"
                ),
                (
                    "- Confirmed runs excluded for missing throughput or peak RAM: "
                    f"{missing_metrics}"
                ),
                (
                    "- Draft/review-pending runs excluded because scores are not "
                    f"confirmed: {draft}"
                ),
                (
                    "- Quarantined runs excluded because their evidence is invalid or "
                    f"retired: {quarantined}"
                ),
                (
                    "- Non-generative runs excluded from the LLM efficiency frontier: "
                    f"{non_generation}"
                ),
                "- The dashboard frontier shows one latest eligible confirmed run per model.",
                "",
                "## Next Actions",
                "",
                (
                    "- Complete independent review or human disposition for "
                    f"{draft} valid draft/review-pending runs."
                ),
                (
                    "- Follow the recorded rerun, rescore, retire, or role-specific "
                    f"remediation for {quarantined} quarantined runs."
                ),
                *(
                    [f"- Capture and score {unscored} truly unscored runs."]
                    if unscored
                    else []
                ),
                (
                    f"- Rerun or re-import {missing_metrics} confirmed runs missing "
                    "throughput or peak RAM."
                ),
                (
                    f"- Backfill or rerun {missing_config} runs missing quantization, "
                    "context window, temperature, or top_p."
                ),
                (
                    "- Record portfolio decisions for "
                    f"{max(0, confirmed_models - decision_models)} confirmed models that "
                    "still lack one."
                ),
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


def write_report(
    db_path,
    output_path,
    include_demo=False,
    eval_results_dir=DEFAULT_EVAL_RESULTS_DIR,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = generate_markdown_report(
        db_path,
        include_demo=include_demo,
        eval_results_dir=eval_results_dir,
    )
    output_path.write_text(report, encoding="utf-8")
    return output_path
