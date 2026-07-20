import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_readiness_report.py"
SPEC = importlib.util.spec_from_file_location("generate_readiness_report", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _scorecard(criteria):
    return {
        "measured_at": "2026-07-18",
        "evaluated_revision": "abc123",
        "patch_state": "dirty and preserved",
        "baseline_score": 68.2,
        "executive_assessment": "Evidence-based assessment.",
        "release_gate": {
            "minimum_score": 92,
            "minimum_criterion": 4,
            "protected_minimum": 4.5,
            "protected_criteria": ["Trust"],
        },
        "criteria": criteria,
        "evidence_register": [
            {"id": "E1", "title": "Tests", "confidence": "High", "finding": "Passed."}
        ],
        "risks": [],
        "journeys": [{"status": "PASS", "name": "Demo", "evidence": "Worked."}],
        "validation": [{"command": "pytest", "status": "PASS", "detail": "One test."}],
    }


def test_render_report_calculates_gate_from_evidence():
    report = MODULE.render_report(
        _scorecard(
            [
                {
                    "criterion": "Trust",
                    "weight": 100,
                    "rating": 4.6,
                    "confidence": "High",
                    "evidence": ["Audited"],
                    "blockers": [],
                    "owner": "Owner",
                }
            ]
        )
    )

    assert "**92.0/100**" in report
    assert "**GO**" in report


def test_render_report_rejects_weights_that_do_not_total_100():
    with pytest.raises(ValueError, match="must total 100"):
        MODULE.render_report(
            _scorecard(
                [
                    {
                        "criterion": "Trust",
                        "weight": 99,
                        "rating": 5,
                        "confidence": "High",
                        "evidence": [],
                        "blockers": [],
                        "owner": "Owner",
                    }
                ]
            )
        )
