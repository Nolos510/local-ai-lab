#!/usr/bin/env python3
"""Local-only benchmark artifact harness.

This harness scaffolds benchmark artifacts, records human-supplied or
local-endpoint raw responses, asks local judge endpoints for draft scoring
suggestions, and exports dashboard-compatible CSVs. It intentionally contains no
model downloader, cloud API integration, third-party HTTP client, or secret use.
"""

import argparse
import csv
import hashlib
import http.client
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

try:
    from datetime import UTC
except ImportError:  # Python < 3.11 compatibility for system python3.
    from datetime import timezone as _timezone

    UTC = _timezone.utc  # noqa: UP017

HARNESS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_ROOT.parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "eval_results"
PROMPT_PATH = HARNESS_ROOT / "prompts" / "ai-lab-local-llm-core-v0.1.json"
RUBRIC_PATH = HARNESS_ROOT / "rubrics" / "ai-lab-local-llm-rubric-v0.1.json"
DEFAULT_OLLAMA_ENDPOINT = "http://127.0.0.1:11434"
BYTES_PER_GIB = 1024**3
VM_STAT_FIXTURE_ENV = "LOCAL_AI_LAB_FAKE_VM_STAT"

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
        "ttft_seconds",
        "total_latency_seconds",
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
        "score_status",
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
SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


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
                raise HarnessError(f"{path} line {line_number} is not valid JSON: {exc}") from exc
    return records


def _sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now():
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _blank(value):
    return "" if value is None else value


def _safe_csv_cell(value):
    value = _blank(value)
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return value


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


def _validate_local_endpoint(endpoint):
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https"):
        raise HarnessError("Endpoint must use http or https.")
    if not parsed.hostname:
        raise HarnessError("Endpoint must include a host.")
    host = parsed.hostname.lower()
    if host == "localhost":
        return parsed
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise HarnessError(
            "Endpoint host must be localhost or a loopback IP."
        ) from exc
    if address.is_loopback:
        return parsed
    raise HarnessError("Endpoint host must be localhost or a loopback IP.")


def _chat_completions_url(endpoint):
    parsed = _validate_local_endpoint(endpoint)
    path = parsed.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        path = "{}/chat/completions".format(path or "")
    return parsed._replace(path=path, params="", query="", fragment="")


def _ollama_generate_url(endpoint):
    parsed = _validate_local_endpoint(endpoint)
    path = parsed.path.rstrip("/")
    if not path.endswith("/api/generate"):
        path = "{}/api/generate".format(path or "")
    return parsed._replace(path=path, params="", query="", fragment="")


def _safe_endpoint(parsed):
    return urlunparse(parsed._replace(query="", fragment=""))


def _post_chat_completion(endpoint, payload, timeout):
    parsed = _chat_completions_url(endpoint)
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    connection_class = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    port = parsed.port
    conn = connection_class(parsed.hostname, port=port, timeout=timeout)
    try:
        path = parsed.path
        if parsed.query:
            path = f"{path}?{parsed.query}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    finally:
        conn.close()
    if response.status < 200 or response.status >= 300:
        raise HarnessError(f"Local endpoint returned HTTP {response.status}: {response_body[:500]}")
    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Local endpoint response was not JSON: {exc}") from exc


def _post_ollama_generate(endpoint, payload, timeout):
    parsed = _ollama_generate_url(endpoint)
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    connection_class = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    conn = connection_class(parsed.hostname, port=parsed.port, timeout=timeout)
    try:
        path = parsed.path
        if parsed.query:
            path = f"{path}?{parsed.query}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        response_body = response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise HarnessError(f"Ollama endpoint request failed: {exc}") from exc
    finally:
        conn.close()
    if response.status < 200 or response.status >= 300:
        raise HarnessError(
            f"Ollama endpoint returned HTTP {response.status}: {response_body[:500]}"
        )
    try:
        parsed_response = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Ollama endpoint response was not JSON: {exc}") from exc
    if not isinstance(parsed_response, dict):
        raise HarnessError("Ollama endpoint response was not a JSON object.")
    if parsed_response.get("error"):
        raise HarnessError(f"Ollama endpoint returned an error: {parsed_response['error']}")
    return parsed_response


def _message_content(response):
    choices = response.get("choices") or []
    if not choices:
        return ""
    first = choices[0]
    message = first.get("message") or {}
    content = message.get("content")
    if content is None:
        content = first.get("text", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        content = "".join(parts)
    return "" if content is None else str(content)


def _finish_reason(response):
    choices = response.get("choices") or []
    if not choices:
        return None
    return choices[0].get("finish_reason")


def _usage_value(response, key):
    usage = response.get("usage") or {}
    value = usage.get(key)
    return value if isinstance(value, (int, float)) else None


def _max_memory_gb(*values):
    numeric = [float(value) for value in values if value not in (None, "")]
    if not numeric:
        return None
    return round(max(numeric), 3)


def _parse_vm_stat_gb(text):
    if not text:
        return None
    page_size = 4096
    header = re.search(r"page size of ([0-9]+) bytes", text, flags=re.IGNORECASE)
    if header:
        page_size = int(header.group(1))
    pages = {}
    for line in str(text).splitlines():
        match = re.match(r"([^:]+):\s*([0-9]+)\.", line.strip())
        if not match:
            continue
        label = re.sub(r"\s+", " ", match.group(1).strip().lower())
        pages[label] = int(match.group(2))
    used_page_count = sum(
        pages.get(label, 0)
        for label in (
            "pages active",
            "pages inactive",
            "pages speculative",
            "pages wired down",
            "pages occupied by compressor",
        )
    )
    if used_page_count <= 0:
        return None
    return round((used_page_count * page_size) / BYTES_PER_GIB, 3)


def _vm_stat_memory_gb():
    fixture = os.environ.get(VM_STAT_FIXTURE_ENV)
    if fixture:
        return _parse_vm_stat_gb(fixture)
    try:
        result = subprocess.run(
            ["vm_stat"],
            text=True,
            capture_output=True,
            check=False,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return _parse_vm_stat_gb(result.stdout)


def _process_rss_gb(pid):
    try:
        result = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            text=True,
            capture_output=True,
            check=False,
            timeout=1.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    try:
        rss_kib = int(text.splitlines()[-1].strip())
    except ValueError:
        return None
    return round((rss_kib * 1024) / BYTES_PER_GIB, 3)


def _run_subprocess_capture(command, timeout):
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    peak_rss_gb = _process_rss_gb(process.pid)
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "stdout": stdout or "",
                "stderr": stderr or "",
                "returncode": None,
                "timed_out": True,
                "peak_rss_gb": peak_rss_gb,
            }
        try:
            stdout, stderr = process.communicate(timeout=min(0.1, remaining))
            peak_rss_gb = _max_memory_gb(peak_rss_gb, _process_rss_gb(process.pid))
            return {
                "stdout": stdout or "",
                "stderr": stderr or "",
                "returncode": process.returncode,
                "timed_out": False,
                "peak_rss_gb": peak_rss_gb,
            }
        except subprocess.TimeoutExpired:
            peak_rss_gb = _max_memory_gb(peak_rss_gb, _process_rss_gb(process.pid))


def _numeric_value(response, key):
    value = response.get(key)
    return value if isinstance(value, (int, float)) else None


def _nanoseconds_to_seconds(value):
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    return float(value) / 1_000_000_000.0


def _ollama_tokens_per_sec(response, latency_ms):
    output_tokens = _numeric_value(response, "eval_count")
    if not output_tokens:
        return None
    eval_seconds = _nanoseconds_to_seconds(_numeric_value(response, "eval_duration"))
    if eval_seconds:
        return round(float(output_tokens) / eval_seconds, 2)
    if latency_ms > 0:
        return round(float(output_tokens) / (latency_ms / 1000.0), 2)
    return None


def _parse_rate_value(text):
    match = re.search(
        r"(?:(?:tokens[/ -]?(?:second|sec)|tokens[ -]?per[ -]?(?:second|sec)):?"
        r"[ \t]*([0-9]+(?:\.[0-9]+)?)|"
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"(?:tok/s|tokens[/ -]?sec|tokens[ -]?per[ -]?(?:second|sec)))",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group(1) or match.group(2))


def _parse_token_count(text):
    match = re.search(r"([0-9]+)[ \t]*tokens?", text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _resolve_lms_path(path=None):
    if path:
        candidate = Path(path).expanduser()
        if candidate.name != "lms":
            raise HarnessError("LM Studio CLI path must point to an `lms` executable.")
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        raise HarnessError(f"LM Studio CLI not found at: {candidate}")
    bundled = Path.home() / ".lmstudio" / "bin" / "lms"
    if bundled.exists() and bundled.is_file():
        return str(bundled)
    found = shutil.which("lms")
    if found:
        return found
    raise HarnessError("LM Studio CLI not found at ~/.lmstudio/bin/lms or on PATH.")


def _parse_lms_stats(text):
    stats = {}
    tokens_per_sec = _parse_rate_value(text)
    if tokens_per_sec:
        stats["tokens_per_sec"] = tokens_per_sec
    input_pattern = (
        r"(?:([0-9]+)[ \t]*(?:input|prompt)[ \t]*tokens?|"
        r"(?:input|prompt)[ \t]*tokens?:[ \t]*([0-9]+))"
    )
    input_tokens = re.search(
        input_pattern,
        text,
        flags=re.IGNORECASE,
    )
    if input_tokens:
        stats["input_tokens"] = int(input_tokens.group(1) or input_tokens.group(2))
    output_pattern = (
        r"(?:([0-9]+)[ \t]*(?:output|completion|predicted)[ \t]*tokens?|"
        r"(?:output|completion|predicted)[ \t]*tokens?:[ \t]*([0-9]+))"
    )
    output_tokens = re.search(
        output_pattern,
        text,
        flags=re.IGNORECASE,
    )
    if output_tokens:
        stats["output_tokens"] = int(output_tokens.group(1) or output_tokens.group(2))
    return stats


def _parse_mlx_lm_stats(text):
    stats = {}
    for line in str(text).splitlines():
        normalized = line.strip().lower()
        if not normalized:
            continue
        if "prompt" in normalized:
            token_count = _parse_token_count(line)
            if token_count is not None:
                stats.setdefault("input_tokens", token_count)
        if any(
            label in normalized
            for label in ("generation", "generated", "completion", "output", "predicted")
        ):
            token_count = _parse_token_count(line)
            if token_count is not None:
                stats["output_tokens"] = token_count
            rate_value = _parse_rate_value(line)
            if rate_value is not None:
                stats["tokens_per_sec"] = rate_value
    if "tokens_per_sec" not in stats:
        rate_value = _parse_rate_value(text)
        if rate_value is not None:
            stats["tokens_per_sec"] = rate_value
    return stats


def _parse_llama_cpp_count(line):
    match = re.search(r"/[ \t]*([0-9]+)[ \t]*(?:tokens?|runs?)", line, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return _parse_token_count(line)


def _parse_llama_cpp_stats(text):
    stats = {}
    for line in str(text).splitlines():
        normalized = line.strip().lower()
        if not normalized:
            continue
        if "prompt eval time" in normalized:
            token_count = _parse_llama_cpp_count(line)
            if token_count is not None:
                stats["input_tokens"] = token_count
            continue
        if "eval time" in normalized and "prompt eval" not in normalized:
            rate_value = _parse_rate_value(line)
            token_count = _parse_llama_cpp_count(line)
            if rate_value is not None:
                stats["tokens_per_sec"] = rate_value
                if token_count is not None:
                    stats["output_tokens"] = token_count
    return stats


def _run_lms_chat(lms_path, model_id, prompt, timeout, ttl):
    command = [
        lms_path,
        "chat",
        model_id,
        "-p",
        prompt,
        "--stats",
        "--ttl",
        str(ttl),
        "--yes",
        "--dont-fetch-catalog",
    ]
    result = _run_subprocess_capture(command, timeout)
    if result["timed_out"]:
        return {
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": None,
            "error": f"LM Studio CLI timed out after {timeout} seconds.",
            "peak_rss_gb": result.get("peak_rss_gb"),
        }
    output = result["stdout"]
    error_output = result["stderr"]
    error = None
    if result["returncode"] != 0:
        detail = (error_output or output).strip()
        error = f"LM Studio CLI returned exit {result['returncode']}: {detail[:500]}"
    return {
        "stdout": output,
        "stderr": error_output,
        "returncode": result["returncode"],
        "error": error,
        "peak_rss_gb": result.get("peak_rss_gb"),
    }


def _resolve_llama_cli_path(path=None):
    if path:
        candidate = Path(path).expanduser()
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        raise HarnessError(f"llama.cpp CLI not found at: {candidate}")
    found = shutil.which("llama-cli")
    if found:
        return found
    raise HarnessError("llama.cpp CLI not found on PATH as `llama-cli`.")


def _run_llama_cpp_generate(llama_cli_path, model_id, prompt, timeout, max_tokens):
    command = [
        llama_cli_path,
        "-m",
        model_id,
        "-p",
        prompt,
        "-n",
        str(max_tokens),
        "--no-display-prompt",
    ]
    result = _run_subprocess_capture(command, timeout)
    if result["timed_out"]:
        return {
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": None,
            "error": f"llama.cpp CLI timed out after {timeout} seconds.",
            "peak_rss_gb": result.get("peak_rss_gb"),
        }
    output = result["stdout"]
    error_output = result["stderr"]
    error = None
    if result["returncode"] != 0:
        detail = (error_output or output).strip()
        error = f"llama.cpp CLI returned exit {result['returncode']}: {detail[:500]}"
    return {
        "stdout": output,
        "stderr": error_output,
        "returncode": result["returncode"],
        "error": error,
        "peak_rss_gb": result.get("peak_rss_gb"),
    }


def _resolve_mlx_python_path(path=None):
    if path:
        candidate = Path(path).expanduser()
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        raise HarnessError(f"MLX-LM Python executable not found at: {candidate}")
    return sys.executable


def _run_mlx_lm_generate(python_path, model_id, prompt, timeout, max_tokens):
    command = [
        python_path,
        "-m",
        "mlx_lm",
        "generate",
        "--model",
        model_id,
        "--prompt",
        prompt,
        "--max-tokens",
        str(max_tokens),
    ]
    result = _run_subprocess_capture(command, timeout)
    if result["timed_out"]:
        return {
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": None,
            "error": f"MLX-LM generation timed out after {timeout} seconds.",
            "peak_rss_gb": result.get("peak_rss_gb"),
        }
    output = result["stdout"]
    error_output = result["stderr"]
    error = None
    if result["returncode"] != 0:
        detail = (error_output or output).strip()
        error = f"MLX-LM generation returned exit {result['returncode']}: {detail[:500]}"
    return {
        "stdout": output,
        "stderr": error_output,
        "returncode": result["returncode"],
        "error": error,
        "peak_rss_gb": result.get("peak_rss_gb"),
    }


def _extract_json_object(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def _load_rubric():
    return _read_json(RUBRIC_PATH)


def _prompt_lookup(prompt_set):
    return {prompt["id"]: prompt for prompt in prompt_set["prompts"]}


def _run_dir(output_root, benchmark_run_id):
    benchmark_run_id = str(benchmark_run_id or "")
    if not SAFE_RUN_ID_RE.fullmatch(benchmark_run_id):
        raise HarnessError(f"Invalid benchmark_run_id: {benchmark_run_id}")
    root = Path(output_root).resolve()
    run_dir = (root / benchmark_run_id).resolve()
    try:
        run_dir.relative_to(root)
    except ValueError as exc:
        raise HarnessError(f"Invalid benchmark_run_id: {benchmark_run_id}") from exc
    return run_dir


def _require_absent_or_force(path, force):
    path = Path(path)
    if path.exists() and not force:
        raise HarnessError(f"{path} already exists; pass --force to overwrite it.")


def _require_absent_empty_or_force(path, force):
    path = Path(path)
    if path.exists() and path.stat().st_size > 0 and not force:
        raise HarnessError(f"{path} already has content; pass --force to overwrite it.")


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
            "ttft_seconds": args.ttft_seconds,
            "total_latency_seconds": args.total_latency_seconds,
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
        "score_status": "confirmed",
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
        "Preserve observations separately from raw responses. Do not paste "
        "private raw output into public notes.",
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
            writer.writerow({field: _safe_csv_cell(row.get(field)) for field in fields})


def _apply_run_perf_summary(metadata, records):
    latencies_ms = [
        float(record.get("latency_ms"))
        for record in records
        if record.get("latency_ms") not in (None, "")
    ]
    output_tokens = [
        float(record.get("output_tokens"))
        for record in records
        if record.get("output_tokens") not in (None, "")
    ]
    tokens_per_sec = [
        float(record.get("tokens_per_sec"))
        for record in records
        if record.get("tokens_per_sec") not in (None, "")
    ]
    ram_values = [
        float(record.get("ram_usage_gb"))
        for record in records
        if record.get("ram_usage_gb") not in (None, "")
    ]
    total_latency_seconds = round(sum(latencies_ms) / 1000.0, 3) if latencies_ms else None
    run = metadata["run"]
    if total_latency_seconds is not None:
        run["total_latency_seconds"] = total_latency_seconds
    if output_tokens and total_latency_seconds and total_latency_seconds > 0:
        run["tokens_per_sec"] = round(sum(output_tokens) / total_latency_seconds, 2)
    elif tokens_per_sec and run.get("tokens_per_sec") in (None, ""):
        run["tokens_per_sec"] = round(sum(tokens_per_sec) / len(tokens_per_sec), 2)
    if ram_values and run.get("ram_usage_gb") in (None, ""):
        run["ram_usage_gb"] = round(max(ram_values), 2)
    run.setdefault("ttft_seconds", None)
    return metadata


def _write_metadata_with_perf(run_dir, metadata, records):
    _apply_run_perf_summary(metadata, records)
    _write_json(Path(run_dir) / "metadata.json", metadata)


def _validate_score(value, field):
    if value is None or value == "":
        raise HarnessError(f"Score field {field} is required.")
    score = float(value)
    if score < 0 or score > 100:
        raise HarnessError(f"Score field {field} must be between 0 and 100.")
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
        "score_status": data.get("score_status", "confirmed"),
    }
    if row["score_status"] not in ("confirmed", "draft"):
        raise HarnessError("score_status must be confirmed or draft.")
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
            output_dir / f"{table_name}.csv",
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
    raise HarnessError(f"Cannot parse keep_installed value: {value!r}")


def init_run(args):
    prompt_set = _load_prompt_set()
    rubric = _load_rubric()
    run_dir = _run_dir(args.output_root, args.benchmark_run_id)
    _require_absent_or_force(run_dir, args.force)
    run_dir.mkdir(parents=True, exist_ok=True)
    metadata = _metadata_from_args(args, prompt_set, rubric, run_dir)

    _write_json(run_dir / "metadata.json", metadata)
    _write_jsonl(
        run_dir / "response-template.jsonl",
        _response_template_records(metadata, prompt_set),
    )
    _write_jsonl(run_dir / "raw_responses.jsonl", [])
    _write_json(run_dir / "scores-template.json", _empty_scores_template(rubric))
    _write_json(run_dir / "decision-template.json", _decision_template())
    (run_dir / "evidence.md").write_text(_evidence_template(metadata, prompt_set), encoding="utf-8")
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


def _capture_log_error(error):
    if not error:
        return ""
    text = _neutralize_terminal(error)
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    for prefix in (
        "llama.cpp CLI returned exit ",
        "MLX-LM generation returned exit ",
        "LM Studio CLI returned exit ",
    ):
        if text.startswith(prefix) and ":" in text:
            text = text.split(":", 1)[0]
            break
    if len(text) > 500:
        return text[:500] + "...[truncated]"
    return text


def _append_cli_capture_metadata(log_lines, prompt_id, source, returncode):
    log_lines.extend(
        [
            f"## {prompt_id}",
            f"returncode={_blank(returncode)}",
            f"latency_ms={_blank(source.get('latency_ms'))}",
            f"input_tokens={_blank(source.get('input_tokens'))}",
            f"output_tokens={_blank(source.get('output_tokens'))}",
            f"tokens_per_sec={_blank(source.get('tokens_per_sec'))}",
            f"stop_reason={_blank(source.get('stop_reason'))}",
            f"error={_capture_log_error(source.get('error'))}",
            "",
        ]
    )


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
            raise HarnessError(f"Unknown prompt_id in response input: {prompt_id}")
        if prompt_id in seen:
            raise HarnessError(f"Duplicate response prompt_id: {prompt_id}")
        seen.add(prompt_id)
        normalized.append(_normalize_response_record(record, metadata, prompts[prompt_id]))
    output_path = run_dir / "raw_responses.jsonl"
    _require_absent_empty_or_force(output_path, args.force)
    _write_jsonl(output_path, normalized)
    return output_path


def run_local(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    model_name = args.model or metadata["model"]["model_name"]
    endpoint = _safe_endpoint(_chat_completions_url(args.endpoint))
    raw_path = run_dir / "raw_responses.jsonl"
    _require_absent_empty_or_force(raw_path, args.force)

    records = []
    for prompt in prompt_set["prompts"]:
        started_at = _utc_now()
        started = time.monotonic()
        source = {
            "prompt_id": prompt["id"],
            "started_at": started_at,
            "raw_response": "",
            "error": None,
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt["prompt"]}],
            "temperature": (
                args.temperature
                if args.temperature is not None
                else metadata["run"].get("temperature")
            ),
            "top_p": args.top_p if args.top_p is not None else metadata["run"].get("top_p"),
            "max_tokens": args.max_tokens,
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        memory_before = _vm_stat_memory_gb()
        try:
            response = _post_chat_completion(args.endpoint, payload, args.timeout)
            completed = time.monotonic()
            memory_after = _vm_stat_memory_gb()
            output_tokens = _usage_value(response, "completion_tokens")
            latency_ms = int(round((completed - started) * 1000))
            source.update(
                {
                    "completed_at": _utc_now(),
                    "latency_ms": latency_ms,
                    "input_tokens": _usage_value(response, "prompt_tokens"),
                    "output_tokens": output_tokens,
                    "tokens_per_sec": (
                        round(float(output_tokens) / (latency_ms / 1000.0), 2)
                        if output_tokens and latency_ms > 0
                        else None
                    ),
                    "stop_reason": _finish_reason(response),
                    "ram_usage_gb": _max_memory_gb(memory_before, memory_after),
                    "raw_response": _message_content(response),
                }
            )
        except HarnessError as exc:
            memory_after = _vm_stat_memory_gb()
            source.update(
                {
                    "completed_at": _utc_now(),
                    "latency_ms": int(round((time.monotonic() - started) * 1000)),
                    "error": str(exc),
                    "ram_usage_gb": _max_memory_gb(memory_before, memory_after),
                    "stop_reason": "error",
                }
            )
        records.append(_normalize_response_record(source, metadata, prompt))

    _write_metadata_with_perf(run_dir, metadata, records)
    _write_jsonl(raw_path, records)
    evidence_path = run_dir / "evidence.md"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Local Runner\n\n")
        handle.write(f"- Endpoint: `{endpoint}`\n")
        handle.write(f"- Model argument: `{model_name}`\n")
        handle.write(f"- Completed at: `{_utc_now()}`\n")
        handle.write(f"- Prompt records: `{len(records)}`\n")
    return raw_path


def run_ollama(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    endpoint = _safe_endpoint(_ollama_generate_url(args.endpoint))
    raw_path = run_dir / "raw_responses.jsonl"
    log_path = run_dir / "ollama-capture.log"
    _require_absent_empty_or_force(raw_path, args.force)
    _require_absent_empty_or_force(log_path, args.force)

    records = []
    log_lines = [
        "Ollama API capture",
        "benchmark_run_id={}".format(metadata["benchmark_run_id"]),
        f"model_id={args.model_id}",
        f"endpoint={endpoint}",
        f"started_at={_utc_now()}",
        "command_shape=POST <ollama-endpoint>/api/generate stream=false",
        "",
    ]
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    for prompt in prompt_set["prompts"]:
        started_at = _utc_now()
        started = time.monotonic()
        source = {
            "prompt_id": prompt["id"],
            "started_at": started_at,
            "raw_response": "",
            "error": None,
        }
        options = {
            "temperature": (
                args.temperature
                if args.temperature is not None
                else metadata["run"].get("temperature")
            ),
            "top_p": args.top_p if args.top_p is not None else metadata["run"].get("top_p"),
            "num_predict": args.max_tokens,
        }
        options = {key: value for key, value in options.items() if value is not None}
        payload = {
            "model": args.model_id,
            "prompt": prompt["prompt"],
            "stream": False,
        }
        if options:
            payload["options"] = options
        memory_before = _vm_stat_memory_gb()
        try:
            response = _post_ollama_generate(args.endpoint, payload, args.timeout)
            completed = time.monotonic()
            memory_after = _vm_stat_memory_gb()
            latency_ms = int(round((completed - started) * 1000))
            input_tokens = _numeric_value(response, "prompt_eval_count")
            output_tokens = _numeric_value(response, "eval_count")
            source.update(
                {
                    "completed_at": _utc_now(),
                    "latency_ms": latency_ms,
                    "input_tokens": int(input_tokens) if input_tokens is not None else None,
                    "output_tokens": int(output_tokens) if output_tokens is not None else None,
                    "tokens_per_sec": _ollama_tokens_per_sec(response, latency_ms),
                    "stop_reason": response.get("done_reason")
                    or ("done" if response.get("done") is True else None),
                    "ram_usage_gb": _max_memory_gb(memory_before, memory_after),
                    "raw_response": str(response.get("response") or ""),
                }
            )
        except HarnessError as exc:
            memory_after = _vm_stat_memory_gb()
            latency_ms = int(round((time.monotonic() - started) * 1000))
            source.update(
                {
                    "completed_at": _utc_now(),
                    "latency_ms": latency_ms,
                    "error": str(exc),
                    "ram_usage_gb": _max_memory_gb(memory_before, memory_after),
                    "stop_reason": "error",
                }
            )
        records.append(_normalize_response_record(source, metadata, prompt))
        log_lines.extend(
            [
                "## {}".format(prompt["id"]),
                f"latency_ms={source.get('latency_ms')}",
                "input_tokens={}".format(source.get("input_tokens") or ""),
                "output_tokens={}".format(source.get("output_tokens") or ""),
                "tokens_per_sec={}".format(source.get("tokens_per_sec") or ""),
                "stop_reason={}".format(source.get("stop_reason") or ""),
                "error={}".format(source.get("error") or ""),
                "",
            ]
        )
        log_path.write_text("\n".join(log_lines), encoding="utf-8")

    _write_metadata_with_perf(run_dir, metadata, records)
    _write_jsonl(raw_path, records)
    evidence_path = run_dir / "evidence.md"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Ollama Runner\n\n")
        handle.write(f"- Endpoint: `{endpoint}`\n")
        handle.write("- Command shape: `POST <ollama-endpoint>/api/generate stream=false`\n")
        handle.write(f"- Model id: `{args.model_id}`\n")
        handle.write(f"- Completed at: `{_utc_now()}`\n")
        handle.write(f"- Prompt records: `{len(records)}`\n")
        handle.write(f"- Capture log: `{_display_path(log_path)}`\n")
    return raw_path


def run_llama_cpp(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    llama_cli_path = _resolve_llama_cli_path(args.llama_cli_path)
    raw_path = run_dir / "raw_responses.jsonl"
    log_path = run_dir / "llama-cpp-capture.log"
    _require_absent_empty_or_force(raw_path, args.force)
    _require_absent_empty_or_force(log_path, args.force)

    records = []
    log_lines = [
        "llama.cpp CLI capture",
        "benchmark_run_id={}".format(metadata["benchmark_run_id"]),
        f"model_id={args.model_id}",
        f"started_at={_utc_now()}",
        "command_shape=llama-cli -m <model-id> -p <prompt> "
        f"-n {args.max_tokens} --no-display-prompt",
        "",
    ]
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    for prompt in prompt_set["prompts"]:
        started_at = _utc_now()
        started = time.monotonic()
        source = {
            "prompt_id": prompt["id"],
            "started_at": started_at,
            "raw_response": "",
            "error": None,
        }
        memory_before = _vm_stat_memory_gb()
        result = _run_llama_cpp_generate(
            llama_cli_path,
            args.model_id,
            prompt["prompt"],
            args.timeout,
            args.max_tokens,
        )
        completed = time.monotonic()
        memory_after = _vm_stat_memory_gb()
        latency_ms = int(round((completed - started) * 1000))
        combined_output = "\n".join(part for part in (result["stdout"], result["stderr"]) if part)
        stats = _parse_llama_cpp_stats(combined_output)
        source.update(
            {
                "completed_at": _utc_now(),
                "latency_ms": latency_ms,
                "input_tokens": stats.get("input_tokens"),
                "output_tokens": stats.get("output_tokens"),
                "tokens_per_sec": stats.get("tokens_per_sec"),
                "stop_reason": ("cli_exit_0" if result["returncode"] == 0 else "error"),
                "error": result["error"],
                "ram_usage_gb": _max_memory_gb(
                    memory_before,
                    memory_after,
                    result.get("peak_rss_gb"),
                ),
                "raw_response": result["stdout"].strip(),
            }
        )
        records.append(_normalize_response_record(source, metadata, prompt))
        _append_cli_capture_metadata(log_lines, prompt["id"], source, result["returncode"])
        log_path.write_text("\n".join(log_lines), encoding="utf-8")

    _write_metadata_with_perf(run_dir, metadata, records)
    _write_jsonl(raw_path, records)
    evidence_path = run_dir / "evidence.md"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## llama.cpp Runner\n\n")
        handle.write(
            "- Command shape: "
            f"`llama-cli -m <model-id> -p <prompt> -n {args.max_tokens} "
            "--no-display-prompt`\n"
        )
        handle.write(f"- Model id: `{args.model_id}`\n")
        handle.write(f"- Completed at: `{_utc_now()}`\n")
        handle.write(f"- Prompt records: `{len(records)}`\n")
        handle.write(f"- Capture log: `{_display_path(log_path)}`\n")
    return raw_path


def run_mlx_lm(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    python_path = _resolve_mlx_python_path(args.python_path)
    raw_path = run_dir / "raw_responses.jsonl"
    log_path = run_dir / "mlx-lm-capture.log"
    _require_absent_empty_or_force(raw_path, args.force)
    _require_absent_empty_or_force(log_path, args.force)

    records = []
    log_lines = [
        "MLX-LM capture",
        "benchmark_run_id={}".format(metadata["benchmark_run_id"]),
        f"model_id={args.model_id}",
        f"started_at={_utc_now()}",
        "command_shape=python -m mlx_lm generate --model <model-id> "
        f"--prompt <prompt> --max-tokens {args.max_tokens}",
        "",
    ]
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    for prompt in prompt_set["prompts"]:
        started_at = _utc_now()
        started = time.monotonic()
        source = {
            "prompt_id": prompt["id"],
            "started_at": started_at,
            "raw_response": "",
            "error": None,
        }
        memory_before = _vm_stat_memory_gb()
        result = _run_mlx_lm_generate(
            python_path,
            args.model_id,
            prompt["prompt"],
            args.timeout,
            args.max_tokens,
        )
        completed = time.monotonic()
        memory_after = _vm_stat_memory_gb()
        latency_ms = int(round((completed - started) * 1000))
        combined_output = "\n".join(part for part in (result["stdout"], result["stderr"]) if part)
        stats = _parse_mlx_lm_stats(combined_output)
        output_tokens = stats.get("output_tokens")
        source.update(
            {
                "completed_at": _utc_now(),
                "latency_ms": latency_ms,
                "input_tokens": stats.get("input_tokens"),
                "output_tokens": output_tokens,
                "tokens_per_sec": stats.get("tokens_per_sec")
                or (
                    round(float(output_tokens) / (latency_ms / 1000.0), 2)
                    if output_tokens and latency_ms > 0
                    else None
                ),
                "stop_reason": ("cli_exit_0" if result["returncode"] == 0 else "error"),
                "error": result["error"],
                "ram_usage_gb": _max_memory_gb(
                    memory_before,
                    memory_after,
                    result.get("peak_rss_gb"),
                ),
                "raw_response": result["stdout"].strip(),
            }
        )
        records.append(_normalize_response_record(source, metadata, prompt))
        _append_cli_capture_metadata(log_lines, prompt["id"], source, result["returncode"])
        log_path.write_text("\n".join(log_lines), encoding="utf-8")

    _write_metadata_with_perf(run_dir, metadata, records)
    _write_jsonl(raw_path, records)
    evidence_path = run_dir / "evidence.md"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## MLX-LM Runner\n\n")
        handle.write(
            "- Command shape: "
            "`python -m mlx_lm generate --model <model-id> --prompt <prompt> "
            f"--max-tokens {args.max_tokens}`\n"
        )
        handle.write(f"- Model id: `{args.model_id}`\n")
        handle.write(f"- Completed at: `{_utc_now()}`\n")
        handle.write(f"- Prompt records: `{len(records)}`\n")
        handle.write(f"- Capture log: `{_display_path(log_path)}`\n")
    return raw_path


def run_lmstudio_cli(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    prompt_set = _load_prompt_set()
    lms_path = _resolve_lms_path(args.lms_path)
    raw_path = run_dir / "raw_responses.jsonl"
    log_path = run_dir / "lms-cli-capture.log"
    _require_absent_empty_or_force(raw_path, args.force)
    _require_absent_empty_or_force(log_path, args.force)

    records = []
    log_lines = [
        "LM Studio CLI capture",
        "benchmark_run_id={}".format(metadata["benchmark_run_id"]),
        f"model_id={args.model_id}",
        f"started_at={_utc_now()}",
        "command_shape="
        f"lms chat <model-id> -p <prompt> --stats --ttl {args.ttl} "
        "--yes --dont-fetch-catalog",
        "",
    ]
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    for prompt in prompt_set["prompts"]:
        started_at = _utc_now()
        started = time.monotonic()
        source = {
            "prompt_id": prompt["id"],
            "started_at": started_at,
            "raw_response": "",
            "error": None,
        }
        memory_before = _vm_stat_memory_gb()
        result = _run_lms_chat(
            lms_path,
            args.model_id,
            prompt["prompt"],
            args.timeout,
            args.ttl,
        )
        completed = time.monotonic()
        memory_after = _vm_stat_memory_gb()
        latency_ms = int(round((completed - started) * 1000))
        combined_output = "\n".join(part for part in (result["stdout"], result["stderr"]) if part)
        stats = _parse_lms_stats(combined_output)
        source.update(
            {
                "completed_at": _utc_now(),
                "latency_ms": latency_ms,
                "input_tokens": stats.get("input_tokens"),
                "output_tokens": stats.get("output_tokens"),
                "tokens_per_sec": stats.get("tokens_per_sec"),
                "stop_reason": ("cli_exit_0" if result["returncode"] == 0 else "error"),
                "error": result["error"],
                "ram_usage_gb": _max_memory_gb(
                    memory_before,
                    memory_after,
                    result.get("peak_rss_gb"),
                ),
                "raw_response": result["stdout"].strip(),
            }
        )
        records.append(_normalize_response_record(source, metadata, prompt))
        _append_cli_capture_metadata(log_lines, prompt["id"], source, result["returncode"])
        log_path.write_text("\n".join(log_lines), encoding="utf-8")

    _write_metadata_with_perf(run_dir, metadata, records)
    _write_jsonl(raw_path, records)
    evidence_path = run_dir / "evidence.md"
    with evidence_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## LM Studio CLI Runner\n\n")
        handle.write(
            "- Command shape: "
            f"`lms chat <model-id> -p <prompt> --stats --ttl {args.ttl} "
            "--yes --dont-fetch-catalog`\n"
        )
        handle.write(f"- Model id: `{args.model_id}`\n")
        handle.write(f"- Completed at: `{_utc_now()}`\n")
        handle.write(f"- Prompt records: `{len(records)}`\n")
        handle.write(f"- Capture log: `{_display_path(log_path)}`\n")
    return raw_path


def _neutralize_terminal(value):
    return "".join(
        char if char in ("\n", "\t") or ord(char) >= 32 else f"\\x{ord(char):02x}"
        for char in str(value)
    )


def _judge_prompt(metadata, raw_records, rubric):
    compact_records = [
        {
            "prompt_id": record.get("prompt_id"),
            "prompt_title": record.get("prompt_title"),
            "error": record.get("error"),
            "raw_response": record.get("raw_response", ""),
            "evaluator_notes": record.get("evaluator_notes", ""),
        }
        for record in raw_records
    ]
    return "\n".join(
        [
            "You are a local benchmark judge for AI Lab OS.",
            "Use only the supplied benchmark responses. Do not infer hidden capabilities.",
            "Return only one JSON object.",
            "Required JSON shape:",
            json.dumps(
                {
                    "scores": {field: 0 for field in rubric["metric_fields"]},
                    "total_score": 0,
                    "final_label": "WATCHLIST",
                    "rationale": "short overall rationale",
                    "metric_rationales": {
                        field: "short rationale" for field in rubric["metric_fields"]
                    },
                },
                indent=2,
            ),
            "Scores must be numbers from 0 to 100.",
            "Valid final labels: {}".format(", ".join(rubric["final_labels"])),
            "Benchmark metadata:",
            json.dumps(metadata, indent=2, sort_keys=True),
            "Raw response records:",
            json.dumps(compact_records, indent=2, sort_keys=True),
        ]
    )


def suggest_scores(args):
    run_dir = Path(args.run_dir).resolve()
    metadata = _read_json(run_dir / "metadata.json")
    rubric = _load_rubric()
    raw_records = _load_jsonl(run_dir / "raw_responses.jsonl")
    output_path = args.out or run_dir / "draft-scores.json"
    _require_absent_or_force(output_path, args.force)
    judge_model = args.judge_model or "local-judge"
    endpoint = _safe_endpoint(_chat_completions_url(args.endpoint))
    prompt = _judge_prompt(metadata, raw_records, rubric)
    response = _post_chat_completion(
        args.endpoint,
        {
            "model": judge_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
        },
        args.timeout,
    )
    content = _message_content(response)
    try:
        suggestion = _extract_json_object(content)
    except json.JSONDecodeError as exc:
        raise HarnessError(f"Judge response did not contain a JSON object: {exc}") from exc
    score_values = suggestion.get("scores") or {}
    draft = {
        "id": metadata["dashboard_ids"].get("score_id"),
        "run_id": metadata["dashboard_ids"]["run_id"],
        "score_status": "draft",
        "scores": {},
        "total_score": suggestion.get("total_score"),
        "final_label": suggestion.get("final_label"),
        "rationale": suggestion.get("rationale", ""),
        "metric_rationales": suggestion.get("metric_rationales", {}),
        "judge": {
            "endpoint": endpoint,
            "model": judge_model,
            "created_at": _utc_now(),
        },
    }
    for field in rubric["metric_fields"]:
        draft["scores"][field] = _validate_score(score_values.get(field), field)
    if draft["total_score"] not in (None, ""):
        draft["total_score"] = _validate_score(draft["total_score"], "total_score")
    if (
        draft["final_label"] not in (None, "")
        and draft["final_label"] not in rubric["final_labels"]
    ):
        raise HarnessError(f"Unknown final_label: {draft['final_label']}")
    _write_json(output_path, draft)
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
        description="Create local benchmark artifacts without downloads or cloud APIs."
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
    init_parser.add_argument("--ttft-seconds", type=float)
    init_parser.add_argument("--total-latency-seconds", type=float)
    init_parser.add_argument("--ram-usage-gb", type=float)
    init_parser.add_argument("--stability-notes")
    init_parser.add_argument("--run-notes")
    init_parser.set_defaults(func=init_run)

    run_parser = subparsers.add_parser(
        "run-local",
        help="Capture prompt responses from a local OpenAI-compatible chat endpoint.",
    )
    run_parser.add_argument("--run-dir", required=True, type=Path)
    run_parser.add_argument("--endpoint", required=True)
    run_parser.add_argument("--model")
    run_parser.add_argument("--timeout", type=float, default=120.0)
    run_parser.add_argument("--max-tokens", type=int, default=1024)
    run_parser.add_argument("--temperature", type=float)
    run_parser.add_argument("--top-p", type=float)
    run_parser.add_argument("--force", action="store_true")
    run_parser.set_defaults(func=run_local)

    ollama_parser = subparsers.add_parser(
        "run-ollama",
        help="Capture prompt responses from a local Ollama API model.",
    )
    ollama_parser.add_argument("--run-dir", required=True, type=Path)
    ollama_parser.add_argument("--model-id", required=True)
    ollama_parser.add_argument("--endpoint", default=DEFAULT_OLLAMA_ENDPOINT)
    ollama_parser.add_argument("--timeout", type=float, default=180.0)
    ollama_parser.add_argument("--max-tokens", type=int, default=1024)
    ollama_parser.add_argument("--temperature", type=float)
    ollama_parser.add_argument("--top-p", type=float)
    ollama_parser.add_argument("--force", action="store_true")
    ollama_parser.set_defaults(func=run_ollama)

    llama_parser = subparsers.add_parser(
        "run-llama-cpp",
        help="Capture prompt responses from llama.cpp llama-cli via subprocess.",
    )
    llama_parser.add_argument("--run-dir", required=True, type=Path)
    llama_parser.add_argument("--model-id", required=True)
    llama_parser.add_argument("--llama-cli-path")
    llama_parser.add_argument("--timeout", type=float, default=180.0)
    llama_parser.add_argument("--max-tokens", type=int, default=1024)
    llama_parser.add_argument("--force", action="store_true")
    llama_parser.set_defaults(func=run_llama_cpp)

    mlx_parser = subparsers.add_parser(
        "run-mlx-lm",
        help="Capture prompt responses from mlx_lm generate via subprocess.",
    )
    mlx_parser.add_argument("--run-dir", required=True, type=Path)
    mlx_parser.add_argument("--model-id", required=True)
    mlx_parser.add_argument("--python-path")
    mlx_parser.add_argument("--timeout", type=float, default=180.0)
    mlx_parser.add_argument("--max-tokens", type=int, default=1024)
    mlx_parser.add_argument("--force", action="store_true")
    mlx_parser.set_defaults(func=run_mlx_lm)

    lmstudio_parser = subparsers.add_parser(
        "run-lmstudio-cli",
        help="Capture prompt responses from an installed LM Studio CLI model.",
    )
    lmstudio_parser.add_argument("--run-dir", required=True, type=Path)
    lmstudio_parser.add_argument("--model-id", required=True)
    lmstudio_parser.add_argument("--lms-path")
    lmstudio_parser.add_argument("--timeout", type=float, default=180.0)
    lmstudio_parser.add_argument("--ttl", type=int, default=3600)
    lmstudio_parser.add_argument("--force", action="store_true")
    lmstudio_parser.set_defaults(func=run_lmstudio_cli)

    record_parser = subparsers.add_parser(
        "record-responses",
        help="Copy human-supplied response JSONL into the run raw_responses.jsonl.",
    )
    record_parser.add_argument("--run-dir", required=True, type=Path)
    record_parser.add_argument("--responses-jsonl", required=True, type=Path)
    record_parser.add_argument("--force", action="store_true")
    record_parser.set_defaults(func=record_responses)

    suggest_parser = subparsers.add_parser(
        "suggest-scores",
        help="Ask a separate local judge endpoint for draft rubric score suggestions.",
    )
    suggest_parser.add_argument("--run-dir", required=True, type=Path)
    suggest_parser.add_argument("--endpoint", required=True)
    suggest_parser.add_argument("--judge-model")
    suggest_parser.add_argument("--out", type=Path)
    suggest_parser.add_argument("--timeout", type=float, default=180.0)
    suggest_parser.add_argument("--max-tokens", type=int, default=2048)
    suggest_parser.add_argument("--temperature", type=float, default=0.0)
    suggest_parser.add_argument("--force", action="store_true")
    suggest_parser.set_defaults(func=suggest_scores)

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
        print(f"harness error: {exc}", file=sys.stderr)
        return 2
    if result is not None:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
