import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import process_request
from core.contracts.contract_lock import enforce_contract
def test_full_pipeline_pure_flow():
    with patch('core.pipeline.explorer.run') as mock_explore, \
         patch('core.pipeline.simulator.run') as mock_simulate, \
         patch('core.pipeline.guardian.validate') as mock_guardian:
        
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

