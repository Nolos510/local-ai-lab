"""Deterministic, dependency-free local model memory fit estimates."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

WEIGHT_OVERHEAD_MULTIPLIER = 1.1
DEFAULT_CONTEXT_OVERHEAD_GB = 8.0
DEFAULT_SYSTEM_RESERVE_GB = 16.0

_PARAMETER_COUNT_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[Bb]\b")
_BIT_QUANT_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*bit\b", re.IGNORECASE)
_Q_QUANT_RE = re.compile(r"(?<![A-Za-z0-9])(?:UD-)?I?Q(\d+(?:\.\d+)?)", re.IGNORECASE)
_FLOAT_INT_RE = re.compile(r"(?<![A-Za-z0-9])(?:BF|FP|F|U?INT)(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class FitAssessment:
    """A model memory estimate and classification against local machine memory."""

    status: str
    params_b: float | None
    bits: float | None
    estimated_weights_gb: float | None
    estimated_memory_gb: float | None
    budget_gb: float | None


def _positive_finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def parse_parameter_count_b(*values: object) -> float | None:
    """Return the first explicit parameter count, in billions, from supplied metadata."""
    for value in values:
        direct = _positive_finite(value)
        if direct is not None and not isinstance(value, str):
            return direct
        text = str(value or "").strip()
        if not text:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            return _positive_finite(text)
        match = _PARAMETER_COUNT_RE.search(text)
        if match and (parsed := _positive_finite(match.group(1))) is not None:
            return parsed
    return None


def parse_quantization_bits(*values: object) -> float | None:
    """Return the first explicit quantization bit-width from supplied metadata."""
    for value in values:
        direct = _positive_finite(value)
        if direct is not None and not isinstance(value, str):
            return direct
        text = str(value or "").strip()
        if not text:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            return _positive_finite(text)
        for pattern in (_BIT_QUANT_RE, _Q_QUANT_RE, _FLOAT_INT_RE):
            match = pattern.search(text)
            if match and (parsed := _positive_finite(match.group(1))) is not None:
                return parsed
    return None


def estimate_weights_gb(params_b: object, bits: object) -> float | None:
    """Estimate model weight memory using decimal billions and a 10% overhead."""
    parameters = _positive_finite(params_b)
    bit_width = _positive_finite(bits)
    if parameters is None or bit_width is None:
        return None
    estimate = parameters * bit_width / 8.0 * WEIGHT_OVERHEAD_MULTIPLIER
    return estimate if math.isfinite(estimate) else None


def estimate_memory_gb(
    params_b: object,
    bits: object,
    *,
    context_overhead_gb: object = DEFAULT_CONTEXT_OVERHEAD_GB,
) -> float | None:
    """Estimate weights plus a transparent fixed context/runtime allowance."""
    weights = estimate_weights_gb(params_b, bits)
    context = _positive_finite(context_overhead_gb)
    if weights is None or context is None:
        return None
    estimate = weights + context
    return estimate if math.isfinite(estimate) else None


def memory_budget_gb(
    memory_gb: object,
    *,
    system_reserve_gb: object = DEFAULT_SYSTEM_RESERVE_GB,
) -> float | None:
    """Return memory available after preserving the system reserve."""
    memory = _positive_finite(memory_gb)
    reserve = _positive_finite(system_reserve_gb)
    if memory is None or reserve is None or memory <= reserve:
        return None
    return memory - reserve


def classify_fit(
    estimated_memory_gb: object,
    memory_gb: object,
    *,
    system_reserve_gb: object = DEFAULT_SYSTEM_RESERVE_GB,
) -> str:
    """Classify an estimate using the sprint's strict percentage boundaries."""
    estimate = _positive_finite(estimated_memory_gb)
    budget = memory_budget_gb(memory_gb, system_reserve_gb=system_reserve_gb)
    if estimate is None or budget is None:
        return "unknown"
    if estimate * 2 < budget:
        return "comfortable"
    if estimate * 5 < budget * 4:
        return "fits"
    if estimate < budget:
        return "tight"
    return "exceeds"


def assess_fit(
    params_b: object,
    bits: object,
    memory_gb: object,
    *,
    context_overhead_gb: object = DEFAULT_CONTEXT_OVERHEAD_GB,
    system_reserve_gb: object = DEFAULT_SYSTEM_RESERVE_GB,
) -> FitAssessment:
    """Build a complete fit assessment without raising on missing or malformed data."""
    parameters = _positive_finite(params_b)
    bit_width = _positive_finite(bits)
    weights = estimate_weights_gb(parameters, bit_width)
    estimate = estimate_memory_gb(
        parameters,
        bit_width,
        context_overhead_gb=context_overhead_gb,
    )
    budget = memory_budget_gb(memory_gb, system_reserve_gb=system_reserve_gb)
    return FitAssessment(
        status=classify_fit(
            estimate,
            memory_gb,
            system_reserve_gb=system_reserve_gb,
        ),
        params_b=parameters,
        bits=bit_width,
        estimated_weights_gb=weights,
        estimated_memory_gb=estimate,
        budget_gb=budget,
    )


def max_estimated_weights_gb(
    memory_gb: object,
    *,
    context_overhead_gb: object = DEFAULT_CONTEXT_OVERHEAD_GB,
    system_reserve_gb: object = DEFAULT_SYSTEM_RESERVE_GB,
) -> float | None:
    """Return the estimated-weight capacity remaining after fixed allowances."""
    budget = memory_budget_gb(memory_gb, system_reserve_gb=system_reserve_gb)
    context = _positive_finite(context_overhead_gb)
    if budget is None or context is None or budget <= context:
        return None
    return budget - context
