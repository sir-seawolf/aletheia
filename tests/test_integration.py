"""
Integration tests — require a running Aletheia server + Ollama.

Skip automatically when server is not reachable.
Run manually:
    python start.py          # terminal 1
    pytest tests/test_integration.py -v --run-slow   # terminal 2
"""
import pytest
import requests

SERVER = "http://localhost:8000"


def _server_available() -> bool:
    try:
        requests.get(f"{SERVER}/health", timeout=3)
        return True
    except Exception:
        return False


def _ollama_available(server_status: dict) -> bool:
    return server_status.get("ollama_ok", False)


pytestmark = pytest.mark.skipif(
    not _server_available(),
    reason="Integration tests require a running Aletheia server (python start.py)"
)


@pytest.fixture(scope="module")
def api():
    """Raw requests session against the live server."""
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    return s


@pytest.fixture(scope="module")
def server_status(api):
    return api.get(f"{SERVER}/api/status").json()


class TestLiveHealth:
    def test_server_responds(self, api):
        r = api.get(f"{SERVER}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_status_has_provider(self, api, server_status):
        assert "provider" in server_status
        assert "fatigue" in server_status

    def test_setup_all_systems_reported(self, api):
        r = api.get(f"{SERVER}/api/setup/status")
        data = r.json()
        system_ids = [s["id"] for s in data["systems"]]
        for expected in ("ollama", "rag", "voice"):
            assert expected in system_ids, f"Missing system: {expected}"


class TestLiveChat:
    def test_chat_v3_responds(self, api, server_status):
        if not _ollama_available(server_status):
            pytest.skip("Ollama not running")
        r = api.post(f"{SERVER}/api/chat", json={
            "question": "¿Qué es Aletheia?",
            "domain": "general",
            "session_id": "test-integration-001",
            "use_v3_modes": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_chat_v1_responds(self, api, server_status):
        if not _ollama_available(server_status):
            pytest.skip("Ollama not running")
        r = api.post(f"{SERVER}/api/chat", json={
            "question": "¿Cuáles son mis gastos más altos?",
            "domain": "finanzas",
            "session_id": "test-integration-002",
            "use_v3_modes": False,
        })
        assert r.status_code == 200
        assert "reply" in r.json()

    def test_simulate_returns_decision_report(self, api, server_status):
        if not _ollama_available(server_status):
            pytest.skip("Ollama not running")
        r = api.post(f"{SERVER}/api/simulate", json={
            "domain": "finanzas",
            "question": "¿Puedo dejar mi trabajo en agosto?",
        })
        assert r.status_code == 200
        data = r.json()
        assert "scenarios" in data
        assert "guardian_block" in data
        assert isinstance(data["scenarios"], list)
        assert len(data["scenarios"]) >= 2

    def test_kronos_mode_activates(self, api, server_status):
        if not _ollama_available(server_status):
            pytest.skip("Ollama not running")
        r = api.post(f"{SERVER}/api/chat", json={
            "question": "¿Cuánto pago de IRPF este año?",
            "domain": "finanzas",
            "session_id": "test-integration-kronos",
            "use_v3_modes": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data


class TestLiveProjects:
    def test_full_project_lifecycle(self, api):
        # Create
        r = api.post(f"{SERVER}/api/projects", json={
            "title": "Test proyecto integración",
            "project_type": "home_improvement",
            "cost_upfront": 5000,
            "benefit_monthly": 80,
            "psychological_reward": 4,
        })
        assert r.status_code == 200
        project = r.json()
        pid = project["id"]
        assert project["score_global"] is not None

        # Read
        r = api.get(f"{SERVER}/api/projects/{pid}")
        assert r.status_code == 200

        # Update
        r = api.put(f"{SERVER}/api/projects/{pid}", json={"status": "active"})
        assert r.status_code == 200
        assert r.json()["status"] == "active"

        # Balance
        r = api.get(f"{SERVER}/api/projects/balance")
        assert r.json()["count"] >= 1

        # Delete
        r = api.delete(f"{SERVER}/api/projects/{pid}")
        assert r.json()["ok"] is True


class TestLiveConsolidation:
    def test_consolidation_status(self, api):
        r = api.get(f"{SERVER}/api/consolidation/status")
        data = r.json()
        assert "state" in data
        assert data["state"] in ("idle", "running", "scheduled")

    def test_pattern_detection(self, api):
        r = api.post(f"{SERVER}/api/consolidation/patterns/detect?since_hours=48")
        assert r.status_code == 200
        data = r.json()
        assert "found" in data

    def test_mark_all_read(self, api):
        r = api.post(f"{SERVER}/api/consolidation/patterns/mark_all_read")
        assert r.status_code == 200


class TestLiveMemory:
    def test_rag_search(self, api):
        r = api.post(f"{SERVER}/api/rag/search", json={
            "query": "finanzas",
            "n_results": 3,
        })
        # RAG might not have indexed anything, but endpoint should respond
        assert r.status_code in (200, 404)

    def test_traces_accessible(self, api):
        r = api.get(f"{SERVER}/api/traces")
        assert r.status_code == 200

    def test_learning_insights_accessible(self, api):
        r = api.get(f"{SERVER}/api/learning/insights")
        assert r.status_code == 200
