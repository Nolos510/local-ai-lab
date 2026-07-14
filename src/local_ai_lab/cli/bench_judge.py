"""Approval-gated, local-only draft scoring for benchmark response artifacts."""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, urlparse, urlunparse

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_ROOT = REPO_ROOT / "evals" / "local-llm-benchmark"
PROMPT_PATH = HARNESS_ROOT / "prompts" / "ai-lab-local-llm-core-v0.1.json"
RUBRIC_PATH = HARNESS_ROOT / "rubrics" / "ai-lab-local-llm-rubric-v0.1.json"
DEFAULT_OLLAMA_ENDPOINT = "http://127.0.0.1:11434"
SUPPORTED_RUNNERS = ("ollama", "lmstudio-cli", "openai-compatible")
SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

METRIC_FIELDS = (
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
)

SPECIALIST_LABELS = (
    ("coding_debugging", "CODING_SPECIALIST"),
    ("research_synthesis", "RESEARCH_SPECIALIST"),
    ("agent_planning", "AGENT_PLANNER"),
    ("creativity", "CREATIVE_WRITER"),
    ("local_ai_lab_usefulness", "LOCAL_AI_ASSISTANT"),
    ("business_seo_strategy", "SEO_BUSINESS_HELPER"),
)


class JudgeError(RuntimeError):
    """Raised for safe, operator-actionable local judge failures."""


class JudgeOutputError(JudgeError):
    """Raised when a judge response cannot supply honest dimension scores."""


@dataclass(frozen=True)
class JudgePlan:
    run_id: str
    run_dir: Path
    db_path: Path
    dashboard_run_id: int
    dashboard_model_id: int
    dashboard_model_name: str
    judge_model: str
    runner: str
    metadata: dict[str, Any]
    rubric: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    prompt_by_id: dict[str, dict[str, Any]]
    input_skips: tuple[str, ...]
    existing_score_status: str | None


@dataclass(frozen=True)
class JudgeResult:
    judged_prompts: int
    skipped_prompts: tuple[tuple[str, str], ...]
    draft_write: str


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise JudgeError(f"Could not read {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise JudgeError(f"Invalid JSON in {label}: {path}") from exc
    if not isinstance(value, dict):
        raise JudgeError(f"{label} must contain one JSON object: {path}")
    return value


def _benchmark_run_id_from_notes(notes: object) -> str:
    for part in str(notes or "").split("|"):
        key, separator, value = part.strip().partition("=")
        if separator and key == "benchmark_run_id":
            return value.strip()
    return ""


def _dashboard_run(plan_db: Path, run_id: str) -> tuple[int, int, str, str | None]:
    if not plan_db.is_file():
        raise JudgeError(f"Dashboard database does not exist: {plan_db}")
    try:
        with sqlite3.connect(f"{plan_db.resolve().as_uri()}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    r.id AS dashboard_run_id,
                    r.model_id AS dashboard_model_id,
                    r.run_notes,
                    m.model_name,
                    s.score_status
                FROM model_runs r
                JOIN models m ON m.id = r.model_id
                LEFT JOIN eval_scores s ON s.run_id = r.id
                ORDER BY r.id, s.id
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise JudgeError(f"Could not inspect dashboard database: {plan_db}") from exc

    matches = [row for row in rows if _benchmark_run_id_from_notes(row["run_notes"]) == run_id]
    if not matches:
        raise JudgeError(
            f"Run {run_id} is not imported in {plan_db}; import it before judging."
        )
    dashboard_run_ids = {int(row["dashboard_run_id"]) for row in matches}
    if len(dashboard_run_ids) != 1:
        raise JudgeError(f"Run {run_id} maps to multiple dashboard run rows.")
    statuses = {row["score_status"] for row in matches if row["score_status"]}
    if "confirmed" in statuses:
        score_status = "confirmed"
    elif "draft" in statuses:
        score_status = "draft"
    else:
        score_status = None
    row = matches[0]
    return (
        int(row["dashboard_run_id"]),
        int(row["dashboard_model_id"]),
        str(row["model_name"]),
        score_status,
    )


def _load_response_records(
    raw_path: Path,
    prompt_by_id: dict[str, dict[str, Any]],
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    try:
        lines = raw_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise JudgeError(f"Could not read raw response artifact: {raw_path}") from exc
    records: list[dict[str, Any]] = []
    skips: list[str] = []
    seen: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            skips.append(f"line {line_number}: invalid JSON")
            continue
        if not isinstance(value, dict):
            skips.append(f"line {line_number}: response record is not an object")
            continue
        prompt_id = value.get("prompt_id")
        if prompt_id not in prompt_by_id:
            skips.append(f"line {line_number}: unknown prompt id")
            continue
        if prompt_id in seen:
            skips.append(f"line {line_number}: duplicate prompt id {prompt_id}")
            continue
        seen.add(str(prompt_id))
        records.append(value)
    if not records:
        raise JudgeError(f"No valid response rows found in {raw_path}")
    return tuple(records), tuple(skips)


def build_plan(
    *,
    run_id: str,
    eval_results: Path,
    db_path: Path,
    judge_model: str,
    runner: str,
) -> JudgePlan:
    if not SAFE_RUN_ID_RE.fullmatch(run_id or ""):
        raise JudgeError(f"Invalid benchmark run id: {run_id}")
    if not judge_model.strip() or any(
        ord(char) < 32 or ord(char) == 127 for char in judge_model
    ):
        raise JudgeError("Judge model must be one exact local model id without control characters.")
    if runner not in SUPPORTED_RUNNERS:
        raise JudgeError(f"Unsupported judge runner: {runner}")

    run_dir = (Path(eval_results).resolve() / run_id).resolve()
    if run_dir.parent != Path(eval_results).resolve():
        raise JudgeError(f"Invalid benchmark run id: {run_id}")
    metadata = _read_json(run_dir / "metadata.json", label="benchmark metadata")
    if metadata.get("benchmark_run_id") != run_id:
        raise JudgeError("Benchmark metadata run id does not match --run.")
    prompt_set = _read_json(PROMPT_PATH, label="benchmark prompt set")
    rubric = _read_json(RUBRIC_PATH, label="benchmark rubric")
    if tuple(rubric.get("metric_fields") or ()) != METRIC_FIELDS:
        raise JudgeError("Benchmark rubric metric fields do not match the dashboard schema.")
    if metadata.get("prompt_set_id") != prompt_set.get("prompt_set_id"):
        raise JudgeError("Benchmark metadata prompt set does not match the scoring prompt set.")
    if metadata.get("rubric_version") != rubric.get("rubric_version"):
        raise JudgeError("Benchmark metadata rubric version does not match the scoring rubric.")
    prompts = prompt_set.get("prompts")
    if not isinstance(prompts, list):
        raise JudgeError("Benchmark prompt set has no prompts list.")
    prompt_by_id = {
        str(prompt["id"]): prompt
        for prompt in prompts
        if isinstance(prompt, dict) and prompt.get("id")
    }
    records, input_skips = _load_response_records(
        run_dir / "raw_responses.jsonl",
        prompt_by_id,
    )
    dashboard_run_id, model_id, model_name, score_status = _dashboard_run(
        Path(db_path),
        run_id,
    )
    return JudgePlan(
        run_id=run_id,
        run_dir=run_dir,
        db_path=Path(db_path),
        dashboard_run_id=dashboard_run_id,
        dashboard_model_id=model_id,
        dashboard_model_name=model_name,
        judge_model=judge_model,
        runner=runner,
        metadata=metadata,
        rubric=rubric,
        records=records,
        prompt_by_id=prompt_by_id,
        input_skips=input_skips,
        existing_score_status=score_status,
    )


def _validated_local_url(endpoint: str, required_suffix: str) -> ParseResult:
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise JudgeError("Judge endpoint must use http or https and include a host.")
    if parsed.username or parsed.password:
        raise JudgeError("Judge endpoint must not include credentials.")
    host = parsed.hostname.lower()
    if host != "localhost":
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise JudgeError("Judge endpoint must use localhost or a loopback IP.") from exc
        if not address.is_loopback:
            raise JudgeError("Judge endpoint must use localhost or a loopback IP.")
    path = parsed.path.rstrip("/")
    if not path.endswith(required_suffix):
        path = f"{path}/{required_suffix}" if path else f"/{required_suffix}"
    return parsed._replace(path=path, params="", query="", fragment="")


def endpoint_display(runner: str, endpoint: str | None) -> str:
    if runner == "lmstudio-cli":
        return (
            "lms chat <judge-model> -p <rubric-prompt> --ttl <seconds> "
            "--yes --dont-fetch-catalog"
        )
    if runner == "ollama":
        parsed = _validated_local_url(endpoint or DEFAULT_OLLAMA_ENDPOINT, "api/generate")
        return f"POST {urlunparse(parsed)} model=<judge-model> format=json"
    if not endpoint:
        return "POST <required-local-endpoint>/chat/completions model=<judge-model>"
    parsed = _validated_local_url(endpoint, "chat/completions")
    return f"POST {urlunparse(parsed)} model=<judge-model>"


def build_judge_prompt(plan: JudgePlan, record: dict[str, Any]) -> str:
    prompt_id = str(record["prompt_id"])
    prompt = plan.prompt_by_id[prompt_id]
    dimensions = tuple(prompt.get("primary_dimensions") or ())
    unknown_dimensions = [field for field in dimensions if field not in METRIC_FIELDS]
    if not dimensions or unknown_dimensions:
        raise JudgeError(f"Prompt {prompt_id} has invalid primary dimensions.")
    dimension_descriptions = plan.rubric.get("dimensions") or {}
    rubric_subset = {
        "score_scale": plan.rubric.get("score_scale"),
        "dimensions": {
            field: dimension_descriptions.get(field)
            for field in dimensions
        },
        "scoring_notes": plan.rubric.get("scoring_notes"),
    }
    run_metrics = plan.metadata.get("run")
    if not isinstance(run_metrics, dict):
        run_metrics = {}
    required_shape = {
        "prompt_id": prompt_id,
        "scores": {field: 0 for field in dimensions},
    }
    evidence = {
        "prompt_id": prompt_id,
        "title": prompt.get("title"),
        "prompt": prompt.get("prompt"),
        "expected_evidence": prompt.get("expected_evidence"),
        "primary_dimensions": dimensions,
        "model_response": record.get("raw_response", ""),
        "response_error": record.get("error"),
        "evaluator_notes": record.get("evaluator_notes", ""),
        "response_metrics": {
            "latency_ms": record.get("latency_ms"),
            "tokens_per_sec": record.get("tokens_per_sec"),
            "ram_usage_gb": record.get("ram_usage_gb"),
        },
        "run_metrics": {
            "tokens_per_sec": run_metrics.get("tokens_per_sec"),
            "total_latency_seconds": run_metrics.get("total_latency_seconds"),
            "ram_usage_gb": run_metrics.get("ram_usage_gb"),
        },
    }
    return "\n".join(
        (
            "You are a local benchmark judge for AI Lab OS.",
            "Score only the supplied response against the supplied rubric and evidence.",
            "Do not infer hidden capabilities or invent evidence.",
            "Return exactly one JSON object and no Markdown or commentary.",
            "Use exactly this JSON shape and exactly the listed score keys:",
            json.dumps(required_shape, indent=2),
            "Every score must be a finite number from 0 to 100.",
            "Rubric:",
            json.dumps(rubric_subset, indent=2, sort_keys=True),
            "Evidence:",
            json.dumps(evidence, indent=2, sort_keys=True),
        )
    )


def parse_judge_output(
    output: str,
    *,
    prompt_id: str,
    dimensions: tuple[str, ...],
) -> dict[str, float]:
    clean = ANSI_ESCAPE_RE.sub("", str(output)).strip()
    try:
        value = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise JudgeOutputError("unparseable judge output") from exc
    if not isinstance(value, dict) or value.get("prompt_id") != prompt_id:
        raise JudgeOutputError("invalid judge output")
    score_values = value.get("scores")
    if not isinstance(score_values, dict) or set(score_values) != set(dimensions):
        raise JudgeOutputError("invalid judge output")
    scores: dict[str, float] = {}
    for field in dimensions:
        raw_score = score_values.get(field)
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            raise JudgeOutputError("invalid judge output")
        score = float(raw_score)
        if not math.isfinite(score) or score < 0 or score > 100:
            raise JudgeOutputError("invalid judge output")
        scores[field] = score
    return scores


def _post_json(endpoint: ParseResult, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    connection_class = (
        http.client.HTTPSConnection
        if endpoint.scheme == "https"
        else http.client.HTTPConnection
    )
    connection = connection_class(endpoint.hostname, port=endpoint.port, timeout=timeout)
    try:
        connection.request(
            "POST",
            endpoint.path,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException) as exc:
        raise JudgeError("Local judge endpoint request failed.") from exc
    finally:
        connection.close()
    if response.status < 200 or response.status >= 300:
        raise JudgeError(f"Local judge endpoint returned HTTP {response.status}.")
    try:
        value = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise JudgeError("Local judge endpoint response was not JSON.") from exc
    if not isinstance(value, dict):
        raise JudgeError("Local judge endpoint response was not a JSON object.")
    return value


def _openai_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return str(choices[0].get("text") or "")
    content = message.get("content")
    if isinstance(content, list):
        return "".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part)
            for part in content
        )
    return "" if content is None else str(content)


def _resolve_lms_path(path: str | None) -> str:
    if path:
        candidate = Path(path).expanduser()
        if candidate.name != "lms" or not candidate.is_file():
            raise JudgeError(f"LM Studio CLI not found at: {candidate}")
        return str(candidate)
    bundled = Path.home() / ".lmstudio" / "bin" / "lms"
    if bundled.is_file():
        return str(bundled)
    found = shutil.which("lms")
    if found:
        return found
    raise JudgeError("LM Studio CLI not found at ~/.lmstudio/bin/lms or on PATH.")


def invoke_judge(
    *,
    runner: str,
    judge_model: str,
    prompt: str,
    endpoint: str | None,
    timeout: float,
    ttl: int,
    max_tokens: int,
    lms_path: str | None,
) -> str:
    if runner == "lmstudio-cli":
        command = [
            _resolve_lms_path(lms_path),
            "chat",
            judge_model,
            "-p",
            prompt,
            "--ttl",
            str(ttl),
            "--yes",
            "--dont-fetch-catalog",
        ]
        try:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise JudgeError("LM Studio judge command failed or timed out.") from exc
        if result.returncode != 0:
            raise JudgeError(f"LM Studio judge command returned exit {result.returncode}.")
        return result.stdout

    if runner == "ollama":
        parsed = _validated_local_url(endpoint or DEFAULT_OLLAMA_ENDPOINT, "api/generate")
        response = _post_json(
            parsed,
            {
                "model": judge_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "num_predict": max_tokens},
            },
            timeout,
        )
        if response.get("error"):
            raise JudgeError("Ollama judge endpoint returned an error.")
        return str(response.get("response") or "")

    if runner == "openai-compatible":
        if not endpoint:
            raise JudgeError("--endpoint is required for --runner openai-compatible.")
        parsed = _validated_local_url(endpoint, "chat/completions")
        response = _post_json(
            parsed,
            {
                "model": judge_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": max_tokens,
            },
            timeout,
        )
        return _openai_message_content(response)
    raise JudgeError(f"Unsupported judge runner: {runner}")


def _suggest_final_label(scores: dict[str, float]) -> str:
    total_score = round(sum(scores.values()) / len(METRIC_FIELDS), 2)
    if total_score < 45:
        return "SKIP"
    if total_score < 58:
        return "SANDBOX_ONLY"
    if (
        total_score >= 85
        and scores["local_ai_lab_usefulness"] >= 80
        and scores["speed_practicality"] >= 70
    ):
        return "DAILY_DRIVER"
    field, label = max(SPECIALIST_LABELS, key=lambda item: scores[item[0]])
    return label if scores[field] >= 75 else "WATCHLIST"


def _write_draft(plan: JudgePlan, scores: dict[str, float]) -> str:
    total_score = round(sum(scores.values()) / len(METRIC_FIELDS), 2)
    final_label = _suggest_final_label(scores)
    fields = ", ".join(METRIC_FIELDS)
    assignments = ", ".join(f"{field} = ?" for field in METRIC_FIELDS)
    try:
        with sqlite3.connect(plan.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT id, score_status FROM eval_scores WHERE run_id = ? ORDER BY id",
                (plan.dashboard_run_id,),
            ).fetchall()
            if any(row["score_status"] == "confirmed" for row in existing):
                conn.rollback()
                return "skipped; confirmed score protected"
            drafts = [row for row in existing if row["score_status"] == "draft"]
            values = [scores[field] for field in METRIC_FIELDS]
            if drafts:
                if len(drafts) != 1:
                    conn.rollback()
                    raise JudgeError(
                        "Run maps to multiple draft score rows; no score was changed."
                    )
                conn.execute(
                    f"""
                    UPDATE eval_scores
                    SET {assignments}, total_score = ?, final_label = ?, score_status = 'draft'
                    WHERE id = ? AND score_status = 'draft'
                    """,
                    (*values, total_score, final_label, drafts[0]["id"]),
                )
                conn.commit()
                return "updated existing draft"
            next_id = int(
                conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM eval_scores").fetchone()[
                    0
                ]
            )
            placeholders = ", ".join("?" for _ in METRIC_FIELDS)
            conn.execute(
                f"""
                INSERT INTO eval_scores (
                    id, run_id, {fields}, total_score, final_label, score_status
                ) VALUES (?, ?, {placeholders}, ?, ?, 'draft')
                """,
                (next_id, plan.dashboard_run_id, *values, total_score, final_label),
            )
            conn.commit()
            return "inserted"
    except sqlite3.Error as exc:
        raise JudgeError("Could not write the draft score; no score was changed.") from exc


def judge_plan(
    plan: JudgePlan,
    *,
    endpoint: str | None,
    timeout: float,
    ttl: int,
    max_tokens: int,
    lms_path: str | None,
) -> JudgeResult:
    if timeout <= 0 or ttl <= 0 or max_tokens <= 0:
        raise JudgeError("Judge timeout, ttl, and max tokens must be positive.")
    if plan.existing_score_status == "confirmed":
        return JudgeResult(
            judged_prompts=0,
            skipped_prompts=(),
            draft_write="skipped; confirmed score protected",
        )

    dimension_scores: dict[str, list[float]] = {field: [] for field in METRIC_FIELDS}
    skipped: list[tuple[str, str]] = []
    judged = 0
    for record in plan.records:
        prompt_id = str(record["prompt_id"])
        dimensions = tuple(plan.prompt_by_id[prompt_id].get("primary_dimensions") or ())
        prompt = build_judge_prompt(plan, record)
        try:
            output = invoke_judge(
                runner=plan.runner,
                judge_model=plan.judge_model,
                prompt=prompt,
                endpoint=endpoint,
                timeout=timeout,
                ttl=ttl,
                max_tokens=max_tokens,
                lms_path=lms_path,
            )
            scores = parse_judge_output(
                output,
                prompt_id=prompt_id,
                dimensions=dimensions,
            )
        except JudgeOutputError as exc:
            skipped.append((prompt_id, str(exc)))
            continue
        except JudgeError:
            skipped.append((prompt_id, "local judge runner error"))
            continue
        for field, score in scores.items():
            dimension_scores[field].append(score)
        judged += 1

    missing = [field for field, values in dimension_scores.items() if not values]
    if missing:
        write_status = "skipped; missing dimension evidence: {}".format(
            ", ".join(missing)
        )
    else:
        aggregate_scores = {
            field: round(sum(values) / len(values), 2)
            for field, values in dimension_scores.items()
        }
        write_status = _write_draft(plan, aggregate_scores)
    return JudgeResult(
        judged_prompts=judged,
        skipped_prompts=tuple(skipped),
        draft_write=write_status,
    )


__all__ = (
    "DEFAULT_OLLAMA_ENDPOINT",
    "JudgeError",
    "JudgePlan",
    "JudgeResult",
    "METRIC_FIELDS",
    "PROMPT_PATH",
    "RUBRIC_PATH",
    "SUPPORTED_RUNNERS",
    "build_judge_prompt",
    "build_plan",
    "endpoint_display",
    "invoke_judge",
    "judge_plan",
    "parse_judge_output",
)
