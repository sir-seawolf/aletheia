"""
Shared fixtures for Aletheia test suite.

- `client`      FastAPI TestClient (no server needed, no Ollama)
- `tmp_db`      Temporary SQLite path for isolation
- `mock_llm`    Patches LLMRouter.generate to return predictable text
- `projects_mgr` Fresh ProjectManager on a temp DB
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Single TestClient reused across the session (avoids repeated app init)."""
    from fastapi.testclient import TestClient
    from core.bootstrap.runtime import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Temporary DB ──────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path):
    """Yields a temp path for SQLite files (auto-deleted after test)."""
    return tmp_path / "test.db"


# ── Mock LLM ─────────────────────────────────────────────────────────────────

_FAKE_RESPONSE = (
    "ANÁLISIS: Este proyecto tiene potencial positivo a largo plazo. "
    "Los costes iniciales son recuperables en menos de 3 años. "
    "Recomendamos proceder con cautela.\n"
    "RECOMENDACIÓN: PROCEDER\n"
    "CONDICIÓN: Tener liquidez suficiente antes de iniciar."
)


@pytest.fixture()
def mock_llm():
    """Patch LLMRouter.generate to avoid calling Ollama/Claude."""
    with patch("core.llm.router.LLMRouter.generate", new_callable=AsyncMock) as m:
        m.return_value = _FAKE_RESPONSE
        yield m


# ── Projects manager on temp DB ───────────────────────────────────────────────

@pytest.fixture()
def projects_mgr(tmp_path):
    from core.projects.manager import ProjectManager
    return ProjectManager(db_path=tmp_path / "projects.db")


# ── Pattern detector on temp DB ──────────────────────────────────────────────

@pytest.fixture()
def pattern_det(tmp_path):
    from core.cognition.pattern_detector import PatternDetector
    return PatternDetector(db_path=str(tmp_path / "aletheia_test.db"))
