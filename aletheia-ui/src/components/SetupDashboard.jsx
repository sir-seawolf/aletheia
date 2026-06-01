/**
 * SetupDashboard — onboarding view showing all system connection statuses.
 * Gives the user a clear picture of what's connected and what needs configuring.
 */
import { useState, useEffect } from "react";

const STATUS_COLOR = {
  ok:      { dot: "#4ade80", bg: "rgba(74,222,128,0.08)",  border: "rgba(74,222,128,0.2)",  label: "Conectado" },
  partial: { dot: "#fbbf24", bg: "rgba(251,191,36,0.08)",  border: "rgba(251,191,36,0.2)",  label: "Parcial"   },
  missing: { dot: "#6b7280", bg: "rgba(107,114,128,0.06)", border: "rgba(107,114,128,0.15)", label: "Sin configurar" },
};

function SystemCard({ system, onNavigate }) {
  const s = STATUS_COLOR[system.status] || STATUS_COLOR.missing;
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: 14,
      padding: "14px 16px",
      background: s.bg,
      border: `1px solid ${s.border}`,
      borderRadius: 12,
      transition: "border-color 0.2s",
    }}>
      {/* Icon + status dot */}
      <div style={{ position: "relative", flexShrink: 0, fontSize: 22, lineHeight: 1 }}>
        {system.icon}
        <span style={{
          position: "absolute", bottom: -2, right: -4,
          width: 9, height: 9, borderRadius: "50%",
          background: s.dot,
          border: "1.5px solid #060610",
          display: "block",
        }} />
      </div>

      {/* Text */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#f9fafb" }}>{system.name}</span>
          {system.critical && (
            <span style={{ fontSize: 10, padding: "1px 6px", borderRadius: 10, background: "rgba(99,102,241,0.15)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.3)" }}>
              esencial
            </span>
          )}
        </div>
        <div style={{ fontSize: 12, color: "#6b7280", lineHeight: 1.4 }}>{system.detail}</div>
      </div>

      {/* Action */}
      {system.status !== "ok" && system.nav && (
        <button
          onClick={() => onNavigate(system.nav, system.section)}
          style={{
            flexShrink: 0,
            padding: "5px 12px",
            borderRadius: 8,
            background: "transparent",
            border: "1px solid #374151",
            color: "#9ca3af",
            fontSize: 12,
            cursor: "pointer",
            whiteSpace: "nowrap",
          }}
        >
          Configurar →
        </button>
      )}
      {system.status === "ok" && (
        <span style={{ flexShrink: 0, fontSize: 12, color: "#4ade80", fontWeight: 600 }}>✓</span>
      )}
    </div>
  );
}

function ProgressBar({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "#4ade80" : pct >= 50 ? "#fbbf24" : "#818cf8";
  return (
    <div style={{ marginBottom: 4 }}>
      <div style={{ height: 6, borderRadius: 3, background: "#1f2937", overflow: "hidden" }}>
        <div style={{
          height: "100%", width: `${pct}%`,
          background: color,
          borderRadius: 3,
          transition: "width 0.6s ease",
        }} />
      </div>
    </div>
  );
}

export default function SetupDashboard({ apiUrl, onNavigate }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    fetch(`${apiUrl}/api/setup/status`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, [apiUrl]);

  // Navigate to settings section
  const handleNavigate = (view, section) => {
    onNavigate(view);
    // Slight delay so SettingsPage mounts before trying to set section
    if (section) {
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent("aletheia:settings-section", { detail: section }));
      }, 80);
    }
  };

  const critical  = data?.systems.filter(s => s.critical)  || [];
  const optional  = data?.systems.filter(s => !s.critical) || [];
  const missing   = data ? data.missing + data.partial : 0;

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 6 }}>Configuración del sistema</h1>
        <p style={{ fontSize: 14, color: "#6b7280" }}>
          Estado de todos los sistemas que Aletheia puede usar. Configura los que necesites para activar cada capacidad.
        </p>
      </div>

      {/* Summary card */}
      {data && (
        <div style={{
          padding: "16px 20px",
          background: "#0d0d1a",
          border: "1px solid #1f2937",
          borderRadius: 14,
          marginBottom: 28,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 10 }}>
            <div>
              <span style={{ fontSize: 28, fontWeight: 800, color: "#f9fafb" }}>{data.connected}</span>
              <span style={{ fontSize: 16, color: "#6b7280" }}> / {data.total} sistemas conectados</span>
            </div>
            <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
              {data.connected > 0 && <span style={{ color: "#4ade80" }}>✓ {data.connected} activos</span>}
              {data.partial > 0  && <span style={{ color: "#fbbf24" }}>◑ {data.partial} parciales</span>}
              {data.missing > 0  && <span style={{ color: "#6b7280" }}>○ {data.missing} sin configurar</span>}
            </div>
          </div>
          <ProgressBar score={data.score} />
          {missing === 0 && (
            <div style={{ marginTop: 8, fontSize: 13, color: "#4ade80" }}>
              Todos los sistemas están conectados. Aletheia está lista al 100%.
            </div>
          )}
          {missing > 0 && (
            <div style={{ marginTop: 8, fontSize: 13, color: "#9ca3af" }}>
              {missing} sistema{missing > 1 ? "s" : ""} pendiente{missing > 1 ? "s" : ""} de configurar.
              Los sistemas sin configurar no bloquean el uso — solo limitan algunas capacidades.
            </div>
          )}
        </div>
      )}

      {loading && (
        <div style={{ color: "#6b7280", fontSize: 14, textAlign: "center", padding: "2rem 0" }}>
          Comprobando sistemas…
        </div>
      )}

      {/* Critical systems */}
      {critical.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
            Sistemas esenciales
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {critical.map(s => (
              <SystemCard key={s.id} system={s} onNavigate={handleNavigate} />
            ))}
          </div>
        </div>
      )}

      {/* Optional systems */}
      {optional.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
            Integraciones opcionales
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {optional.map(s => (
              <SystemCard key={s.id} system={s} onNavigate={handleNavigate} />
            ))}
          </div>
        </div>
      )}

      {/* Refresh */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          onClick={refresh}
          style={{
            padding: "6px 16px", borderRadius: 8,
            background: "transparent", border: "1px solid #374151",
            color: "#6b7280", fontSize: 13, cursor: "pointer",
          }}
        >
          Actualizar estado
        </button>
      </div>
    </div>
  );
}
