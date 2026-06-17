from io import StringIO
from pathlib import Path
from typing import Any

import httpx

from local_ai_lab.cli.doctor import CheckStatus, DoctorCheck, collect_doctor_checks, run_doctor
from local_ai_lab.config.settings import Settings


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_doctor_passes_required_checks_with_ollama_available(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    calls: list[str] = []
    settings = Settings(
        llm_provider="ollama",
        qdrant_url="http://localhost:6333",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3:14b",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        calls.append(url)
        payloads = {
            "http://localhost:6333/collections": {"result": {"collections": []}},
            "http://localhost:11434/api/tags": {"models": [{"name": "qwen3:14b"}]},
        }
        return FakeResponse(payloads[url])

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    assert exit_code == 0
    assert calls == ["http://localhost:6333/collections", "http://localhost:11434/api/tags"]
    report = output.getvalue()
    assert "Local AI Lab Doctor" in report
    assert "Qdrant" in report
    assert "PASS" in report
    assert "LM Studio/OpenAI-compatible endpoint" in report
    assert "LM Studio/OpenAI-compatible model" in report
    assert "WARN" in report


def test_doctor_fails_when_selected_ollama_is_unreachable(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        llm_provider="ollama",
        qdrant_url="http://localhost:6333",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3:14b",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        if url == "http://localhost:6333/collections":
            return FakeResponse({"result": {"collections": []}})
        request = httpx.Request("GET", url)
        raise httpx.ConnectError("connection failed", request=request)

    checks = collect_doctor_checks(root=root, settings_factory=lambda: settings, http_get=fake_get)

    assert _status(checks, "Qdrant") == CheckStatus.PASS
    assert _status(checks, "Ollama endpoint") == CheckStatus.FAIL
    assert _status(checks, "Ollama model") == CheckStatus.FAIL
    assert any(check.required and check.status == CheckStatus.FAIL for check in checks)


def test_doctor_fails_with_actionable_detail_when_selected_ollama_model_is_missing(
    tmp_path: Path,
) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        llm_provider="ollama",
        qdrant_url="http://localhost:6333",
        ollama_base_url="http://user:supersecret@localhost:11434/private?token=abc",
        ollama_model="qwen3:14b",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        if url == "http://localhost:6333/collections":
            return FakeResponse({"result": {"collections": []}})
        assert "supersecret" in url
        return FakeResponse({"models": [{"name": "llama3.2:3b"}]})

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    report = output.getvalue()
    assert exit_code == 1
    assert "Ollama model" in report
    assert "FAIL" in report
    assert "configured model 'qwen3:14b' is not available locally" in report
    assert "`ollama pull qwen3:14b`" in report
    assert "LOCAL_AI_LAB_OLLAMA_MODEL" in report
    assert "supersecret" not in report
    assert "token=abc" not in report
    assert "/private" not in report


def test_doctor_passes_when_openai_compatible_model_is_available(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    calls: list[str] = []
    settings = Settings(llm_provider="lm_studio")

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        calls.append(url)
        payloads = {
            "http://localhost:6333/collections": {"result": {"collections": []}},
            "http://localhost:1234/v1/models": {"data": [{"id": "local-model"}]},
        }
        return FakeResponse(payloads[url])

    exit_code = run_doctor(
        root=root,
        output=StringIO(),
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    assert exit_code == 0
    assert calls == ["http://localhost:6333/collections", "http://localhost:1234/v1/models"]


def test_doctor_fails_when_openai_compatible_model_is_missing(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        llm_provider="lm_studio",
        qdrant_url="http://localhost:6333",
        lm_studio_base_url="http://localhost:1234/v1",
        lm_studio_model="qwen-coder-30b-instruct-mlx",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        payloads = {
            "http://localhost:6333/collections": {"result": {"collections": []}},
            "http://localhost:1234/v1/models": {"data": [{"id": "other-local-model"}]},
        }
        return FakeResponse(payloads[url])

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    report = output.getvalue()
    assert exit_code == 1
    assert "LM Studio/OpenAI-compatible model" in report
    assert "FAIL" in report
    assert "configured model 'qwen-coder-30b-instruct-mlx' was not found" in report
    assert "curl -s http://localhost:1234/v1/models | uv run python -m json.tool" in report
    assert "copy one of the returned `id` values into LOCAL_AI_LAB_LM_STUDIO_MODEL" in report


def test_doctor_sanitizes_openai_compatible_missing_model_detail(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        llm_provider="openai_compatible",
        qdrant_url="http://localhost:6333",
        lm_studio_base_url="http://user:supersecret@localhost:1234/private/v1?token=abc",
        lm_studio_model="missing-model",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        if url == "http://localhost:6333/collections":
            return FakeResponse({"result": {"collections": []}})
        assert "supersecret" in url
        return FakeResponse({"data": [{"id": "available-model"}]})

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    report = output.getvalue()
    assert exit_code == 1
    assert "configured model 'missing-model' was not found" in report
    assert "uv run python -m json.tool" in report
    assert "supersecret" not in report
    assert "token=abc" not in report
    assert "/private" not in report


def test_doctor_warns_on_openai_compatible_model_when_provider_not_selected(
    tmp_path: Path,
) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(llm_provider="mock")

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        assert url == "http://localhost:6333/collections"
        return FakeResponse({"result": {"collections": []}})

    checks = collect_doctor_checks(root=root, settings_factory=lambda: settings, http_get=fake_get)

    assert _status(checks, "LM Studio/OpenAI-compatible endpoint") == CheckStatus.WARN
    assert _status(checks, "LM Studio/OpenAI-compatible model") == CheckStatus.WARN


def test_doctor_checks_ollama_embedding_model_when_selected(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    calls: list[str] = []
    settings = Settings(
        embedding_provider="ollama",
        llm_provider="mock",
        qdrant_url="http://localhost:6333",
        ollama_base_url="http://localhost:11434",
        ollama_embedding_model="bge-m3",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        calls.append(url)
        payloads = {
            "http://localhost:6333/collections": {"result": {"collections": []}},
            "http://localhost:11434/api/tags": {"models": [{"name": "bge-m3"}]},
        }
        return FakeResponse(payloads[url])

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    assert exit_code == 0
    assert calls == ["http://localhost:6333/collections", "http://localhost:11434/api/tags"]
    report = output.getvalue()
    assert "Ollama embedding model" in report
    assert "configured embedding model is available locally" in report
    assert "Ollama model" in report
    assert "provider not selected; not checked" in report


def test_doctor_fails_when_ollama_embedding_model_is_missing(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        embedding_provider="ollama",
        llm_provider="mock",
        qdrant_url="http://localhost:6333",
        ollama_base_url="http://user:secret@localhost:11434/private?token=abc",
        ollama_embedding_model="bge-m3",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        if url == "http://localhost:6333/collections":
            return FakeResponse({"result": {"collections": []}})
        assert "secret" in url
        return FakeResponse({"models": [{"name": "nomic-embed-text:latest"}]})

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    report = output.getvalue()
    assert exit_code == 1
    assert "configured embedding model 'bge-m3' is not available locally" in report
    assert "`ollama pull bge-m3`" in report
    assert "LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL" in report
    assert "secret" not in report
    assert "token=abc" not in report
    assert "/private" not in report


def test_doctor_fails_without_calling_services_when_settings_do_not_parse(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)

    def bad_settings() -> Settings:
        msg = "bad settings"
        raise ValueError(msg)

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        raise AssertionError(f"unexpected live check: {url} {timeout}")

    exit_code = run_doctor(
        root=root,
        output=StringIO(),
        settings_factory=bad_settings,
        http_get=fake_get,
    )

    assert exit_code == 1


def test_doctor_sanitizes_configured_urls(tmp_path: Path) -> None:
    root = _make_project_root(tmp_path)
    settings = Settings(
        llm_provider="mock",
        qdrant_url="http://user:secret@localhost:6333/private?token=abc",
    )

    def fake_get(url: str, *, timeout: float) -> FakeResponse:
        del timeout
        assert "secret" in url
        return FakeResponse({"result": {"collections": []}})

    output = StringIO()
    exit_code = run_doctor(
        root=root,
        output=output,
        settings_factory=lambda: settings,
        http_get=fake_get,
    )

    assert exit_code == 0
    report = output.getvalue()
    assert "secret" not in report
    assert "token" not in report
    assert "private" not in report
    assert "http://localhost:6333" in report


def _make_project_root(root: Path) -> Path:
    root.joinpath("pyproject.toml").write_text(
        '[project]\nname = "local-ai-lab"\n',
        encoding="utf-8",
    )
    for path in (
        "data/raw",
        "data/parsed",
        "data/chunked",
        "data/eval",
        "data/synthetic",
        "data/sample_docs",
    ):
        root.joinpath(path).mkdir(parents=True)
    root.joinpath("compose.yaml").write_text("services: {}\n", encoding="utf-8")
    return root


def _status(checks: list[DoctorCheck], name: str) -> CheckStatus:
    return next(check.status for check in checks if check.name == name)
