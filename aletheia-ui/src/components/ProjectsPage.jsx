/**
 * ProjectsPage — Multi-dimensional life project cards.
 *
 * Props: apiUrl, onNavigate
 *
 * Each project card captures: type, status, time cost, economic cost,
 * ROI, psychological/physical/relational impact, pros/cons/risks, and
 * a global score computed on the backend.
 */
import { useState, useEffect, useCallback } from "react";

// ── Constants ────────────────────────────────────────────────────────────────

const TYPE_META = {
  life_decision:    { label: "Decisión vital",     icon: "⚖️" },
  career:           { label: "Carrera / Trabajo",  icon: "💼" },
  home_improvement: { label: "Reforma / Hogar",    icon: "🏠" },
  purchase:         { label: "Compra importante",  icon: "🛒" },
  financial_goal:   { label: "Meta financiera",    icon: "💶" },
  health_wellness:  { label: "Salud / Bienestar",  icon: "❤️" },
  education:        { label: "Formación",          icon: "📚" },
  business:         { label: "Negocio / Proyecto", icon: "🚀" },
  other:            { label: "Otro",               icon: "◇"  },
};

const STATUS_META = {
  idea:      { label: "Idea",      color: "#818cf8", bg: "rgba(129,140,248,0.12)" },
  active:    { label: "Activo",    color: "#4ade80", bg: "rgba(74,222,128,0.12)" },
  deferred:  { label: "Diferido",  color: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
  done:      { label: "Completado",color: "#34d399", bg: "rgba(52,211,153,0.1)" },
  discarded: { label: "Descartado",color: "#6b7280", bg: "rgba(107,114,128,0.1)" },
};

const REC_META = {
  proceed: { label: "Proceder",   color: "#4ade80" },
  defer:   { label: "Diferir",    color: "#fbbf24" },
  review:  { label: "Revisar",    color: "#818cf8" },
  discard: { label: "Descartar",  color: "#f87171" },
};

const EMPTY_FORM = {
  title: "", description: "", project_type: "other", status: "idea", priority: 3,
  scheduled_date: "", review_date: "",
  time_research_hours: "", time_execution_hours: "", time_maintenance_hours_year: "",
  cost_upfront: "", cost_recurring_monthly: "", benefit_monthly: "", savings_required: "",
  psychological_stress: 3, psychological_reward: 3,
  physical_effort: 1, physical_benefit: 1,
  relational_impact: 0,
  pros: [], cons: [], risks: [],
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const chip = (label, color, bg) => (
  <span style={{
    padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600,
    color, background: bg, border: `1px solid ${color}44`, whiteSpace: "nowrap",
  }}>
    {label}
  </span>
);

function ScoreBar({ score }) {
  if (score == null) return <span style={{ fontSize: 11, color: "#4b5563" }}>sin puntuación</span>;
  const pct = ((score + 10) / 20) * 100;
  const color = score >= 5 ? "#4ade80" : score >= 1 ? "#fbbf24" : score >= -2 ? "#818cf8" : "#f87171";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ flex: 1, height: 6, background: "#1f2937", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.4s" }} />
      </div>
      <span style={{ fontSize: 11, color, fontWeight: 700, minWidth: 32, textAlign: "right" }}>
        {score > 0 ? "+" : ""}{score}
      </span>
    </div>
  );
}

function DimBar({ label, value, max = 5, color = "#818cf8" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
      <span style={{ fontSize: 11, color: "#6b7280", minWidth: 130 }}>{label}</span>
      <div style={{ flex: 1, height: 5, background: "#1f2937", borderRadius: 3 }}>
        <div style={{
          width: `${(value / max) * 100}%`, height: "100%",
          background: color, borderRadius: 3,
        }} />
      </div>
      <span style={{ fontSize: 11, color: "#9ca3af", minWidth: 20, textAlign: "right" }}>{value}</span>
    </div>
  );
}

function TagList({ items, color = "#818cf8", prefix = "" }) {
  if (!items || items.length === 0) return <span style={{ fontSize: 11, color: "#4b5563" }}>—</span>;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
      {items.map((item, i) => (
        <span key={i} style={{
          padding: "2px 7px", borderRadius: 8, fontSize: 11,
          background: `${color}18`, border: `1px solid ${color}44`, color,
        }}>
          {prefix}{typeof item === "object" ? item.description : item}
        </span>
      ))}
    </div>
  );
}

// ── Form ─────────────────────────────────────────────────────────────────────

function ProjectForm({ initial = EMPTY_FORM, onSave, onCancel, saving }) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initial });
  const [tab, setTab] = useState("basic");
  const [prosInput, setProsInput] = useState("");
  const [consInput, setConsInput] = useState("");
  const [riskInput, setRiskInput] = useState("");

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const addPro  = () => { if (prosInput.trim()) { set("pros",  [...(form.pros  || []), prosInput.trim()]); setProsInput(""); } };
  const addCon  = () => { if (consInput.trim()) { set("cons",  [...(form.cons  || []), consInput.trim()]); setConsInput(""); } };
  const addRisk = () => { if (riskInput.trim()) { set("risks", [...(form.risks || []), { description: riskInput.trim() }]); setRiskInput(""); } };

  const inputStyle = {
    width: "100%", boxSizing: "border-box",
    background: "#0d0d1a", border: "1px solid #374151",
    borderRadius: 8, color: "#f9fafb", fontSize: 13, padding: "7px 10px",
  };
  const labelStyle = { fontSize: 11, color: "#6b7280", marginBottom: 4, display: "block" };
  const fieldWrap  = { marginBottom: 14 };

  const TABS = [
    { id: "basic",   label: "Básico" },
    { id: "dims",    label: "Dimensiones" },
    { id: "details", label: "Pros / Contras" },
  ];

  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #374151",
      borderRadius: 14, padding: "20px 22px",
    }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 6, marginBottom: 18 }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: "5px 14px", borderRadius: 8, fontSize: 12, fontWeight: 600,
            background: tab === t.id ? "rgba(99,102,241,0.2)" : "transparent",
            border: `1px solid ${tab === t.id ? "#818cf8" : "#374151"}`,
            color: tab === t.id ? "#818cf8" : "#6b7280", cursor: "pointer",
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Básico ── */}
      {tab === "basic" && (
        <>
          <div style={fieldWrap}>
            <label style={labelStyle}>Título *</label>
            <input style={inputStyle} value={form.title} onChange={e => set("title", e.target.value)} placeholder="¿Qué quieres hacer?" />
          </div>
          <div style={fieldWrap}>
            <label style={labelStyle}>Descripción</label>
            <textarea style={{ ...inputStyle, resize: "vertical" }} rows={3} value={form.description} onChange={e => set("description", e.target.value)} placeholder="Contexto, motivación, objetivos..." />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={labelStyle}>Tipo de proyecto</label>
              <select style={inputStyle} value={form.project_type} onChange={e => set("project_type", e.target.value)}>
                {Object.entries(TYPE_META).map(([id, m]) => (
                  <option key={id} value={id}>{m.icon} {m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Estado</label>
              <select style={inputStyle} value={form.status} onChange={e => set("status", e.target.value)}>
                {Object.entries(STATUS_META).filter(([id]) => id !== "discarded").map(([id, m]) => (
                  <option key={id} value={id}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div>
              <label style={labelStyle}>Fecha objetivo</label>
              <input type="date" style={inputStyle} value={form.scheduled_date} onChange={e => set("scheduled_date", e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Prioridad (1–5)</label>
              <input type="number" min="1" max="5" style={inputStyle} value={form.priority} onChange={e => set("priority", +e.target.value)} />
            </div>
          </div>
        </>
      )}

      {/* ── Tab: Dimensiones ── */}
      {tab === "dims" && (
        <>
          <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 14 }}>
            Cuanto más rellenes, más preciso será el análisis. Deja en 0 lo que no aplique.
          </p>

          {/* Time */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: "#818cf8", fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em" }}>
              ⏱ Tiempo (horas)
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              {[
                ["time_research_hours",          "Investigación"],
                ["time_execution_hours",         "Ejecución"],
                ["time_maintenance_hours_year",  "Mantenimiento/año"],
              ].map(([k, label]) => (
                <div key={k}>
                  <label style={labelStyle}>{label}</label>
                  <input type="number" min="0" style={inputStyle} value={form[k]} onChange={e => set(k, e.target.value)} />
                </div>
              ))}
            </div>
          </div>

          {/* Economic */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: "#4ade80", fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em" }}>
              💶 Económico (€)
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                ["cost_upfront",           "Coste inicial"],
                ["cost_recurring_monthly", "Coste recurrente/mes"],
                ["benefit_monthly",        "Beneficio/ahorro/mes"],
                ["savings_required",       "Ahorro previo necesario"],
              ].map(([k, label]) => (
                <div key={k}>
                  <label style={labelStyle}>{label}</label>
                  <input type="number" min="0" style={inputStyle} value={form[k]} onChange={e => set(k, e.target.value)} placeholder="0" />
                </div>
              ))}
            </div>
            <p style={{ fontSize: 11, color: "#4b5563", marginTop: 6 }}>
              "Ahorro previo necesario" = cuánto dinero ahorrado necesitas antes de dar el paso (útil para cambios laborales, mudanzas, etc.)
            </p>
          </div>

          {/* Wellbeing */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: "#f472b6", fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em" }}>
              ❤️ Bienestar
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                ["psychological_stress",  "Estrés estimado (1-5)",        1, 5],
                ["psychological_reward",  "Satisfacción esperada (1-5)",  1, 5],
                ["physical_effort",       "Esfuerzo físico (1-5)",        1, 5],
                ["physical_benefit",      "Beneficio físico (1-5)",       1, 5],
              ].map(([k, label, min, max]) => (
                <div key={k}>
                  <label style={labelStyle}>{label}</label>
                  <input type="number" min={min} max={max} style={inputStyle} value={form[k]} onChange={e => set(k, +e.target.value)} />
                </div>
              ))}
            </div>
            <div style={{ marginTop: 10 }}>
              <label style={labelStyle}>Impacto relacional (-2 a +2)</label>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                {[-2, -1, 0, 1, 2].map(v => (
                  <button key={v} onClick={() => set("relational_impact", v)} style={{
                    padding: "5px 12px", borderRadius: 8, fontSize: 13, cursor: "pointer",
                    background: form.relational_impact === v ? "rgba(129,140,248,0.2)" : "transparent",
                    border: `1px solid ${form.relational_impact === v ? "#818cf8" : "#374151"}`,
                    color: form.relational_impact === v ? "#818cf8" : "#6b7280",
                  }}>
                    {v > 0 ? `+${v}` : v}
                  </button>
                ))}
                <span style={{ fontSize: 11, color: "#4b5563" }}>
                  {form.relational_impact < 0 ? "Negativo para familia/entorno" : form.relational_impact > 0 ? "Positivo para familia/entorno" : "Sin impacto relacional"}
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Tab: Pros / Contras ── */}
      {tab === "details" && (
        <>
          {/* Pros */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ ...labelStyle, color: "#4ade80" }}>Ventajas (pros)</label>
            <div style={{ display: "flex", gap: 6 }}>
              <input style={{ ...inputStyle, flex: 1 }} value={prosInput} onChange={e => setProsInput(e.target.value)} onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addPro())} placeholder="Añadir ventaja y pulsar Enter…" />
              <button onClick={addPro} style={{ padding: "7px 12px", background: "rgba(74,222,128,0.1)", border: "1px solid #4ade8044", borderRadius: 8, color: "#4ade80", cursor: "pointer", fontSize: 13 }}>+</button>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 6 }}>
              {(form.pros || []).map((p, i) => (
                <span key={i} style={{ padding: "2px 8px", borderRadius: 8, fontSize: 11, background: "rgba(74,222,128,0.08)", border: "1px solid #4ade8044", color: "#4ade80", cursor: "pointer" }}
                  onClick={() => set("pros", form.pros.filter((_, j) => j !== i))}>
                  {p} ✕
                </span>
              ))}
            </div>
          </div>

          {/* Cons */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ ...labelStyle, color: "#f87171" }}>Inconvenientes (contras)</label>
            <div style={{ display: "flex", gap: 6 }}>
              <input style={{ ...inputStyle, flex: 1 }} value={consInput} onChange={e => setConsInput(e.target.value)} onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addCon())} placeholder="Añadir inconveniente y pulsar Enter…" />
              <button onClick={addCon} style={{ padding: "7px 12px", background: "rgba(248,113,113,0.1)", border: "1px solid #f8717144", borderRadius: 8, color: "#f87171", cursor: "pointer", fontSize: 13 }}>+</button>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 6 }}>
              {(form.cons || []).map((c, i) => (
                <span key={i} style={{ padding: "2px 8px", borderRadius: 8, fontSize: 11, background: "rgba(248,113,113,0.08)", border: "1px solid #f8717144", color: "#f87171", cursor: "pointer" }}
                  onClick={() => set("cons", form.cons.filter((_, j) => j !== i))}>
                  {c} ✕
                </span>
              ))}
            </div>
          </div>

          {/* Risks */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ ...labelStyle, color: "#fbbf24" }}>Riesgos</label>
            <div style={{ display: "flex", gap: 6 }}>
              <input style={{ ...inputStyle, flex: 1 }} value={riskInput} onChange={e => setRiskInput(e.target.value)} onKeyDown={e => e.key === "Enter" && (e.preventDefault(), addRisk())} placeholder="Añadir riesgo y pulsar Enter…" />
              <button onClick={addRisk} style={{ padding: "7px 12px", background: "rgba(251,191,36,0.1)", border: "1px solid #fbbf2444", borderRadius: 8, color: "#fbbf24", cursor: "pointer", fontSize: 13 }}>+</button>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 6 }}>
              {(form.risks || []).map((r, i) => (
                <span key={i} style={{ padding: "2px 8px", borderRadius: 8, fontSize: 11, background: "rgba(251,191,36,0.08)", border: "1px solid #fbbf2444", color: "#fbbf24", cursor: "pointer" }}
                  onClick={() => set("risks", form.risks.filter((_, j) => j !== i))}>
                  {typeof r === "object" ? r.description : r} ✕
                </span>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
        <button onClick={onCancel} style={{
          padding: "8px 18px", borderRadius: 8, background: "transparent",
          border: "1px solid #374151", color: "#6b7280", fontSize: 13, cursor: "pointer",
        }}>
          Cancelar
        </button>
        <button onClick={() => onSave(form)} disabled={saving || !form.title.trim()} style={{
          padding: "8px 22px", borderRadius: 8, fontSize: 13, fontWeight: 700,
          background: form.title.trim() ? "linear-gradient(135deg,#4f46e5,#7c3aed)" : "#1f2937",
          color: form.title.trim() ? "#fff" : "#4b5563",
          border: "none", cursor: form.title.trim() ? "pointer" : "not-allowed",
        }}>
          {saving ? "Guardando…" : "Guardar proyecto"}
        </button>
      </div>
    </div>
  );
}

// ── Detail panel ─────────────────────────────────────────────────────────────

function ProjectDetail({ project, apiUrl, onClose, onUpdated, onDelete }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const meta = TYPE_META[project.project_type] || TYPE_META.other;
  const statusM = STATUS_META[project.status] || STATUS_META.idea;
  const recM = project.recommendation ? REC_META[project.recommendation] : null;

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const r = await fetch(`${apiUrl}/api/projects/${project.id}/analyze`, { method: "POST" });
      const updated = await r.json();
      onUpdated(updated);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = async (form) => {
    setSaving(true);
    try {
      const r = await fetch(`${apiUrl}/api/projects/${project.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const updated = await r.json();
      onUpdated(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const totalTime = (project.time_research_hours || 0) + (project.time_execution_hours || 0);

  if (editing) {
    return (
      <div>
        <button onClick={() => setEditing(false)} style={{ marginBottom: 12, fontSize: 12, color: "#6b7280", background: "none", border: "none", cursor: "pointer" }}>
          ← Volver al detalle
        </button>
        <ProjectForm initial={project} onSave={handleSave} onCancel={() => setEditing(false)} saving={saving} />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#f9fafb", marginBottom: 4 }}>
            {meta.icon} {project.title}
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {chip(statusM.label, statusM.color, statusM.bg)}
            {chip(meta.label, "#6b7280", "rgba(107,114,128,0.1)")}
            {recM && chip(`→ ${recM.label}`, recM.color, `${recM.color}18`)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => setEditing(true)} style={{
            padding: "6px 14px", borderRadius: 8, fontSize: 12,
            background: "transparent", border: "1px solid #374151", color: "#9ca3af", cursor: "pointer",
          }}>
            Editar
          </button>
          <button onClick={onClose} style={{
            padding: "6px 12px", borderRadius: 8, fontSize: 14,
            background: "transparent", border: "1px solid #374151", color: "#6b7280", cursor: "pointer",
          }}>
            ✕
          </button>
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <p style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.6, marginBottom: 16 }}>{project.description}</p>
      )}

      {/* Score */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.07em" }}>Puntuación global</div>
        <ScoreBar score={project.score_global} />
      </div>

      {/* Dimensions grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 16 }}>

        {/* Time */}
        <div style={{ background: "#0d0d1a", borderRadius: 10, padding: "12px 14px", border: "1px solid #1f2937" }}>
          <div style={{ fontSize: 11, color: "#818cf8", fontWeight: 700, marginBottom: 8, textTransform: "uppercase" }}>⏱ Tiempo</div>
          <div style={{ fontSize: 13, color: "#f9fafb" }}>{totalTime || "—"} h comprometidas</div>
          {project.time_maintenance_hours_year > 0 && (
            <div style={{ fontSize: 11, color: "#6b7280" }}>+ {project.time_maintenance_hours_year} h/año mantenimiento</div>
          )}
        </div>

        {/* Economic */}
        <div style={{ background: "#0d0d1a", borderRadius: 10, padding: "12px 14px", border: "1px solid #1f2937" }}>
          <div style={{ fontSize: 11, color: "#4ade80", fontWeight: 700, marginBottom: 8, textTransform: "uppercase" }}>💶 Económico</div>
          {project.cost_upfront > 0 && (
            <div style={{ fontSize: 13, color: "#f9fafb" }}>Coste: {project.cost_upfront.toLocaleString("es-ES")} €</div>
          )}
          {project.cost_recurring_monthly > 0 && (
            <div style={{ fontSize: 11, color: "#6b7280" }}>Recurrente: {project.cost_recurring_monthly} €/mes</div>
          )}
          {project.benefit_monthly > 0 && (
            <div style={{ fontSize: 11, color: "#4ade80" }}>Beneficio: {project.benefit_monthly} €/mes</div>
          )}
          {project.payback_months > 0 && (
            <div style={{ fontSize: 11, color: "#fbbf24" }}>Retorno en ~{project.payback_months} meses</div>
          )}
          {project.savings_required > 0 && (
            <div style={{ fontSize: 11, color: "#f87171" }}>Ahorro necesario: {project.savings_required.toLocaleString("es-ES")} €</div>
          )}
        </div>

        {/* Psychological */}
        <div style={{ background: "#0d0d1a", borderRadius: 10, padding: "12px 14px", border: "1px solid #1f2937" }}>
          <div style={{ fontSize: 11, color: "#f472b6", fontWeight: 700, marginBottom: 8, textTransform: "uppercase" }}>❤️ Psicológico</div>
          <DimBar label="Estrés estimado" value={project.psychological_stress || 3} color="#f87171" />
          <DimBar label="Satisfacción esperada" value={project.psychological_reward || 3} color="#4ade80" />
        </div>

        {/* Physical + relational */}
        <div style={{ background: "#0d0d1a", borderRadius: 10, padding: "12px 14px", border: "1px solid #1f2937" }}>
          <div style={{ fontSize: 11, color: "#fb923c", fontWeight: 700, marginBottom: 8, textTransform: "uppercase" }}>⚡ Físico / Relacional</div>
          <DimBar label="Esfuerzo físico" value={project.physical_effort || 1} color="#f87171" />
          <DimBar label="Beneficio físico" value={project.physical_benefit || 1} color="#4ade80" />
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
            Impacto relacional: <span style={{ color: project.relational_impact > 0 ? "#4ade80" : project.relational_impact < 0 ? "#f87171" : "#6b7280", fontWeight: 700 }}>
              {project.relational_impact > 0 ? "+" : ""}{project.relational_impact}
            </span>
          </div>
        </div>
      </div>

      {/* Pros / Cons / Risks */}
      {((project.pros?.length > 0) || (project.cons?.length > 0) || (project.risks?.length > 0)) && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 16 }}>
          {project.pros?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#4ade80", fontWeight: 700, marginBottom: 6 }}>Ventajas</div>
              <TagList items={project.pros} color="#4ade80" />
            </div>
          )}
          {project.cons?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#f87171", fontWeight: 700, marginBottom: 6 }}>Contras</div>
              <TagList items={project.cons} color="#f87171" />
            </div>
          )}
          {project.risks?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#fbbf24", fontWeight: 700, marginBottom: 6 }}>Riesgos</div>
              <TagList items={project.risks} color="#fbbf24" />
            </div>
          )}
        </div>
      )}

      {/* LLM Analysis */}
      <div style={{ background: "#0d0d1a", borderRadius: 10, padding: "14px 16px", border: "1px solid #1f2937", marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 11, color: "#818cf8", fontWeight: 700, textTransform: "uppercase" }}>Análisis Aletheia</div>
          <button onClick={handleAnalyze} disabled={analyzing} style={{
            padding: "4px 12px", borderRadius: 8, fontSize: 11, fontWeight: 600,
            background: "rgba(99,102,241,0.15)", border: "1px solid #818cf844",
            color: "#818cf8", cursor: analyzing ? "not-allowed" : "pointer",
          }}>
            {analyzing ? "Analizando…" : "Analizar con IA"}
          </button>
        </div>
        {project.analysis_summary ? (
          <p style={{ fontSize: 13, color: "#d1d5db", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
            {project.analysis_summary}
          </p>
        ) : (
          <p style={{ fontSize: 12, color: "#4b5563", fontStyle: "italic" }}>
            Pulsa "Analizar con IA" para obtener un diagnóstico narrativo completo de este proyecto.
          </p>
        )}
        {project.analysis_updated_at && (
          <div style={{ fontSize: 10, color: "#374151", marginTop: 6 }}>
            Actualizado: {new Date(project.analysis_updated_at).toLocaleString("es-ES")}
          </div>
        )}
      </div>

      {/* Dates */}
      {(project.scheduled_date || project.review_date) && (
        <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#4b5563", marginBottom: 12 }}>
          {project.scheduled_date && <span>Fecha objetivo: <strong style={{ color: "#9ca3af" }}>{project.scheduled_date}</strong></span>}
          {project.review_date && <span>Revisión: <strong style={{ color: "#9ca3af" }}>{project.review_date}</strong></span>}
        </div>
      )}

      {/* Danger zone */}
      <div style={{ borderTop: "1px solid #1f2937", paddingTop: 12, display: "flex", justifyContent: "flex-end" }}>
        <button onClick={() => onDelete(project.id)} style={{
          padding: "5px 14px", borderRadius: 8, fontSize: 12,
          background: "transparent", border: "1px solid #374151",
          color: "#6b7280", cursor: "pointer",
        }}>
          Descartar proyecto
        </button>
      </div>
    </div>
  );
}

// ── Card ─────────────────────────────────────────────────────────────────────

function ProjectCard({ project, onClick }) {
  const meta = TYPE_META[project.project_type] || TYPE_META.other;
  const statusM = STATUS_META[project.status] || STATUS_META.idea;
  const recM = project.recommendation ? REC_META[project.recommendation] : null;
  const totalTime = (project.time_research_hours || 0) + (project.time_execution_hours || 0);

  return (
    <div onClick={onClick} style={{
      background: "#0a0a14", border: "1px solid #1f2937",
      borderRadius: 12, padding: "14px 16px", cursor: "pointer",
      transition: "border-color 0.15s, transform 0.1s",
    }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = "#374151"; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = "#1f2937"; e.currentTarget.style.transform = ""; }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb" }}>
          {meta.icon} {project.title}
        </div>
        <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
          {chip(statusM.label, statusM.color, statusM.bg)}
        </div>
      </div>

      {project.description && (
        <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 8, lineHeight: 1.5, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
          {project.description}
        </p>
      )}

      <ScoreBar score={project.score_global} />

      <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: 11, color: "#4b5563" }}>
        {totalTime > 0 && <span>⏱ {totalTime}h</span>}
        {project.cost_upfront > 0 && <span>💶 {project.cost_upfront.toLocaleString("es-ES")}€</span>}
        {project.benefit_monthly > 0 && <span style={{ color: "#4ade80" }}>+{project.benefit_monthly}€/mes</span>}
        {project.savings_required > 0 && <span style={{ color: "#f87171" }}>ahorro: {project.savings_required.toLocaleString("es-ES")}€</span>}
        {recM && <span style={{ color: recM.color, marginLeft: "auto" }}>→ {recM.label}</span>}
      </div>
    </div>
  );
}

// ── Balance widget ────────────────────────────────────────────────────────────

function PortfolioBalance({ balance }) {
  if (!balance || balance.count === 0) return null;
  return (
    <div style={{ background: "#0a0a14", border: "1px solid #1f2937", borderRadius: 12, padding: "14px 18px", marginBottom: 20 }}>
      <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 10 }}>
        Balance del portafolio
      </div>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800, color: "#818cf8" }}>{balance.count}</div>
          <div style={{ fontSize: 11, color: "#6b7280" }}>proyectos activos/idea</div>
        </div>
        {balance.total_cost_upfront > 0 && (
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "#f87171" }}>{balance.total_cost_upfront.toLocaleString("es-ES")} €</div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>coste total comprometido</div>
          </div>
        )}
        {balance.total_hours > 0 && (
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "#fbbf24" }}>{Math.round(balance.total_hours)} h</div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>horas comprometidas</div>
          </div>
        )}
        {balance.avg_score != null && (
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: balance.avg_score >= 3 ? "#4ade80" : balance.avg_score >= 0 ? "#fbbf24" : "#f87171" }}>
              {balance.avg_score > 0 ? "+" : ""}{balance.avg_score}
            </div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>puntuación media</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ProjectsPage({ apiUrl }) {
  const [projects, setProjects]     = useState([]);
  const [balance, setBalance]       = useState(null);
  const [reminders, setReminders]   = useState([]);
  const [loading, setLoading]       = useState(true);
  const [filter, setFilter]         = useState("all");
  const [selected, setSelected]     = useState(null);
  const [creating, setCreating]     = useState(false);
  const [saving, setSaving]         = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pRes, bRes, rRes] = await Promise.all([
        fetch(`${apiUrl}/api/projects`),
        fetch(`${apiUrl}/api/projects/balance`),
        fetch(`${apiUrl}/api/projects/reminders`),
      ]);
      const [p, b, r] = await Promise.all([pRes.json(), bRes.json(), rRes.json()]);
      setProjects(Array.isArray(p) ? p : []);
      setBalance(b);
      setReminders(Array.isArray(r) ? r : []);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (form) => {
    setSaving(true);
    try {
      await fetch(`${apiUrl}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setCreating(false);
      load();
    } finally {
      setSaving(false);
    }
  };

  const handleUpdated = (updated) => {
    setProjects(ps => ps.map(p => p.id === updated.id ? updated : p));
    setSelected(updated);
  };

  const handleDelete = async (id) => {
    await fetch(`${apiUrl}/api/projects/${id}`, { method: "DELETE" });
    setSelected(null);
    load();
  };

  const FILTERS = [
    { id: "all",      label: "Todos" },
    { id: "active",   label: "Activos" },
    { id: "idea",     label: "Ideas" },
    { id: "deferred", label: "Diferidos" },
    { id: "done",     label: "Completados" },
  ];

  const visible = filter === "all"
    ? projects.filter(p => p.status !== "discarded")
    : projects.filter(p => p.status === filter);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>◇ Proyectos y decisiones</h1>
          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
            Fichas de proyecto con análisis multi-dimensional: tiempo, economía, bienestar y relaciones.
          </p>
        </div>
        <button onClick={() => { setCreating(true); setSelected(null); }} style={{
          padding: "9px 18px", borderRadius: 10, fontSize: 13, fontWeight: 700,
          background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
          color: "#fff", border: "none", cursor: "pointer",
        }}>
          + Nuevo proyecto
        </button>
      </div>

      {/* Reminders */}
      {reminders.length > 0 && (
        <div style={{
          background: "rgba(251,191,36,0.06)", border: "1px solid #fbbf2444",
          borderRadius: 10, padding: "10px 14px", marginBottom: 16,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <span style={{ color: "#fbbf24", fontSize: 15 }}>⏰</span>
          <span style={{ fontSize: 12, color: "#fbbf24" }}>
            {reminders.length} proyecto{reminders.length > 1 ? "s" : ""} pendiente{reminders.length > 1 ? "s" : ""} de revisión:
            {" "}{reminders.map(r => r.title).join(", ")}
          </span>
        </div>
      )}

      {/* Balance */}
      <PortfolioBalance balance={balance} />

      {/* Create form */}
      {creating && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#818cf8", marginBottom: 10 }}>Nuevo proyecto</div>
          <ProjectForm onSave={handleCreate} onCancel={() => setCreating(false)} saving={saving} />
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <div style={{ marginBottom: 20 }}>
          <ProjectDetail
            project={selected}
            apiUrl={apiUrl}
            onClose={() => setSelected(null)}
            onUpdated={handleUpdated}
            onDelete={handleDelete}
          />
        </div>
      )}

      {/* Filter pills */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
        {FILTERS.map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)} style={{
            padding: "5px 14px", borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: "pointer",
            background: filter === f.id ? "rgba(129,140,248,0.15)" : "transparent",
            border: `1px solid ${filter === f.id ? "#818cf8" : "#1f2937"}`,
            color: filter === f.id ? "#818cf8" : "#6b7280",
          }}>
            {f.label}
            {f.id !== "all" && (
              <span style={{ marginLeft: 5, opacity: 0.6 }}>
                {projects.filter(p => p.status === f.id).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#4b5563" }}>Cargando proyectos…</div>
      ) : visible.length === 0 ? (
        <div style={{ textAlign: "center", padding: "40px 0" }}>
          <div style={{ fontSize: 32, marginBottom: 10 }}>◇</div>
          <div style={{ color: "#4b5563", fontSize: 14 }}>
            {filter === "all" ? "No tienes proyectos todavía. Crea el primero." : `No hay proyectos en estado "${FILTERS.find(f => f.id === filter)?.label}".`}
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
          {visible.map(p => (
            <ProjectCard
              key={p.id}
              project={p}
              onClick={() => { setSelected(p); setCreating(false); }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
