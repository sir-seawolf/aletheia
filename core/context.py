"""Constructor del estado mental de Aletheia."""

from typing import List, Optional, Dict, Any
from memory.models import UserProfile


class Context:
    """Representa el contexto completo de una solicitud."""

    def __init__(
        self,
        domain: str,
        risk: Dict[str, Any],
        memory: List[str],
        question: str,
        constraints: Optional[List[str]] = None,
        user_profile: Optional[UserProfile] = None,
        session_id: str = "local",
    ):
        self.domain = domain
        self.risk = risk
        self.memory = memory
        self.question = question
        self.constraints = constraints or []
        self.user_profile = user_profile
        self.session_id = session_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "risk": self.risk,
            "memory": self.memory,
            "question": self.question,
            "constraints": self.constraints,
            "user_profile": self.user_profile,
            "session_id": self.session_id,
        }

    def summary(self) -> str:
        """Retorna una línea de resumen del contexto para debugging rápido."""
        risk_level = self.risk.get("level", "unknown")
        mem_count = len(self.memory)
        profile_hint = ""
        if self.user_profile:
            profile_hint = f" | profile={self.user_profile.verbosity_preference}"
        return f"[Aletheia] domain={self.domain} | risk={risk_level} | memory={mem_count}{profile_hint} | q={self.question[:40]}..."

    @classmethod
    def from_request(
        cls,
        domain: str,
        question: str,
        memory: List[str],
        risk_config: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        user_profile: Optional[UserProfile] = None,
        session_id: str = "local",
    ) -> "Context":
        return cls(
            domain=domain,
            risk=risk_config,
            memory=memory,
            question=question,
            constraints=constraints,
            user_profile=user_profile,
            session_id=session_id,
        )

