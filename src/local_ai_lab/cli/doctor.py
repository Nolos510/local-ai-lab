from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from difflib import get_close_matches
from enum import StrEnum
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlsplit, urlunsplit

import httpx

from local_ai_lab.config.settings import Settings

DOCTOR_TIMEOUT_SECONDS = 3.0
REQUIRED_DATA_DIRS = (
    Path("data/raw"),
    Path("data/parsed"),
    Path("data/chunked"),
    Path("data/eval"),
    Path("data/synthetic"),
)
OLLAMA_PROVIDER = "ollama"
OPENAI_COMPATIBLE_PROVIDERS = {"lm_studio", "openai_compatible"}
SUPPORTED_EMBEDDING_PROVIDERS = {"deterministic", "ollama"}
SUPPORTED_VECTOR_STORE_PROVIDERS = {"qdrant"}

HttpGet = Callable[..., Any]
SettingsFactory = Callable[[], Settings]


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: CheckStatus
    detail: str
    required: bool = True


def run_doctor(
    *,
    root: Path | None = None,
    output: TextIO | None = None,
    settings_factory: SettingsFactory = Settings,
    http_get: HttpGet = httpx.get,
) -> int:
    """Run local health checks and print a compact status table."""

    resolved_root = root or Path.cwd()
    checks = collect_doctor_checks(
        root=resolved_root,
        settings_factory=settings_factory,
        http_get=http_get,
    )
    print_doctor_report(checks, output=output)
    return 1 if any(check.required and check.status == CheckStatus.FAIL for check in checks) else 0


def collect_doctor_checks(
    *,
    root: Path,
    settings_factory: SettingsFactory = Settings,
    http_get: HttpGet = httpx.get,
) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = [
        _check_package_config(root),
        _check_data_dirs(root),
        _check_sample_docs(root),
        _check_compose_file(root),
    ]

    settings_check, settings = _check_settings(settings_factory)
    checks.insert(1, settings_check)
    if settings is None:
        checks.extend(
            [
                _failed_config_check("Embedding provider"),
                _failed_config_check("Vector store provider"),
                _failed_config_check("Qdrant"),
                DoctorCheck(
                    "Ollama endpoint",
                    CheckStatus.WARN,
                    "settings unavailable",
                    required=False,
                ),
                DoctorCheck(
                    "Ollama model",
                    CheckStatus.WARN,
                    "settings unavailable",
                    required=False,
                ),
                DoctorCheck(
                    "Ollama embedding model",
                    CheckStatus.WARN,
                    "settings unavailable",
                    required=False,
                ),
                DoctorCheck(
                    "LM Studio/OpenAI-compatible endpoint",
                    CheckStatus.WARN,
                    "settings unavailable",
                    required=False,
                ),
            ]
        )
        return checks

    checks.extend(
        [
            _check_embedding_provider(settings),
            _check_vector_store_provider(settings),
            _check_qdrant(settings, http_get=http_get),
        ]
    )

    ollama_tags_payload: dict[str, Any] | None = None
    ollama_selected = settings.llm_provider.lower() == OLLAMA_PROVIDER
    ollama_embedding_selected = settings.embedding_provider.lower() == OLLAMA_PROVIDER
    ollama_endpoint_check, ollama_tags_payload = _check_ollama_endpoint(
        settings,
        http_get=http_get,
        required=ollama_selected or ollama_embedding_selected,
    )
    checks.append(ollama_endpoint_check)
    checks.append(
        _check_ollama_model(
            settings,
            tags_payload=ollama_tags_payload,
            endpoint_status=ollama_endpoint_check.status,
            required=ollama_selected,
        )
    )
    checks.append(
        _check_ollama_embedding_model(
            settings,
            tags_payload=ollama_tags_payload,
            endpoint_status=ollama_endpoint_check.status,
            required=ollama_embedding_selected,
        )
    )

    openai_selected = settings.llm_provider.lower() in OPENAI_COMPATIBLE_PROVIDERS
    checks.append(
        _check_openai_compatible_endpoint(
            settings,
            http_get=http_get,
            required=openai_selected,
        )
    )
    return checks


def print_doctor_report(checks: list[DoctorCheck], *, output: TextIO | None = None) -> None:
    stream = output
    print("Local AI Lab Doctor", file=stream)
    print("", file=stream)
    widths = {
        "name": max(len("Check"), *(len(check.name) for check in checks)),
        "status": len("Status"),
    }
    header = f"{'Check':<{widths['name']}}  {'Status':<{widths['status']}}  Detail"
    print(header, file=stream)
    print("-" * len(header), file=stream)
    for check in checks:
        status = check.status.value
        print(
            f"{check.name:<{widths['name']}}  {status:<{widths['status']}}  {check.detail}",
            file=stream,
        )


def _check_package_config(root: Path) -> DoctorCheck:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return DoctorCheck("Package configuration", CheckStatus.FAIL, "pyproject.toml is missing")
    try:
        import tomllib

        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except Exception:
        return DoctorCheck(
            "Package configuration",
            CheckStatus.FAIL,
            "pyproject.toml could not be parsed",
        )
    project_name = payload.get("project", {}).get("name")
    if project_name != "local-ai-lab":
        return DoctorCheck("Package configuration", CheckStatus.FAIL, "unexpected project metadata")
    return DoctorCheck("Package configuration", CheckStatus.PASS, "pyproject.toml loaded")


def _check_settings(settings_factory: SettingsFactory) -> tuple[DoctorCheck, Settings | None]:
    try:
        settings = settings_factory()
    except Exception:
        return (
            DoctorCheck(
                "Settings",
                CheckStatus.FAIL,
                ".env or environment settings could not be parsed",
            ),
            None,
        )
    return (
        DoctorCheck("Settings", CheckStatus.PASS, ".env and environment settings parsed"),
        settings,
    )


def _check_data_dirs(root: Path) -> DoctorCheck:
    missing = [path.as_posix() for path in REQUIRED_DATA_DIRS if not (root / path).is_dir()]
    if missing:
        return DoctorCheck(
            "Required data directories",
            CheckStatus.FAIL,
            f"missing: {', '.join(missing)}",
        )
    return DoctorCheck(
        "Required data directories",
        CheckStatus.PASS,
        ", ".join(path.as_posix() for path in REQUIRED_DATA_DIRS),
    )


def _check_sample_docs(root: Path) -> DoctorCheck:
    path = Path("data/sample_docs")
    if (root / path).is_dir():
        return DoctorCheck("Sample docs", CheckStatus.PASS, path.as_posix())
    return DoctorCheck("Sample docs", CheckStatus.FAIL, "data/sample_docs is missing")


def _check_compose_file(root: Path) -> DoctorCheck:
    path = Path("compose.yaml")
    if (root / path).is_file():
        return DoctorCheck("Docker Compose file", CheckStatus.PASS, path.as_posix())
    return DoctorCheck("Docker Compose file", CheckStatus.FAIL, "compose.yaml is missing")


def _check_embedding_provider(settings: Settings) -> DoctorCheck:
    provider = settings.embedding_provider.lower()
    if provider in SUPPORTED_EMBEDDING_PROVIDERS:
        return DoctorCheck("Embedding provider", CheckStatus.PASS, provider)
    return DoctorCheck("Embedding provider", CheckStatus.FAIL, "unsupported or empty provider")


def _check_vector_store_provider(settings: Settings) -> DoctorCheck:
    provider = settings.vector_store_provider.lower()
    if provider in SUPPORTED_VECTOR_STORE_PROVIDERS:
        return DoctorCheck("Vector store provider", CheckStatus.PASS, provider)
    return DoctorCheck("Vector store provider", CheckStatus.FAIL, "unsupported or empty provider")


def _check_qdrant(settings: Settings, *, http_get: HttpGet) -> DoctorCheck:
    url = _join_url(settings.qdrant_url, "collections")
    ok, detail, _ = _get_json(url, http_get=http_get, timeout_seconds=_timeout(settings))
    if ok:
        return DoctorCheck(
            "Qdrant",
            CheckStatus.PASS,
            f"reachable at {_sanitize_url(settings.qdrant_url)}",
        )
    return DoctorCheck("Qdrant", CheckStatus.FAIL, detail)


def _check_ollama_endpoint(
    settings: Settings,
    *,
    http_get: HttpGet,
    required: bool,
) -> tuple[DoctorCheck, dict[str, Any] | None]:
    if not required:
        return (
            DoctorCheck(
                "Ollama endpoint",
                CheckStatus.WARN,
                "provider not selected; not checked",
                required=False,
            ),
            None,
        )

    url = _join_url(settings.ollama_base_url, "api/tags")
    ok, detail, payload = _get_json(url, http_get=http_get, timeout_seconds=_timeout(settings))
    if ok:
        return (
            DoctorCheck(
                "Ollama endpoint",
                CheckStatus.PASS,
                f"reachable at {_sanitize_url(settings.ollama_base_url)}",
            ),
            payload,
        )
    return DoctorCheck("Ollama endpoint", CheckStatus.FAIL, detail), None


def _check_ollama_model(
    settings: Settings,
    *,
    tags_payload: dict[str, Any] | None,
    endpoint_status: CheckStatus,
    required: bool,
) -> DoctorCheck:
    if not required:
        return DoctorCheck(
            "Ollama model",
            CheckStatus.WARN,
            "provider not selected; not checked",
            required=False,
        )
    if endpoint_status != CheckStatus.PASS or tags_payload is None:
        return DoctorCheck("Ollama model", CheckStatus.FAIL, "Ollama model list unavailable")

    model_names = {
        str(model.get("name"))
        for model in tags_payload.get("models", [])
        if isinstance(model, dict) and model.get("name") is not None
    }
    if settings.ollama_model in model_names:
        return DoctorCheck(
            "Ollama model",
            CheckStatus.PASS,
            "configured model is available locally",
        )
    suggestion = _ollama_model_suggestion(settings.ollama_model, model_names)
    if suggestion:
        return DoctorCheck(
            "Ollama model",
            CheckStatus.FAIL,
            (
                f"configured model '{settings.ollama_model}' is not available locally; "
                f"installed models include {', '.join(sorted(model_names))}; "
                f"set `LOCAL_AI_LAB_OLLAMA_MODEL={suggestion}` to use the closest "
                "installed model, or run "
                f"`ollama pull {settings.ollama_model}` to install the configured model"
            ),
        )
    return DoctorCheck(
        "Ollama model",
        CheckStatus.FAIL,
        (
            f"configured model '{settings.ollama_model}' is not available locally; "
            "no Ollama chat models were reported locally; "
            f"run `ollama pull {settings.ollama_model}` or set "
            "LOCAL_AI_LAB_OLLAMA_MODEL to an installed model"
        ),
    )


def _check_ollama_embedding_model(
    settings: Settings,
    *,
    tags_payload: dict[str, Any] | None,
    endpoint_status: CheckStatus,
    required: bool,
) -> DoctorCheck:
    if not required:
        return DoctorCheck(
            "Ollama embedding model",
            CheckStatus.WARN,
            "provider not selected; not checked",
            required=False,
        )
    if endpoint_status != CheckStatus.PASS or tags_payload is None:
        return DoctorCheck(
            "Ollama embedding model",
            CheckStatus.FAIL,
            "Ollama model list unavailable",
        )

    model_names = {
        str(model.get("name"))
        for model in tags_payload.get("models", [])
        if isinstance(model, dict) and model.get("name") is not None
    }
    if settings.ollama_embedding_model in model_names:
        return DoctorCheck(
            "Ollama embedding model",
            CheckStatus.PASS,
            "configured embedding model is available locally",
        )
    return DoctorCheck(
        "Ollama embedding model",
        CheckStatus.FAIL,
        (
            f"configured embedding model '{settings.ollama_embedding_model}' "
            "is not available locally; "
            f"run `ollama pull {settings.ollama_embedding_model}` or set "
            "LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL to an installed embedding model"
        ),
    )


def _check_openai_compatible_endpoint(
    settings: Settings,
    *,
    http_get: HttpGet,
    required: bool,
) -> DoctorCheck:
    if not required:
        return DoctorCheck(
            "LM Studio/OpenAI-compatible endpoint",
            CheckStatus.WARN,
            "provider not selected; not checked",
            required=False,
        )

    url = _join_url(settings.lm_studio_base_url, "models")
    ok, detail, _ = _get_json(url, http_get=http_get, timeout_seconds=_timeout(settings))
    if ok:
        return DoctorCheck(
            "LM Studio/OpenAI-compatible endpoint",
            CheckStatus.PASS,
            f"reachable at {_sanitize_url(settings.lm_studio_base_url)}",
        )
    return DoctorCheck("LM Studio/OpenAI-compatible endpoint", CheckStatus.FAIL, detail)


def _get_json(
    url: str,
    *,
    http_get: HttpGet,
    timeout_seconds: float,
) -> tuple[bool, str, dict[str, Any] | None]:
    safe_url = _sanitize_url(url)
    try:
        response = http_get(url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        return False, f"HTTP {exc.response.status_code} from {safe_url}", None
    except httpx.RequestError:
        return False, f"not reachable at {safe_url}", None
    except ValueError:
        return False, f"invalid JSON from {safe_url}", None
    except Exception as exc:
        return False, f"{exc.__class__.__name__} while checking {safe_url}", None
    if not isinstance(payload, dict):
        return False, f"unexpected response from {safe_url}", None
    return True, f"reachable at {safe_url}", payload


def _join_url(base_url: str, suffix: str) -> str:
    return f"{base_url.rstrip('/')}/{suffix.lstrip('/')}"


def _sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.hostname:
        return "configured URL"
    hostname = parts.hostname or ""
    netloc = hostname
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))


def _ollama_model_suggestion(configured_model: str, installed_models: set[str]) -> str | None:
    if not installed_models:
        return None
    matches = get_close_matches(
        configured_model.lower(),
        [model.lower() for model in installed_models],
        n=1,
        cutoff=0.0,
    )
    if not matches:
        return sorted(installed_models)[0]
    lowered_to_original = {model.lower(): model for model in installed_models}
    return lowered_to_original[matches[0]]


def _timeout(settings: Settings) -> float:
    return min(float(settings.request_timeout_seconds), DOCTOR_TIMEOUT_SECONDS)


def _failed_config_check(name: str) -> DoctorCheck:
    return DoctorCheck(name, CheckStatus.FAIL, "settings unavailable")
