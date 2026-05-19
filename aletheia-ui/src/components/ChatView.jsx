/**
 * ChatView — multi-turn conversational interface.
 *
 * Props:
 *   apiUrl: string
 *   sessionId: string
 *   domain: string
 *   onDecisionRequest(question): void  — escalates to full pipeline
 */
import { useState, useEffect, useRef } from "react";
import VoiceInput from "./VoiceInput";

const ROLE_STYLE = {
  user: {
    align: "flex-end",
    bg:    "rgba(99,102,241,0.18)",
    border:"1px solid rgba(99,102,241,0.35)",
    color: "#e0e7ff",
  },
  assistant: {
    align: "flex-start",
    bg:    "#0d0d1a",
    border:"1px solid #1f2937",
    color: "#f9fafb",
  },
};

const AGENT_CHIP = {
  kronos: {
    label: "KRONOS",
    color: "#a78bfa",
    bg:    "rgba(167,139,250,0.12)",
    border:"1px solid rgba(167,139,250,0.3)",
  },
  aletheia: {
    label: "Aletheia",
    color: "#60a5fa",
    bg:    "rgba(96,165,250,0.10)",
    border:"1px solid rgba(96,165,250,0.25)",
  },
};

function AgentChip({ agent }) {
  const chip = AGENT_CHIP[agent] || AGENT_CHIP.aletheia;
  return (
    <span style={{
      display: "inline-block",
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      color: chip.color,
      background: chip.bg,
      border: chip.border,
      borderRadius: 6,
      padding: "1px 6px",
      marginBottom: 5,
    }}>
      {chip.label}
    </span>
  );
}

function Bubble({ turn }) {
  const style = ROLE_STYLE[turn.role] || ROLE_STYLE.assistant;
  const showChip = turn.role === "assistant" && turn.agent;
  return (
    <div style={{ display: "flex", justifyContent: style.align, marginBottom: 10 }}>
      <div style={{
        maxWidth: "78%",
        background: style.bg,
        border: style.border,
        borderRadius: turn.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        padding: "10px 14px",
        fontSize: 14,
        color: style.color,
        lineHeight: 1.55,
        position: "relative",
      }}>
        {showChip && <div><AgentChip agent={turn.agent} /></div>}
        {turn.action && turn.action !== "kronos" && (
          <div style={{ fontSize: 10, color: "#818cf8", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            ⚡ {turn.action.replace("_", " ")}
          </div>
        )}
        {turn.content}
        <div style={{ fontSize: 9, color: "#4b5563", marginTop: 4, textAlign: "right" }}>
          {turn.ts ? new Date(turn.ts).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }) : ""}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 10 }}>
      <div style={{
        background: "#0d0d1a", border: "1px solid #1f2937",
        borderRadius: "18px 18px 18px 4px",
        padding: "10px 16px", display: "flex", gap: 5, alignItems: "center",
      }}>
        {[0, 0.2, 0.4].map((delay, i) => (
          <div key={i} style={{
            width: 6, height: 6, borderRadius: "50%", background: "#818cf8",
            animation: "bounce 1s infinite",
            animationDelay: `${delay}s`,
          }} />
        ))}
      </div>
    </div>
  );
}

export default function ChatView({ apiUrl = "http://localhost:8000", sessionId, domain = "general", onDecisionRequest }) {
  const [history, setHistory]     = useState([]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [inputMode, setInputMode] = useState("text");
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    // Load existing history on mount
    fetch(`${apiUrl}/api/chat/${sessionId}/history`)
      .then(r => r.json())
      .then(d => { if (d.history?.length) setHistory(d.history); })
      .catch(() => {});
  }, [sessionId, apiUrl]);

  useEffect(() => {
    const handler = (e) => {
      const prompt = e.detail;
      if (prompt) send(prompt);
    };
    window.addEventListener("aletheia:prefill", handler);
    return () => window.removeEventListener("aletheia:prefill", handler);
  }, [loading]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setHistory(h => [...h, { role: "user", content: msg, ts: new Date().toISOString() }]);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId, domain }),
      });
      const data = await res.json();

      setHistory(h => [...h, {
        role:    "assistant",
        content: data.reply || "…",
        ts:      new Date().toISOString(),
        action:  data.action || null,
        agent:   data.agent || "aletheia",
      }]);

      // If the reply suggests a deep analysis, offer to escalate
      if (data.reply?.toLowerCase().includes("análisis de decisión") && onDecisionRequest) {
        onDecisionRequest(msg);
      }
    } catch {
      setHistory(h => [...h, {
        role: "assistant",
        content: "Error de conexión. Comprueba que el servidor está activo.",
        ts: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const clearChat = async () => {
    await fetch(`${apiUrl}/api/chat/${sessionId}`, { method: "DELETE" }).catch(() => {});
    setHistory([]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)", maxHeight: 700 }}>
      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
      `}</style>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>Chat</h1>
          <div style={{ fontSize: 12, color: "#6b7280" }}>Dominio: {domain}</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {/* Input mode toggle */}
          {["text","voice"].map(m => (
            <button key={m} onClick={() => setInputMode(m)} style={{
              padding: "4px 12px", borderRadius: 20,
              border: `1px solid ${inputMode === m ? "#818cf8" : "#374151"}`,
              background: inputMode === m ? "rgba(129,140,248,0.15)" : "transparent",
              color: inputMode === m ? "#818cf8" : "#6b7280",
              fontSize: 12, cursor: "pointer",
            }}>
              {m === "text" ? "⌨ Texto" : "🎙 Voz"}
            </button>
          ))}
          {history.length > 0 && (
            <button onClick={clearChat} style={{
              padding: "4px 12px", border: "1px solid #374151",
              borderRadius: 20, background: "transparent",
              color: "#6b7280", fontSize: 12, cursor: "pointer",
            }}>
              Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "8px 0",
        scrollbarWidth: "thin", scrollbarColor: "#1f2937 transparent",
      }}>
        {history.length === 0 && !loading && (
          <div style={{ textAlign: "center", color: "#374151", paddingTop: 60 }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🧠</div>
            <div style={{ fontSize: 15, color: "#6b7280" }}>
              Hola. Puedes preguntarme lo que necesites,<br />pedirme que importe tus facturas o analice una decisión.
            </div>
          </div>
        )}
        {history.map((turn, i) => <Bubble key={i} turn={turn} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div style={{
        borderTop: "1px solid #1f2937", paddingTop: 12, marginTop: 4,
      }}>
        {inputMode === "text" ? (
          <div style={{ display: "flex", gap: 8 }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder="Escribe un mensaje… (Enter para enviar, Shift+Enter para nueva línea)"
              rows={2}
              disabled={loading}
              style={{
                flex: 1, padding: "10px 14px",
                background: "#0d0d1a", border: "1px solid #374151",
                borderRadius: 14, color: "#f9fafb",
                fontSize: 14, resize: "none", outline: "none", lineHeight: 1.5,
              }}
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || loading}
              style={{
                padding: "0 20px", alignSelf: "stretch",
                background: input.trim() && !loading
                  ? "linear-gradient(135deg,#4f46e5,#7c3aed)"
                  : "#1f2937",
                border: "none", borderRadius: 14,
                color: input.trim() && !loading ? "#fff" : "#4b5563",
                fontWeight: 700, fontSize: 14, cursor: input.trim() ? "pointer" : "not-allowed",
              }}
            >
              →
            </button>
          </div>
        ) : (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center",
            padding: "12px", background: "#0d0d1a",
            border: "1px solid #374151", borderRadius: 14, gap: 8,
          }}>
            <VoiceInput
              onTranscript={text => { setInput(text); send(text); }}
              disabled={loading}
              apiUrl={apiUrl}
            />
            {input && <div style={{ fontSize: 12, color: "#6b7280", fontStyle: "italic" }}>"{input}"</div>}
          </div>
        )}
      </div>
    </div>
  );
}
