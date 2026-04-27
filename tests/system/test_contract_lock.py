import pytest
from core.contracts.contract_lock import validate_final_report, ContractViolation, normalize_report

def test_normalize_report():
    report = {"scenarios": [], "risks": []}
    normalized = normalize_report(report)
    assert normalized["guardian_block"] == False
    assert normalized["confidence"] == 0.5
    assert "version" in normalized

def test_validate_required_fields():
    from datetime import datetime
    valid_report = {
        "domain": "test",
        "question": "test?",
        "timestamp": datetime.now(),
        "facts": [],
        "gaps": [],
        "scenarios": [{"a":1}, {"b":2}],
        "risks": {"risk": 0.5},
        "assumptions": [],
        "llm_insight": "",
        "llm_explanation": "",
        "confidence": 0.8,
        "risk_level": "medium",
        "prediction": "test",
        "guardian_block": False
    }
    validated = validate_final_report(valid_report)
    assert validated["confidence"] == 0.8
    assert validated["guardian_block"] == False

def test_missing_scenarios():
    report = {"guardian_block": False}
    with pytest.raises(ContractViolation):
        validate_final_report(report)

def test_invalid_scenarios():
    report = {"scenarios": ["not", "list"], "guardian_block": False}
    with pytest.raises(ContractViolation):
        validate_final_report(report)

def test_contract_version():
    from core.contracts.contract_lock import freeze_contract_version
    assert freeze_contract_version() == "1.0"

