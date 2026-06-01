/**
 * ThinkingPanel — real-time cognitive event stream + cognitive state meters.
 *
 * Top section: live energy/fatigue bars + last routing decision.
 * Bottom section: event stream from WebSocket /stream/{sessionId}.
 *
 * Props:
 *   sessionId:       string
 *   apiUrl:          string
 *   domain:          string
 *   open:            bool
 *   onToggle():      void
 *   onAgentChange(agent, confidence): void — feeds BrainLoader
 */
import { useState, useEffect, useRef, useCallback } from "react";

const C = {
  accent: "#818cf8",
  green:  "#4ade80",
  yellow: "#fbbf24",
  red:    "#f87171",
  muted:  "#6b7280",
  dim:    "#374151",
  bg:     "#080811",
  surface:"#0d0d1a",
  border: "#1f2937",
  text:   "#f9fafb",
};

const AGENT_META = {
  explorer:      { icon: "🔍", color: C.accent,  label: "Explorador"  },
  simulator:     { icon: "🎲", color: "#34d399",  label: "Simulador"   },
  guardian:      { icon: "🛡️", color: C.yellow,  label: "Guardián"    },
  shadow_runner: { icon: "👁",  color: "#a78bfa",  label: "Shadow"      },
  kronos:        { icon: "💶", color: C.yellow,   label: "KRONOS"      },
  orchestrator:  { icon: "🧠", color: C.accent,   label: "Observer"    },
};

const ROUTING_SOURCE_LABELS = {
  learned_blend:  { icon: "★", color: "#c084fc", label: "aprendido (blend)" },
  learned_mode:   { icon: "★", color: C.accent,  label: "aprendido (modo)"  },
  blend_keyword:  { icon: "⊕", color: "#a78bfa", label: "blend keywords"     },
  keyword:        { icon: "○", color: C.muted,   label: "keyword routing"    },
};

/* ── Tiny bar ────────────────────────────────────────────────────────────── */
function MiniBar({ value = 0, color = C.accent, label }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div style={{ marginBottom: 5 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
        <span style={{ fontSize: 9, color: C.muted }}>{label}</span>
        <span style={{ fontSize: 9, color, fontVariantNumeric: "tabular-nums" }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ height: 3, background: C.dim, borderRadius: 2, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 2, transition: "width 0.5s ease" }} />
      </div>
    </div>
  );
}

/* ── Cognitive State Widget ──────────────────────────────────────────────── */
function CogStateWidget({ apiUrl, domain, sessionId }) {
  const [state, setState]   = useState(null);
  const [reco,  setReco]    = useState(null);
  const [lastTrace, setLast] = useState(null);

  const poll = useCallback(() => {
    if (!sessionId) return;
    fetch(`${apiUrl}/api/learning/recommend?domain=${encodeURIComponent(domain || "general")}&session_id=${encodeURIComponent(sessionId)}`)
      .then(r => r.json()).then(d => { setState(d.cognitive_state); setReco(d); }).catch(() => {});
    fetch(`${apiUrl}/api/traces?limit=1&session_id=${encodeURIComponent(sessionId)}`)
      .then(r => r.json()).then(d => { if (d.traces?.length) setLast(d.traces[0]); }).catch(() => {});
  }, [apiUrl, domain, sessionId]);

  useEffect(() => { poll(); const t = setInterval(poll, 10000); return () => clearInterval(t); }, [poll]);

  if (!state) return null;

  const fatigueColor = state.fatigue > 0.7 ? C.red : state.fatigue > 0.4 ? C.yellow : C.green;
  const energyColor  = state.energy  < 0.3 ? C.red : state.energy  < 0.6 ? C.yellow : C.green;
  const rsInfo = lastTrace?.observer_routing_reason && ROUTING_SOURCE_LABELS[lastTrace.observer_routing_reason];

  return (
    <div style={{ padding: "10px 12px", borderBottom: `1px solid ${C.border}` }}>
      <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>
        Estado cognitivo
      </div>
      <MiniBar label="Energía"    value={state.energy}    color={energyColor} />
      <MiniBar label="Fatiga"     value={state.fatigue}   color={fatigueColor} />
      <MiniBar label="Coherencia" value={state.coherence} color={C.accent} />

      {/* Last routing decision */}
      {(reco?.recommended_mode || reco?.recommended_blend || lastTrace) && (
        <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4 }}>
          {reco?.recommended_mode && (
            <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 8, background: `${C.accent}18`, border: `1px solid ${C.accent}40`, color: C.accent }}>
              {reco.recommended_mode}
            </span>
          )}
          {reco?.recommended_blend && (
            <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 8, background: "#c084fc18", border: "1px solid #c084fc40", color: "#c084fc" }}>
              blend:{reco.recommended_blend}
            </span>
          )}
          {reco?.recommended_provider && (
            <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 8, background: `${C.green}12`, border: `1px solid ${C.green}35`, color: C.green }}>
              {reco.recommended_provider}
            </span>
          )}
          {rsInfo && (
            <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 8, background: `${rsInfo.color}12`, border: `1px solid ${rsInfo.color}35`, color: rsInfo.color }}>
              {rsInfo.icon} {rsInfo.label}
            </span>
          )}
        </div>
      )}

      {lastTrace && (
        <div style={{ marginTop: 6, fontSize: 9, color: C.muted, display: "flex", gap: 8 }}>
          {lastTrace.latency_ms && <span>{lastTrace.latency_ms.toFixed(0)}ms</span>}
          {lastTrace.tokens_used > 0 && <span>{lastTrace.tokens_used} tok</span>}
          {lastTrace.fatigue_delta > 0 && (
            <span style={{ color: lastTrace.fatigue_delta > 0.07 ? C.red : C.muted }}>
              +{(lastTrace.fatigue_delta * 100).toFixed(1)}% fatiga
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Event Row ───────────────────────────────────────────────────────────── */
function EventRow({ event, idx }) {
  const meta = AGENT_META[event.agent] || { icon: "⚙", color: C.muted, label: event.agent };
  const conf = typeof event.confidence === "number" ? event.confidence : null;

  const lines = [];
  const p = event.payload || {};
  if (p.facts?.length)      lines.push(`Hechos: ${p.facts.slice(0, 2).join(" · ")}`);
  if (p.gaps?.length)       lines.push(`Gaps: ${p.gaps.slice(0, 1).join("")}`);
  if (p.domain)             lines.push(`Dominio: ${p.domain}`);
  if (p.blend_label)        lines.push(`Blend: ${p.blend_label}`);
  if (p.routing_source)     lines.push(`Routing: ${p.routing_source}`);
  if (p.shadow_preview)     lines.push(`Shadow: ${p.shadow_preview.slice(0, 60)}…`);
  if (p.v1_preview)         lines.push(`v1: ${p.v1_preview.slice(0, 60)}…`);

  const isDivergence = event.event_type === "shadow_divergence";

  return (
    <div style={{
      padding: "7px 10px",
      borderLeft: `2px solid ${isDivergence ? C.yellow : meta.color}`,
      marginBottom: 5,
      background: isDivergence
        ? "rgba(251,191,36,0.04)"
        : idx % 2 === 0 ? "rgba(255,255,255,0.02)" : "transparent",
      borderRadius: "0 6px 6px 0",
      animation: "fadeIn 0.25s ease",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: lines.length ? 2 : 0 }}>
        <span style={{ fontSize: 12 }}>{isDivergence ? "⚡" : meta.icon}</span>
        <span style={{ fontSize: 10, fontWeight: 700, color: isDivergence ? C.yellow : meta.color, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {isDivergence ? "Divergencia" : meta.label}
        </span>
        <span style={{ fontSize: 9, color: "#4b5563", marginLeft: 1 }}>
          {event.stage} / {event.event_type}
        </span>
        {conf !== null && (
          <span style={{ marginLeft: "auto", fontSize: 9, color: meta.color, fontVariantNumeric: "tabular-nums" }}>
            {Math.round(conf * 100)}%
          </span>
        )}
      </div>
      {lines.map((l, i) => (
        <div key={i} style={{ fontSize: 10, color: "#6b7280", paddingLeft: 18, lineHeight: 1.5 }}>{l}</div>
      ))}
    </div>
  );
}

/* ── Main Panel ──────────────────────────────────────────────────────────── */
export default function ThinkingPanel({
  sessionId,
  cogSessionId,   // stable chat session for cognitive state polling; falls back to sessionId
  apiUrl = "http://localhost:8000",
  domain = "general",
  open,
  onToggle,
  onAgentChange,
}) {
  const [events,    setEvents]    = useState([]);
  const [connected, setConnected] = useState(false);
  const [tab,       setTab]       = useState("stream");
  const wsRef    = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;
    setEvents([]);
    let dead = false;
    let retryTimer;

    const connect = () => {
      if (dead) return;
      const wsUrl = apiUrl.replace(/^http/, "ws") + `/stream/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen  = () => setConnected(true);
      ws.onerror = () => setConnected(false);
      ws.onclose = () => {
        setConnected(false);
        if (!dead) retryTimer = setTimeout(connect, 2000);
      };
      ws.onmessage = (msg) => {
        try {
          const ev = JSON.parse(msg.data);
          setEvents(prev => [...prev.slice(-100), ev]);
          if (ev.agent && onAgentChange) onAgentChange(ev.agent, ev.confidence ?? 0);
        } catch { /* ignore */ }
      };
    };

    connect();
    return () => {
      dead = true;
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [sessionId, apiUrl]);

  useEffect(() => {
    if (tab === "stream") bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events, tab]);

  const panelWidth = open ? 300 : 40;

  return (
    <div style={{
      position: "fixed", top: 60, right: 0, bottom: 0,
      width: panelWidth,
      background: C.bg, borderLeft: `1px solid ${C.border}`,
      display: "flex", flexDirection: "column",
      transition: "width 0.25s ease",
      zIndex: 50, overflow: "hidden",
    }}>
      {/* Toggle tab */}
      <button
        onClick={onToggle}
        style={{
          position: "absolute", left: -32, top: 80,
          width: 32, height: 64,
          background: "#0d0d1a", border: `1px solid ${C.border}`,
          borderRight: "none", borderRadius: "8px 0 0 8px",
          color: connected ? C.accent : C.dim,
          fontSize: 13, cursor: "pointer",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          gap: 4, writingMode: "vertical-rl", padding: "8px 6px",
        }}
        title={open ? "Cerrar panel" : "Ver flujo de pensamiento"}
      >
        <span style={{ fontSize: 11 }}>{connected ? "●" : "○"}</span>
        <span style={{ fontSize: 9, letterSpacing: "0.1em", color: C.muted }}>
          {open ? "CERRAR" : "MENTE"}
        </span>
      </button>

      {open && (
        <>
          {/* Header */}
          <div style={{ padding: "10px 12px 0", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.text }}>Flujo cognitivo</div>
                <div style={{ fontSize: 9, color: connected ? C.green : C.muted }}>
                  {connected ? "● en vivo" : "○ inactivo"}
                </div>
              </div>
              {events.length > 0 && (
                <button
                  onClick={() => setEvents([])}
                  style={{ fontSize: 9, color: C.muted, background: "none", border: "none", cursor: "pointer" }}
                >
                  limpiar
                </button>
              )}
            </div>
            {/* Tabs */}
            <div style={{ display: "flex", gap: 3, paddingBottom: 8 }}>
              {[["stream", "Eventos"], ["state", "Estado"]].map(([t, l]) => (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: "2px 8px", borderRadius: "6px 6px 0 0",
                  fontSize: 9, cursor: "pointer",
                  background: tab === t ? C.surface : "transparent",
                  border: `1px solid ${tab === t ? C.border : "transparent"}`,
                  borderBottom: tab === t ? `1px solid ${C.surface}` : "none",
                  color: tab === t ? C.text : C.muted,
                }}>{l}</button>
              ))}
            </div>
          </div>

          {/* State tab */}
          {tab === "state" && (
            <div style={{ flex: 1, overflowY: "auto" }}>
              <CogStateWidget apiUrl={apiUrl} domain={domain} sessionId={cogSessionId || sessionId} />
            </div>
          )}

          {/* Stream tab */}
          {tab === "stream" && (
            <div style={{ flex: 1, overflowY: "auto", padding: "8px 8px 0" }}>
              <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}`}</style>
              {events.length === 0 ? (
                <div style={{ color: C.dim, fontSize: 11, textAlign: "center", paddingTop: 30 }}>
                  Los eventos aparecerán<br />cuando proceses una consulta.
                </div>
              ) : (
                events.map((ev, i) => <EventRow key={i} event={ev} idx={i} />)
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
