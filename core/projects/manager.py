"""ProjectManager — CRUD for multi-dimensional life project cards."""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path("memory/data/projects.db")

PROJECT_TYPES: dict[str, dict] = {
    "life_decision":    {"label": "Decisión vital",     "icon": "⚖️"},
    "career":           {"label": "Carrera / Trabajo",  "icon": "💼"},
    "home_improvement": {"label": "Reforma / Hogar",    "icon": "🏠"},
    "purchase":         {"label": "Compra importante",  "icon": "🛒"},
    "financial_goal":   {"label": "Meta financiera",    "icon": "💶"},
    "health_wellness":  {"label": "Salud / Bienestar",  "icon": "❤️"},
    "education":        {"label": "Formación",          "icon": "📚"},
    "business":         {"label": "Negocio / Proyecto", "icon": "🚀"},
    "other":            {"label": "Otro",               "icon": "◇"},
}

STATUSES = ["idea", "active", "deferred", "done", "discarded"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS project_cards (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    project_type TEXT NOT NULL DEFAULT 'other',
    status TEXT NOT NULL DEFAULT 'idea',
    priority INTEGER DEFAULT 3,
    scheduled_date TEXT,
    review_date TEXT,

    -- Time dimensions (hours)
    time_research_hours REAL DEFAULT 0,
    time_execution_hours REAL DEFAULT 0,
    time_maintenance_hours_year REAL DEFAULT 0,

    -- Economic dimensions
    cost_upfront REAL DEFAULT 0,
    cost_recurring_monthly REAL DEFAULT 0,
    benefit_monthly REAL DEFAULT 0,
    savings_required REAL DEFAULT 0,
    payback_months INTEGER,

    -- Wellbeing dimensions (1-5 scale)
    psychological_stress INTEGER DEFAULT 3,
    psychological_reward INTEGER DEFAULT 3,
    physical_effort INTEGER DEFAULT 1,
    physical_benefit INTEGER DEFAULT 1,

    -- Relational impact (-2 to +2)
    relational_impact INTEGER DEFAULT 0,

    -- Structured data (JSON)
    pros TEXT DEFAULT '[]',
    cons TEXT DEFAULT '[]',
    risks TEXT DEFAULT '[]',
    extra_data TEXT DEFAULT '{}',

    -- Analysis output
    score_global REAL,
    recommendation TEXT,
    analysis_summary TEXT,
    analysis_updated_at TEXT,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class ProjectManager:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init()

    @contextmanager
    def _conn(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init(self):
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    def _parse(self, row) -> dict:
        d = dict(row)
        for field in ("pros", "cons", "risks"):
            try:
                d[field] = json.loads(d[field] or "[]")
            except Exception:
                d[field] = []
        try:
            d["extra_data"] = json.loads(d.get("extra_data") or "{}")
        except Exception:
            d["extra_data"] = {}
        t = d.get("project_type", "other")
        d["type_meta"] = PROJECT_TYPES.get(t, PROJECT_TYPES["other"])
        return d

    # ── CRUD ──────────────────────────────────────────────────────────────

    def list(self, status: str | None = None, project_type: str | None = None) -> list[dict]:
        with self._conn() as conn:
            q = "SELECT * FROM project_cards WHERE 1=1"
            params: list = []
            if status:
                q += " AND status = ?"
                params.append(status)
            if project_type:
                q += " AND project_type = ?"
                params.append(project_type)
            q += (
                " ORDER BY "
                "CASE status WHEN 'active' THEN 0 WHEN 'idea' THEN 1 "
                "WHEN 'deferred' THEN 2 WHEN 'done' THEN 3 ELSE 4 END, "
                "priority DESC, created_at DESC"
            )
            return [self._parse(r) for r in conn.execute(q, params).fetchall()]

    def get(self, project_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM project_cards WHERE id = ?", (project_id,)
            ).fetchone()
            return self._parse(row) if row else None

    def create(self, data: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        pid = str(uuid.uuid4())

        cost_upfront = float(data.get("cost_upfront") or 0)
        benefit_monthly = float(data.get("benefit_monthly") or 0)
        cost_recurring = float(data.get("cost_recurring_monthly") or 0)
        payback = data.get("payback_months")
        if not payback and cost_upfront > 0 and benefit_monthly > cost_recurring:
            payback = int(cost_upfront / (benefit_monthly - cost_recurring))

        status = data.get("status", "idea")
        review_date = data.get("review_date")
        if not review_date:
            days = 30 if status == "active" else 90
            review_date = (
                datetime.now(timezone.utc) + timedelta(days=days)
            ).date().isoformat()

        fields = {
            "id": pid,
            "title": (data.get("title") or "Sin título").strip(),
            "description": data.get("description", ""),
            "project_type": data.get("project_type", "other"),
            "status": status,
            "priority": int(data.get("priority") or 3),
            "scheduled_date": data.get("scheduled_date"),
            "review_date": review_date,
            "time_research_hours": float(data.get("time_research_hours") or 0),
            "time_execution_hours": float(data.get("time_execution_hours") or 0),
            "time_maintenance_hours_year": float(data.get("time_maintenance_hours_year") or 0),
            "cost_upfront": cost_upfront,
            "cost_recurring_monthly": cost_recurring,
            "benefit_monthly": benefit_monthly,
            "savings_required": float(data.get("savings_required") or 0),
            "payback_months": payback,
            "psychological_stress": int(data.get("psychological_stress") or 3),
            "psychological_reward": int(data.get("psychological_reward") or 3),
            "physical_effort": int(data.get("physical_effort") or 1),
            "physical_benefit": int(data.get("physical_benefit") or 1),
            "relational_impact": int(data.get("relational_impact") or 0),
            "pros": json.dumps(data.get("pros") or [], ensure_ascii=False),
            "cons": json.dumps(data.get("cons") or [], ensure_ascii=False),
            "risks": json.dumps(data.get("risks") or [], ensure_ascii=False),
            "extra_data": json.dumps(data.get("extra_data") or {}, ensure_ascii=False),
            "score_global": None,
            "recommendation": None,
            "analysis_summary": None,
            "analysis_updated_at": None,
            "created_at": now,
            "updated_at": now,
        }

        cols = ", ".join(fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO project_cards ({cols}) VALUES ({placeholders})",
                list(fields.values()),
            )
        return self.get(pid)  # type: ignore[return-value]

    def update(self, project_id: str, data: dict) -> dict | None:
        existing = self.get(project_id)
        if not existing:
            return None

        now = datetime.now(timezone.utc).isoformat()

        # Recompute payback if financial fields changed
        cost_upfront = float(data.get("cost_upfront", existing["cost_upfront"]) or 0)
        benefit = float(data.get("benefit_monthly", existing["benefit_monthly"]) or 0)
        recurring = float(data.get("cost_recurring_monthly", existing["cost_recurring_monthly"]) or 0)
        if cost_upfront > 0 and benefit > recurring and "payback_months" not in data:
            data["payback_months"] = int(cost_upfront / (benefit - recurring))

        scalar_cols = [
            "title", "description", "project_type", "status", "priority",
            "scheduled_date", "review_date",
            "time_research_hours", "time_execution_hours", "time_maintenance_hours_year",
            "cost_upfront", "cost_recurring_monthly", "benefit_monthly",
            "savings_required", "payback_months",
            "psychological_stress", "psychological_reward",
            "physical_effort", "physical_benefit", "relational_impact",
            "score_global", "recommendation", "analysis_summary", "analysis_updated_at",
        ]
        json_cols = {"pros", "cons", "risks", "extra_data"}

        sets, params = [], []
        for col in scalar_cols:
            if col in data:
                sets.append(f"{col} = ?")
                params.append(data[col])
        for col in json_cols:
            if col in data:
                sets.append(f"{col} = ?")
                params.append(json.dumps(data[col], ensure_ascii=False))

        sets.append("updated_at = ?")
        params.append(now)
        params.append(project_id)

        with self._conn() as conn:
            conn.execute(
                f"UPDATE project_cards SET {', '.join(sets)} WHERE id = ?", params
            )
        return self.get(project_id)

    def discard(self, project_id: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            n = conn.execute(
                "UPDATE project_cards SET status = 'discarded', updated_at = ? WHERE id = ?",
                (now, project_id),
            ).rowcount
        return n > 0

    # ── Queries ───────────────────────────────────────────────────────────

    def get_reminders(self) -> list[dict]:
        """Projects with overdue review or approaching scheduled date (≤7 days)."""
        from datetime import date
        today = date.today().isoformat()
        week_ahead = (date.today() + timedelta(days=7)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM project_cards
                WHERE status NOT IN ('done', 'discarded')
                AND (
                    (review_date IS NOT NULL AND review_date <= :today)
                    OR (scheduled_date IS NOT NULL AND scheduled_date <= :week)
                )
                ORDER BY scheduled_date ASC, review_date ASC
                """,
                {"today": today, "week": week_ahead},
            ).fetchall()
        return [self._parse(r) for r in rows]

    def get_portfolio_balance(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM project_cards WHERE status IN ('active', 'idea')"
            ).fetchall()
        projects = [self._parse(r) for r in rows]

        if not projects:
            return {
                "count": 0, "total_cost_upfront": 0,
                "total_hours": 0, "avg_score": None,
                "by_type": {}, "by_status": {},
            }

        total_cost = sum(p.get("cost_upfront") or 0 for p in projects)
        total_hours = sum(
            (p.get("time_research_hours") or 0) + (p.get("time_execution_hours") or 0)
            for p in projects
        )
        scores = [p["score_global"] for p in projects if p.get("score_global") is not None]
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for p in projects:
            by_type[p["project_type"]] = by_type.get(p["project_type"], 0) + 1
            by_status[p["status"]] = by_status.get(p["status"], 0) + 1

        return {
            "count": len(projects),
            "total_cost_upfront": total_cost,
            "total_hours": total_hours,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
            "by_type": by_type,
            "by_status": by_status,
        }


project_manager = ProjectManager()
