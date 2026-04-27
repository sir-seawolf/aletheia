"""
Contract API Gateway - Enforces input contracts for all endpoints.
Input validation ONLY.
"""

from typing import Any, Dict


class APIContractGate:
    """
    API Input Contract Enforcement Layer.
    ALL requests MUST pass through validate_request().
    """

    @staticmethod
    def validate_request(req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming API request structure.
        """
        if not isinstance(req, dict):
            raise ValueError("Request must be dict")

        if "domain" not in req or not isinstance(req["domain"], str):
            raise ValueError("Invalid domain")

        if "question" not in req or not isinstance(req["question"], str):
            raise ValueError("Invalid question")

        return req

