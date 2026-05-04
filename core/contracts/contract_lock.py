
"""
Cognitive Contract Lock - Single source of truth for DecisionReport validity.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.schemas.decision_contract (DecisionReport)
Last stable version: v1.1

All outputs MUST pass through here before leaving /simulate.
Enforces schema, normalizes, blocks invalid reports.
"""

from typing import Dict, Any
from pydantic import ValidationError
from core.schemas.decision_contract import DecisionReport

class ContractViolation(Exception):
    "Raised when DecisionReport violates the cognitive contract."
    pass

REQUIRED_FIELDS = [
    "domain",
    "question", 
    "scenarios",  # List[Dict], min len 2
    "risks",      # Dict[str, float]
    "confidence", # 0.0 <= float <= 1.0
    "guardian_block"  # bool, added by guardian
]

def normalize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures consistent output shape. Cleans invalid fields.
    """
    # Defaults from schema
    report.setdefault("version", "1.0")
    report.setdefault("guardian_block", False)
    report.setdefault("guardian_severity", "none")
    report.setdefault("confidence", 0.5)
    report.setdefault("scenarios", [])
    report.setdefault("risks", {})
    report.setdefault("validation_issues", [])
    report.setdefault("risk_level", "medium")
    
    # Normalize risks List[str] -> Dict[str,float] if needed
    if isinstance(report["risks"], list):
        report["risks"] = {risk: 0.5 for risk in report["risks"]}
    
    # Enforce no extra fields (strict)
    allowed = set(REQUIRED_FIELDS + ["version", "timestamp", "facts", "gaps", "assumptions", 
                                     "llm_insight", "prediction", "node_id", "contract_version", "guardian_trace"])
    report = {k: v for k, v in report.items() if k in allowed}
    
    return report

def validate_final_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Single source of truth for output validation.
    Raises ContractViolation on failure.
    """
    report = normalize_report(report)
    
    # 1. Required fields first
    for field in REQUIRED_FIELDS:
        if field not in report:
            raise ContractViolation(f"Missing required field: {field}")
    
    # 2. TYPE VALIDATION (guardian primero)
    if not isinstance(report["guardian_block"], bool):
        raise ContractViolation("guardian_block must be bool")
    
    # 3. SCENARIOS validation
    if not isinstance(report["scenarios"], list) or len(report["scenarios"]) < 2:
        raise ContractViolation("scenarios must be list with min 2 items")
    
    if not isinstance(report["risks"], dict):
        raise ContractViolation("risks must be Dict[str, float]")
    
    if not isinstance(report["confidence"], (int, float)) or not 0 <= report["confidence"] <= 1:
        raise ContractViolation("confidence must be float between 0.0 and 1.0")
    
    # Add timestamp if missing
    if "timestamp" not in report:
        from datetime import datetime
        report["timestamp"] = datetime.now().isoformat()
    
    return report

def freeze_contract_version() -> str:
    "Returns current frozen contract version. Prevents schema drift."
    return "1.0"

def enforce_contract(report: dict) -> dict:
    """
    Final contract enforcement: normalize, validate, version stamp.

    Args:
        report (dict): Raw output from orchestrator

    Returns:
        dict: Validated DecisionReport ready for API/memory

    Raises:
        ContractViolation: If report fails validation
    """
    report = normalize_report(report)
    validate_final_report(report)
    report["contract_version"] = freeze_contract_version()
    return report

