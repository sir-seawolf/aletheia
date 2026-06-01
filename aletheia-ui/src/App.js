import { useEffect, useState, useCallback } from "react";
import "./App.css";

import DecisionResult   from './components/DecisionResult';
import BrainLoader      from './components/BrainLoader';
import DocBrowser       from './components/DocBrowser';
import SettingsPage     from './components/SettingsPage';
import ThinkingPanel    from './components/ThinkingPanel';
import ChatView         from './components/ChatView';
import Sidebar          from './components/Sidebar';
import CommandPalette      from './components/CommandPalette';
import HelpPanel           from './components/HelpPanel';
import CognitiveDashboard  from './components/CognitiveDashboard';
import SetupDashboard      from './components/SetupDashboard';
import UseCasesPage        from './components/UseCasesPage';
import ProjectsPage        from './components/ProjectsPage';

// Dynamic API URL — start.py writes REACT_APP_API_URL to .env.local before npm start
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

/* ── Navbar ─────────────────────────────────────────────────────────────── */

function StatusChip({ ok, label }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 20,
      background: ok ? "rgba(74,222,128,0.08)" : "rgba(107,114,128,0.08)",
      border: `1px solid ${ok ? "rgba(74,222,128,0.25)" : "rgba(107,114,128,0.2)"}`,
      fontSize: 11, color: ok ? "#4ade80" : "#6b7280",
    }}>
      <span style={{ fontSize: 8 }}>●</span> {label}
    </span>
  );
}

function FatigueChip({ fatigue }) {
  if (fatigue == null) return null;
  const pct   = Math.round(fatigue * 100);
  const color = fatigue > 0.7 ? "#f87171" : fatigue > 0.4 ? "#fbbf24" : "#4ade80";
  const bg    = fatigue > 0.7 ? "rgba(248,113,113,0.08)" : fatigue > 0.4 ? "rgba(251,191,36,0.08)" : "rgba(74,222,128,0.06)";
  const label = fatigue > 0.7 ? "fatiga alta" : fatigue > 0.4 ? "fatiga" : "fresca";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 20,
      background: bg,
      border: `1px solid ${color}44`,
      fontSize: 11, color,
    }}>
      <span style={{ fontSize: 8 }}>◈</span> {pct}% {label}
    </span>
  );
}

function Navbar({ status, onPalette, onHelp, panelOpen, onTogglePanel }) {
  return (
    <nav style={{
      height: 52,
      background: "#040408",
      borderBottom: "1px solid #1f2937",
      display: "flex",
      alignItems: "center",
      padding: "0 16px",
      gap: 12,
      position: "sticky", top: 0, zIndex: 40,
      flexShrink: 0,
    }}>
      {/* Logo */}
      <span style={{ color: "#818cf8", fontWeight: 800, fontSize: 16, letterSpacing: "0.1em", marginRight: 8, flexShrink: 0 }}>
        ALETHEIA
      </span>

      {/* Status chips */}
      <div style={{ display: "flex", gap: 6, flex: 1, flexWrap: "nowrap", overflow: "hidden" }}>
        <StatusChip
          ok={status.ollama_ok || (status.provider !== "ollama")}
          label={status.provider === "ollama" ? "LOCAL" : `CLOUD · ${status.provider || "?"}`}
        />
        <FatigueChip fatigue={status.fatigue ?? null} />
        {status.memory > 0 && (
          <span style={{ fontSize: 11, color: "#6b7280" }}>🧠 {status.memory}</span>
        )}
        {status.docs > 0 && (
          <span style={{ fontSize: 11, color: "#6b7280" }}>📄 {status.docs}</span>
        )}
        {status.fin_total > 0 && (
          <span style={{ fontSize: 11, color: "#6b7280" }}>💶 {status.fin_total.toFixed(0)}€</span>
        )}
      </div>

      {/* Right controls */}
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
        <button
          onClick={onHelp}
          style={{
            padding: "4px 10px", borderRadius: 8,
            background: "transparent",
            border: "1px solid #374151",
            color: "#6b7280", fontSize: 13, cursor: "pointer",
            fontWeight: 700, lineHeight: 1,
          }}
          title="Ayuda (Ctrl+/ o ?)"
          aria-label="Abrir ayuda"
        >
          ?
        </button>
        <button
          onClick={onPalette}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "4px 10px", borderRadius: 8,
            background: "rgba(99,102,241,0.1)",
            border: "1px solid rgba(99,102,241,0.25)",
            color: "#818cf8", fontSize: 12, cursor: "pointer",
          }}
          title="Paleta de comandos (Ctrl+K)"
        >
          ⌘K
        </button>
        <button
          onClick={onTogglePanel}
          style={{
            padding: "4px 10px", borderRadius: 8,
            background: panelOpen ? "rgba(99,102,241,0.15)" : "transparent",
            border: `1px solid ${panelOpen ? "rgba(99,102,241,0.4)" : "#374151"}`,
            color: panelOpen ? "#818cf8" : "#6b7280",
            fontSize: 11, cursor: "pointer",
          }}
          title="Panel de pensamiento"
        >
          mente {panelOpen ? "◀" : "▶"}
        </button>
      </div>
    </nav>
  );
}

/* ── Main App ────────────────────────────────────────────────────────────── */

export default function App() {
  const [activeView, setActiveView]   = useState("chat");
  const [domain, setDomain]           = useState("tecnologia");
  const [question, setQuestion]       = useState("");
  const [result, setResult]           = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [profile, setProfile]         = useState({});
  const [sessionId, setSessionId]     = useState(() => crypto.randomUUID());
  const [chatSessionId]               = useState(() => "chat-" + crypto.randomUUID());
  const [panelOpen, setPanelOpen]     = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);
  const [agentConf, setAgentConf]     = useState(0);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helpOpen, setHelpOpen]       = useState(false);
  const [recentQueries, setRecentQueries] = useState([]);
  const [status, setStatus]           = useState({ provider: "ollama", ollama_ok: false, docs: 0, memory: 0, fin_total: 0, fatigue: null });
  const [setupMissing, setSetupMissing] = useState(0);

  // Boot
  useEffect(() => {
    fetch(`${API_URL}/api/profile`).then(r => r.json()).then(setProfile).catch(() => {});
    refreshStatus();
    const t = setInterval(refreshStatus, 30_000);

    const handleNav = (e) => setActiveView(e.detail);
    window.addEventListener("aletheia:nav", handleNav);

    const handlePalette = () => setPaletteOpen(true);
    window.addEventListener("aletheia:palette", handlePalette);

    const handleHelp = () => setHelpOpen(true);
    window.addEventListener("aletheia:help", handleHelp);

    return () => {
      clearInterval(t);
      window.removeEventListener("aletheia:nav", handleNav);
      window.removeEventListener("aletheia:palette", handlePalette);
      window.removeEventListener("aletheia:help", handleHelp);
    };
  }, []);

  const refreshStatus = () => {
    fetch(`${API_URL}/api/status`).then(r => r.json()).then(setStatus).catch(() => {});
    fetch(`${API_URL}/api/setup/status`).then(r => r.json()).then(d => {
      setSetupMissing(d.missing + d.partial);
    }).catch(() => {});
  };

  const handleProfileUpdate = (updates) => {
    fetch(`${API_URL}/api/profile`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    }).then(r => r.json()).then(setProfile).catch(() => {});
  };

  const runSimulation = useCallback(async (overrideQuestion) => {
    const q = (overrideQuestion || question).trim();
    if (!q) return;
    const sid = crypto.randomUUID();
    setSessionId(sid);
    setActiveAgent("explorer");
    setAgentConf(0);
    setLoading(true);
    setError(null);
    setResult(null);
    setActiveView("simulate");
    setRecentQueries(prev => [q, ...prev.filter(x => x !== q)].slice(0, 10));
    try {
      const res = await fetch(`${API_URL}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain, question: q, session_id: sid }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
      if (data.user_profile) setProfile(data.user_profile);
      refreshStatus();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setActiveAgent(null);
    }
  }, [question, domain]);

  // Command palette handlers
  const handlePaletteNavigate = (view) => setActiveView(view);
  const handlePaletteQuery    = (q)    => {
    setQuestion(q);
    if (q.length > 8) runSimulation(q);
    else setActiveView("chat");
  };
  const handlePaletteAction   = (action, payload) => {
    if (action === "open_palette") { setPaletteOpen(true); return; }
    if (action === "voice")        { setActiveView("simulate"); }
    if (action === "web_search")   { setActiveView("docs"); }
    if (action === "domain")       { setDomain(payload); }
  };

  /* ── Render ──────────────────────────────────────────────────────────── */
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#060610", color: "#f9fafb", fontFamily: "system-ui, sans-serif" }}>

      {/* Navbar */}
      <Navbar
        status={status}
        onPalette={() => setPaletteOpen(true)}
        onHelp={() => setHelpOpen(true)}
        panelOpen={panelOpen}
        onTogglePanel={() => setPanelOpen(o => !o)}
      />

      {/* Body — sidebar + main + thinking panel */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* Sidebar */}
        <Sidebar
          activeView={activeView}
          onNavigate={(view) => {
            if (view === "help") { setHelpOpen(true); return; }
            setActiveView(view);
          }}
          domain={domain}
          onDomain={setDomain}
          status={status}
          apiUrl={API_URL}
          setupMissing={setupMissing}
        />

        {/* Main content — margin-right tracks the ThinkingPanel width so it never overlaps */}
        <main style={{ flex: 1, overflowY: "auto", padding: "1.5rem 2rem", marginRight: panelOpen ? 300 : 40 }}>

          {/* CHAT */}
          {activeView === "chat" && (
            <ChatView
              apiUrl={API_URL}
              sessionId={chatSessionId}
              domain={domain}
              onDecisionRequest={(q) => { setQuestion(q); runSimulation(q); }}
            />
          )}

          {/* SIMULATE */}
          {activeView === "simulate" && (
            <div>
              {!loading && !result && (
                <>
                  <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 20 }}>Análisis cognitivo</h1>
                  <textarea
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) runSimulation(); }}
                    placeholder="Describe tu decisión… (Ctrl+Enter para analizar)"
                    rows={4}
                    style={{
                      width: "100%", padding: "1rem", boxSizing: "border-box",
                      background: "#0d0d1a", border: "1px solid #374151",
                      borderRadius: 12, color: "#f9fafb", fontSize: 15,
                      resize: "vertical", outline: "none", lineHeight: 1.6,
                    }}
                  />
                  <button
                    onClick={() => runSimulation()}
                    disabled={!question.trim()}
                    style={{
                      marginTop: 10, width: "100%", padding: "12px 0",
                      background: question.trim() ? "linear-gradient(135deg,#4f46e5,#7c3aed)" : "#1f2937",
                      color: question.trim() ? "#fff" : "#4b5563",
                      border: "none", borderRadius: 12,
                      fontSize: 15, fontWeight: 700, cursor: question.trim() ? "pointer" : "not-allowed",
                    }}
                  >
                    Analizar
                  </button>
                </>
              )}

              {loading && (
                <div style={{ textAlign: "center", paddingTop: 20 }}>
                  <p style={{ color: "#4b5563", fontSize: 13, fontStyle: "italic", marginBottom: 8 }}>"{question}"</p>
                  <BrainLoader domain={domain} activeAgent={activeAgent} agentConfidence={agentConf} />
                </div>
              )}

              {error && (
                <div style={{ marginTop: 16, padding: "1rem", background: "rgba(127,29,29,0.3)", border: "1px solid rgba(239,68,68,0.4)", borderRadius: 12, color: "#f87171", fontSize: 14 }}>
                  {error}
                </div>
              )}

              {result && (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                    <span style={{ color: "#6b7280", fontSize: 13 }}>Análisis completado</span>
                    <button
                      onClick={() => { setResult(null); setError(null); setQuestion(""); }}
                      style={{ padding: "5px 14px", background: "transparent", border: "1px solid #374151", borderRadius: 8, color: "#9ca3af", fontSize: 12, cursor: "pointer" }}
                    >
                      Nueva consulta
                    </button>
                  </div>
                  <DecisionResult report={result} />
                </div>
              )}
            </div>
          )}

          {/* PROJECTS */}
          {activeView === "projects" && (
            <ProjectsPage apiUrl={API_URL} />
          )}

          {/* DOCS */}
          {activeView === "docs" && (
            <DocBrowser
              apiUrl={API_URL}
              domain={domain}
              onResult={(r) => { setResult(r); setActiveView("simulate"); }}
            />
          )}

          {/* COGNITIVE */}
          {activeView === "cognitive" && (
            <CognitiveDashboard
              apiUrl={API_URL}
              domain={domain}
              sessionId={chatSessionId}
            />
          )}

          {/* SETUP */}
          {activeView === "setup" && (
            <SetupDashboard
              apiUrl={API_URL}
              onNavigate={(view) => setActiveView(view)}
            />
          )}

          {/* USE CASES */}
          {activeView === "usecases" && (
            <UseCasesPage
              apiUrl={API_URL}
              onNavigate={(view) => setActiveView(view)}
              onQuery={(q) => {
                setActiveView("chat");
                setTimeout(() => {
                  window.dispatchEvent(new CustomEvent("aletheia:prefill", { detail: q }));
                }, 80);
              }}
            />
          )}

          {/* SETTINGS */}
          {activeView === "settings" && (
            <SettingsPage
              apiUrl={API_URL}
              profile={profile}
              onProfileUpdate={handleProfileUpdate}
            />
          )}
        </main>

        {/* Thinking Panel
            sessionId    — simulation WebSocket (changes per run)
            cogSessionId — stable chat session (for cognitive state polling) */}
        <ThinkingPanel
          sessionId={sessionId}
          cogSessionId={chatSessionId}
          apiUrl={API_URL}
          domain={domain}
          open={panelOpen}
          onToggle={() => setPanelOpen(o => !o)}
          onAgentChange={(agent, conf) => { setActiveAgent(agent); setAgentConf(conf); }}
        />
      </div>

      {/* Command Palette */}
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigate={handlePaletteNavigate}
        onQuery={handlePaletteQuery}
        onAction={handlePaletteAction}
        recentQueries={recentQueries}
      />

      {/* Help Panel */}
      <HelpPanel
        open={helpOpen}
        onClose={() => setHelpOpen(false)}
        onNavigate={(view) => { setActiveView(view); setHelpOpen(false); }}
        onQuery={(q) => { handlePaletteQuery(q); setHelpOpen(false); }}
      />
    </div>
  );
}
