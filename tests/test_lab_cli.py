from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_ai_lab.cli import lab, quant_advisor


def write_registry(path: Path) -> None:
    fieldnames = [
        "candidate_id",
        "model_name",
        "model_family",
        "provider_or_org",
        "status",
        "format_or_runtime",
        "source_packet_path",
        "report_path",
        "benchmark_run_id",
        "model_page_url",
        "github_url",
        "lm_studio_url",
        "ollama_url",
        "runtime_availability",
        "local_runner",
        "local_model_id",
        "default_endpoint",
        "why_interesting",
        "risk_notes",
        "proposed_eval",
        "security_review_status",
        "download_approval",
        "license_review_status",
        "provenance_status",
        "security_notes",
        "isolation_notes",
        "security_review_path",
    ]
    rows = [
        {
            "candidate_id": "candidate-ready",
            "model_name": "Ready Model",
            "model_family": "Ready",
            "provider_or_org": "Local Org",
            "status": "ready_for_eval",
            "format_or_runtime": "GGUF",
            "model_page_url": "https://example.test/model",
            "local_runner": "llama.cpp",
            "why_interesting": "Small local candidate.",
            "proposed_eval": "Run local benchmark spec.",
        },
        {
            "candidate_id": "candidate-watch",
            "model_name": "Watch Model",
            "status": "watchlist",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_queue_registry(path: Path, *, missing_field: str | None = None) -> None:
    fieldnames = [
        "candidate_id",
        "model_name",
        "status",
        "local_runner",
        "local_model_id",
        "benchmark_run_id",
        "default_endpoint",
        "security_review_status",
        "download_approval",
    ]
    rows = [
        {
            "candidate_id": "queue-one",
            "model_name": "Queue One",
            "status": "ready_for_eval",
            "local_runner": "lmstudio-cli",
            "local_model_id": "local-model-one",
            "benchmark_run_id": "20260714-queue-one-r1",
            "security_review_status": "local_inventory_reviewed",
            "download_approval": "not_needed_local",
        },
        {
            "candidate_id": "queue-two",
            "model_name": "Queue Two",
            "status": "ready_for_eval",
            "local_runner": "ollama",
            "local_model_id": "local-model-two:latest",
            "benchmark_run_id": "20260714-queue-two-r1",
            "default_endpoint": "http://127.0.0.1:11434",
            "security_review_status": "approved",
            "download_approval": "approved",
        },
    ]
    if missing_field:
        rows[1][missing_field] = ""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_dashboard_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE models (id integer primary key)")
        conn.execute("CREATE TABLE model_runs (id integer primary key)")
        conn.execute("CREATE TABLE eval_scores (id integer primary key)")
        conn.execute("CREATE TABLE decisions (id integer primary key)")
        conn.execute("INSERT INTO models (id) VALUES (1)")
        conn.execute("INSERT INTO model_runs (id) VALUES (1)")
        conn.execute("INSERT INTO eval_scores (id) VALUES (1)")
        conn.execute("INSERT INTO decisions (id) VALUES (1)")


def capture_commands(monkeypatch):
    commands = []

    def fake_run(command, check=False):
        commands.append(command)
        assert check is False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(lab.subprocess, "run", fake_run)
    return commands


def test_status_reads_registry_artifacts_and_dashboard_db(tmp_path, capsys) -> None:
    registry = tmp_path / "candidates.csv"
    eval_results = tmp_path / "eval_results"
    db_path = tmp_path / "dashboard.sqlite"
    write_registry(registry)
    write_dashboard_db(db_path)
    (eval_results / "run-one").mkdir(parents=True)

    exit_code = lab.main(
        [
            "status",
            "--registry",
            str(registry),
            "--eval-results",
            str(eval_results),
            "--db",
            str(db_path),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Candidates: 2" in output
    assert "ready_for_eval: 1" in output
    assert "watchlist: 1" in output
    assert "Benchmark artifacts: 1" in output
    assert "models=1, runs=1, scores=1, decisions=1" in output


def test_radar_list_filters_candidates(tmp_path, capsys) -> None:
    registry = tmp_path / "candidates.csv"
    write_registry(registry)

    exit_code = lab.main(["radar", "list", "--registry", str(registry), "--status", "watchlist"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "candidate_id\tstatus\tmodel_name\tlocal_runner" in output
    assert "candidate-watch\twatchlist\tWatch Model\t" in output
    assert "candidate-ready" not in output


def test_quant_advise_default_does_not_lookup_network(monkeypatch, capsys) -> None:
    def fail_fetch(*_args, **_kwargs):
        raise AssertionError("default quant advise must not perform network lookup")

    monkeypatch.setattr(quant_advisor, "fetch_hf_json", fail_fetch)

    exit_code = lab.main(
        [
            "quant",
            "advise",
            "--repo-id",
            "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Network lookup: `no`" in output
    assert "needs_quantized_artifact" in output


def test_quant_advise_lookup_hf_uses_mocked_stdlib_metadata(monkeypatch, capsys) -> None:
    def fake_fetch(url: str, *, timeout: float = 10.0):
        if "search=" in url:
            return [{"modelId": "lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF"}]
        return {
            "modelId": "lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF",
            "siblings": [{"rfilename": "DeepSeek-R1-0528-Qwen3-8B-Q5_K_M.gguf"}],
        }

    monkeypatch.setattr(quant_advisor, "fetch_hf_json", fake_fetch)

    exit_code = lab.main(
        [
            "quant",
            "advise",
            "--repo-id",
            "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "--lookup-hf",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["network_lookup"] is True
    assert payload["options"][0]["quantization"] == "Q5_K_M"


def test_quant_advise_rejects_unsafe_output_path(capsys) -> None:
    exit_code = lab.main(
        [
            "quant",
            "advise",
            "--repo-id",
            "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "--out-json",
            "/tmp/quant-advice.json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "inside the repository" in captured.err


def test_bench_run_builds_harness_init_command(tmp_path, monkeypatch) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "run",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--run-id",
            "20260616-candidate-ready-r1",
            "--output-root",
            str(output_root),
        ]
    )

    assert exit_code == 0
    command = commands[0]
    assert command[:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert "--benchmark-run-id" in command
    assert "20260616-candidate-ready-r1" in command
    assert "--model-name" in command
    assert "Ready Model" in command
    assert "--backend" in command
    assert "llama.cpp" in command


def test_bench_execute_refuses_without_approval_before_subprocess(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench execute must not call subprocess without approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)
    monkeypatch.setattr(lab.sys.stdin, "isatty", lambda: False)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "explicit-local-model",
            "--runner",
            "lmstudio-cli",
            "--run-id",
            "20260617-explicit-local-model-r1",
            "--output-root",
            str(output_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Benchmark execution preflight" in captured.out
    assert "model_id: explicit-local-model" in captured.out
    assert "runner: lmstudio-cli" in captured.out
    assert "prompt_set_id: ai-lab-local-llm-core-v0.1" in captured.out
    assert "approval: missing" in captured.err


def test_bench_execute_preflight_redacts_endpoint_query_before_approval(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench execute must not call subprocess without approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)
    monkeypatch.setattr(lab.sys.stdin, "isatty", lambda: False)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "explicit-local-model",
            "--runner",
            "openai-compatible",
            "--endpoint",
            "http://127.0.0.1:1234/v1?token=secret#fragment",
            "--run-id",
            "20260617-explicit-local-model-r1",
            "--output-root",
            str(output_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "POST http://127.0.0.1:1234/v1/chat/completions" in captured.out
    assert "secret" not in captured.out
    assert "fragment" not in captured.out


def test_bench_execute_refuses_ollama_without_approval_before_subprocess(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench execute must not call subprocess without approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)
    monkeypatch.setattr(lab.sys.stdin, "isatty", lambda: False)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "fixture-ollama:latest",
            "--runner",
            "ollama",
            "--endpoint",
            "http://127.0.0.1:11434?token=secret#fragment",
            "--run-id",
            "20260623-fixture-ollama-r1",
            "--output-root",
            str(output_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "runner: ollama" in captured.out
    assert "POST http://127.0.0.1:11434/api/generate" in captured.out
    assert "secret" not in captured.out
    assert "fragment" not in captured.out
    assert "approval: missing" in captured.err


def test_bench_execute_refuses_mlx_lm_without_approval_before_subprocess(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench execute must not call subprocess without approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)
    monkeypatch.setattr(lab.sys.stdin, "isatty", lambda: False)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "mlx-community/Fixture-4bit",
            "--runner",
            "mlx-lm",
            "--run-id",
            "20260623-fixture-mlx-r1",
            "--output-root",
            str(output_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "runner: mlx-lm" in captured.out
    assert "python -m mlx_lm generate" in captured.out
    assert "approval: missing" in captured.err


def test_bench_execute_refuses_llama_cpp_without_approval_before_subprocess(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench execute must not call subprocess without approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)
    monkeypatch.setattr(lab.sys.stdin, "isatty", lambda: False)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "/tmp/fixture-model.gguf",
            "--runner",
            "llama-cpp",
            "--run-id",
            "20260623-fixture-llama-r1",
            "--output-root",
            str(output_root),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "runner: llama-cpp" in captured.out
    assert "llama-cli -m <model-id>" in captured.out
    assert "approval: missing" in captured.err


def test_bench_execute_approved_lmstudio_flow_builds_expected_commands(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    db_path = tmp_path / "dashboard.sqlite"
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "explicit-local-model",
            "--runner",
            "lmstudio-cli",
            "--run-id",
            "20260617-explicit-local-model-r1",
            "--output-root",
            str(output_root),
            "--db",
            str(db_path),
            "--i-approve-local-run",
            "--import-dashboard",
            "--force",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "approval: explicit --i-approve-local-run" in output
    assert len(commands) == 4
    assert commands[0][:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert "20260617-explicit-local-model-r1" in commands[0]
    assert commands[1][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "run-lmstudio-cli",
    ]
    assert "--model-id" in commands[1]
    assert "explicit-local-model" in commands[1]
    assert commands[2][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "export-dashboard",
    ]
    assert commands[3][:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "import-csv"]


def test_bench_execute_approved_ollama_flow_builds_expected_commands(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "fixture-ollama:latest",
            "--runner",
            "ollama",
            "--endpoint",
            "http://127.0.0.1:11434",
            "--run-id",
            "20260623-fixture-ollama-r1",
            "--output-root",
            str(output_root),
            "--max-tokens",
            "64",
            "--i-approve-local-run",
            "--force",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "approval: explicit --i-approve-local-run" in output
    assert len(commands) == 3
    assert commands[0][:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert commands[1][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "run-ollama",
    ]
    assert "--model-id" in commands[1]
    assert "fixture-ollama:latest" in commands[1]
    assert "--endpoint" in commands[1]
    assert "http://127.0.0.1:11434" in commands[1]
    assert "--max-tokens" in commands[1]
    assert "64" in commands[1]
    assert commands[2][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "export-dashboard",
    ]


def test_bench_execute_approved_mlx_lm_flow_builds_expected_commands(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "mlx-community/Fixture-4bit",
            "--runner",
            "mlx-lm",
            "--run-id",
            "20260623-fixture-mlx-r1",
            "--output-root",
            str(output_root),
            "--mlx-python",
            str(fake_python),
            "--max-tokens",
            "64",
            "--i-approve-local-run",
            "--force",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "approval: explicit --i-approve-local-run" in output
    assert len(commands) == 3
    assert commands[0][:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert commands[1][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "run-mlx-lm",
    ]
    assert "--model-id" in commands[1]
    assert "mlx-community/Fixture-4bit" in commands[1]
    assert "--python-path" in commands[1]
    assert str(fake_python) in commands[1]
    assert "--max-tokens" in commands[1]
    assert "64" in commands[1]
    assert commands[2][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "export-dashboard",
    ]


def test_bench_execute_approved_llama_cpp_flow_builds_expected_commands(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    fake_llama = tmp_path / "llama-cli"
    fake_llama.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    write_registry(registry)
    commands = capture_commands(monkeypatch)

    exit_code = lab.main(
        [
            "bench",
            "execute",
            "--candidate",
            "candidate-ready",
            "--registry",
            str(registry),
            "--model-id",
            "/tmp/fixture-model.gguf",
            "--runner",
            "llama-cpp",
            "--run-id",
            "20260623-fixture-llama-r1",
            "--output-root",
            str(output_root),
            "--llama-cli-path",
            str(fake_llama),
            "--max-tokens",
            "64",
            "--i-approve-local-run",
            "--force",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "approval: explicit --i-approve-local-run" in output
    assert len(commands) == 3
    assert commands[0][:3] == [lab.sys.executable, str(lab.HARNESS_PATH), "init-run"]
    assert commands[1][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "run-llama-cpp",
    ]
    assert "--model-id" in commands[1]
    assert "/tmp/fixture-model.gguf" in commands[1]
    assert "--llama-cli-path" in commands[1]
    assert str(fake_llama) in commands[1]
    assert "--max-tokens" in commands[1]
    assert "64" in commands[1]
    assert commands[2][:3] == [
        lab.sys.executable,
        str(lab.HARNESS_PATH),
        "export-dashboard",
    ]


def test_bench_execute_requires_endpoint_for_openai_runner_after_approval(
    tmp_path,
    monkeypatch,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("missing endpoint must stop before subprocess")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)

    with pytest.raises(SystemExit) as exc:
        lab.main(
            [
                "bench",
                "execute",
                "--candidate",
                "candidate-ready",
                "--registry",
                str(registry),
                "--model-id",
                "explicit-local-model",
                "--runner",
                "openai-compatible",
                "--run-id",
                "20260617-explicit-local-model-r1",
                "--output-root",
                str(output_root),
                "--i-approve-local-run",
            ]
        )

    assert exc.value.code == "--endpoint is required for --runner openai-compatible"


def test_bench_queue_refuses_without_approval_before_any_execution(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    write_queue_registry(registry)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("bench queue must not call subprocess without batch approval")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)

    exit_code = lab.main(
        [
            "bench",
            "queue",
            "--candidate",
            "queue-one",
            "--candidate",
            "queue-two",
            "--registry",
            str(registry),
            "--output-root",
            str(tmp_path / "eval_results"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Benchmark queue preflight" in captured.out
    assert "queue-one" in captured.out
    assert "local-model-one" in captured.out
    assert "lmstudio-cli" in captured.out
    assert "20260714-queue-one-r1" in captured.out
    assert "queue-two" in captured.out
    assert "local-model-two:latest" in captured.out
    assert "ollama" in captured.out
    assert "20260714-queue-two-r1" in captured.out
    assert "approval: missing" in captured.err


@pytest.mark.parametrize("missing_field", ["local_model_id", "local_runner"])
def test_bench_queue_refuses_entire_batch_when_exact_runtime_metadata_is_missing(
    tmp_path,
    monkeypatch,
    capsys,
    missing_field,
) -> None:
    registry = tmp_path / "candidates.csv"
    write_queue_registry(registry, missing_field=missing_field)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("invalid bench queue must not call subprocess")

    monkeypatch.setattr(lab.subprocess, "run", fail_if_called)

    exit_code = lab.main(
        [
            "bench",
            "queue",
            "--candidate",
            "queue-one",
            "--candidate",
            "queue-two",
            "--registry",
            str(registry),
            "--i-approve-local-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Benchmark queue preflight" in captured.out
    assert "<missing>" in captured.out
    assert f"queue-two: missing {missing_field}" in captured.err
    assert "refusing entire batch before any execution" in captured.err


def test_bench_queue_enumerates_complete_batch_before_first_execution(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    write_queue_registry(registry)
    commands = []
    output_before_first_call = []

    def fake_run(command, check=False):
        if not commands:
            output_before_first_call.append(capsys.readouterr().out)
        commands.append(command)
        assert check is False
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(lab.subprocess, "run", fake_run)

    exit_code = lab.main(
        [
            "bench",
            "queue",
            "--candidate",
            "queue-one",
            "--candidate",
            "queue-two",
            "--registry",
            str(registry),
            "--output-root",
            str(tmp_path / "eval_results"),
            "--i-approve-local-run",
        ]
    )

    assert exit_code == 0
    assert len(output_before_first_call) == 1
    pre_execution = output_before_first_call[0]
    assert pre_execution.index("queue-one") < pre_execution.index("queue-two")
    for expected in (
        "local-model-one",
        "lmstudio-cli",
        "20260714-queue-one-r1",
        "local-model-two:latest",
        "ollama",
        "20260714-queue-two-r1",
        "approval: explicit --i-approve-local-run for enumerated batch of 2",
    ):
        assert expected in pre_execution
    assert len(commands) == 6


def test_bench_queue_continues_after_failure_and_prints_metric_summary(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    registry = tmp_path / "candidates.csv"
    output_root = tmp_path / "eval_results"
    write_queue_registry(registry)
    for run_id, latency, tokens_per_sec in (
        ("20260714-queue-one-r1", 8.5, 12.25),
        ("20260714-queue-two-r1", 4.0, 33.5),
    ):
        run_dir = output_root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "runtime-metrics.json").write_text(
            json.dumps(
                {
                    "total_latency_seconds": latency,
                    "tokens": {"tokens_per_sec": tokens_per_sec},
                }
            ),
            encoding="utf-8",
        )

    commands = []

    def fake_run(command, check=False):
        commands.append(command)
        assert check is False
        exit_code = 9 if command[2] == "run-lmstudio-cli" else 0
        return SimpleNamespace(returncode=exit_code)

    monkeypatch.setattr(lab.subprocess, "run", fake_run)

    exit_code = lab.main(
        [
            "bench",
            "queue",
            "--candidate",
            "queue-one",
            "--candidate",
            "queue-two",
            "--registry",
            str(registry),
            "--output-root",
            str(output_root),
            "--i-approve-local-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert any(command[2] == "run-ollama" for command in commands)
    assert "Benchmark queue summary" in output
    assert "| Candidate | Run id | Status | Latency (s) | Tok/s |" in output
    assert "| queue-one | 20260714-queue-one-r1 | failed (exit 9) | 8.5 | 12.25 |" in output
    assert "| queue-two | 20260714-queue-two-r1 | passed | 4 | 33.5 |" in output


def test_import_report_and_dashboard_shell_out(tmp_path, monkeypatch) -> None:
    commands = capture_commands(monkeypatch)
    db_path = tmp_path / "dashboard.sqlite"
    out_path = tmp_path / "report.md"

    assert (
        lab.main(
            ["import", "--run", "run-1", "--eval-results", str(tmp_path), "--db", str(db_path)]
        )
        == 0
    )
    assert lab.main(["report", "--db", str(db_path), "--out", str(out_path)]) == 0
    assert (
        lab.main(
            [
                "dashboard",
                "--db",
                str(db_path),
                "--port",
                "9999",
                "--demo",
                "--enable-delete-actions",
            ]
        )
        == 0
    )

    import_command, report_command, dashboard_command = commands
    assert import_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "import-csv"]
    assert str(tmp_path / "run-1" / "dashboard-import" / "models.csv") in import_command
    assert report_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "report"]
    assert str(out_path) in report_command
    assert dashboard_command[:3] == [lab.sys.executable, str(lab.DASHBOARD_ENTRYPOINT), "serve"]
    assert "--port" in dashboard_command
    assert "9999" in dashboard_command
    assert "--demo" in dashboard_command
    assert "--enable-delete-actions" in dashboard_command


def test_unknown_subcommand_exits_nonzero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        lab.main(["unknown"])

    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
