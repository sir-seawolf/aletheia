/**
 * HelpPanel — modal de ayuda accesible.
 *
 * Activación:
 *   - Botón ? en la navbar
 *   - Tecla ? (fuera de inputs)
 *   - Ctrl+/ desde cualquier lugar
 *   - Comando "ayuda" en CommandPalette
 */
import { useState, useEffect, useCallback } from "react";

/* ── contenido por sección ─────────────────────────────────────────────── */

const SECTIONS = [
  {
    id: "chat",
    icon: "💬",
    label: "Chat",
    content: {
      intro: "El chat es la forma principal de hablar con Aletheia. Mantiene historial multi-turno — recuerda lo que dijiste antes en la misma sesión.",
      items: [
        { label: "Pregunta libre", examples: ["¿Qué es el IRPF?", "Dame ideas para ahorrar", "Explícame la regla del 50/30/20"] },
        { label: "Análisis de decisión", examples: ["¿Debería cambiar de trabajo ahora?", "Comparo dos opciones: quedarme en alquiler o comprar"] },
        { label: "Resúmenes", examples: ["Resume lo que hemos hablado", "¿Qué puntos clave saqué hoy?"] },
      ],
      tip: "Si la pregunta es compleja o implica una decisión, Aletheia la redirige automáticamente al pipeline cognitivo (análisis de escenarios + guardián).",
    },
  },
  {
    id: "docs",
    icon: "📂",
    label: "Documentos",
    content: {
      intro: "PALACE almacena todos tus documentos con SHA-256, versiones y búsqueda semántica.",
      items: [
        { label: "Importar desde el chat", examples: ["Importa mis facturas del correo de 2024", "Lee esta página: https://..."] },
        { label: "Subir archivo", examples: ["Arrastra un PDF/DOCX/CSV a la sección Documentos"] },
        { label: "Buscar documentos", examples: ["/buscar factura Movistar", "¿Qué documentos tengo de seguros?"] },
        { label: "Explorar drive local", examples: ["Busca mis contratos en Drive", "¿Qué hay en OneDrive?"] },
      ],
      tip: "Cada documento ingestado se indexa automáticamente en RAG. Las próximas preguntas del chat usarán ese contexto.",
    },
  },
  {
    id: "finanzas",
    icon: "💶",
    label: "Finanzas",
    content: {
      intro: "Aletheia puede leer tus extractos bancarios, calcular impuestos y llevar un resumen financiero.",
      items: [
        { label: "Resumen de gastos", examples: ["¿Cuánto he gastado este año?", "Resumen financiero 2024", "¿Cuáles son mis mayores gastos?"] },
        { label: "IRPF", examples: ["¿Cuánto IRPF pago con 38.000€ brutos?", "Calcula mi tipo efectivo de IRPF", "¿Cuánto me retienen siendo autónomo?"] },
        { label: "IVA / Modelo 303", examples: ["IVA de una factura de 1.200€", "Modelo 303 del segundo trimestre", "¿Cuánto IVA tengo que ingresar?"] },
        { label: "Modelo 130", examples: ["Pago fraccionado del tercer trimestre", "Modelo 130 con 20.000€ de ingresos y 4.000€ de gastos"] },
      ],
      tip: "Importa tus extractos bancarios (CSV de CaixaBank, BBVA, Santander, ING, Sabadell…) para que los resúmenes sean automáticos.",
    },
  },
  {
    id: "calendario",
    icon: "📅",
    label: "Calendario",
    content: {
      intro: "Acceso a Google Calendar desde el chat o la voz. Requiere configurar credenciales en Ajustes.",
      items: [
        { label: "Ver agenda", examples: ["¿Qué tengo hoy?", "Agenda de mañana", "Eventos de esta semana"] },
        { label: "Crear evento", examples: ["Crea una reunión con el banco el viernes a las 10", "Agénda una cita médica el lunes 3 a las 9:30"] },
        { label: "Buscar eventos", examples: ["¿Cuándo fue mi última revisión médica?", "Busca reuniones con Hacienda"] },
      ],
      tip: "Usa el mismo credentials.json de Google Drive si ya lo tienes configurado — solo necesitas añadir el permiso de Calendar en Google Cloud Console.",
    },
  },
  {
    id: "voz",
    icon: "🎤",
    label: "Voz",
    content: {
      intro: "Modo voz push-to-talk completamente offline. STT con faster-whisper, TTS con Piper (es_ES-davefx).",
      items: [
        { label: "Activar desde CLI", examples: ["python start.py --voice", "python cli.py voice"] },
        { label: "Uso", examples: ["Pulsa ENTER para hablar, suelta y espera la respuesta", "Di 'Aletheia' + tu pregunta"] },
        { label: "Diagnóstico de voces", examples: ["python cli.py voices"] },
      ],
      tip: "Los modelos se descargan automáticamente en PALACE/voice_models/ la primera vez (~215 MB en total).",
    },
  },
  {
    id: "telegram",
    icon: "✈️",
    label: "Telegram",
    content: {
      intro: "Acceso al chat de Aletheia desde el móvil. Sin abrir el navegador.",
      items: [
        { label: "Comandos del bot", examples: ["/start — presentación y ayuda", "/agenda — eventos de hoy", "/gastos — resumen financiero", "/fiscal — calculadora IRPF/IVA", "/buscar <texto> — búsqueda semántica", "/status — estado del sistema"] },
        { label: "Documentos", examples: ["Envía un PDF al bot → se ingesta en PALACE automáticamente"] },
        { label: "Activar el bot", examples: ["python start.py --telegram"] },
      ],
      tip: "Crea el bot en 2 min: escribe a @BotFather en Telegram → /newbot. Guarda el token en PALACE/config/telegram.json.",
    },
  },
  {
    id: "atajos",
    icon: "⌨️",
    label: "Atajos",
    content: {
      intro: "Navega toda la aplicación sin ratón.",
      items: [
        { label: "Paleta de comandos", examples: ["Ctrl+K — abre la paleta", "Escribe para buscar cualquier vista o acción"] },
        { label: "Ayuda", examples: ["? — abre este panel (fuera de inputs)", "Ctrl+/ — abre ayuda siempre"] },
        { label: "Chat", examples: ["Enter — enviar mensaje", "Shift+Enter — salto de línea"] },
        { label: "Análisis", examples: ["Ctrl+Enter — lanzar análisis"] },
        { label: "Cerrar modales", examples: ["Escape — cierra paleta, ayuda, etc."] },
      ],
      tip: "La sidebar se puede colapsar con el botón ◀ para ganar espacio en pantalla pequeña.",
    },
  },
  {
    id: "rag",
    icon: "🔍",
    label: "Búsqueda RAG",
    content: {
      intro: "Búsqueda semántica sobre todos tus documentos. Usa embeddings de Ollama (nomic-embed-text).",
      items: [
        { label: "Desde el chat", examples: ["¿Qué decía mi contrato de alquiler?", "Busca en mis documentos algo sobre el seguro de salud"] },
        { label: "Reindexar", examples: ["POST /api/rag/reindex — indexa todos los artefactos existentes"] },
        { label: "Requisito", examples: ["ollama pull nomic-embed-text", "pip install chromadb"] },
      ],
      tip: "Los documentos nuevos se indexan automáticamente. El reindex solo es necesario para los ya existentes antes de instalar el sistema RAG.",
    },
  },
  {
    id: "config",
    icon: "⚙️",
    label: "Configuración",
    content: {
      intro: "Accesible desde el icono ⚙️ en la sidebar o con Ctrl+K → \"Configuración\".",
      items: [
        { label: "LLM", examples: ["Elige proveedor: Ollama (local), Claude, OpenAI, DeepSeek, Groq, Mistral", "TURBO mode: specialist / race / panel para multi-proveedor"] },
        { label: "Google", examples: ["Gmail: credentials.json para importar facturas", "Google Drive: acceso a documentos", "Google Calendar: agenda integrada"] },
        { label: "Carpetas locales", examples: ["Añade rutas de OneDrive, Dropbox o cualquier carpeta local"] },
        { label: "Voz", examples: ["Modelo Piper, velocidad, volumen"] },
      ],
      tip: "Todos los credenciales se guardan en PALACE/config/ — excluido de git, solo en tu máquina.",
    },
  },
];

/* ── estilos inline compartidos ────────────────────────────────────────── */

const S = {
  overlay: {
    position: "fixed", inset: 0, zIndex: 1000,
    background: "rgba(0,0,0,0.55)", backdropFilter: "blur(4px)",
    display: "flex", alignItems: "flex-start", justifyContent: "flex-end",
  },
  panel: {
    width: 680, maxWidth: "95vw",
    height: "100vh",
    background: "#0a0a18",
    borderLeft: "1px solid #1f2937",
    display: "flex", flexDirection: "column",
    overflowY: "auto",
    animation: "slideIn 0.2s ease",
  },
  header: {
    padding: "20px 24px 16px",
    borderBottom: "1px solid #1f2937",
    display: "flex", alignItems: "center", justifyContent: "space-between",
    position: "sticky", top: 0, background: "#0a0a18", zIndex: 1,
  },
  title: { color: "#f9fafb", fontWeight: 800, fontSize: 17 },
  closeBtn: {
    background: "transparent", border: "1px solid #374151",
    borderRadius: 8, color: "#6b7280", fontSize: 13,
    padding: "4px 12px", cursor: "pointer",
  },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  nav: {
    width: 140, flexShrink: 0,
    borderRight: "1px solid #1f2937",
    padding: "12px 0",
    overflowY: "auto",
  },
  navBtn: (active) => ({
    display: "flex", alignItems: "center", gap: 8,
    width: "100%", padding: "8px 16px",
    background: active ? "rgba(99,102,241,0.15)" : "transparent",
    borderLeft: `3px solid ${active ? "#818cf8" : "transparent"}`,
    border: "none", borderRight: "none",
    color: active ? "#f9fafb" : "#6b7280",
    fontSize: 13, cursor: "pointer", textAlign: "left",
    transition: "all 0.12s",
  }),
  content: {
    flex: 1, padding: "20px 24px", overflowY: "auto",
  },
  intro: {
    fontSize: 14, color: "#9ca3af", lineHeight: 1.7,
    marginBottom: 20, padding: "12px 14px",
    background: "rgba(99,102,241,0.06)",
    borderRadius: 10, borderLeft: "3px solid #4f46e5",
  },
  group: { marginBottom: 20 },
  groupLabel: {
    fontSize: 11, color: "#4b5563",
    textTransform: "uppercase", letterSpacing: "0.08em",
    marginBottom: 8,
  },
  examples: { display: "flex", flexDirection: "column", gap: 6 },
  example: {
    display: "inline-block",
    padding: "5px 12px",
    background: "#0d0d1a",
    border: "1px solid #1f2937",
    borderRadius: 8,
    color: "#c4b5fd",
    fontSize: 13,
    fontFamily: "monospace",
    cursor: "pointer",
    transition: "border-color 0.12s, background 0.12s",
    maxWidth: "100%",
    overflowX: "auto",
    whiteSpace: "nowrap",
  },
  tip: {
    marginTop: 20,
    padding: "10px 14px",
    background: "rgba(34,197,94,0.05)",
    border: "1px solid rgba(34,197,94,0.15)",
    borderRadius: 8,
    fontSize: 12,
    color: "#6ee7b7",
    lineHeight: 1.6,
  },
};

/* ── component ──────────────────────────────────────────────────────────── */

export default function HelpPanel({ open, onClose, onNavigate, onQuery }) {
  const [active, setActive] = useState("chat");

  const section = SECTIONS.find(s => s.id === active) || SECTIONS[0];

  // Close on Escape; open on ? or Ctrl+/
  const handleKey = useCallback((e) => {
    if (!open) {
      if ((e.key === "?" && !["INPUT","TEXTAREA"].includes(e.target.tagName)) ||
          (e.key === "/" && e.ctrlKey)) {
        e.preventDefault();
        // Caller handles open, but we emit a custom event as fallback
        window.dispatchEvent(new CustomEvent("aletheia:help"));
      }
      return;
    }
    if (e.key === "Escape") onClose();
  }, [open, onClose]);

  useEffect(() => {
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [handleKey]);

  if (!open) return null;

  const handleExampleClick = (text) => {
    if (text.startsWith("python ") || text.startsWith("ollama ") || text.startsWith("pip ") || text.startsWith("POST ")) {
      navigator.clipboard?.writeText(text).catch(() => {});
      return;
    }
    if (onQuery) {
      onQuery(text);
      onClose();
    }
  };

  return (
    <>
      <style>{`@keyframes slideIn { from { transform: translateX(40px); opacity: 0; } to { transform: none; opacity: 1; } }`}</style>
      <div style={S.overlay} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
        <div style={S.panel} role="dialog" aria-label="Ayuda de Aletheia">

          {/* Header */}
          <div style={S.header}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: 20 }}>📖</span>
              <span style={S.title}>Cómo usar Aletheia</span>
              <span style={{ fontSize: 11, color: "#4b5563", marginLeft: 4 }}>Ctrl+/ para abrir · Esc para cerrar</span>
            </div>
            <button style={S.closeBtn} onClick={onClose} aria-label="Cerrar ayuda">✕ cerrar</button>
          </div>

          {/* Body */}
          <div style={S.body}>

            {/* Section nav */}
            <nav style={S.nav} aria-label="Secciones de ayuda">
              {SECTIONS.map(s => (
                <button
                  key={s.id}
                  style={S.navBtn(active === s.id)}
                  onClick={() => setActive(s.id)}
                  aria-current={active === s.id ? "page" : undefined}
                >
                  <span>{s.icon}</span>
                  <span>{s.label}</span>
                </button>
              ))}
            </nav>

            {/* Content */}
            <div style={S.content}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                <span style={{ fontSize: 22 }}>{section.icon}</span>
                <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: "#f9fafb" }}>{section.label}</h2>
              </div>

              <p style={S.intro}>{section.content.intro}</p>

              {section.content.items.map((item, i) => (
                <div key={i} style={S.group}>
                  <div style={S.groupLabel}>{item.label}</div>
                  <div style={S.examples}>
                    {item.examples.map((ex, j) => (
                      <span
                        key={j}
                        style={S.example}
                        onClick={() => handleExampleClick(ex)}
                        title={
                          ex.startsWith("python ") || ex.startsWith("ollama ") || ex.startsWith("POST ")
                            ? "Clic para copiar al portapapeles"
                            : "Clic para enviar al chat"
                        }
                        onMouseEnter={e => {
                          e.currentTarget.style.borderColor = "#4f46e5";
                          e.currentTarget.style.background = "rgba(79,70,229,0.08)";
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.borderColor = "#1f2937";
                          e.currentTarget.style.background = "#0d0d1a";
                        }}
                      >
                        {ex}
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              <div style={S.tip}>
                💡 {section.content.tip}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
