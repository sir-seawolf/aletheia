import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000/simulate";

export default function App() {
  const [events, setEvents] = useState([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [wsStatus, setWsStatus] = useState("connecting");
  const [sessionId, setSessionId] = useState("");

  const wsUrl = useMemo(
    () => (sessionId ? `ws://localhost:8000/stream/${sessionId}` : ""),
    [sessionId]
  );

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setWsStatus("open");
    ws.onerror = () => setWsStatus("error");
    ws.onclose = () => setWsStatus("closed");

    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data);
        setEvents((prev) => [...prev, event]);
      } catch {
        // ignorar eventos malformados
      }
    };

    return () => ws.close();
  }, [wsUrl, sessionId]);

  const runSimulation = async () => {
    if (!question.trim()) return;

    const newSessionId =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    setSessionId(newSessionId);
    setEvents([]);
    setResult(null);
    setError("");

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: newSessionId,
          domain: "finanzas",
          question,
          memory: ["ahorros: 10000€", "gasto mensual: 1200€"],
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.detail ? JSON.stringify(data.detail) : "Error en /simulate");
        return;
      }

      setResult(data.final_output ?? data);
    } catch (e) {
      setError(`Fallo de red: ${e.message}`);
    }
  };

  const agents = ["explorer", "simulator", "guardian"];

  return (
    <div className="layout">
      <div className="header">🧠 Aletheia — Cognitive System</div>

      <div className="grid">
        <div className="agents">
          <h3>Agentes</h3>
          {agents.map((a) => (
            <div key={a} className="agent">
              {a.toUpperCase()}
            </div>
          ))}
          <div className="meta">
            <small>WS: {wsStatus}</small>
            <small>session: {sessionId || "—"}</small>
          </div>
        </div>

        <div className="stream">
          {events.length === 0 ? (
            <div className="empty">Sin eventos todavía…</div>
          ) : (
            events.map((e, i) => (
              <div key={i} className={`event ${e.agent || ""}`}>
                <b>{e.agent || "unknown"}</b> → {e.event_type || "event"}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bottom">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ej: ¿Puedo dejar mi trabajo en 9 meses?"
        />
        <button onClick={runSimulation}>Simular</button>

        {error && <div className="error">{error}</div>}

        {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
      </div>
    </div>
  );
}
