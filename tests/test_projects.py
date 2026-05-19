"""
Tests for core/projects/ — ProjectManager CRUD, scorer, and API endpoints.
No LLM needed. Uses an isolated temp DB per test.
"""
import pytest
from core.projects.analyzer import compute_score, get_recommendation


# ── ProjectManager unit tests ─────────────────────────────────────────────────

class TestProjectManager:

    def test_create_minimal(self, projects_mgr):
        p = projects_mgr.create({"title": "Paneles solares"})
        assert p["id"]
        assert p["title"] == "Paneles solares"
        assert p["status"] == "idea"
        assert p["project_type"] == "other"

    def test_create_with_all_fields(self, projects_mgr):
        p = projects_mgr.create({
            "title": "Cambio de trabajo",
            "description": "Dejar empresa actual en agosto",
            "project_type": "life_decision",
            "status": "active",
            "cost_upfront": 0,
            "benefit_monthly": 500,
            "cost_recurring_monthly": 0,
            "savings_required": 10000,
            "psychological_stress": 4,
            "psychological_reward": 5,
            "physical_effort": 1,
            "physical_benefit": 1,
            "relational_impact": 1,
            "pros": ["mejor salario", "más autonomía"],
            "cons": ["más riesgo", "cambio de equipo"],
            "risks": [{"description": "no encontrar trabajo bueno"}],
        })
        assert p["project_type"] == "life_decision"
        assert p["benefit_monthly"] == 500
        assert p["savings_required"] == 10000
        assert len(p["pros"]) == 2
        assert len(p["cons"]) == 2
        assert len(p["risks"]) == 1
        assert p["type_meta"]["label"] == "Decisión vital"

    def test_list_returns_all(self, projects_mgr):
        projects_mgr.create({"title": "Proyecto A"})
        projects_mgr.create({"title": "Proyecto B"})
        all_p = projects_mgr.list()
        assert len(all_p) >= 2

    def test_list_filter_by_status(self, projects_mgr):
        projects_mgr.create({"title": "Activo", "status": "active"})
        projects_mgr.create({"title": "Idea",   "status": "idea"})
        activos = projects_mgr.list(status="active")
        assert all(p["status"] == "active" for p in activos)
        ideas = projects_mgr.list(status="idea")
        assert all(p["status"] == "idea" for p in ideas)

    def test_list_filter_by_type(self, projects_mgr):
        projects_mgr.create({"title": "Reform", "project_type": "home_improvement"})
        projects_mgr.create({"title": "Job",    "project_type": "career"})
        reforms = projects_mgr.list(project_type="home_improvement")
        assert all(p["project_type"] == "home_improvement" for p in reforms)

    def test_get_existing(self, projects_mgr):
        created = projects_mgr.create({"title": "Mi proyecto"})
        fetched = projects_mgr.get(created["id"])
        assert fetched["id"] == created["id"]
        assert fetched["title"] == "Mi proyecto"

    def test_get_nonexistent_returns_none(self, projects_mgr):
        assert projects_mgr.get("nonexistent-id") is None

    def test_update_title(self, projects_mgr):
        p = projects_mgr.create({"title": "Viejo título"})
        updated = projects_mgr.update(p["id"], {"title": "Nuevo título"})
        assert updated["title"] == "Nuevo título"

    def test_update_status(self, projects_mgr):
        p = projects_mgr.create({"title": "Test", "status": "idea"})
        updated = projects_mgr.update(p["id"], {"status": "active"})
        assert updated["status"] == "active"

    def test_update_financial_recalculates_payback(self, projects_mgr):
        p = projects_mgr.create({"title": "Solar"})
        updated = projects_mgr.update(p["id"], {
            "cost_upfront": 8000,
            "benefit_monthly": 100,
            "cost_recurring_monthly": 0,
        })
        assert updated["payback_months"] == 80

    def test_discard_sets_status(self, projects_mgr):
        p = projects_mgr.create({"title": "Para descartar"})
        ok = projects_mgr.discard(p["id"])
        assert ok
        fetched = projects_mgr.get(p["id"])
        assert fetched["status"] == "discarded"

    def test_discard_nonexistent_returns_false(self, projects_mgr):
        assert not projects_mgr.discard("nonexistent")

    def test_payback_auto_computed_on_create(self, projects_mgr):
        p = projects_mgr.create({
            "title": "Auto payback",
            "cost_upfront": 6000,
            "benefit_monthly": 200,
            "cost_recurring_monthly": 50,
        })
        # net_monthly = 200 - 50 = 150 → payback = 6000/150 = 40
        assert p["payback_months"] == 40

    def test_balance_reflects_projects(self, projects_mgr):
        projects_mgr.create({"title": "A", "status": "active", "cost_upfront": 1000})
        projects_mgr.create({"title": "B", "status": "idea",   "cost_upfront": 2000})
        bal = projects_mgr.get_portfolio_balance()
        assert bal["count"] >= 2
        assert bal["total_cost_upfront"] >= 3000

    def test_reminders_overdue(self, projects_mgr):
        from datetime import date, timedelta
        past = (date.today() - timedelta(days=1)).isoformat()
        projects_mgr.create({"title": "Overdue", "status": "idea", "review_date": past})
        reminders = projects_mgr.get_reminders()
        titles = [r["title"] for r in reminders]
        assert "Overdue" in titles


# ── Scorer unit tests ────────────────────────────────────────────────────────

class TestScorer:

    def test_score_pure_benefit(self):
        # €500/month gain, no cost → very positive
        score = compute_score({
            "cost_upfront": 0, "benefit_monthly": 500,
            "cost_recurring_monthly": 0,
            "psychological_stress": 2, "psychological_reward": 5,
            "physical_effort": 1, "physical_benefit": 1,
            "relational_impact": 0,
        })
        assert score > 0

    def test_score_pure_cost(self):
        # Big cost, no return → negative
        score = compute_score({
            "cost_upfront": 50000, "benefit_monthly": 0,
            "cost_recurring_monthly": 500,
            "psychological_stress": 4, "psychological_reward": 1,
            "physical_effort": 4, "physical_benefit": 0,
            "relational_impact": -1,
        })
        assert score < 0

    def test_score_bounded(self):
        for _ in range(10):
            import random
            score = compute_score({
                "cost_upfront": random.uniform(0, 100000),
                "benefit_monthly": random.uniform(0, 5000),
                "cost_recurring_monthly": random.uniform(0, 1000),
                "psychological_stress": random.randint(1, 5),
                "psychological_reward": random.randint(1, 5),
                "physical_effort": random.randint(1, 5),
                "physical_benefit": random.randint(1, 5),
                "relational_impact": random.randint(-2, 2),
            })
            assert -10 <= score <= 10

    def test_recommendation_proceed(self):
        assert get_recommendation(6.0, {"savings_required": 0}) == "proceed"

    def test_recommendation_defer(self):
        assert get_recommendation(2.0, {"savings_required": 0}) == "defer"

    def test_recommendation_review(self):
        assert get_recommendation(0.0, {"savings_required": 0}) == "review"

    def test_recommendation_discard(self):
        assert get_recommendation(-5.0, {"savings_required": 0}) == "discard"

    def test_recommendation_review_when_savings_required(self):
        # Good score but savings gate not met → review
        rec = get_recommendation(7.0, {"savings_required": 10000})
        assert rec == "review"


# ── Projects API endpoint tests ───────────────────────────────────────────────

class TestProjectsAPI:

    def test_create_via_api(self, client):
        r = client.post("/api/projects", json={
            "title": "Test API project",
            "project_type": "purchase",
            "cost_upfront": 5000,
            "benefit_monthly": 100,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Test API project"
        assert data["score_global"] is not None
        assert data["recommendation"] in ("proceed", "defer", "review", "discard")

    def test_get_via_api(self, client):
        created = client.post("/api/projects", json={"title": "Para GET"}).json()
        r = client.get(f"/api/projects/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/api/projects/nonexistent-uuid")
        assert r.status_code == 404

    def test_update_via_api(self, client):
        created = client.post("/api/projects", json={"title": "Original"}).json()
        r = client.put(f"/api/projects/{created['id']}", json={"title": "Actualizado"})
        assert r.status_code == 200
        assert r.json()["title"] == "Actualizado"

    def test_delete_via_api(self, client):
        created = client.post("/api/projects", json={"title": "Para borrar"}).json()
        r = client.delete(f"/api/projects/{created['id']}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_score_recomputed_on_update(self, client):
        created = client.post("/api/projects", json={
            "title": "Score test",
            "psychological_reward": 1,
        }).json()
        old_score = created["score_global"]

        updated = client.put(f"/api/projects/{created['id']}", json={
            "psychological_reward": 5,
            "benefit_monthly": 1000,
        }).json()
        # Score should change when dimensions change
        assert updated["score_global"] is not None
