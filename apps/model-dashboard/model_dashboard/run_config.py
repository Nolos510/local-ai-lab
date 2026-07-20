"""Run configuration inference and provenance helpers."""

from __future__ import annotations

import re

DEFAULT_CONTEXT_WINDOW = 4096
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9

QUANT_PATTERNS = (
    re.compile(r"\b(MLX[-_ ]?4bit)\b", re.IGNORECASE),
    re.compile(r"\b(Q[0-9]+(?:_[A-Z0-9]+)*)\b", re.IGNORECASE),
    re.compile(r"\b([0-9]+bit)\b", re.IGNORECASE),
)


def infer_quantization(*values):
    for value in values:
        text = str(value or "")
        if not text:
            continue
        for pattern in QUANT_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            raw = match.group(1)
            normalized = raw.lower().replace("_", "-").replace(" ", "-")
            if normalized == "mlx-4bit":
                return "4bit", "inferred:model_name_or_path"
            if raw.lower().endswith("bit"):
                return raw.lower(), "inferred:model_name_or_path"
            return raw.upper(), "inferred:model_name_or_path"
    return None, None


def run_note_value(notes, key):
    prefix = f"{key}="
    for part in str(notes or "").split("|"):
        part = part.strip()
        if part.startswith(prefix):
            return part.split("=", 1)[1].strip()
    return ""


def append_run_note(notes, key, value):
    parts = [part.strip() for part in str(notes or "").split("|") if part.strip()]
    prefix = f"{key}="
    parts = [part for part in parts if not part.startswith(prefix)]
    if value not in (None, ""):
        parts.append(f"{key}={value}")
    return " | ".join(parts)


def apply_run_config_defaults(run, model=None, *, source_when_present="artifact"):
    model = model or {}
    updated = dict(run)
    notes = updated.get("run_notes") or ""
    if updated.get("quantization") in (None, ""):
        inferred, source = infer_quantization(
            model.get("model_name"),
            model.get("source_url"),
            model.get("notes"),
            updated.get("format"),
            updated.get("run_notes"),
        )
        if inferred:
            updated["quantization"] = inferred
            notes = append_run_note(notes, "quantization_source", source)
    elif not run_note_value(notes, "quantization_source"):
        notes = append_run_note(notes, "quantization_source", source_when_present)

    defaults = {
        "context_window": (DEFAULT_CONTEXT_WINDOW, "context_window_source"),
        "temperature": (DEFAULT_TEMPERATURE, "temperature_source"),
        "top_p": (DEFAULT_TOP_P, "top_p_source"),
    }
    for field, (default, note_key) in defaults.items():
        if updated.get(field) in (None, ""):
            updated[field] = default
            notes = append_run_note(notes, note_key, "inferred:benchmark_default")
        elif not run_note_value(notes, note_key):
            notes = append_run_note(notes, note_key, source_when_present)
    updated["run_notes"] = notes
    return updated


__all__ = (
    "DEFAULT_CONTEXT_WINDOW",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TOP_P",
    "append_run_note",
    "apply_run_config_defaults",
    "infer_quantization",
    "run_note_value",
)
