from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from local_ai_lab.cli import quant_advisor


def test_extracts_common_quant_suffixes_from_filenames_and_refs() -> None:
    values = [
        "DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf",
        "model.Q5_K_M.gguf",
        "model-Q6_K.gguf",
        "model-Q8_0.gguf",
        "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:UD-Q4_K_XL",
    ]

    assert [quant_advisor.extract_quantization(value) for value in values] == [
        "Q4_K_M",
        "Q5_K_M",
        "Q6_K",
        "Q8_0",
        "UD-Q4_K_XL",
    ]


def test_non_gguf_safetensors_metadata_returns_quantized_artifact_need() -> None:
    advice = quant_advisor.build_advice(
        base_repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        artifact_refs=[
            quant_advisor.ArtifactRef(
                repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
                artifact_ref="model.safetensors",
                filename="model.safetensors",
            )
        ],
        looked_up_at=datetime(2026, 6, 22, tzinfo=UTC),
    )

    assert advice["options"][0]["recommendation"] == "needs_quantized_artifact"
    assert advice["options"][0]["format"] == "source-or-safetensors"


def test_8b_256gb_ranking_prefers_balanced_and_quality_over_tiny_quants() -> None:
    refs = [
        quant_advisor.ArtifactRef("random/repo-GGUF", "model-IQ3_M.gguf", "model-IQ3_M.gguf"),
        quant_advisor.ArtifactRef("unsloth/repo-GGUF", "model-Q4_K_M.gguf", "model-Q4_K_M.gguf"),
        quant_advisor.ArtifactRef("bartowski/repo-GGUF", "model-Q6_K.gguf", "model-Q6_K.gguf"),
        quant_advisor.ArtifactRef(
            "lmstudio-community/repo-GGUF",
            "model-Q5_K_M.gguf",
            "model-Q5_K_M.gguf",
        ),
    ]

    advice = quant_advisor.build_advice(
        base_repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        artifact_refs=refs,
        looked_up_at=datetime(2026, 6, 22, tzinfo=UTC),
    )

    options = advice["options"]
    assert options[0]["quantization"] == "Q5_K_M"
    assert options[0]["recommendation"] == "recommended_balanced"
    assert options[1]["quantization"] == "Q6_K"
    assert all(option["fit_tier"] != "fit_constrained_large_model_only" for option in options)


def test_fit_constrained_tiny_quant_is_not_default_for_8b_machine() -> None:
    advice = quant_advisor.build_advice(
        base_repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        artifact_refs=[
            quant_advisor.ArtifactRef("random/repo-GGUF", "model-IQ3_M.gguf", "model-IQ3_M.gguf")
        ],
        looked_up_at=datetime(2026, 6, 22, tzinfo=UTC),
    )

    assert advice["options"][0]["fit_tier"] == "fit_constrained_large_model_only"
    assert advice["options"][0]["recommendation"] == "avoid_for_this_8b_lab_default"


def test_unknown_license_and_provenance_keeps_download_blocked() -> None:
    advice = quant_advisor.build_advice(
        base_repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        artifact_refs=[
            quant_advisor.ArtifactRef(
                "lmstudio-community/repo-GGUF",
                "model-Q5_K_M.gguf",
                "model-Q5_K_M.gguf",
            )
        ],
        candidate={"local_runner": "lmstudio-cli", "local_model_id": "local-id"},
        looked_up_at=datetime(2026, 6, 22, tzinfo=UTC),
    )

    assert "not_approved_to_download" in advice["options"][0]["approval_state"]


def test_lookup_hf_uses_public_metadata_and_parses_gguf_siblings(monkeypatch) -> None:
    calls: list[str] = []

    def fake_fetch(url: str, *, timeout: float = 10.0):
        calls.append(url)
        if "search=" in url:
            return [{"modelId": "lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF"}]
        return {
            "modelId": "lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF",
            "siblings": [
                {"rfilename": "DeepSeek-R1-0528-Qwen3-8B-Q5_K_M.gguf"},
                {"rfilename": "model.safetensors"},
            ],
        }

    monkeypatch.setattr(quant_advisor, "fetch_hf_json", fake_fetch)

    advice = quant_advisor.advise(
        repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        lookup_hf=True,
    )

    assert advice["network_lookup"] is True
    assert calls
    assert advice["options"][0]["quantization"] == "Q5_K_M"


def test_json_output_is_valid_json() -> None:
    advice = quant_advisor.build_advice(
        base_repo_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        looked_up_at=datetime(2026, 6, 22, tzinfo=UTC),
    )

    parsed = json.loads(quant_advisor.format_json(advice))

    assert parsed["base_repo_id"] == "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"


def test_invalid_repo_ids_are_rejected() -> None:
    with pytest.raises(ValueError):
        quant_advisor.validate_repo_id("../unsafe")
