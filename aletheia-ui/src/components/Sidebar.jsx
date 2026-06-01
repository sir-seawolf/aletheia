/**
 * Sidebar — persistent left panel with context at a glance.
 *
 * Props:
 *   activeView: string
 *   onNavigate(view)
 *   domain: string
 *   onDomain(d)
 *   status: { provider, ollama_ok, docs, memory, fin_total }
 *   apiUrl: string
 *   setupMissing: number  — count of unconfigured systems (shows badge on Inicio)
 */
import { useState, useEffect } from "react";

const VIEWS = [
  { id: "setup",     icon: "◎",  label: "Inicio" },
  { id: "usecases",  icon: "◇",  label: "Capacidades" },
  { id: "chat",      icon: "💬", label: "Chat" },
  { id: "simulate",  icon: "🧠", label: "Análisis" },
  { id: "projects",  icon: "⚖️", label: "Proyectos" },
  { id: "docs",      icon: "📂", label: "Documentos" },
  { id: "cognitive", icon: "◈",  label: "Cognitivo" },
  { id: "settings",  icon: "⚙️",  label: "Config" },
  { id: "help",      icon: "❓", label: "Ayuda" },
];

const DOMAINS = [
  { value: "finanzas",    icon: "💶" },
  { value: "carrera",     icon: "💼" },
  { value: "tecnologia",  icon: "💻" },
  { value: "salud",       icon: "❤️" },
  { value: "relaciones",  icon: "🤝" },
  { value: "objetivos",   icon: "🎯" },
  { value: "aprendizaje", icon: "📚" },
  { value: "creatividad", icon: "✨" },
];

export default function Sidebar({ activeView, onNavigate, domain, onDomain, status = {}, apiUrl, setupMissing = 0 }) {
  const [recentArtifacts, setRecentArtifacts] = useState([]);
  const [expanded, setExpanded]               = useState(true);

  useEffect(() => {
    fetch(`${apiUrl}/api/artifacts?limit=5`)
      .then(r => r.json())
      .then(d => { if (Array.isArray(d)) setRecentArtifacts(d.slice(0, 4)); })
      .catch(() => {});
  }, [apiUrl]);

  const w = expanded ? 220 : 52;

  const navBtn = (view) => {
    const active  = activeView === view.id;
    const showBadge = view.id === "setup" && setupMissing > 0;
    return (
      <button
        key={view.id}
        onClick={() => onNavigate(view.id)}
        title={!expanded ? view.label : ""}
        style={{
          display: "flex", alignItems: "center", gap: 10,
          width: "100%", padding: expanded ? "9px 14px" : "9px",
          justifyContent: expanded ? "flex-start" : "center",
          background: active ? "rgba(99,102,241,0.18)" : "transparent",
          border: "none",
          borderLeft: `3px solid ${active ? "#818cf8" : "transparent"}`,
          borderRadius: "0 8px 8px 0",
          color: active ? "#f9fafb" : "#6b7280",
          fontSize: 13, fontWeight: active ? 600 : 400,
          cursor: "pointer", textAlign: "left",
          transition: "all 0.15s",
          position: "relative",
        }}
      >
        <span style={{ fontSize: 15, flexShrink: 0, position: "relative" }}>
          {view.icon}
          {showBadge && !expanded && (
            <span style={{
              position: "absolute", top: -4, right: -6,
              minWidth: 14, height: 14, borderRadius: 7,
              background: "#f87171", color: "#fff",
              fontSize: 9, fontWeight: 700, lineHeight: "14px",
              textAlign: "center", padding: "0 3px",
              border: "1.5px solid #060610",
            }}>
              {setupMissing}
            </span>
          )}
        </span>
        {expanded && <span style={{ flex: 1 }}>{view.label}</span>}
        {expanded && showBadge && (
          <span style={{
            minWidth: 18, height: 18, borderRadius: 9,
            background: "#f87171", color: "#fff",
            fontSize: 10, fontWeight: 700, lineHeight: "18px",
            textAlign: "center", padding: "0 4px",
          }}>
            {setupMissing}
          </span>
        )}
      </button>
    );
  };

  return (
    <div style={{
      width: w, minWidth: w, flexShrink: 0,
      background: "#080811",
      borderRight: "1px solid #1f2937",
      display: "flex", flexDirection: "column",
      height: "calc(100vh - 52px)",
      overflowY: "auto", overflowX: "hidden",
      transition: "width 0.2s",
      position: "sticky", top: 52,
    }}>
      {/* Collapse toggle */}
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          alignSelf: "flex-end", margin: "8px 8px 4px",
          background: "transparent", border: "none",
          color: "#4b5563", fontSize: 12, cursor: "pointer", padding: 4,
        }}
        title={expanded ? "Colapsar sidebar" : "Expandir sidebar"}
      >
        {expanded ? "◀" : "▶"}
      </button>

      {/* Navigation */}
      <div style={{ paddingBottom: 8 }}>
        {VIEWS.map(navBtn)}
      </div>

      {expanded && (
        <>
          {/* Domain selector */}
          <div style={{ padding: "8px 12px 4px", borderTop: "1px solid #1f2937" }}>
            <div style={{ fontSize: 10, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
              Dominio
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {DOMAINS.map(d => (
                <button
                  key={d.value}
                  onClick={() => onDomain(d.value)}
                  title={d.value}
                  style={{
                    padding: "3px 7px",
                    borderRadius: 6,
                    border: `1px solid ${domain === d.value ? "#818cf8" : "#1f2937"}`,
                    background: domain === d.value ? "rgba(129,140,248,0.15)" : "transparent",
                    color: domain === d.value ? "#818cf8" : "#6b7280",
                    fontSize: 13, cursor: "pointer",
                  }}
                >
                  {d.icon}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 10, color: "#818cf8", marginTop: 4 }}>
              {domain}
            </div>
          </div>

          {/* Quick stats */}
          <div style={{ padding: "8px 12px", borderTop: "1px solid #1f2937" }}>
            <div style={{ fontSize: 10, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
              Estado
            </div>
            {[
              ["🧠", "Memoria", status.memory ?? "–"],
              ["📄", "Documentos", status.docs ?? "–"],
              ["💶", "Gastos año", status.fin_total != null ? `${status.fin_total.toFixed(0)} €` : "–"],
            ].map(([icon, label, val]) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0", fontSize: 12 }}>
                <span style={{ color: "#6b7280" }}>{icon} {label}</span>
                <span style={{ color: "#f9fafb", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{val}</span>
              </div>
            ))}
          </div>

          {/* Recent artifacts */}
          {recentArtifacts.length > 0 && (
            <div style={{ padding: "8px 12px", borderTop: "1px solid #1f2937", flex: 1 }}>
              <div style={{ fontSize: 10, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                Reciente
              </div>
              {recentArtifacts.map((a, i) => (
                <div key={i} style={{ fontSize: 11, color: "#6b7280", padding: "2px 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {a.type === "invoice" ? "🧾" : a.type === "webpage" ? "🌐" : "📄"} {a.filename || a.id.slice(0, 10)}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
