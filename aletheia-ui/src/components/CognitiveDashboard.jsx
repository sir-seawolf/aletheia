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

function Card({ title, children, action }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "14px 16px" }}>
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
        <CognitiveStateSection  apiUrl={apiUrl} domain={domain} sessionId={sessionId} />
        <SystemHealthSection    apiUrl={apiUrl} />
        <ModeIntelligenceSection apiUrl={apiUrl} domain={domain} />
        <RecentTracesSection    apiUrl={apiUrl} domain={domain} />
      </div>
    </div>
  );
}
