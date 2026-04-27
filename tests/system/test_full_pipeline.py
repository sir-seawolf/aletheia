import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import process_request
from core.contracts.contract_lock import enforce_contract
from agents import explorer, simulator, guardian

def test_full_pipeline_pure_flow():
    # Mock agents for new pure router
    with patch('agents.explorer.run') as mock_explore, \
         patch('agents.simulator.run') as mock_simulate, \
         patch('agents.guardian.validate') as mock_guardian:
        
        mock_explore.return_value = {"facts": ["fact1"], "gaps": [], "confidence": 0.8}
        mock_simulate.return_value = {"scenarios": [{"outcome": "test"}], "risks": {"test": 0.5}, "assumptions": ["assum"]}
        mock_guardian.return_value = {
            "valid": True, 
            "issues": [],
            "corrected_output": {"domain": "test", "question": "test", "scenarios": [...], "guardian_block": False}
        }
        
        result = process_request("test", "test?")
        
        enforce_contract(result)
        assert "guardian_block" in result
        assert result["guardian_block"] == False
        print("✅ Pure pipeline produces guardian-protected contract-compliant report")

