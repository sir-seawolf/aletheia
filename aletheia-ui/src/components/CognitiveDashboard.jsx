/**
 * CognitiveDashboard — observability view for Aletheia 3.0.
 *
 * Sections:
 *   1. Cognitive State  — live energy/fatigue/coherence meters
 *   2. Mode Intelligence — ranked insights from TraceLearner
 *   3. Recent Traces    — trace history with inline replay
 *   4. System Health    — divergence win rates, degraded strategies, replay outcomes
 *
 * Props:
 *   apiUrl: string
 *   domain: string
 *   sessionId: string
 */
import { useState, useEffect, useCallback } from "react";

const C = {
  accent:   "#818cf8",
  green:    "#4ade80",
  yellow:   "#fbbf24",
  red:      "#f87171",
  muted:    "#6b7280",
  dim:      "#374151",
  bg:       "#080811",
  surface:  "#0d0d1a",
  border:   "#1f2937",
  text:     "#f9fafb",
};

/* ── Primitives ──────────────────────────────────────────────────────────── */

function Card({ title, children, action, style: extraStyle }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "14px 16px", ...extraStyle }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: C.text, textTransform: "uppercase", letterSpacing: "0.07em" }}>{title}</span>
        {action}
      </div>
      {children}
    </div>
  );
}

function Bar({ value = 0, color = C.accent, label, sublabel }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: C.muted }}>{label}</span>
        <span style={{ fontSize: 11, color, fontVariantNumeric: "tabular-nums" }}>
          {sublabel !== undefined ? sublabel : `${pct}%`}
        </span>
      </div>
      <div style={{ height: 4, background: C.dim, borderRadius: 3, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3, transition: "width 0.4s ease" }} />
      </div>
    </div>
  );
}

function Badge({ text, color = C.accent }) {
  return (
    <span style={{
      display: "inline-block", padding: "1px 7px", borderRadius: 10,
      fontSize: 10, fontWeight: 600, letterSpacing: "0.05em",
      background: `${color}22`, border: `1px solid ${color}55`, color,
    }}>{text}</span>
  );
}

function Spinner() {
  return <span style={{ color: C.muted, fontSize: 12 }}>…</span>;
}

/* ── Section 1: Cognitive State ─────────────────────────────────────────── */

function CognitiveStateSection({ apiUrl, domain, sessionId }) {
  const [state, setState]     = useState(null);
  const [reco, setReco]       = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    Promise.all([
      fetch(`${apiUrl}/api/learning/recommend?domain=${encodeURIComponent(domain)}&session_id=${encodeURIComponent(sessionId)}`)
        .then(r => r.json()).catch(() => null),
    ]).then(([r]) => {
      if (r) {
        setState(r.cognitive_state);
        setReco(r);
      }
      setLoading(false);
    });
  }, [apiUrl, domain, sessionId]);

  useEffect(() => { refresh(); const t = setInterval(refresh, 8000); return () => clearInterval(t); }, [refresh]);

  if (loading) return <Card title="Estado cognitivo"><Spinner /></Card>;
  if (!state) return <Card title="Estado cognitivo"><span style={{ fontSize: 12, color: C.muted }}>Sin datos de sesión aún.</span></Card>;

  const fatigueColor = state.fatigue > 0.7 ? C.red : state.fatigue > 0.4 ? C.yellow : C.green;
  const energyColor  = state.energy  < 0.3 ? C.red : state.energy  < 0.6 ? C.yellow : C.green;

  return (
    <Card title="Estado cognitivo" action={
      <span style={{ fontSize: 10, color: C.muted }}>{state.preferred_depth} · {state.model_tier}</span>
    }>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 24px" }}>
        <Bar label="Energía"    value={state.energy}    color={energyColor} />
        <Bar label="Fatiga"     value={state.fatigue}   color={fatigueColor} />
        <Bar label="Coherencia" value={state.coherence} color={C.accent} />
        <Bar label="Foco"       value={state.focus}     color={C.accent} />
      </div>
      <Bar
        label="Presión de memoria"
        value={state.memory_pressure}
        color={state.memory_pressure > 0.6 ? C.red : C.yellow}
      />
      <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
        {reco?.recommended_mode  && <Badge text={`modo: ${reco.recommended_mode}`}  color={C.accent} />}
        {reco?.recommended_blend && <Badge text={`blend: ${reco.recommended_blend}`} color="#c084fc" />}
        {reco?.recommended_provider && <Badge text={reco.recommended_provider}       color={C.green} />}
        <Badge text={`tokens: ${state.token_budget}`} color={C.muted} />
        <Badge text={`llm calls: ${state.llm_calls}`} color={C.muted} />
      </div>
    </Card>
  );
}

/* ── Section 2: Mode Intelligence ───────────────────────────────────────── */

const MODE_COLORS = {
  KRONOS: "#fbbf24", ANALYTICAL: "#818cf8", STRATEGIC: "#34d399",
  CREATIVE: "#f472b6", REFLECTIVE: "#a78bfa", GUARDIAN: "#f87171",
  EXECUTIVE: "#60a5fa", RESEARCHER: "#38bdf8", WORLD_MODEL: "#fb923c",
  OBSERVER: "#6b7280", MEMORY_CURATOR: "#a3e635",
};

function ModeIntelligenceSection({ apiUrl, domain }) {
  const [insights, setInsights] = useState(null);
  const [tab, setTab]           = useState("modes");

  useEffect(() => {
    fetch(`${apiUrl}/api/learning/insights${domain ? `?domain=${encodeURIComponent(domain)}` : ""}`)
      .then(r => r.json()).then(setInsights).catch(() => {});
  }, [apiUrl, domain]);

  const modes     = insights?.modes     || [];
  const providers = insights?.providers || [];
  const qualified = modes.filter(m => m.qualifies);
  const degraded  = modes.filter(m => m.degraded);

  return (
    <Card title="Inteligencia de modos" action={
      <div style={{ display: "flex", gap: 4 }}>
        {["modes", "providers"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: "2px 8px", borderRadius: 6, fontSize: 10, cursor: "pointer",
            background: tab === t ? `${C.accent}22` : "transparent",
            border: `1px solid ${tab === t ? C.accent : C.dim}`,
            color: tab === t ? C.accent : C.muted,
          }}>{t === "modes" ? "Modos" : "Providers"}</button>
        ))}
      </div>
    }>
      {!insights && <Spinner />}

      {tab === "modes" && insights && (
        <>
          <div style={{ fontSize: 10, color: C.muted, marginBottom: 8 }}>
            {qualified.length} calificados · {degraded.length} degradados · mín. 5 muestras
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[...modes]
              .sort((a, b) => b.rank_score - a.rank_score)
              .slice(0, 8)
              .map(m => (
                <div key={`${m.domain}-${m.mode_or_blend}`} style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "5px 8px", borderRadius: 6,
                  background: m.degraded ? "rgba(239,68,68,0.05)" : "rgba(255,255,255,0.02)",
                  border: `1px solid ${m.degraded ? "rgba(239,68,68,0.2)" : C.border}`,
                  opacity: m.degraded ? 0.6 : 1,
                }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                    background: MODE_COLORS[m.mode_or_blend] || C.muted,
                  }} />
                  <span style={{ fontSize: 11, color: C.text, flex: 1, fontWeight: 500 }}>{m.mode_or_blend}</span>
                  <span style={{ fontSize: 10, color: C.muted }}>{m.domain}</span>
                  <div style={{ width: 60 }}>
                    <div style={{ height: 3, background: C.dim, borderRadius: 2, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${m.rank_score * 100}%`, background: m.degraded ? C.red : C.accent, borderRadius: 2 }} />
                    </div>
                  </div>
                  <span style={{ fontSize: 10, color: C.accent, minWidth: 30, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                    {(m.rank_score * 100).toFixed(0)}
                  </span>
                  {m.degraded && <Badge text="degraded" color={C.red} />}
                  {!m.qualifies && !m.degraded && <Badge text="insuf." color={C.muted} />}
                </div>
              ))}
          </div>
        </>
      )}

      {tab === "providers" && insights && (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {[...providers]
            .sort((a, b) => b.efficiency_score - a.efficiency_score)
            .map(p => (
              <div key={`${p.provider}-${p.model_tier}`} style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "5px 8px", borderRadius: 6,
                background: "rgba(255,255,255,0.02)", border: `1px solid ${C.border}`,
              }}>
                <span style={{ fontSize: 11, color: C.text, flex: 1 }}>{p.provider}</span>
                <Badge text={p.model_tier} color={p.model_tier === "premium" ? C.yellow : p.model_tier === "free" ? C.accent : C.green} />
                <span style={{ fontSize: 10, color: C.muted }}>{p.avg_latency_ms.toFixed(0)}ms</span>
                <span style={{ fontSize: 10, color: C.muted }}>{p.avg_tokens.toFixed(0)}tok</span>
                <span style={{ fontSize: 10, color: C.green, minWidth: 40, textAlign: "right" }}>
                  {(p.efficiency_score).toFixed(2)} eff
                </span>
              </div>
            ))}
          {providers.length === 0 && <span style={{ fontSize: 12, color: C.muted }}>Sin datos de provider aún.</span>}
        </div>
      )}
    </Card>
  );
}

/* ── Section 3: Recent Traces ───────────────────────────────────────────── */

function RecentTracesSection({ apiUrl, domain }) {
  const [traces, setTraces]     = useState([]);
  const [source, setSource]     = useState("v1_pipeline");
  const [replaying, setReplaying] = useState(null);
  const [replayResult, setReplayResult] = useState(null);

  const refresh = useCallback(() => {
    const params = new URLSearchParams({ limit: 12 });
    if (source) params.set("source", source);
    if (domain && domain !== "general") params.set("domain", domain);
    fetch(`${apiUrl}/api/traces?${params}`).then(r => r.json())
      .then(d => setTraces(d.traces || [])).catch(() => {});
  }, [apiUrl, source, domain]);

  useEffect(() => { refresh(); const t = setInterval(refresh, 15000); return () => clearInterval(t); }, [refresh]);

  const doReplay = async (traceId, targetMode) => {
    setReplaying(traceId);
    setReplayResult(null);
    try {
      const r = await fetch(`${apiUrl}/api/traces/${traceId}/replay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_mode: targetMode, label: `replay:${targetMode || "auto"}` }),
      });
      const d = await r.json();
      setReplayResult(d);
    } catch { /* */ } finally {
      setReplaying(null);
    }
  };

  const modeColor = m => MODE_COLORS[m] || C.muted;
  const impColor  = i => ({ better: C.green, worse: C.red, tie: C.yellow })[i] || C.muted;

  return (
    <Card title="Trazas recientes" action={
      <div style={{ display: "flex", gap: 4 }}>
        {["v1_pipeline", "shadow_3.0", "replay"].map(s => (
          <button key={s} onClick={() => setSource(s)} style={{
            padding: "2px 6px", borderRadius: 5, fontSize: 9, cursor: "pointer",
            background: source === s ? `${C.accent}22` : "transparent",
            border: `1px solid ${source === s ? C.accent : C.dim}`,
            color: source === s ? C.accent : C.muted,
          }}>{s}</button>
        ))}
        <button onClick={refresh} style={{ padding: "2px 6px", borderRadius: 5, fontSize: 9, cursor: "pointer", background: "transparent", border: `1px solid ${C.dim}`, color: C.muted }}>↻</button>
      </div>
    }>
      {replayResult && (
        <div style={{ marginBottom: 10, padding: "8px 10px", background: `${impColor(replayResult.improvement)}15`, border: `1px solid ${impColor(replayResult.improvement)}44`, borderRadius: 8, fontSize: 11 }}>
          <span style={{ color: impColor(replayResult.improvement), fontWeight: 700 }}>
            {replayResult.improvement === "better" ? "↑ Mejorado" : replayResult.improvement === "worse" ? "↓ Empeoró" : "= Empate"}
          </span>
          <span style={{ color: C.muted, marginLeft: 8 }}>{replayResult.summary}</span>
          <button onClick={() => setReplayResult(null)} style={{ float: "right", background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 10 }}>✕</button>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {traces.length === 0 && <span style={{ fontSize: 12, color: C.muted }}>Sin trazas registradas aún.</span>}
        {traces.map(t => (
          <div key={t.trace_id} style={{
            display: "grid",
            gridTemplateColumns: "8px 1fr 60px 50px 50px 40px 60px",
            alignItems: "center", gap: 6,
            padding: "5px 6px", borderRadius: 6,
            background: "rgba(255,255,255,0.015)", border: `1px solid ${C.border}`,
            fontSize: 10,
          }}>
            {/* Mode dot */}
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: modeColor(t.mode_activated) }} />
            {/* Question */}
            <span style={{ color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
              title={t.question_preview}>{t.question_preview || "—"}</span>
            {/* Mode badge */}
            <span style={{ color: modeColor(t.mode_activated), fontWeight: 600 }}>{t.mode_activated || "—"}</span>
            {/* Provider */}
            <span style={{ color: C.muted }}>{t.provider_used || "—"}</span>
            {/* Latency */}
            <span style={{ color: C.text, fontVariantNumeric: "tabular-nums" }}>{t.latency_ms ? `${t.latency_ms.toFixed(0)}ms` : "—"}</span>
            {/* Fatigue */}
            <span style={{ color: t.fatigue_delta > 0.07 ? C.red : C.muted }}>
              {t.fatigue_delta != null ? `+${(t.fatigue_delta * 100).toFixed(1)}%` : "—"}
            </span>
            {/* Replay button */}
            <button
              onClick={() => doReplay(t.trace_id, "ANALYTICAL")}
              disabled={replaying === t.trace_id}
              style={{
                padding: "2px 6px", borderRadius: 5, fontSize: 9, cursor: "pointer",
                background: "transparent", border: `1px solid ${C.dim}`,
                color: replaying === t.trace_id ? C.muted : C.accent,
              }}
              title="Replay con ANALYTICAL"
            >
              {replaying === t.trace_id ? "…" : "replay"}
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ── Section 4: System Health ───────────────────────────────────────────── */

function SystemHealthSection({ apiUrl }) {
  const [divStats,  setDivStats]  = useState(null);
  const [repStats,  setRepStats]  = useState(null);
  const [degraded,  setDegraded]  = useState([]);
  const [analyzing, setAnalyzing] = useState(false);

  const refresh = useCallback(() => {
    fetch(`${apiUrl}/api/traces/divergences/stats`).then(r => r.json()).then(setDivStats).catch(() => {});
    fetch(`${apiUrl}/api/replay/stats`).then(r => r.json()).then(setRepStats).catch(() => {});
    fetch(`${apiUrl}/api/learning/degradation`).then(r => r.json())
      .then(d => setDegraded(d.degraded || [])).catch(() => {});
  }, [apiUrl]);

  useEffect(() => { refresh(); }, [refresh]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      await fetch(`${apiUrl}/api/traces/analyze`, { method: "POST" });
      await fetch(`${apiUrl}/api/learning/recompute`, { method: "POST" });
      refresh();
    } finally { setAnalyzing(false); }
  };

  const shadowWinRate = divStats?.shadow_win_rate ?? null;
  const repTotal      = repStats?.total ?? 0;
  const repBetter     = repStats?.by_improvement?.better?.count ?? 0;
  const repRate       = repTotal > 0 ? repBetter / repTotal : null;

  return (
    <Card title="Salud del sistema" action={
      <button onClick={runAnalysis} disabled={analyzing} style={{
        padding: "3px 10px", borderRadius: 6, fontSize: 10, cursor: analyzing ? "not-allowed" : "pointer",
        background: `${C.accent}15`, border: `1px solid ${C.accent}44`, color: C.accent,
      }}>{analyzing ? "Analizando…" : "↺ Analizar"}</button>
    }>

      {/* KPI row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 14 }}>
        {[
          {
            label: "Shadow win rate",
            value: shadowWinRate != null ? `${(shadowWinRate * 100).toFixed(1)}%` : "–",
            sub:   divStats ? `${divStats.total ?? 0} comparadas` : "sin datos",
            color: shadowWinRate > 0.5 ? C.green : shadowWinRate != null ? C.yellow : C.muted,
          },
          {
            label: "Replay mejoras",
            value: repRate != null ? `${(repRate * 100).toFixed(1)}%` : "–",
            sub:   `${repTotal} replays`,
            color: repRate > 0.5 ? C.green : repRate != null ? C.yellow : C.muted,
          },
          {
            label: "Modos degradados",
            value: String(degraded.length),
            sub:   "activos",
            color: degraded.length > 2 ? C.red : degraded.length > 0 ? C.yellow : C.green,
          },
        ].map(({ label, value, sub, color }) => (
          <div key={label} style={{ background: C.bg, borderRadius: 8, padding: "8px 10px", border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 18, fontWeight: 800, color, fontVariantNumeric: "tabular-nums" }}>{value}</div>
            <div style={{ fontSize: 10, color: C.text, marginTop: 1 }}>{label}</div>
            <div style={{ fontSize: 9, color: C.muted, marginTop: 1 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Dim averages */}
      {divStats?.dim_averages && (
        <div>
          <div style={{ fontSize: 10, color: C.muted, marginBottom: 6 }}>Dimensiones (shadow vs v1)</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
            {Object.entries(divStats.dim_averages)
              .filter(([k]) => k !== "overall_score")
              .map(([k, v]) => (
                <div key={k} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 10, color: C.muted, flex: 1 }}>{k.replace(/_/g, " ")}</span>
                  <span style={{ fontSize: 10, color: v > 0 ? C.green : v < 0 ? C.red : C.muted, fontVariantNumeric: "tabular-nums" }}>
                    {v > 0 ? "+" : ""}{(v * 100).toFixed(1)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Degraded list */}
      {degraded.length > 0 && (
        <div style={{ marginTop: 12, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
          <div style={{ fontSize: 10, color: C.red, marginBottom: 6 }}>Estrategias degradadas</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {degraded.map(d => (
              <Badge
                key={`${d.domain}-${d.mode_or_blend}`}
                text={`${d.mode_or_blend} (${d.domain})`}
                color={C.red}
              />
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

/* ── Cognitive Patterns Sub-section ─────────────────────────────────────── */

function PatternsSubSection({ apiUrl }) {
  const [patterns, setPatterns]   = useState([]);
  const [detecting, setDetecting] = useState(false);
  const [loaded, setLoaded]       = useState(false);

  const load = useCallback(() => {
    fetch(`${apiUrl}/api/consolidation/patterns?limit=15`)
      .then(r => r.json())
      .then(d => { setPatterns(Array.isArray(d) ? d : []); setLoaded(true); })
      .catch(() => { setLoaded(true); });
  }, [apiUrl]);

  useEffect(() => { load(); }, [load]);

  const markAllRead = async () => {
    await fetch(`${apiUrl}/api/consolidation/patterns/mark_all_read`, { method: "POST" });
    load();
  };

  const markRead = async (id) => {
    await fetch(`${apiUrl}/api/consolidation/patterns/${id}/mark_read`, { method: "POST" });
    setPatterns(ps => ps.map(p => p.id === id ? { ...p, shown: true } : p));
  };

  const detectNow = async () => {
    setDetecting(true);
    try {
      await fetch(`${apiUrl}/api/consolidation/patterns/detect?since_hours=48`, { method: "POST" });
      load();
    } finally {
      setDetecting(false);
    }
  };

  const unread = patterns.filter(p => !p.shown).length;

  const RELEVANCE_COLOR = (r) =>
    r >= 0.7 ? C.green : r >= 0.4 ? C.yellow : C.muted;

  const TYPE_LABEL = {
    recurring_topic:      "Tema recurrente",
    dominant_mode:        "Modo dominante",
    new_concept:          "Concepto nuevo",
    cross_domain_link:    "Conexión cruzada",
    high_fatigue_session: "Alta carga",
    low_confidence_zone:  "Zona de duda",
  };

  return (
    <div style={{ marginTop: 20, borderTop: `1px solid ${C.border}`, paddingTop: 16 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>
            Insights del último sueño
          </span>
          {unread > 0 && (
            <span style={{
              minWidth: 18, height: 18, borderRadius: 9, padding: "0 5px",
              background: C.accent, color: "#fff",
              fontSize: 10, fontWeight: 700, lineHeight: "18px", textAlign: "center",
            }}>
              {unread}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button
            onClick={detectNow}
            disabled={detecting}
            style={{
              padding: "4px 11px", borderRadius: 7, fontSize: 11, cursor: "pointer",
              background: "transparent", border: `1px solid ${C.dim}`, color: C.muted,
              opacity: detecting ? 0.6 : 1,
            }}
          >
            {detecting ? "Detectando…" : "Detectar ahora"}
          </button>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              style={{
                padding: "4px 11px", borderRadius: 7, fontSize: 11, cursor: "pointer",
                background: "transparent", border: `1px solid ${C.dim}`, color: C.muted,
              }}
            >
              Marcar todo leído
            </button>
          )}
        </div>
      </div>

      {/* Pattern list */}
      {!loaded ? (
        <div style={{ fontSize: 12, color: C.muted, fontStyle: "italic" }}>Cargando patrones…</div>
      ) : patterns.length === 0 ? (
        <div style={{ fontSize: 12, color: C.dim, fontStyle: "italic" }}>
          Sin patrones detectados. Ejecuta una consolidación para analizar las conversaciones recientes.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {patterns.map(p => (
            <div
              key={p.id}
              onClick={() => !p.shown && markRead(p.id)}
              style={{
                display: "flex", alignItems: "flex-start", gap: 10,
                padding: "10px 12px", borderRadius: 9,
                background: p.shown ? "#060610" : "rgba(99,102,241,0.06)",
                border: `1px solid ${p.shown ? C.border : "rgba(99,102,241,0.2)"}`,
                cursor: p.shown ? "default" : "pointer",
                transition: "background 0.15s",
                opacity: p.shown ? 0.65 : 1,
              }}
            >
              <span style={{ fontSize: 18, flexShrink: 0, lineHeight: 1.2 }}>{p.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{p.title}</span>
                  {!p.shown && (
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: "1px 5px", borderRadius: 4,
                      background: C.accent, color: "#fff", textTransform: "uppercase",
                    }}>
                      nuevo
                    </span>
                  )}
                  <span style={{
                    fontSize: 10, padding: "1px 6px", borderRadius: 4, marginLeft: "auto",
                    background: "rgba(107,114,128,0.1)", color: C.muted,
                  }}>
                    {TYPE_LABEL[p.type] || p.type}
                  </span>
                </div>
                <p style={{ fontSize: 12, color: C.muted, margin: 0, lineHeight: 1.5 }}>
                  {p.description}
                </p>
                {/* Relevance bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 5 }}>
                  <div style={{ flex: 1, height: 3, background: C.dim, borderRadius: 2 }}>
                    <div style={{
                      width: `${Math.round(p.relevance * 100)}%`, height: "100%",
                      background: RELEVANCE_COLOR(p.relevance), borderRadius: 2,
                    }} />
                  </div>
                  <span style={{ fontSize: 10, color: C.muted, minWidth: 30 }}>
                    {Math.round(p.relevance * 100)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


/* ── Sleep / Consolidation Section ─────────────────────────────────────── */

function SleepSection({ apiUrl }) {
  const [data, setData]           = useState(null);
  const [running, setRunning]     = useState(false);
  const [schedHour, setSchedH]    = useState(2);
  const [schedMin, setSchedM]     = useState(0);
  const [schedOn, setSchedOn]     = useState(false);
  const [deferred, setDeferred]   = useState(false);
  const [savingDef, setSavingDef] = useState(false);

  const refresh = useCallback(() => {
    fetch(`${apiUrl}/api/consolidation/status`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        if (d.schedule) {
          setSchedH(d.schedule.hour ?? 2);
          setSchedM(d.schedule.minute ?? 0);
          setSchedOn(d.schedule.enabled ?? false);
        }
      })
      .catch(() => {});
    fetch(`${apiUrl}/api/settings`)
      .then(r => r.json())
      .then(d => { if (d.system) setDeferred(!!d.system.deferred_mode); })
      .catch(() => {});
  }, [apiUrl]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  const triggerRun = async (mode) => {
    setRunning(true);
    try {
      await fetch(`${apiUrl}/api/consolidation/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      setTimeout(refresh, 800);
    } finally {
      if (mode === "background") setRunning(false);
      else setTimeout(() => { setRunning(false); refresh(); }, 1000);
    }
  };

  const triggerStop = async () => {
    await fetch(`${apiUrl}/api/consolidation/stop`, { method: "POST" });
    setTimeout(refresh, 600);
  };

  const saveSchedule = async () => {
    await fetch(`${apiUrl}/api/consolidation/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hour: schedHour, minute: schedMin, enabled: schedOn }),
    });
    refresh();
  };

  const toggleDeferred = async (val) => {
    setDeferred(val);
    setSavingDef(true);
    try {
      await fetch(`${apiUrl}/api/settings/preferences`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "system", updates: { deferred_mode: val } }),
      });
    } finally {
      setSavingDef(false);
    }
  };

  const state     = data?.state || "idle";
  const isRunning = state === "running";
  const pending   = data?.queue?.pending ?? 0;
  const progress  = data?.progress || {};
  const lastRes   = data?.last_result || {};
  const lastRun   = data?.last_run;

  const stateColor  = isRunning ? C.yellow : state === "scheduled" ? C.accent : C.muted;
  const stateLabel  = isRunning ? "Consolidando…" : state === "scheduled" ? "Programado" : "En reposo";

  return (
    <Card title="Sueño cognitivo" style={{ gridColumn: "1 / -1" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* Left — state + controls */}
        <div>
          {/* State indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <span style={{
              width: 10, height: 10, borderRadius: "50%",
              background: stateColor,
              boxShadow: isRunning ? `0 0 8px ${stateColor}` : "none",
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{stateLabel}</span>
            {pending > 0 && (
              <span style={{ fontSize: 11, padding: "1px 8px", borderRadius: 10, background: "rgba(251,191,36,0.1)", border: "1px solid rgba(251,191,36,0.25)", color: C.yellow }}>
                {pending} en cola
              </span>
            )}
          </div>

          {/* Progress step */}
          {isRunning && progress.step && (
            <div style={{ marginBottom: 12, padding: "8px 10px", borderRadius: 8, background: "rgba(251,191,36,0.05)", border: `1px solid rgba(251,191,36,0.15)`, fontSize: 12, color: C.yellow }}>
              {progress.step}
            </div>
          )}

          {/* Last run stats */}
          {lastRun && (
            <div style={{ marginBottom: 12, fontSize: 12, color: C.muted }}>
              Última consolidación: <span style={{ color: C.text }}>{lastRun?.slice(0, 16).replace("T", " ")}</span>
              {lastRes.nodes != null && (
                <div style={{ marginTop: 4, display: "flex", gap: 12 }}>
                  <span>📦 {lastRes.nodes} nodos</span>
                  <span>💡 {lastRes.insights} insights</span>
                  <span>⏱ {lastRes.elapsed_s}s</span>
                  {lastRes.buffer_items > 0 && <span>📥 {lastRes.buffer_items} de cola</span>}
                </div>
              )}
              {lastRes.errors?.length > 0 && (
                <div style={{ marginTop: 4, color: C.red, fontSize: 11 }}>{lastRes.errors.length} advertencia(s)</div>
              )}
            </div>
          )}

          {/* Control buttons */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {!isRunning ? (
              <>
                <button
                  onClick={() => triggerRun("background")}
                  disabled={running}
                  style={{
                    padding: "7px 16px", borderRadius: 8, border: "none",
                    background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
                    color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
                    opacity: running ? 0.6 : 1,
                  }}
                >
                  {running ? "Iniciando…" : "Consolidar ahora"}
                </button>
              </>
            ) : (
              <button
                onClick={triggerStop}
                style={{
                  padding: "7px 16px", borderRadius: 8,
                  background: "transparent", border: `1px solid ${C.red}`,
                  color: C.red, fontSize: 13, cursor: "pointer",
                }}
              >
                Detener
              </button>
            )}
          </div>

          {/* Deferred mode toggle */}
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            marginTop: 14, padding: "10px 12px",
            background: deferred ? "rgba(99,102,241,0.06)" : "#060610",
            borderRadius: 8,
            border: `1px solid ${deferred ? "rgba(99,102,241,0.25)" : C.border}`,
            transition: "background 0.2s, border-color 0.2s",
          }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>
                Modo diferido {savingDef && <span style={{ fontSize: 10, color: C.muted }}>guardando…</span>}
              </div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                {deferred
                  ? "Activo — conversaciones encolan en buffer para procesar durante el sueño"
                  : "Inactivo — comportamiento estándar (sin buffer adicional)"}
              </div>
            </div>
            <button
              onClick={() => toggleDeferred(!deferred)}
              style={{
                width: 44, height: 24, borderRadius: 12, border: "none", cursor: "pointer",
                background: deferred ? "rgba(99,102,241,0.8)" : C.dim,
                position: "relative", flexShrink: 0, transition: "background 0.2s",
              }}
            >
              <span style={{
                display: "block", width: 18, height: 18, borderRadius: "50%", background: "#fff",
                position: "absolute", top: 3,
                left: deferred ? 23 : 3, transition: "left 0.2s",
              }} />
            </button>
          </div>

          {/* Explanation */}
          <p style={{ fontSize: 11, color: C.muted, marginTop: 10, lineHeight: 1.5 }}>
            Durante conversaciones Aletheia responde rápido sin procesar en profundidad.
            La consolidación mueve datos al grafo semántico, recomputa insights y comprime el contexto.
          </p>
        </div>

        {/* Right — schedule */}
        <div>
          <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
            Programación automática (sueño)
          </div>

          {/* Enable toggle */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", background: "#060610", borderRadius: 8, border: `1px solid ${C.border}`, marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: C.text }}>Consolidación automática</span>
            <button
              onClick={() => setSchedOn(v => !v)}
              style={{
                width: 40, height: 22, borderRadius: 11, border: "none", cursor: "pointer",
                background: schedOn ? "rgba(99,102,241,0.8)" : C.dim,
                position: "relative", transition: "background 0.2s",
              }}
            >
              <span style={{
                display: "block", width: 16, height: 16, borderRadius: "50%", background: "#fff",
                position: "absolute", top: 3,
                left: schedOn ? 21 : 3, transition: "left 0.2s",
              }} />
            </button>
          </div>

          {/* Time picker */}
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12, opacity: schedOn ? 1 : 0.4 }}>
            <div>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 3 }}>Hora</div>
              <select
                value={schedHour}
                onChange={e => setSchedH(Number(e.target.value))}
                disabled={!schedOn}
                style={{ background: "#060610", border: `1px solid ${C.border}`, borderRadius: 6, color: C.text, padding: "5px 8px", fontSize: 13, cursor: schedOn ? "pointer" : "not-allowed" }}
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, "0")}h</option>
                ))}
              </select>
            </div>
            <div>
              <div style={{ fontSize: 10, color: C.muted, marginBottom: 3 }}>Min</div>
              <select
                value={schedMin}
                onChange={e => setSchedM(Number(e.target.value))}
                disabled={!schedOn}
                style={{ background: "#060610", border: `1px solid ${C.border}`, borderRadius: 6, color: C.text, padding: "5px 8px", fontSize: 13, cursor: schedOn ? "pointer" : "not-allowed" }}
              >
                {[0, 15, 30, 45].map(m => (
                  <option key={m} value={m}>{String(m).padStart(2, "0")}</option>
                ))}
              </select>
            </div>
            <div style={{ marginTop: 16 }}>
              <button
                onClick={saveSchedule}
                style={{
                  padding: "6px 14px", borderRadius: 8,
                  background: "transparent", border: `1px solid ${C.dim}`,
                  color: C.muted, fontSize: 12, cursor: "pointer",
                }}
              >
                Guardar
              </button>
            </div>
          </div>

          {schedOn && (
            <div style={{ fontSize: 12, color: C.accent, padding: "7px 10px", borderRadius: 8, background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.15)" }}>
              Consolidación programada cada día a las {String(schedHour).padStart(2, "0")}:{String(schedMin).padStart(2, "0")} h
            </div>
          )}
        </div>
      </div>

      <PatternsSubSection apiUrl={apiUrl} />
    </Card>
  );
}


/* ── Main Component ─────────────────────────────────────────────────────── */

export default function CognitiveDashboard({ apiUrl = "http://localhost:8000", domain = "general", sessionId }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: C.text, margin: 0 }}>Observabilidad cognitiva</h1>
          <p style={{ fontSize: 12, color: C.muted, margin: "4px 0 0" }}>
            Trazabilidad · Aprendizaje adaptativo · Divergencia · Replay
          </p>
        </div>
        <Badge text={`dominio: ${domain}`} color={C.accent} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <CognitiveStateSection   apiUrl={apiUrl} domain={domain} sessionId={sessionId} />
        <SystemHealthSection     apiUrl={apiUrl} />
        <ModeIntelligenceSection apiUrl={apiUrl} domain={domain} />
        <RecentTracesSection     apiUrl={apiUrl} domain={domain} />
        <SleepSection            apiUrl={apiUrl} />
      </div>
    </div>
  );
}
