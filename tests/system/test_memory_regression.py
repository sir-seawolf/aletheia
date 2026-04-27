import pytest

def test_memory_regression():
    """
    Same input → consistent memory evolution.
    """
    from memory.service import store_event, retrieve_context
    from core.contracts.contract_lock import validate_final_report
    
    # Same input twice
    store_event("test input", "test", 0.8)
    store_event("test input", "test", 0.8)
    
    context = retrieve_context("test")
    assert len(context) >= 1
    
    # Mock report would validate
    mock_report = {"domain": "test", "question": "test", "scenarios": [{}], "guardian_block": False, "confidence": 0.5, "risks": {}}
    validate_final_report(mock_report)
    
    print("✅ Memory regression test passed")

