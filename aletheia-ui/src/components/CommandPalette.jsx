/**
 * CommandPalette — Ctrl+K / Cmd+K quick launcher.
 *
 * Groups: Navigation · Actions · Domains · Recent
 *
 * Props:
 *   open: bool
 *   onClose()
 *   onNavigate(view: string)
 *   onAction(action: string, payload?: any)
 *   onQuery(text: string)   — submits a chat/simulate query directly
 *   recentQueries: string[]
 */
import { useState, useEffect, useRef } from "react";

const COMMANDS = [
  // Navigation
  { id: "nav:chat",     label: "Ir a Chat",            icon: "💬", group: "Navegación",  action: "nav", payload: "chat" },
  { id: "nav:simulate", label: "Nueva decisión",        icon: "🧠", group: "Navegación",  action: "nav", payload: "simulate" },
  { id: "nav:docs",     label: "Documentos",            icon: "📂", group: "Navegación",  action: "nav", payload: "docs" },
  { id: "nav:settings", label: "Configuración",         icon: "⚙️",  group: "Navegación",  action: "nav", payload: "settings" },
  { id: "nav:dashboard",label: "Dashboard",             icon: "📊", group: "Navegación",  action: "nav", payload: "dashboard" },
  // Actions
  { id: "act:voice",    label: "Activar entrada por voz", icon: "🎙", group: "Acciones",   action: "action", payload: "voice" },
  { id: "act:gmail",    label: "Escanear Gmail",          icon: "✉️",  group: "Acciones",   action: "query", payload: "escanea el correo del año en curso" },
  { id: "act:search",   label: "Buscar en internet…",     icon: "🔍", group: "Acciones",   action: "action", payload: "web_search" },
  { id: "act:summary",  label: "Resumen financiero",      icon: "💶", group: "Acciones",   action: "query", payload: `resumen de gastos ${new Date().getFullYear()}` },
  { id: "act:artifacts",label: "Ver artefactos",          icon: "🗄️",  group: "Acciones",   action: "nav",    payload: "docs" },
  // Domains
  ...["finanzas","carrera","tecnologia","salud","relaciones","objetivos","aprendizaje","creatividad"].map(d => ({
    id:      `domain:${d}`,
    label:   `Cambiar dominio → ${d}`,
    icon:    "🏷",
    group:   "Dominio",
    action:  "domain",
    payload: d,
  })),
];

function fuzzy(str, query) {
  const s = str.toLowerCase();
  const q = query.toLowerCase();
  let si = 0;
  for (let i = 0; i < q.length; i++) {
    si = s.indexOf(q[i], si);
    if (si === -1) return false;
    si++;
  }
  return true;
}

export default function CommandPalette({ open, onClose, onNavigate, onAction, onQuery, recentQueries = [] }) {
  const [query, setQuery]     = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef(null);
  const listRef  = useRef(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        open ? onClose() : onAction?.("open_palette");
      }
      if (e.key === "Escape" && open) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose, onAction]);

  // Filter commands
  const recentCmds = recentQueries.slice(0, 3).map((q, i) => ({
    id:      `recent:${i}`,
    label:   q,
    icon:    "🕐",
    group:   "Reciente",
    action:  "query",
    payload: q,
  }));

  const allCmds = [...recentCmds, ...COMMANDS];

  const filtered = query.trim()
    ? allCmds.filter(c => fuzzy(c.label, query) || fuzzy(c.group, query))
    : allCmds;

  // If query looks like a free-form question, add a "Preguntar a Aletheia" item
  const isQuestion = query.trim().length > 4;
  const withAsk = isQuestion
    ? [{ id: "ask", label: `Preguntar: "${query}"`, icon: "→", group: "Chat", action: "query", payload: query }, ...filtered]
    : filtered;

  // Group items
  const groups: Record<string, typeof COMMANDS> = {};
  for (const cmd of withAsk) {
    if (!groups[cmd.group]) groups[cmd.group] = [];
    groups[cmd.group].push(cmd);
  }

  const flatItems = withAsk;

  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, flatItems.length - 1)); }
    if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === "Enter")     { e.preventDefault(); execute(flatItems[selected]); }
  };

  const execute = (cmd) => {
    if (!cmd) return;
    onClose();
    if (cmd.action === "nav")    onNavigate?.(cmd.payload);
    if (cmd.action === "query")  onQuery?.(cmd.payload);
    if (cmd.action === "action") onAction?.(cmd.payload);
    if (cmd.action === "domain") onAction?.("domain", cmd.payload);
  };

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 1000,
        background: "rgba(0,0,0,0.65)",
        display: "flex", alignItems: "flex-start", justifyContent: "center",
        paddingTop: "12vh",
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: "100%", maxWidth: 580,
          background: "#0d0d1a",
          border: "1px solid #374151",
          borderRadius: 16,
          overflow: "hidden",
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        }}
      >
        {/* Input */}
        <div style={{ display: "flex", alignItems: "center", padding: "14px 16px", borderBottom: "1px solid #1f2937", gap: 10 }}>
          <span style={{ color: "#6b7280", fontSize: 16 }}>⌘</span>
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelected(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Buscar comandos, acciones o pregunta algo…"
            style={{
              flex: 1, background: "transparent", border: "none",
              color: "#f9fafb", fontSize: 15, outline: "none",
            }}
          />
          <span style={{ fontSize: 10, color: "#4b5563", background: "#1f2937", padding: "2px 6px", borderRadius: 4 }}>ESC</span>
        </div>

        {/* Results */}
        <div ref={listRef} style={{ maxHeight: 400, overflowY: "auto", padding: "8px 0" }}>
          {Object.entries(groups).map(([group, items]) => (
            <div key={group}>
              <div style={{ fontSize: 10, color: "#4b5563", padding: "6px 16px 2px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {group}
              </div>
              {items.map((cmd) => {
                const idx = flatItems.indexOf(cmd);
                const isSelected = idx === selected;
                return (
                  <div
                    key={cmd.id}
                    onClick={() => execute(cmd)}
                    onMouseEnter={() => setSelected(idx)}
                    style={{
                      display: "flex", alignItems: "center", gap: 10,
                      padding: "9px 16px",
                      background: isSelected ? "rgba(99,102,241,0.15)" : "transparent",
                      cursor: "pointer",
                      transition: "background 0.1s",
                    }}
                  >
                    <span style={{ fontSize: 15, width: 22, textAlign: "center" }}>{cmd.icon}</span>
                    <span style={{ flex: 1, fontSize: 14, color: isSelected ? "#f9fafb" : "#d1d5db" }}>{cmd.label}</span>
                    {isSelected && (
                      <span style={{ fontSize: 10, color: "#6b7280", background: "#1f2937", padding: "2px 6px", borderRadius: 4 }}>↵</span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
          {flatItems.length === 0 && (
            <div style={{ padding: "20px", textAlign: "center", color: "#4b5563", fontSize: 13 }}>
              Sin resultados
            </div>
          )}
        </div>

        <div style={{ padding: "8px 16px", borderTop: "1px solid #1f2937", display: "flex", gap: 16, fontSize: 10, color: "#4b5563" }}>
          <span>↑↓ navegar</span>
          <span>↵ ejecutar</span>
          <span>Ctrl+K abrir/cerrar</span>
        </div>
      </div>
    </div>
  );
}
