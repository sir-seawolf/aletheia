import { useEffect, useState } from "react";
import "./App.css";

import DashboardKPIs from './components/DashboardKPIs';
import DqsChart from './components/DqsChart';
import DecisionList from './components/DecisionList';
import DecisionResult from './components/DecisionResult';
import BrainLoader from './components/BrainLoader';
import ProfileCard from './components/ProfileCard';

const API_URL = "http://localhost:8000";

const DOMAINS = [
  { value: "finanzas",    label: "Finanzas" },
  { value: "carrera",     label: "Carrera" },
  { value: "tecnologia",  label: "Tecnologia" },
  { value: "salud",       label: "Salud" },
  { value: "relaciones",  label: "Relaciones" },
  { value: "objetivos",   label: "Objetivos" },
  { value: "aprendizaje", label: "Aprendizaje" },
  { value: "creatividad", label: "Creatividad" },
];

const NAV_STYLE = {
  background: '#080811',
  borderBottom: '1px solid #1f2937',
  padding: '0 2rem',
  display: 'flex',
  alignItems: 'center',
  gap: '2rem',
  height: 60,
};

const navBtnStyle = (active) => ({
  background: 'none',
  border: 'none',
  color: active ? '#818cf8' : '#6b7280',
  fontWeight: active ? 700 : 400,
  fontSize: 15,
  borderBottom: active ? '2px solid #818cf8' : '2px solid transparent',
  cursor: 'pointer',
  paddingBottom: 4,
  letterSpacing: '0.02em',
});

export default function App() {
  const [activeView, setActiveView]           = useState('simulate');
  const [metrics, setMetrics]                 = useState({});
  const [recentDecisions, setRecentDecisions] = useState([]);
  const [question, setQuestion]               = useState("");
  const [domain, setDomain]                   = useState("tecnologia");
  const [result, setResult]                   = useState(null);
  const [loading, setLoading]                 = useState(false);
  const [error, setError]                     = useState(null);
  const [profile, setProfile]                 = useState({});

  useEffect(() => {
    fetch(`${API_URL}/api/profile`).then(r => r.json()).then(setProfile).catch(() => {});
  }, []);

  useEffect(() => {
    if (activeView === 'dashboard') {
      fetch(`${API_URL}/system/metrics`)
        .then(res => res.json())
        .then(setMetrics)
        .catch(() => {});
      setRecentDecisions([]);
    }
  }, [activeView]);

  const handleProfileUpdate = (updates) => {
    fetch(`${API_URL}/api/profile`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    }).then(r => r.json()).then(setProfile).catch(() => {});
  };

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain, question }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setResult(data);
      if (data.user_profile) setProfile(data.user_profile);
    } catch (e) {
      setError(e.message || "Error al conectar con la API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#060610', color: '#f9fafb', fontFamily: 'system-ui, sans-serif' }}>
      {/* Nav */}
      <nav style={NAV_STYLE}>
        <span style={{ color: '#818cf8', fontWeight: 800, fontSize: 18, marginRight: 16, letterSpacing: '0.05em' }}>
          ALETHEIA
        </span>
        <button style={navBtnStyle(activeView === 'dashboard')} onClick={() => setActiveView('dashboard')}>
          Dashboard
        </button>
        <button style={navBtnStyle(activeView === 'simulate')} onClick={() => setActiveView('simulate')}>
          Nueva decision
        </button>
      </nav>

      <main style={{ maxWidth: 900, margin: '0 auto', padding: '2.5rem 1.5rem' }}>

        {/* Dashboard */}
        {activeView === 'dashboard' && (
          <div>
            <DashboardKPIs metrics={metrics} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
              <DqsChart data={[]} />
              <DecisionList decisions={recentDecisions} />
            </div>
          </div>
        )}

        {/* Simulate */}
        {activeView === 'simulate' && (
          <div>
            <ProfileCard profile={profile} onUpdate={handleProfileUpdate} />

            {!loading && !result && (
              <>
                <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 28, color: '#f9fafb' }}>
                  Nueva decision
                </h1>

                {/* Domain selector */}
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: 'block', fontSize: 12, color: '#9ca3af', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
                    Dominio
                  </label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {DOMAINS.map(d => (
                      <button
                        key={d.value}
                        onClick={() => setDomain(d.value)}
                        style={{
                          padding: '6px 16px',
                          borderRadius: 20,
                          border: `1px solid ${domain === d.value ? '#818cf8' : '#374151'}`,
                          background: domain === d.value ? 'rgba(129,140,248,0.15)' : 'transparent',
                          color: domain === d.value ? '#818cf8' : '#9ca3af',
                          fontSize: 13,
                          cursor: 'pointer',
                          fontWeight: domain === d.value ? 600 : 400,
                          transition: 'all 0.15s',
                        }}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Question textarea */}
                <textarea
                  style={{
                    width: '100%',
                    padding: '1rem 1.25rem',
                    background: '#0d0d1a',
                    border: '1px solid #374151',
                    borderRadius: 14,
                    color: '#f9fafb',
                    fontSize: 16,
                    resize: 'vertical',
                    marginBottom: 16,
                    outline: 'none',
                    boxSizing: 'border-box',
                    lineHeight: 1.6,
                  }}
                  rows="4"
                  placeholder="Describe tu decision... Ej: Deberia cambiar de trabajo? Tengo X en ahorros, gasto Y, oferta Z"
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  disabled={loading}
                />

                <button
                  onClick={runSimulation}
                  disabled={!question.trim() || loading}
                  style={{
                    width: '100%',
                    padding: '14px 0',
                    background: !question.trim() ? '#1f2937' : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                    color: !question.trim() ? '#6b7280' : '#fff',
                    border: 'none',
                    borderRadius: 14,
                    fontSize: 16,
                    fontWeight: 700,
                    cursor: !question.trim() ? 'not-allowed' : 'pointer',
                    letterSpacing: '0.04em',
                    transition: 'opacity 0.2s',
                  }}
                >
                  Analizar
                </button>
              </>
            )}

            {/* Brain loader during processing */}
            {loading && (
              <div style={{ textAlign: 'center', paddingTop: 20 }}>
                <h2 style={{ color: '#9ca3af', fontSize: 16, fontWeight: 400, marginBottom: 4 }}>
                  Procesando decision cognitiva...
                </h2>
                <p style={{ color: '#4b5563', fontSize: 13, marginBottom: 16 }}>
                  {question}
                </p>
                <BrainLoader domain={domain} />
              </div>
            )}

            {/* Error */}
            {error && (
              <div style={{
                marginTop: 16,
                padding: '1rem',
                background: 'rgba(127,29,29,0.3)',
                border: '1px solid rgba(239,68,68,0.4)',
                borderRadius: 12,
                color: '#f87171',
                fontSize: 14,
              }}>
                {error}
              </div>
            )}

            {/* Result */}
            {result && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                  <h2 style={{ color: '#9ca3af', fontSize: 14, fontWeight: 400, margin: 0 }}>
                    Analisis completado
                  </h2>
                  <button
                    onClick={() => { setResult(null); setError(null); }}
                    style={{
                      padding: '6px 16px',
                      background: 'transparent',
                      border: '1px solid #374151',
                      borderRadius: 8,
                      color: '#9ca3af',
                      fontSize: 13,
                      cursor: 'pointer',
                    }}
                  >
                    Nueva consulta
                  </button>
                </div>
                <DecisionResult report={result} />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
