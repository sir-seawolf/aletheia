/**
 * UseCasesPage — guía interactiva de capacidades de Aletheia.
 * Muestra qué puede hacer, cuánto tarda cada tipo de respuesta,
 * y si la capacidad está disponible según la configuración actual.
 * Los ejemplos de prompt son clicables y se envían directamente al chat.
 */
import { useState, useEffect } from "react";

// ── Definición de casos de uso ─────────────────────────────────────────────

const SPEED = {
  fast:   { label: "1–3 s",   icon: "⚡", color: "#4ade80" },
  medium: { label: "5–15 s",  icon: "◑", color: "#fbbf24" },
  slow:   { label: "20–60 s", icon: "⧗", color: "#f87171" },
};

// system_ids que deben estar "ok" o "partial" para considerar disponible
const USE_CASES = [
  {
    id: "chat",
    category: "Conversación",
    icon: "💬",
    name: "Chat cognitivo",
    description: "Cualquier pregunta, reflexión o tarea. Aletheia elige automáticamente el modo de razonamiento más adecuado (analítico, estratégico, creativo…).",
    speed: "fast",
    requires: ["ollama"],
    examples: [
      "¿Cómo debería priorizar mis proyectos esta semana?",
      "Explícame qué es el efecto compuesto en finanzas",
      "Dame tres formas de mejorar mi concentración",
    ],
  },
  {
    id: "kronos",
    category: "Finanzas",
    icon: "💶",
    name: "Análisis financiero (KRONOS)",
    description: "Analiza tus gastos, ingresos, deuda e inversiones con datos reales de tu PALACE. Responde en modo 'voz' (2-4 frases) o análisis completo.",
    speed: "medium",
    requires: ["ollama"],
    examples: [
      "¿Cuánto he gastado en alimentación este trimestre?",
      "Analiza mi situación financiera actual",
      "¿Cuánto tiempo me falta para ahorrar 10.000 €?",
    ],
  },
  {
    id: "hestia",
    category: "Finanzas",
    icon: "🎯",
    name: "Metas financieras (HESTIA)",
    description: "Seguimiento de tus objetivos económicos a largo plazo. HESTIA contrasta tu progreso real con la meta configurada y te alerta proactivamente.",
    speed: "fast",
    requires: ["ollama"],
    examples: [
      "¿Cómo voy con mi meta de ahorro anual?",
      "¿Cuánto necesito ahorrar al mes para llegar a clase media?",
      "Muéstrame mi progreso financiero",
    ],
  },
  {
    id: "calendar",
    category: "Agenda",
    icon: "📅",
    name: "Google Calendar",
    description: "Consulta y crea eventos en tu calendario. Aletheia entiende lenguaje natural: 'mañana a las 10', 'la próxima semana', 'cancela la reunión del jueves'.",
    speed: "fast",
    requires: ["calendar"],
    examples: [
      "¿Qué tengo esta semana?",
      "Crea una reunión el lunes a las 10 h llamada 'Planning'",
      "¿Tengo algo el próximo viernes?",
    ],
  },
  {
    id: "rag",
    category: "Documentos",
    icon: "🔍",
    name: "Búsqueda en documentos (RAG)",
    description: "Busca información en tus PDFs, contratos, facturas y archivos indexados. La búsqueda semántica encuentra conceptos aunque no uses las mismas palabras.",
    speed: "fast",
    requires: ["rag"],
    examples: [
      "¿Qué dice mi contrato de trabajo sobre las vacaciones?",
      "Busca facturas de Amazon del año pasado",
      "¿Cuánto pagué de IVA en el último trimestre?",
    ],
  },
  {
    id: "web",
    category: "Investigación",
    icon: "🌐",
    name: "Búsqueda web (DuckDuckGo)",
    description: "Busca información actualizada en la web sin necesidad de API key. Útil para noticias, precios, documentación técnica o cualquier consulta de internet.",
    speed: "medium",
    requires: ["ollama"],
    examples: [
      "Busca las últimas noticias sobre inteligencia artificial",
      "¿Cuál es el tipo de interés del BCE ahora mismo?",
      "Investiga las mejores opciones de inversión en 2026",
    ],
  },
  {
    id: "analysis",
    category: "Decisiones",
    icon: "🧠",
    name: "Análisis profundo (pipeline completo)",
    description: "Pipeline completo con exploración, simulación de escenarios, validación y trazabilidad. Genera un informe estructurado con confianza y riesgos. Úsalo para decisiones importantes.",
    speed: "slow",
    requires: ["ollama"],
    examples: [
      "Analiza si debería cambiar de trabajo",
      "¿Merece la pena comprar un coche eléctrico ahora?",
      "Ayúdame a decidir si pedir una hipoteca este año",
    ],
    hint: "Usa la vista 'Análisis' (sidebar) para acceder al pipeline completo con trazas.",
    navOverride: "simulate",
  },
  {
    id: "voice",
    category: "Voz",
    icon: "🎙️",
    name: "Sesión de voz offline",
    description: "Conversa con Aletheia sin internet usando Whisper (STT) y Piper (TTS). Todo procesado en tu PC. Di 'Aletheia' como wake word en modo siempre activo.",
    speed: "medium",
    requires: ["voice"],
    examples: [
      "¿Cuánto he gastado este mes?",
      "¿Qué tengo hoy en el calendario?",
      "Resume mi situación financiera",
    ],
    hint: "Arranca la sesión de voz con: python start.py --voice",
    noChat: true,
  },
  {
    id: "telegram",
    category: "Móvil",
    icon: "✈️",
    name: "Chat desde el móvil (Telegram)",
    description: "Chatea con Aletheia desde cualquier lugar usando tu bot de Telegram. Soporta texto, documentos adjuntos y comandos (/agenda, /gastos, /buscar). HESTIA puede enviarte notificaciones proactivas.",
    speed: "medium",
    requires: ["telegram"],
    examples: [
      "/agenda — eventos de hoy",
      "/gastos — resumen financiero",
      "/buscar <texto> — búsqueda en documentos",
    ],
    hint: "Arranca el bot con: python start.py --telegram",
    noChat: true,
  },
];

// ── Helpers ────────────────────────────────────────────────────────────────

function speedBadge(speed) {
  const s = SPEED[speed];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: 11, padding: "2px 8px", borderRadius: 10,
      background: "rgba(255,255,255,0.04)",
      border: "1px solid #374151",
      color: s.color,
    }}>
      {s.icon} {s.label}
    </span>
  );
}

function availabilityBadge(status) {
  const map = {
    ok:      { label: "Disponible",   color: "#4ade80", bg: "rgba(74,222,128,0.08)",  border: "rgba(74,222,128,0.2)"  },
    partial: { label: "Parcial",      color: "#fbbf24", bg: "rgba(251,191,36,0.08)",  border: "rgba(251,191,36,0.2)"  },
    missing: { label: "Sin configurar", color: "#6b7280", bg: "rgba(107,114,128,0.06)", border: "rgba(107,114,128,0.15)" },
  };
  const s = map[status] || map.missing;
  return (
    <span style={{
      fontSize: 11, padding: "2px 8px", borderRadius: 10,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
    }}>
      {s.label}
    </span>
  );
}

function resolveAvailability(useCase, systemMap) {
  if (!systemMap || useCase.requires.length === 0) return "ok";
  const statuses = useCase.requires.map(id => systemMap[id] || "missing");
  if (statuses.every(s => s === "ok")) return "ok";
  if (statuses.some(s => s === "missing")) return "missing";
  return "partial";
}

// ── Componente principal ───────────────────────────────────────────────────

export default function UseCasesPage({ apiUrl, onQuery, onNavigate }) {
  const [systemMap, setSystemMap]   = useState({});
  const [filter, setFilter]         = useState("all");
  const [expanded, setExpanded]     = useState(null);

  useEffect(() => {
    fetch(`${apiUrl}/api/setup/status`)
      .then(r => r.json())
      .then(d => {
        const map = {};
        (d.systems || []).forEach(s => { map[s.id] = s.status; });
        setSystemMap(map);
      })
      .catch(() => {});
  }, [apiUrl]);

  const categories = ["all", ...Array.from(new Set(USE_CASES.map(u => u.category)))];

  const filtered = USE_CASES.filter(u =>
    filter === "all" || u.category === filter
  );

  const handleExample = (uc, prompt) => {
    if (uc.noChat) return;
    const view = uc.navOverride || "chat";
    onNavigate(view);
    if (onQuery) onQuery(prompt);
  };

  return (
    <div style={{ maxWidth: 760, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 6 }}>Qué puede hacer Aletheia</h1>
        <p style={{ fontSize: 14, color: "#6b7280" }}>
          Guía de capacidades con tiempos de respuesta esperados. Pulsa cualquier ejemplo para lanzarlo directamente al chat.
        </p>
      </div>

      {/* Category filter */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 24 }}>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            style={{
              padding: "5px 14px", borderRadius: 20, fontSize: 12,
              border: `1px solid ${filter === cat ? "#818cf8" : "#374151"}`,
              background: filter === cat ? "rgba(129,140,248,0.15)" : "transparent",
              color: filter === cat ? "#818cf8" : "#6b7280",
              cursor: "pointer", fontWeight: filter === cat ? 600 : 400,
            }}
          >
            {cat === "all" ? "Todos" : cat}
          </button>
        ))}
      </div>

      {/* Use case cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {filtered.map(uc => {
          const avail    = resolveAvailability(uc, systemMap);
          const isOpen   = expanded === uc.id;
          const dimmed   = avail === "missing";

          return (
            <div
              key={uc.id}
              style={{
                background: "#0d0d1a",
                border: "1px solid #1f2937",
                borderRadius: 14,
                overflow: "hidden",
                opacity: dimmed ? 0.75 : 1,
                transition: "opacity 0.2s",
              }}
            >
              {/* Card header — always visible */}
              <button
                onClick={() => setExpanded(isOpen ? null : uc.id)}
                style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 14,
                  padding: "14px 18px", background: "transparent", border: "none",
                  cursor: "pointer", textAlign: "left",
                }}
              >
                <span style={{ fontSize: 22, flexShrink: 0 }}>{uc.icon}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 3 }}>
                    <span style={{ fontSize: 15, fontWeight: 600, color: "#f9fafb" }}>{uc.name}</span>
                    <span style={{ fontSize: 10, color: "#4b5563", padding: "1px 6px", borderRadius: 8, background: "#1f2937" }}>
                      {uc.category}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "#6b7280", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: isOpen ? "normal" : "nowrap" }}>
                    {uc.description}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 }}>
                  {availabilityBadge(avail)}
                  {speedBadge(uc.speed)}
                </div>
                <span style={{ color: "#4b5563", fontSize: 12, marginLeft: 4 }}>{isOpen ? "▲" : "▼"}</span>
              </button>

              {/* Expanded content */}
              {isOpen && (
                <div style={{ padding: "0 18px 18px", borderTop: "1px solid #1f2937" }}>

                  {/* Hint (voice/telegram) */}
                  {uc.hint && (
                    <div style={{ marginTop: 14, padding: "8px 12px", borderRadius: 8, background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.2)", fontSize: 12, color: "#818cf8" }}>
                      {uc.hint}
                    </div>
                  )}

                  {/* Missing systems warning */}
                  {avail === "missing" && (
                    <div style={{ marginTop: 14, padding: "8px 12px", borderRadius: 8, background: "rgba(107,114,128,0.06)", border: "1px solid rgba(107,114,128,0.2)", fontSize: 12, color: "#9ca3af" }}>
                      Requiere configurar:{" "}
                      <strong style={{ color: "#f9fafb" }}>
                        {uc.requires
                          .filter(id => !systemMap[id] || systemMap[id] === "missing")
                          .join(", ")}
                      </strong>
                      {" "} — ve a{" "}
                      <button
                        onClick={() => onNavigate("setup")}
                        style={{ background: "none", border: "none", color: "#818cf8", cursor: "pointer", padding: 0, fontSize: 12, textDecoration: "underline" }}
                      >
                        Inicio → Configuración
                      </button>
                    </div>
                  )}

                  {/* Example prompts */}
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                      {uc.noChat ? "Comandos de ejemplo" : "Pruébalo — pulsa para enviar al chat"}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {uc.examples.map((ex, i) => (
                        <button
                          key={i}
                          onClick={() => handleExample(uc, ex)}
                          disabled={uc.noChat || avail === "missing"}
                          style={{
                            textAlign: "left",
                            padding: "8px 12px",
                            borderRadius: 8,
                            background: "#060610",
                            border: "1px solid #374151",
                            color: (uc.noChat || avail === "missing") ? "#4b5563" : "#d1d5db",
                            fontSize: 13,
                            cursor: (uc.noChat || avail === "missing") ? "default" : "pointer",
                            fontFamily: "inherit",
                            transition: "border-color 0.15s, color 0.15s",
                          }}
                          onMouseEnter={e => {
                            if (!uc.noChat && avail !== "missing") {
                              e.currentTarget.style.borderColor = "#818cf8";
                              e.currentTarget.style.color = "#f9fafb";
                            }
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.borderColor = "#374151";
                            e.currentTarget.style.color = (uc.noChat || avail === "missing") ? "#4b5563" : "#d1d5db";
                          }}
                        >
                          {uc.noChat ? (
                            <code style={{ color: "#818cf8", fontSize: 12 }}>{ex}</code>
                          ) : (
                            <>
                              <span style={{ color: "#4b5563", marginRight: 8 }}>›</span>
                              {ex}
                            </>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div style={{ marginTop: 28, padding: "12px 16px", borderRadius: 10, background: "#0d0d1a", border: "1px solid #1f2937", display: "flex", gap: 20, flexWrap: "wrap" }}>
        <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", alignSelf: "center" }}>Velocidad</div>
        {Object.entries(SPEED).map(([k, s]) => (
          <div key={k} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
            <span style={{ color: s.color }}>{s.icon}</span>
            <span style={{ color: "#9ca3af" }}>{s.label}</span>
          </div>
        ))}
        <div style={{ width: 1, background: "#1f2937" }} />
        <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", alignSelf: "center" }}>Estado</div>
        {[["#4ade80","Disponible"],["#fbbf24","Parcial"],["#6b7280","Sin configurar"]].map(([c,l]) => (
          <div key={l} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: c, display: "inline-block" }} />
            <span style={{ color: "#9ca3af" }}>{l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
