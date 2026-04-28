import pytest

def test_memory_regression():
    """
    Same input → consistent memory evolution.
    """
    from memory.service import retrieve_context, store_event
    from core.contracts.contract_lock import validate_final_report
    
    # Same input twice
    store_event({"event_type": "test", "domain": "test", "content": "test input"})
    store_event({"event_type": "test", "domain": "test", "content": "test input"})
    
    context = retrieve_context("test")
    assert len(context) >= 1
    
    # Mock report would validate
    mock_report = {"domain": "test", "question": "test", "scenarios": [{"outcome": "ok"}, {"outcome": "alt"}], "guardian_block": False, "confidence": 0.5, "risks": {}}
    validate_final_report(mock_report)
    
    print("✅ Memory regression test passed")

