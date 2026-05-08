/**
 * ThinkingPanel — real-time cognitive event stream via WebSocket.
 *
 * Connects to /stream/{sessionId} and renders each pipeline event
 * as it arrives: explorer facts, simulator scenarios, guardian checks.
 *
 * Props:
 *   sessionId: string
 *   apiUrl: string
 *   open: bool
 *   onToggle(): void
 *   onAgentChange(agent, confidence): void  — feeds BrainLoader
 */
import { useState, useEffect, useRef } from "react";

const AGENT_META = {
  explorer:  { icon: "🔍", color: "#818cf8", label: "Explorador" },
  simulator: { icon: "🎲", color: "#34d399", label: "Simulador"  },
  guardian:  { icon: "🛡️", color: "#f59e0b", label: "Guardián"  },
};

function EventRow({ event, idx }) {
  const meta = AGENT_META[event.agent] || { icon: "⚙", color: "#6b7280", label: event.agent };
  const conf = typeof event.confidence === "number" ? event.confidence : null;

  const payloadLines = [];
  const p = event.payload || {};
  if (p.facts?.length)   payloadLines.push(`Hechos: ${p.facts.slice(0, 2).join(" · ")}`);
  if (p.gaps?.length)    payloadLines.push(`Gaps: ${p.gaps.slice(0, 1).join("")}`);
  if (p.domain)          payloadLines.push(`Dominio: ${p.domain}`);

  return (
    <div style={{
      padding: "8px 10px",
      borderLeft: `2px solid ${meta.color}`,
      marginBottom: 6,
      background: idx % 2 === 0 ? "rgba(255,255,255,0.02)" : "transparent",
      borderRadius: "0 6px 6px 0",
      animation: "fadeIn 0.25s ease",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
        <span style={{ fontSize: 13 }}>{meta.icon}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: meta.color, textTransform: "uppercase", letterSpacing: "0.06em" }}>
          {meta.label}
        </span>
        <span style={{ fontSize: 10, color: "#4b5563", marginLeft: 2 }}>
          {event.stage} / {event.event_type}
        </span>
        {conf !== null && (
          <span style={{ marginLeft: "auto", fontSize: 10, color: meta.color }}>
            {Math.round(conf * 100)}%
          </span>
        )}
      </div>
      {payloadLines.map((l, i) => (
        <div key={i} style={{ fontSize: 11, color: "#6b7280", paddingLeft: 20, lineHeight: 1.5 }}>{l}</div>
      ))}
    </div>
  );
}

export default function ThinkingPanel({ sessionId, apiUrl = "http://localhost:8000", open, onToggle, onAgentChange }) {
  const [events, setEvents]     = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef   = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;
    setEvents([]);

    let ws;
    let retryTimer;
    let dead = false;

    const connect = () => {
      if (dead) return;
      const wsUrl = apiUrl.replace(/^http/, "ws") + `/stream/${sessionId}`;
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen  = () => setConnected(true);
      ws.onerror = () => setConnected(false);
      ws.onclose = () => {
        setConnected(false);
        if (!dead) retryTimer = setTimeout(connect, 2000);
      };

      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data);
          setEvents(prev => [...prev.slice(-80), event]);
          if (event.agent && onAgentChange) {
            onAgentChange(event.agent, event.confidence ?? 0);
          }
        } catch { /* ignore malformed */ }
      };
    };

    connect();

    return () => {
      dead = true;
      clearTimeout(retryTimer);
      if (ws) ws.close();
    };
  }, [sessionId, apiUrl]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const panelWidth = open ? 300 : 40;

  return (
    <div style={{
      position: "fixed",
      top: 60,
      right: 0,
      bottom: 0,
      width: panelWidth,
      background: "#080811",
      borderLeft: "1px solid #1f2937",
      display: "flex",
      flexDirection: "column",
      transition: "width 0.25s ease",
      zIndex: 50,
      overflow: "hidden",
    }}>
      {/* Toggle tab */}
      <button
        onClick={onToggle}
        style={{
          position: "absolute",
          left: -32,
          top: 80,
          width: 32,
          height: 64,
          background: "#0d0d1a",
          border: "1px solid #1f2937",
          borderRight: "none",
          borderRadius: "8px 0 0 8px",
          color: connected ? "#818cf8" : "#374151",
          fontSize: 14,
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          writingMode: "vertical-rl",
          padding: "8px 6px",
        }}
        title={open ? "Cerrar panel" : "Ver flujo de pensamiento"}
      >
        <span style={{ fontSize: 12 }}>{connected ? "●" : "○"}</span>
        <span style={{ fontSize: 9, letterSpacing: "0.1em", color: "#6b7280" }}>
          {open ? "CERRAR" : "MENTE"}
        </span>
      </button>

      {open && (
        <>
          {/* Header */}
          <div style={{
            padding: "12px 14px 8px",
            borderBottom: "1px solid #1f2937",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f9fafb" }}>Flujo de pensamiento</div>
              <div style={{ fontSize: 10, color: connected ? "#4ade80" : "#6b7280" }}>
                {connected ? "● en vivo" : "○ inactivo"}
              </div>
            </div>
            {events.length > 0 && (
              <button
                onClick={() => setEvents([])}
                style={{ fontSize: 10, color: "#4b5563", background: "none", border: "none", cursor: "pointer" }}
              >
                limpiar
              </button>
            )}
          </div>

          {/* Events */}
          <div style={{ flex: 1, overflowY: "auto", padding: "10px 10px 0" }}>
            <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:none; } }`}</style>

            {events.length === 0 ? (
              <div style={{ color: "#374151", fontSize: 12, textAlign: "center", paddingTop: 40 }}>
                Los eventos aparecerán<br />cuando proceses una consulta.
              </div>
            ) : (
              events.map((ev, i) => <EventRow key={i} event={ev} idx={i} />)
            )}
            <div ref={bottomRef} />
          </div>
        </>
      )}
    </div>
  );
}
