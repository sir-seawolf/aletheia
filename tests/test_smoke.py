"""
Smoke tests — every key endpoint responds with 2xx and expected shape.
No Ollama, no external deps. Fails fast if something is badly broken.
"""
import pytest


class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "system" in data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_system_health(self, client):
        r = client.get("/system/health")
        assert r.status_code == 200

    def test_api_status(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert "provider" in data
        assert "fatigue" in data

    def test_api_profile(self, client):
        r = client.get("/api/profile")
        assert r.status_code == 200


class TestSetup:
    def test_setup_status(self, client):
        r = client.get("/api/setup/status")
        assert r.status_code == 200
        data = r.json()
        assert "systems" in data
        assert "missing" in data
        assert "partial" in data
        assert isinstance(data["systems"], list)

    def test_setup_systems_have_required_fields(self, client):
        r = client.get("/api/setup/status")
        for sys in r.json()["systems"]:
            assert "id" in sys
            assert "status" in sys
            assert sys["status"] in ("ok", "partial", "missing")


class TestSettings:
    def test_get_settings(self, client):
        r = client.get("/api/settings")
        assert r.status_code == 200

    def test_get_preferences(self, client):
        r = client.get("/api/settings")
        data = r.json()
        assert isinstance(data, dict)


class TestMemory:
    def test_artifacts_list(self, client):
        r = client.get("/api/artifacts")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_artifacts_stats(self, client):
        r = client.get("/api/artifacts/stats")
        assert r.status_code == 200

    def test_rag_search(self, client):
        r = client.post("/api/rag/search", json={"query": "finanzas", "n_results": 3})
        assert r.status_code in (200, 422)  # 422 if RAG not indexed yet


class TestProjects:
    def test_projects_list_empty(self, client):
        r = client.get("/api/projects")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_projects_types(self, client):
        r = client.get("/api/projects/types")
        assert r.status_code == 200
        types = r.json()
        assert isinstance(types, list)
        ids = [t["id"] for t in types]
        assert "life_decision" in ids
        assert "home_improvement" in ids
        assert "career" in ids

    def test_projects_balance(self, client):
        r = client.get("/api/projects/balance")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data

    def test_projects_reminders(self, client):
        r = client.get("/api/projects/reminders")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestConsolidation:
    def test_consolidation_status(self, client):
        r = client.get("/api/consolidation/status")
        assert r.status_code == 200
        data = r.json()
        assert "state" in data

    def test_patterns_list(self, client):
        r = client.get("/api/consolidation/patterns")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_patterns_unread_count(self, client):
        r = client.get("/api/consolidation/patterns/unread_count")
        assert r.status_code == 200
        assert "count" in r.json()


class TestCognitive:
    def test_traces_empty(self, client):
        r = client.get("/api/traces")
        assert r.status_code == 200

    def test_learning_insights(self, client):
        r = client.get("/api/learning/insights")
        assert r.status_code == 200

    def test_modes_status(self, client):
        r = client.get("/api/modes/status")
        assert r.status_code == 200
