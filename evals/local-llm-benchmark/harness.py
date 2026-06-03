#!/usr/bin/env python3
"""Local-only benchmark artifact harness.

This harness scaffolds benchmark artifacts, records human-supplied raw
responses, and exports dashboard-compatible CSVs. It intentionally contains no
model runner, downloader, network client, or cloud API integration.
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path


HARNESS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_ROOT.parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "eval_results"
PROMPT_PATH = HARNESS_ROOT / "prompts" / "ai-lab-local-llm-core-v0.1.json"
RUBRIC_PATH = HARNESS_ROOT / "rubrics" / "ai-lab-local-llm-rubric-v0.1.json"

TABLE_FIELDS = {
    "models": (
        "id",
        "model_name",
        "model_family",
        "provider",
        "params_b",
        "license",
        "source_url",
        "notes",
    ),
    "model_runs": (
        "id",
        "model_id",
        "date_tested",
        "backend",
        "format",
        "quantization",
        "context_window",
        "hardware",
        "temperature",
        "top_p",
        "tokens_per_sec",
        "ram_usage_gb",
        "stability_notes",
        "run_notes",
    ),
    "eval_scores": (
        "id",
        "run_id",
        "instruction_following",
        "truthfulness_uncertainty",
        "reasoning",
        "coding_debugging",
        "agent_planning",
        "local_ai_lab_usefulness",
        "research_synthesis",
        "business_seo_strategy",
        "long_context",
        "creativity",
        "speed_practicality",
        "total_score",
        "final_label",
    ),
    "decisions": (
        "id",
        "model_id",
        "decision",
        "keep_installed",
        "best_use_case",
        "weakness",
        "retest_condition",
        "created_at",
    ),
}
IMPORT_ORDER = ("models", "model_runs", "eval_scores", "decisions")
RESPONSE_FIELDS = (
    "benchmark_run_id",
    "prompt_set_id",
    "rubric_version",
    "prompt_id",
    "prompt_title",
    "prompt_text_sha256",
    "started_at",
    "completed_at",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "tokens_per_sec",
    "ram_usage_gb",
    "stop_reason",
    "error",
    "raw_response",
    "evaluator_notes",
)


class HarnessError(RuntimeError):
    pass


def _read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _load_jsonl(path):
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise HarnessError(
                    "{} line {} is not valid JSON: {}".format(path, line_number, exc)
                )
    return records


def _sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _blank(value):
    return "" if value is None else value


def _display_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_prompt_set():
    prompt_set = _read_json(PROMPT_PATH)
    seen = set()
    for prompt in prompt_set["prompts"]:
        if prompt["id"] in seen:
            raise HarnessError("Duplicate prompt id: {}".format(prompt["id"]))
        seen.add(prompt["id"])
    return prompt_set


def _load_rubric():
    return _read_json(RUBRIC_PATH)


def _prompt_lookup(prompt_set):
    return {prompt["id"]: prompt for prompt in prompt_set["prompts"]}


def _run_dir(output_root, benchmark_run_id):
    return Path(output_root).resolve() / benchmark_run_id


def _require_absent_or_force(path, force):
    path = Path(path)
    if path.exists() and not force:
        raise HarnessError("{} already exists; pass --force to overwrite it.".format(path))


def _require_absent_empty_or_force(path, force):
    path = Path(path)
    if path.exists() and path.stat().st_size > 0 and not force:
        raise HarnessError("{} already has content; pass --force to overwrite it.".format(path))


def _metadata_from_args(args, prompt_set, rubric, run_dir):
    model_id = args.model_id
    run_id = args.run_id
    return {
        "artifact_version": "local-llm-benchmark-harness-v0.1",
        "benchmark_run_id": args.benchmark_run_id,
        "created_at": _utc_now(),
        "prompt_set_id": prompt_set["prompt_set_id"],
        "rubric_version": rubric["rubric_version"],
        "prompts_path": _display_path(PROMPT_PATH),
        "rubric_path": _display_path(RUBRIC_PATH),
        "artifact_paths": {
            "metadata": _display_path(run_dir / "metadata.json"),
            "raw_responses": _display_path(run_dir / "raw_responses.jsonl"),
            "response_template": _display_path(run_dir / "response-template.jsonl"),
            "evidence": _display_path(run_dir / "evidence.md"),
            "dashboard_import": _display_path(run_dir / "dashboard-import"),
        },
        "dashboard_ids": {
            "model_id": model_id,
            "run_id": run_id,
            "score_id": args.score_id,
            "decision_id": args.decision_id,
        },
        "model": {
            "id": model_id,
            "model_name": args.model_name,
            "model_family": args.model_family,
            "provider": args.provider,
            "params_b": args.params_b,
            "license": args.license,
            "source_url": args.source_url,
            "notes": args.model_notes,
        },
        "run": {
            "id": run_id,
            "model_id": model_id,
            "date_tested": args.date_tested,
            "backend": args.backend,
            "format": args.format,
            "quantization": args.quantization,
            "context_window": args.context_window,
            "hardware": args.hardware,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "tokens_per_sec": args.tokens_per_sec,
            "ram_usage_gb": args.ram_usage_gb,
            "stability_notes": args.stability_notes,
            "run_notes": args.run_notes,
        },
    }


def _response_template_records(metadata, prompt_set):
    records = []
    for prompt in prompt_set["prompts"]:
        records.append(
            {
                "prompt_id": prompt["id"],
                "prompt_title": prompt["title"],
                "started_at": None,
                "completed_at": None,
                "latency_ms": None,
                "input_tokens": None,
                "output_tokens": None,
                "tokens_per_sec": None,
                "ram_usage_gb": None,
                "stop_reason": None,
                "error": None,
                "raw_response": "",
                "evaluator_notes": "",
            }
        )
    return records


def _empty_scores_template(rubric):
    scores = {field: None for field in rubric["metric_fields"]}
    return {
        "id": None,
        "run_id": None,
        "scores": scores,
        "total_score": None,
        "final_label": None,
    }


def _decision_template():
    return {
        "id": None,
        "model_id": None,
        "decision": "watchlist",
        "keep_installed": 0,
        "best_use_case": "",
        "weakness": "",
        "retest_condition": "",
        "created_at": None,
    }


def _evidence_template(metadata, prompt_set):
    lines = [
        "# Benchmark Evidence",
        "",
        "Benchmark run: `{}`".format(metadata["benchmark_run_id"]),
        "",
        "Preserve observations separately from raw responses. Do not paste private raw output into public notes.",
        "",
    ]
    for prompt in prompt_set["prompts"]:
        lines.extend(
            [
                "## {}: {}".format(prompt["id"], prompt["title"]),
                "",
                "- Evaluator observation:",
                "- Score rationale:",
                "- Dashboard summary:",
                "",
            ]
        )
    return "\n".join(lines)


def _manual_run_notes(metadata):
    base_notes = [
        "benchmark_run_id={}".format(metadata["benchmark_run_id"]),
        "prompt_set_id={}".format(metadata["prompt_set_id"]),
        "rubric_version={}".format(metadata["rubric_version"]),
        "raw_artifact={}".format(metadata["artifact_paths"]["raw_responses"]),
    ]
    existing = metadata["run"].get("run_notes")
    if existing:
        base_notes.append(str(existing))
    return " | ".join(base_notes)


def _write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _blank(row.get(field)) for field in fields})


def _validate_score(value, field):
    if value is None or value == "":
        raise HarnessError("Score field {} is required.".format(field))
    score = float(value)
    if score < 0 or score > 100:
        raise HarnessError("Score field {} must be between 0 and 100.".format(field))
    return score


def _load_score_row(scores_path, metadata, rubric):
    if not scores_path:
        return None
    data = _read_json(scores_path)
    score_values = data.get("scores", data)
    row = {
        "id": data.get("id", metadata["dashboard_ids"].get("score_id")),
        "run_id": data.get("run_id", metadata["dashboard_ids"]["run_id"]),
        "total_score": data.get("total_score"),
        "final_label": data.get("final_label"),
    }
    for field in rubric["metric_fields"]:
        row[field] = _validate_score(score_values.get(field), field)
    labels = set(rubric["final_labels"])
    if row["final_label"] not in (None, "") and row["final_label"] not in labels:
        raise HarnessError("Unknown final_label: {}".format(row["final_label"]))
    if row["total_score"] not in (None, ""):
        row["total_score"] = _validate_score(row["total_score"], "total_score")
    return row


def _load_decision_row(decision_path, metadata, rubric):
    if not decision_path:
        return None
    data = _read_json(decision_path)
    decision = data.get("decision")
    if decision not in rubric["decision_values"]:
        raise HarnessError(
            "Decision must be one of: {}".format(", ".join(rubric["decision_values"]))
        )
    keep_installed = _coerce_boolish(data.get("keep_installed"))
    if keep_installed is None:
        keep_installed = 1 if decision == "keep" else 0
    return {
        "id": data.get("id", metadata["dashboard_ids"].get("decision_id")),
        "model_id": data.get("model_id", metadata["dashboard_ids"]["model_id"]),
        "decision": decision,
        "keep_installed": keep_installed,
        "best_use_case": data.get("best_use_case", ""),
        "weakness": data.get("weakness", ""),
        "retest_condition": data.get("retest_condition", ""),
        "created_at": data.get("created_at") or _utc_now(),
    }


def write_dashboard_csvs(run_dir, metadata, rubric, scores_path=None, decision_path=None):
    run_dir = Path(run_dir)
    output_dir = run_dir / "dashboard-import"
    model = dict(metadata["model"])
    run = dict(metadata["run"])
    run["run_notes"] = _manual_run_notes(metadata)
    score_row = _load_score_row(scores_path, metadata, rubric)
    decision_row = _load_decision_row(decision_path, metadata, rubric)

    rows_by_table = {
        "models": [model],
        "model_runs": [run],
        "eval_scores": [score_row] if score_row else [],
        "decisions": [decision_row] if decision_row else [],
    }
    for table_name in IMPORT_ORDER:
        _write_csv(
            output_dir / "{}.csv".format(table_name),
            TABLE_FIELDS[table_name],
            rows_by_table[table_name],
        )
    return output_dir


def _coerce_boolish(value):
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return 1 if value else 0
    normalized = str(value).strip().lower()
    if normalized in ("1", "true", "yes", "y", "keep"):
        return 1
    if normalized in ("0", "false", "no", "n", "skip", "watchlist", "retest"):
        return 0
    raise HarnessError("Cannot parse keep_installed value: {!r}".format(value))


def init_run(args):
    prompt_set = _load_prompt_set()
    rubric = _load_rubric()
    run_dir = _run_dir(args.output_root, args.benchmark_run_id)
    _require_absent_or_force(run_dir, args.force)
    run_dir.mkdir(parents=True, exist_ok=True)
    metadata = _metadata_from_args(args, prompt_set, rubric, run_dir)

    _write_json(run_dir / "metadata.json", metadata)
    _write_jsonl(run_dir / "response-template.jsonl", _response_template_records(metadata, prompt_set))
    _write_jsonl(run_dir / "raw_responses.jsonl", [])
    _write_json(run_dir / "scores-template.json", _empty_scores_template(rubric))
    _write_json(run_dir / "decision-template.json", _decision_template())
    (run_dir / "evidence.md").write_text(
        _evidence_template(metadata, prompt_set), encoding="utf-8"
    )
    write_dashboard_csvs(run_dir, metadata, rubric)
    return run_dir


def _normalize_response_record(source, metadata, prompt):
    normalized = {
        "benchmark_run_id": metadata["benchmark_run_id"],
        "prompt_set_id": metadata["prompt_set_id"],
        "rubric_version": metadata["rubric_version"],
        "prompt_id": prompt["id"],
        "prompt_title": prompt["title"],
        "prompt_text_sha256": _sha256_text(prompt["prompt"]),
        "started_at": source.get("started_at"),
        "completed_at": source.get("completed_at"),
        "latency_ms": source.get("latency_ms"),
        "input_tokens": source.get("input_tokens"),
        "output_tokens": source.get("output_tokens"),
        "tokens_per_sec": source.get("tokens_per_sec"),
        "ram_usage_gb": source.get("ram_usage_gb"),
        "stop_reason": source.get("stop_reason"),
        "error": source.get("error"),
        "raw_response": source.get("raw_response", ""),
        "evaluator_notes": source.get("evaluator_notes", ""),
    }
    return {field: normalized.get(field) for field in RESPONSE_FIELDS}


def record_responses(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    prompts = _prompt_lookup(prompt_set)
    records = _load_jsonl(args.responses_jsonl)
    normalized = []
    seen = set()
    for record in records:
        prompt_id = record.get("prompt_id")
        if prompt_id not in prompts:
            raise HarnessError("Unknown prompt_id in response input: {}".format(prompt_id))
        if prompt_id in seen:
            raise HarnessError("Duplicate response prompt_id: {}".format(prompt_id))
        seen.add(prompt_id)
        normalized.append(_normalize_response_record(record, metadata, prompts[prompt_id]))
    output_path = run_dir / "raw_responses.jsonl"
    _require_absent_empty_or_force(output_path, args.force)
    _write_jsonl(output_path, normalized)
    return output_path


def export_dashboard(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    rubric = _load_rubric()
    return write_dashboard_csvs(
        run_dir,
        metadata,
        rubric,
        scores_path=args.scores_json,
        decision_path=args.decision_json,
    )


def list_prompts(args):
    prompt_set = _load_prompt_set()
    if args.json:
        print(json.dumps(prompt_set, indent=2, sort_keys=True))
        return
    print(prompt_set["prompt_set_id"])
    for prompt in prompt_set["prompts"]:
        print("{}\t{}".format(prompt["id"], prompt["title"]))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Create local benchmark artifacts without calling or downloading models."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-prompts", help="Print local prompt IDs.")
    list_parser.add_argument("--json", action="store_true", help="Print the full prompt JSON.")
    list_parser.set_defaults(func=list_prompts)

    init_parser = subparsers.add_parser(
        "init-run", help="Create a local benchmark run artifact directory."
    )
    init_parser.add_argument("--benchmark-run-id", required=True)
    init_parser.add_argument("--model-name", required=True)
    init_parser.add_argument("--backend", required=True)
    init_parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--model-id", type=int, default=1)
    init_parser.add_argument("--run-id", type=int, default=1)
    init_parser.add_argument("--score-id", type=int, default=1)
    init_parser.add_argument("--decision-id", type=int, default=1)
    init_parser.add_argument("--date-tested", default=date.today().isoformat())
    init_parser.add_argument("--model-family")
    init_parser.add_argument("--provider", default="Local")
    init_parser.add_argument("--params-b", type=float)
    init_parser.add_argument("--license")
    init_parser.add_argument("--source-url")
    init_parser.add_argument("--model-notes")
    init_parser.add_argument("--format")
    init_parser.add_argument("--quantization")
    init_parser.add_argument("--context-window", type=int)
    init_parser.add_argument("--hardware")
    init_parser.add_argument("--temperature", type=float)
    init_parser.add_argument("--top-p", type=float)
    init_parser.add_argument("--tokens-per-sec", type=float)
    init_parser.add_argument("--ram-usage-gb", type=float)
    init_parser.add_argument("--stability-notes")
    init_parser.add_argument("--run-notes")
    init_parser.set_defaults(func=init_run)

    record_parser = subparsers.add_parser(
        "record-responses",
        help="Copy human-supplied response JSONL into the run raw_responses.jsonl.",
    )
    record_parser.add_argument("--run-dir", required=True, type=Path)
    record_parser.add_argument("--responses-jsonl", required=True, type=Path)
    record_parser.add_argument("--force", action="store_true")
    record_parser.set_defaults(func=record_responses)

    export_parser = subparsers.add_parser(
        "export-dashboard", help="Write dashboard-compatible CSVs for a run."
    )
    export_parser.add_argument("--run-dir", required=True, type=Path)
    export_parser.add_argument("--scores-json", type=Path)
    export_parser.add_argument("--decision-json", type=Path)
    export_parser.set_defaults(func=export_dashboard)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except HarnessError as exc:
        print("harness error: {}".format(exc), file=sys.stderr)
        return 2
    if result is not None:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
