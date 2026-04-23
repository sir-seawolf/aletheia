"""Constructor del estado mental de Aletheia."""

from typing import List, Optional, Dict, Any


class Context:
    """Representa el contexto completo de una solicitud."""

    def __init__(
        self,
        domain: str,
        risk: Dict[str, Any],
        memory: List[str],
        question: str,
        constraints: Optional[List[str]] = None,
    ):
        self.domain = domain
        self.risk = risk
        self.memory = memory
        self.question = question
        self.constraints = constraints or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "risk": self.risk,
            "memory": self.memory,
            "question": self.question,
            "constraints": self.constraints,
        }

    @classmethod
    def from_request(
        cls,
        domain: str,
        question: str,
        memory: List[str],
        risk_config: Dict[str, Any],
        constraints: Optional[List[str]] = None,
    ) -> "Context":
        return cls(
            domain=domain,
            risk=risk_config,
            memory=memory,
            question=question,
            constraints=constraints,
        )

