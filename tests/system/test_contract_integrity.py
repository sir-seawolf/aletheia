import pytest
from core.contracts.contract_lock import ContractViolation, validate_final_report, enforce_contract
from core.orchestrator import process_request

def test_broken_simulator():
    broken_report = {"domain": "test", "question": "test", "scenarios": [], "risks": {}, "confidence": 0.5}
    with pytest.raises(ContractViolation, match="scenarios must be list with min 2"):
        validate_final_report(broken_report)
    print("OK Broken simulator blocked")

def test_broken_guardian():
    broken_report = {"domain": "test", "question": "test", "scenarios": [{}], "risks": {}, "confidence": 0.5, "guardian_block": "not bool"}
    with pytest.raises(ContractViolation, match="guardian_block must be bool"):
        validate_final_report(broken_report)
    print("OK Broken guardian blocked")

def test_every_output_passes_contract():
    """
    Every process_request output passes full contract enforcement.
    """
    result = process_request(domain="test", question="What is the best approach?")
    final = enforce_contract(result)
    print("OK Full pipeline passes contract")
    print(f"Contract version: {final.get('contract_version', 'missing')}")

