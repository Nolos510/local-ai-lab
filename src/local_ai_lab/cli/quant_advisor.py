"""Local-first quantization advice for AI Lab OS candidates.

The advisor treats quant choices as metadata hypotheses. It never downloads,
installs, runs, or scores a model; optional Hugging Face lookup reads public
metadata only when explicitly requested by the caller.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HF_BASE_URL = "https://huggingface.co"
HF_API_URL = "https://huggingface.co/api/models"
USER_AGENT = "ai-lab-os-quant-advisor/0.1"
DEFAULT_MEMORY_GB = 256.0
TRUSTED_REPO_PREFIXES = ("lmstudio-community/", "bartowski/", "unsloth/")
SHORTLIST_QUANTS = {"Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q4_K_XL", "UD-Q4_K_XL"}
RUNTIME_FORMATS = (".gguf",)
REPO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
REPO_ID_SCAN_RE = re.compile(
    r"(?:https?://(?:huggingface\.co|hf\.co)/)?"
    r"([A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*)"
    r"(?::([A-Za-z0-9][A-Za-z0-9_-]*))?"
)
QUANT_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(UD-Q\d(?:_[A-Z0-9]+)+|IQ\d(?:_[A-Z0-9]+)+|Q\d(?:_[A-Z0-9]+)+|BF16|F16)"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)
GGUF_FILE_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.+~-]*\.gguf)", re.IGNORECASE)
PARAM_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*[Bb](?![A-Za-z0-9])")


@dataclass(frozen=True)
class ArtifactRef:
    repo_id: str
    artifact_ref: str
    filename: str = ""


def validate_repo_id(repo_id: str) -> str:
    value = (repo_id or "").strip().strip("/")
    if not REPO_ID_RE.fullmatch(value):
        raise ValueError(f"Invalid Hugging Face repo id: {repo_id}")
    if ".." in value or "\\" in value:
        raise ValueError(f"Invalid Hugging Face repo id: {repo_id}")
    return value


def repo_id_from_url_or_id(value: str) -> str:
    text = (value or "").strip()
    for prefix in (f"{HF_BASE_URL}/", "https://hf.co/", "hf.co/"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    text = text.split("?", 1)[0].split("#", 1)[0].strip("/")
    parts = text.split("/")
    if len(parts) >= 2:
        text = "/".join(parts[:2])
    return validate_repo_id(text)


def extract_repo_ids(text: str) -> list[str]:
    seen: set[str] = set()
    repo_ids: list[str] = []
    for match in REPO_ID_SCAN_RE.finditer(text or ""):
        try:
            repo_id = validate_repo_id(match.group(1))
        except ValueError:
            continue
        if repo_id not in seen:
            seen.add(repo_id)
            repo_ids.append(repo_id)
    return repo_ids


def extract_quantization(value: str) -> str:
    match = QUANT_RE.search(value or "")
    if not match:
        return ""
    return match.group(1).upper()


def extract_params_b(*values: str) -> float | None:
    for value in values:
        match = PARAM_RE.search(value or "")
        if match:
            return float(match.group(1))
    return None


def artifact_refs_from_text(text: str, *, default_repo_id: str = "") -> list[ArtifactRef]:
    refs: list[ArtifactRef] = []
    for match in REPO_ID_SCAN_RE.finditer(text or ""):
        repo_id = match.group(1)
        quant = match.group(2) or ""
        if quant and extract_quantization(quant):
            repo_id = validate_repo_id(repo_id)
            refs.append(ArtifactRef(repo_id=repo_id, artifact_ref=f"hf.co/{repo_id}:{quant}"))

    active_repo = default_repo_id
    repo_ids = extract_repo_ids(text)
    if repo_ids:
        active_repo = repo_ids[-1]
    for match in GGUF_FILE_RE.finditer(text or ""):
        filename = match.group(1)
        repo_id = active_repo or default_repo_id
        if not repo_id:
            continue
        refs.append(ArtifactRef(repo_id=repo_id, artifact_ref=filename, filename=filename))
    return _dedupe_refs(refs)


def artifact_refs_from_hf_model(model: dict[str, Any]) -> list[ArtifactRef]:
    repo_id = validate_repo_id(str(model.get("modelId") or model.get("id") or ""))
    refs: list[ArtifactRef] = []
    for sibling in model.get("siblings") or []:
        filename = str(sibling.get("rfilename") or "")
        if filename.lower().endswith(RUNTIME_FORMATS):
            refs.append(
                ArtifactRef(
                    repo_id=repo_id,
                    artifact_ref=f"{repo_id}/{filename}",
                    filename=filename,
                )
            )
    return refs


def _dedupe_refs(refs: list[ArtifactRef]) -> list[ArtifactRef]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.repo_id, ref.artifact_ref)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def fetch_hf_json(url: str, *, timeout: float = 10.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def lookup_hf_quant_refs(base_repo_id: str, *, timeout: float = 10.0) -> list[ArtifactRef]:
    base_repo_id = validate_repo_id(base_repo_id)
    base_name = base_repo_id.split("/", 1)[1]
    query = urllib.parse.quote(f"{base_name} GGUF")
    search_url = f"{HF_API_URL}?search={query}&limit=20"
    search_results = fetch_hf_json(search_url, timeout=timeout)
    if not isinstance(search_results, list):
        return []

    refs: list[ArtifactRef] = []
    for result in search_results:
        model_id = str(result.get("modelId") or result.get("id") or "")
        if not _looks_like_related_gguf_repo(base_repo_id, model_id):
            continue
        model_url = f"{HF_API_URL}/{urllib.parse.quote(model_id, safe='/')}"
        model = fetch_hf_json(model_url, timeout=timeout)
        if isinstance(model, dict):
            refs.extend(artifact_refs_from_hf_model(model))
    return _dedupe_refs(refs)


def build_advice(
    *,
    base_repo_id: str,
    candidate_id: str = "",
    candidate: dict[str, str] | None = None,
    artifact_refs: list[ArtifactRef] | None = None,
    network_lookup: bool = False,
    looked_up_at: datetime | None = None,
    memory_gb: float = DEFAULT_MEMORY_GB,
) -> dict[str, Any]:
    base_repo_id = validate_repo_id(base_repo_id)
    candidate = candidate or {}
    params_b = extract_params_b(
        candidate.get("model_name", ""),
        candidate.get("model_family", ""),
        base_repo_id,
    )
    options = [
        _option_from_ref(ref, candidate=candidate, params_b=params_b, memory_gb=memory_gb)
        for ref in (artifact_refs or [])
        if _is_runtime_ref(ref)
    ]
    options = [option for option in options if option["quantization"]]
    if options:
        options = _rank_options(options)
    else:
        options = [_needs_quantized_artifact_option(base_repo_id, candidate)]

    timestamp = looked_up_at or datetime.now(UTC)
    return {
        "base_repo_id": base_repo_id,
        "candidate_id": candidate_id,
        "looked_up_at": timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "network_lookup": bool(network_lookup),
        "options": options,
    }


def advise(
    *,
    repo_id: str | None = None,
    candidate_id: str = "",
    candidate: dict[str, str] | None = None,
    source_text: str = "",
    lookup_hf: bool = False,
    timeout: float = 10.0,
    memory_gb: float = DEFAULT_MEMORY_GB,
) -> dict[str, Any]:
    candidate = candidate or {}
    base_repo_id = _base_repo_id(repo_id=repo_id, candidate=candidate, source_text=source_text)
    refs = artifact_refs_from_text(source_text, default_repo_id=base_repo_id)
    if lookup_hf:
        refs.extend(lookup_hf_quant_refs(base_repo_id, timeout=timeout))
    return build_advice(
        base_repo_id=base_repo_id,
        candidate_id=candidate_id,
        candidate=candidate,
        artifact_refs=_dedupe_refs(refs),
        network_lookup=lookup_hf,
        memory_gb=memory_gb,
    )


def format_markdown(advice: dict[str, Any]) -> str:
    lines = [
        "# Quantization Advice",
        "",
        f"Base repo: `{_md(advice.get('base_repo_id', ''))}`",
        f"Candidate: `{_md(advice.get('candidate_id') or 'not linked')}`",
        f"Network lookup: `{'yes' if advice.get('network_lookup') else 'no'}`",
        "",
        (
            "These recommendations are metadata hypotheses only. They do not approve a "
            "download, install, model run, or eval score."
        ),
        "",
        "| Recommendation | Runtime | Artifact repo | Quant | Fit | Approval | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for option in advice.get("options") or []:
        lines.append(
            "| {recommendation} | {runtime} | {artifact_repo_id} | {quantization} | "
            "{fit_tier} | {approval_state} | {reason} |".format(
                recommendation=_md(option.get("recommendation")),
                runtime=_md(option.get("runtime")),
                artifact_repo_id=_md(option.get("artifact_repo_id")),
                quantization=_md(option.get("quantization") or "-"),
                fit_tier=_md(option.get("fit_tier")),
                approval_state=_md(option.get("approval_state")),
                reason=_md(option.get("reason")),
            )
        )
    lines.extend(
        [
            "",
            "Next benchmark step: register or select one exact local runtime model ID, "
            "complete source/license/provenance review, then use `uv run ai-lab bench "
            "execute` with explicit local-run approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def format_json(advice: dict[str, Any]) -> str:
    return json.dumps(advice, indent=2, sort_keys=True) + "\n"


def write_markdown(path: Path, advice: dict[str, Any], *, repo_root: Path) -> Path:
    output_path = _resolve_repo_local_output(path, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_markdown(advice), encoding="utf-8")
    return output_path


def write_json(path: Path, advice: dict[str, Any], *, repo_root: Path) -> Path:
    output_path = _resolve_repo_local_output(path, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_json(advice), encoding="utf-8")
    return output_path


def _base_repo_id(
    *,
    repo_id: str | None,
    candidate: dict[str, str],
    source_text: str,
) -> str:
    if repo_id:
        return repo_id_from_url_or_id(repo_id)
    for field in ("model_page_url", "lm_studio_url", "ollama_url"):
        value = candidate.get(field)
        if value and ("huggingface.co/" in value or "hf.co/" in value):
            return repo_id_from_url_or_id(value)
    repo_ids = extract_repo_ids(source_text)
    if repo_ids:
        return repo_ids[0]
    raise ValueError("Provide --repo-id, --candidate with a Hugging Face URL, or --source-note.")


def _is_runtime_ref(ref: ArtifactRef) -> bool:
    value = f"{ref.artifact_ref} {ref.filename}".lower()
    return value.endswith(RUNTIME_FORMATS) or bool(extract_quantization(value))


def _option_from_ref(
    ref: ArtifactRef,
    *,
    candidate: dict[str, str],
    params_b: float | None,
    memory_gb: float,
) -> dict[str, str]:
    quant = extract_quantization(ref.artifact_ref) or extract_quantization(ref.filename)
    fit_tier = _fit_tier(quant, params_b=params_b, memory_gb=memory_gb)
    recommendation = _recommendation(quant, fit_tier)
    return {
        "artifact_repo_id": ref.repo_id,
        "runtime": "LM Studio / Ollama / llama.cpp",
        "format": "GGUF",
        "quantization": quant,
        "artifact_ref": ref.artifact_ref,
        "fit_tier": fit_tier,
        "recommendation": recommendation,
        "reason": _reason(quant, fit_tier, params_b=params_b, memory_gb=memory_gb),
        "approval_state": _approval_state(candidate),
    }


def _needs_quantized_artifact_option(
    base_repo_id: str,
    candidate: dict[str, str],
) -> dict[str, str]:
    return {
        "artifact_repo_id": base_repo_id,
        "runtime": "review",
        "format": "source-or-safetensors",
        "quantization": "",
        "artifact_ref": base_repo_id,
        "fit_tier": "not_runnable_local_runtime",
        "recommendation": "needs_quantized_artifact",
        "reason": "No local-runtime GGUF quantized artifact was found in approved metadata.",
        "approval_state": _approval_state(candidate),
    }


def _rank_options(options: list[dict[str, str]]) -> list[dict[str, str]]:
    ranked = sorted(options, key=_rank_key)
    has_balanced = any(option["quantization"] == "Q5_K_M" for option in ranked)
    for option in ranked:
        if option["quantization"] == "Q5_K_M":
            option["recommendation"] = "recommended_balanced"
        elif option["quantization"] in {"Q8_0", "Q6_K"}:
            option["recommendation"] = "quality_check" if has_balanced else "recommended_quality"
        elif option["quantization"] in {"Q4_K_M", "Q4_K_XL", "UD-Q4_K_XL"}:
            option["recommendation"] = (
                "fast_alternate" if has_balanced else "recommended_fast_start"
            )
    return _shortlist_options(ranked)


def _shortlist_options(options: list[dict[str, str]], *, limit: int = 12) -> list[dict[str, str]]:
    trusted = [
        option
        for option in options
        if _repo_priority(option["artifact_repo_id"]) < len(TRUSTED_REPO_PREFIXES)
    ]
    source = trusted or options
    shortlist = [option for option in source if option["quantization"] in SHORTLIST_QUANTS]
    if not shortlist:
        shortlist = source
    return shortlist[:limit]


def _rank_key(option: dict[str, str]) -> tuple[int, int, str]:
    return (
        _repo_priority(option["artifact_repo_id"]),
        _quant_priority(option["quantization"]),
        option["artifact_ref"],
    )


def _repo_priority(repo_id: str) -> int:
    lowered = repo_id.lower()
    for index, prefix in enumerate(TRUSTED_REPO_PREFIXES):
        if lowered.startswith(prefix):
            return index
    return len(TRUSTED_REPO_PREFIXES)


def _quant_priority(quant: str) -> int:
    order = {
        "Q5_K_M": 0,
        "Q6_K": 1,
        "Q8_0": 2,
        "Q4_K_M": 3,
        "Q4_K_XL": 4,
        "UD-Q4_K_XL": 5,
    }
    if quant in order:
        return order[quant]
    if quant.startswith("IQ") or quant.startswith(("Q2", "Q3")):
        return 90
    return 50


def _fit_tier(quant: str, *, params_b: float | None, memory_gb: float) -> str:
    if quant in {"Q8_0", "Q6_K", "Q5_K_M"}:
        return "quality_first_practical" if _fits_quality(params_b, memory_gb) else "review_fit"
    if quant in {"Q4_K_M", "Q4_K_XL", "UD-Q4_K_XL"} or quant.startswith("Q4"):
        return "fast_smaller"
    if quant.startswith("IQ") or quant.startswith(("Q2", "Q3")):
        return "fit_constrained_large_model_only"
    return "review"


def _fits_quality(params_b: float | None, memory_gb: float) -> bool:
    if params_b is None:
        return memory_gb >= 64
    return params_b <= 32 and memory_gb >= 64


def _recommendation(quant: str, fit_tier: str) -> str:
    if quant == "Q5_K_M":
        return "recommended_balanced"
    if quant in {"Q8_0", "Q6_K"}:
        return "recommended_quality"
    if quant in {"Q4_K_M", "Q4_K_XL", "UD-Q4_K_XL"}:
        return "recommended_fast_start"
    if fit_tier == "fit_constrained_large_model_only":
        return "avoid_for_this_8b_lab_default"
    return "needs_review"


def _reason(quant: str, fit_tier: str, *, params_b: float | None, memory_gb: float) -> str:
    size = f"{params_b:g}B" if params_b else "this size class"
    if quant == "Q5_K_M":
        return f"Balanced starting point for {size} on a {memory_gb:g} GB Apple Silicon target."
    if quant in {"Q8_0", "Q6_K"}:
        return (
            f"Quality-first comparison quant that should be practical for {size} "
            "if local runtime support is confirmed."
        )
    if quant in {"Q4_K_M", "Q4_K_XL", "UD-Q4_K_XL"}:
        return "Fast/smaller alternate for throughput checks or runtime compatibility triage."
    if fit_tier == "fit_constrained_large_model_only":
        return (
            "Tiny/IQ quant; keep as a fit-constrained fallback, not the default "
            "for an 8B model on this machine."
        )
    return "Quantization needs manual review before selection."


def _approval_state(candidate: dict[str, str]) -> str:
    local_model_id = (candidate.get("local_model_id") or "").strip()
    runner = (candidate.get("local_runner") or "").strip()
    security = (candidate.get("security_review_status") or "").strip().lower()
    download = (candidate.get("download_approval") or "").strip().lower()
    license_state = (candidate.get("license_review_status") or "").strip().lower()
    provenance = (candidate.get("provenance_status") or "").strip().lower()
    if (
        local_model_id
        and runner
        and security in {"approved", "local_inventory_reviewed", "reviewed_local"}
        and download in {"approved", "not_needed_local", "not_required", "local_only"}
        and license_state in {"approved", "reviewed", "not_needed_local", "needs_review"}
        and provenance in {"approved", "local_inventory", "verified", "reviewed_local"}
    ):
        return "ready_for_local_benchmark"
    return "metadata_only; not_approved_to_download; needs_license_review; needs_provenance_review"


def _looks_like_related_gguf_repo(base_repo_id: str, candidate_repo_id: str) -> bool:
    lowered = candidate_repo_id.lower()
    if "gguf" not in lowered:
        return False
    base_name = base_repo_id.split("/", 1)[1].lower()
    normalized_base = re.sub(r"[^a-z0-9]+", "", base_name)
    normalized_candidate = re.sub(r"[^a-z0-9]+", "", lowered)
    return normalized_base in normalized_candidate


def _md(value: object) -> str:
    return str(value or "-").replace("\n", " ").replace("|", "\\|")


def _resolve_repo_local_output(path: Path, *, repo_root: Path) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    resolved_repo = repo_root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_repo)
    except ValueError as exc:
        raise ValueError(f"output path must stay inside the repository: {path}") from exc
    return resolved_candidate
