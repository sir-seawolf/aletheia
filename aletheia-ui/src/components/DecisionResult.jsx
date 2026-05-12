import React from 'react';

function cleanText(text) {
  if (!text || typeof text !== 'string') return '';
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/^#+\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function AgentCard({ icon, title, colorKey, status, children }) {
  const palettes = {
    blue:   { border: '#3b82f6', glow: 'rgba(59,130,246,0.15)', label: '#60a5fa', bg: 'rgba(30,58,138,0.2)' },
    purple: { border: '#a855f7', glow: 'rgba(168,85,247,0.15)', label: '#c084fc', bg: 'rgba(88,28,135,0.2)' },
    green:  { border: '#22c55e', glow: 'rgba(34,197,94,0.15)',  label: '#4ade80', bg: 'rgba(20,83,45,0.2)'  },
    red:    { border: '#ef4444', glow: 'rgba(239,68,68,0.15)',  label: '#f87171', bg: 'rgba(127,29,29,0.2)' },
  };
  const p = palettes[colorKey] || palettes.blue;
  return (
    <div style={{
      borderRadius: 16,
      border: `1px solid ${p.border}`,
      background: `#0d0d1a`,
      boxShadow: `0 0 24px ${p.glow}`,
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <span style={{ color: p.label, fontWeight: 700, letterSpacing: '0.1em', fontSize: 13, textTransform: 'uppercase' }}>{title}</span>
        {status && <span style={{ marginLeft: 'auto', fontSize: 11, color: '#6b7280' }}>{status}</span>}
      </div>
      <div style={{ color: '#d1d5db', fontSize: 13, lineHeight: 1.6 }}>{children}</div>
    </div>
  );
}

function FactList({ items, accent }) {
  if (!items?.length) return <span style={{ color: '#4b5563', fontStyle: 'italic' }}>Sin datos</span>;
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
      {items.slice(0, 5).map((f, i) => (
        <li key={i} style={{ display: 'flex', gap: 8 }}>
          <span style={{ color: accent, flexShrink: 0 }}>▸</span>
          <span>{typeof f === 'string' ? f : JSON.stringify(f)}</span>
        </li>
      ))}
    </ul>
  );
}

export default function DecisionResult({ report }) {
  if (!report) return null;

  const insight = typeof report.llm_insight === 'string'
    ? report.llm_insight
    : report.llm_insight?.insight || '';

  const facts     = report.facts     || [];
  const gaps      = report.gaps      || [];
  const scenarios = report.scenarios || [];
  const risks     = report.risks     || [];
  const guardianOk = !report.guardian_block;
  const issues     = report.guardian_trace?.rules_triggered || [];

  const dqs = report.dqs;
  const dqsColor = dqs >= 0.7 ? '#4ade80' : dqs >= 0.4 ? '#facc15' : '#f87171';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{
        background: '#0d0d1a',
        border: '1px solid #1f2937',
        borderRadius: 16,
        padding: '1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 16,
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#6b7280', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 6 }}>
            {report.domain}
          </div>
          <h2 style={{ color: '#f9fafb', fontSize: 20, fontWeight: 700, margin: 0 }}>{report.question}</h2>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 32, fontWeight: 800, color: dqsColor, lineHeight: 1 }}>
            {dqs != null ? (dqs * 100).toFixed(0) + '%' : 'N/A'}
          </div>
          <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>DQS</div>
        </div>
      </div>

      {/* 3 Agent Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>

        {/* Explorer */}
        <AgentCard
          icon="🔍" title="Explorador" colorKey="blue"
          status={`${((report.exploration_confidence || 0) * 100).toFixed(0)}% confianza`}
        >
          <FactList items={facts} accent="#60a5fa" />
          {gaps.length > 0 && (
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(59,130,246,0.2)' }}>
              <div style={{ fontSize: 11, color: '#60a5fa', marginBottom: 4, letterSpacing: '0.1em' }}>GAPS</div>
              {gaps.slice(0, 2).map((g, i) => (
                <div key={i} style={{ color: '#9ca3af', fontSize: 12 }}>
                  — {typeof g === 'string' ? g : JSON.stringify(g)}
                </div>
              ))}
            </div>
          )}
        </AgentCard>

        {/* Simulator */}
        <AgentCard
          icon="🎲" title="Simulador" colorKey="purple"
          status={`${scenarios.length} escenarios`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {scenarios.length === 0 && <span style={{ color: '#4b5563', fontStyle: 'italic' }}>Sin escenarios</span>}
            {scenarios.slice(0, 3).map((s, i) => (
              <div key={i} style={{
                padding: '8px 10px',
                borderRadius: 10,
                background: 'rgba(88,28,135,0.25)',
                border: '1px solid rgba(168,85,247,0.2)',
              }}>
                <div style={{ fontWeight: 600, color: '#e9d5ff', fontSize: 12 }}>
                  {s.description || s.name || `Escenario ${i + 1}`}
                </div>
                {s.outcome && <div style={{ color: '#9ca3af', fontSize: 11, marginTop: 2 }}>{s.outcome}</div>}
                {s.probability != null && (
                  <div style={{ marginTop: 6, height: 3, borderRadius: 9, background: 'rgba(88,28,135,0.5)' }}>
                    <div style={{ height: 3, borderRadius: 9, background: '#a855f7', width: `${(s.probability * 100).toFixed(0)}%` }} />
                  </div>
                )}
              </div>
            ))}
          </div>
          {risks.length > 0 && (
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(168,85,247,0.2)' }}>
              <div style={{ fontSize: 11, color: '#c084fc', marginBottom: 4, letterSpacing: '0.1em' }}>RIESGOS</div>
              {risks.slice(0, 3).map((r, i) => (
                <div key={i} style={{ color: '#9ca3af', fontSize: 12 }}>
                  • {typeof r === 'string' ? r : r.description || JSON.stringify(r)}
                </div>
              ))}
            </div>
          )}
        </AgentCard>

        {/* Guardian */}
        <AgentCard
          icon="🛡️" title="Guardián" colorKey={guardianOk ? 'green' : 'red'}
          status={report.guardian_severity}
        >
          <div style={{
            textAlign: 'center',
            padding: '12px 0',
            borderRadius: 10,
            fontWeight: 800,
            fontSize: 16,
            color: guardianOk ? '#4ade80' : '#f87171',
            background: guardianOk ? 'rgba(20,83,45,0.3)' : 'rgba(127,29,29,0.3)',
            border: `1px solid ${guardianOk ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
          }}>
            {guardianOk ? '✓ VALIDADO' : '⚠ BLOQUEADO'}
          </div>
          {report.guardian_recommendation && (
            <p style={{ textAlign: 'center', color: '#9ca3af', fontSize: 12, margin: '4px 0 0' }}>
              {report.guardian_recommendation}
            </p>
          )}
          {issues.length > 0 && (
            <ul style={{ margin: '8px 0 0', padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 4 }}>
              {issues.map((issue, i) => (
                <li key={i} style={{ color: '#f87171', fontSize: 11, display: 'flex', gap: 6 }}>
                  <span>!</span><span>{issue}</span>
                </li>
              ))}
            </ul>
          )}
          {report.guardian_confidence_adjust != null && (
            <div style={{ textAlign: 'center', color: '#6b7280', fontSize: 11, marginTop: 8 }}>
              Ajuste confianza: {(report.guardian_confidence_adjust * 100).toFixed(0)}%
            </div>
          )}
        </AgentCard>
      </div>

      {/* LLM Insight */}
      {insight && (
        <div style={{
          background: '#0d0d1a',
          border: '1px solid #1f2937',
          borderRadius: 16,
          padding: '1.5rem',
        }}>
          <div style={{ fontSize: 11, color: '#6b7280', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 12 }}>
            Análisis Cognitivo
          </div>
          <p style={{ color: '#e5e7eb', lineHeight: 1.75, whiteSpace: 'pre-wrap', fontSize: 14, margin: 0 }}>
            {cleanText(insight)}
          </p>
        </div>
      )}
    </div>
  );
}
