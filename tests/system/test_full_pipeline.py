from unittest.mock import patch

from core.contracts.contract_lock import enforce_contract
from core.orchestrator import process_request


def test_full_pipeline_pure_flow():
    with patch("core.orchestrator.profile_module.load", return_value={}), \
         patch("core.orchestrator.profile_module.extract_from_text", side_effect=lambda q, p: p), \
         patch("core.orchestrator.profile_module.to_context_str", return_value=""), \
         patch("core.orchestrator.retrieve_context", return_value=[]), \
         patch("core.orchestrator.apply_aco", side_effect=lambda c: {**c, "aco_policy": {"mode": "balanced"}}), \
         patch("core.orchestrator.cel.execute", return_value=None), \
         patch("core.orchestrator.emit_event", return_value=None), \
         patch("core.orchestrator.build_event", return_value={}), \
         patch("core.orchestrator.explorer.run") as mock_explore, \
         patch("core.orchestrator.simulator.run") as mock_simulate, \
         patch("core.orchestrator.guardian.validate") as mock_guardian, \
         patch("core.orchestrator.read_palace", return_value=[]), \
         patch("core.orchestrator.compute_dqs", return_value=0.81), \
         patch("core.orchestrator.aco_optimizer.observe", return_value=None), \
         patch("core.orchestrator.aco_learning.record", return_value=None), \
         patch("core.orchestrator.attach_to_palace", return_value=None):

        mock_explore.return_value = {"facts": ["fact1"], "gaps": [], "confidence": 0.8}
        mock_simulate.return_value = {
            "scenarios": [{"outcome": "test"}],
            "risks": {"test": 0.5},
            "assumptions": ["assum"],
        }
        mock_guardian.return_value = {
            "valid": True,
            "issues": [],
            "corrected_output": {
                "domain": "test",
                "question": "test",
                "scenarios": [...],
                "guardian_block": False,
            },
        }

        result = process_request("test", "test?")

        enforce_contract(result)
        assert "guardian_block" in result
        assert result["guardian_block"] is False

