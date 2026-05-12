import { useState } from 'react';

const FIELD_META = {
  nombre:             { label: 'Nombre',          icon: '👤', type: 'text'   },
  edad:               { label: 'Edad',             icon: '🎂', type: 'number' },
  pais:               { label: 'País',             icon: '🌍', type: 'text'   },
  ciudad:             { label: 'Ciudad',           icon: '🏙️', type: 'text'   },
  ingresos_anuales:   { label: 'Ingresos/año (€)', icon: '💶', type: 'number' },
  ocupacion:          { label: 'Ocupación',        icon: '💼', type: 'text'   },
  situacion_familiar: { label: 'Situación fam.',   icon: '👨‍👩‍👧', type: 'text'   },
  ahorros:            { label: 'Ahorros (€)',      icon: '🏦', type: 'number' },
  gastos_mensuales:   { label: 'Gastos/mes (€)',   icon: '📊', type: 'number' },
};

function formatValue(key, val) {
  if (val === null || val === undefined) return null;
  if (key === 'edad') return `${val} años`;
  if (key === 'ingresos_anuales') return `${Number(val).toLocaleString('es-ES')} €/año`;
  if (key === 'ahorros') return `${Number(val).toLocaleString('es-ES')} €`;
  if (key === 'gastos_mensuales') return `${Number(val).toLocaleString('es-ES')} €/mes`;
  return String(val);
}

export default function ProfileCard({ profile, onUpdate }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});

  const knownFields = Object.entries(FIELD_META).filter(
    ([k]) => profile?.[k] !== null && profile?.[k] !== undefined
  );
  const emptyCount = Object.keys(FIELD_META).length - knownFields.length;

  const openEdit = () => {
    const initial = {};
    Object.keys(FIELD_META).forEach(k => { initial[k] = profile?.[k] ?? ''; });
    setForm(initial);
    setEditing(true);
  };

  const handleSave = () => {
    const updates = {};
    Object.entries(form).forEach(([k, v]) => {
      if (v !== '' && v !== null) {
        updates[k] = FIELD_META[k].type === 'number' ? Number(v) : v;
      } else {
        updates[k] = null;
      }
    });
    onUpdate(updates);
    setEditing(false);
  };

  return (
    <div style={{
      background: '#0d0d1a',
      border: '1px solid #1f2937',
      borderRadius: 16,
      padding: '1.25rem',
      marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>🧠</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#6b7280', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Perfil conocido
          </span>
          {emptyCount > 0 && (
            <span style={{
              fontSize: 11, color: '#f59e0b',
              background: 'rgba(245,158,11,0.1)',
              border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 20, padding: '1px 8px',
            }}>
              {emptyCount} campos vacíos
            </span>
          )}
        </div>
        <button
          onClick={openEdit}
          style={{
            background: 'transparent',
            border: '1px solid #374151',
            borderRadius: 8,
            color: '#9ca3af',
            fontSize: 12,
            padding: '4px 12px',
            cursor: 'pointer',
          }}
        >
          Editar
        </button>
      </div>

      {knownFields.length === 0 ? (
        <p style={{ color: '#4b5563', fontSize: 13, fontStyle: 'italic' }}>
          Sin datos aún — Aletheia aprende de tus preguntas automáticamente.
        </p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {knownFields.map(([k, meta]) => (
            <span
              key={k}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                background: 'rgba(99,102,241,0.1)',
                border: '1px solid rgba(99,102,241,0.25)',
                borderRadius: 20,
                padding: '4px 12px',
                fontSize: 12,
                color: '#a5b4fc',
              }}
            >
              <span>{meta.icon}</span>
              <span style={{ color: '#6b7280' }}>{meta.label}:</span>
              <span>{formatValue(k, profile[k])}</span>
            </span>
          ))}
        </div>
      )}

      {/* Edit modal */}
      {editing && (
        <div style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.75)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100,
        }}>
          <div style={{
            background: '#0d0d1a',
            border: '1px solid #374151',
            borderRadius: 20,
            padding: '2rem',
            width: '100%', maxWidth: 480,
            maxHeight: '85vh', overflowY: 'auto',
          }}>
            <h3 style={{ color: '#f9fafb', fontSize: 16, fontWeight: 700, marginBottom: 20 }}>
              Editar perfil
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {Object.entries(FIELD_META).map(([k, meta]) => (
                <div key={k}>
                  <label style={{ fontSize: 11, color: '#6b7280', letterSpacing: '0.08em', display: 'block', marginBottom: 4 }}>
                    {meta.icon} {meta.label}
                  </label>
                  <input
                    type={meta.type}
                    value={form[k] ?? ''}
                    onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                    placeholder={`${meta.label}...`}
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      background: '#060610',
                      border: '1px solid #374151',
                      borderRadius: 8,
                      color: '#f9fafb',
                      padding: '8px 12px',
                      fontSize: 14,
                      outline: 'none',
                    }}
                  />
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button
                onClick={handleSave}
                style={{
                  flex: 1, padding: '10px 0',
                  background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                  border: 'none', borderRadius: 10,
                  color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer',
                }}
              >
                Guardar
              </button>
              <button
                onClick={() => setEditing(false)}
                style={{
                  flex: 1, padding: '10px 0',
                  background: 'transparent',
                  border: '1px solid #374151',
                  borderRadius: 10,
                  color: '#9ca3af', fontSize: 14, cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
