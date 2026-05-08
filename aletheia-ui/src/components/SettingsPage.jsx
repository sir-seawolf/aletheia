/**
 * SettingsPage — Perfil · LLM · Google Drive · OneDrive · Gmail · Carpetas · Voz
 */
import { useState, useEffect, useRef } from "react";

const SECTION = {
  background: "#0d0d1a",
  border: "1px solid #1f2937",
  borderRadius: 14,
  padding: "1.5rem",
  marginBottom: 16,
};

const LABEL = {
  fontSize: 11,
  color: "#6b7280",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  display: "block",
  marginBottom: 5,
};

const INPUT = {
  width: "100%",
  boxSizing: "border-box",
  background: "#060610",
  border: "1px solid #374151",
  borderRadius: 8,
  color: "#f9fafb",
  padding: "8px 12px",
  fontSize: 14,
  outline: "none",
};

const BTN_PRIMARY = {
  padding: "8px 20px",
  background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
  border: "none",
  borderRadius: 8,
  color: "#fff",
  fontWeight: 600,
  fontSize: 13,
  cursor: "pointer",
};

const BTN_GHOST = {
  padding: "7px 16px",
  background: "transparent",
  border: "1px solid #374151",
  borderRadius: 8,
  color: "#9ca3af",
  fontSize: 13,
  cursor: "pointer",
};

const Badge = ({ ok, trueLabel = "Configurado", falseLabel = "No configurado" }) => (
  <span style={{
    fontSize: 11,
    padding: "2px 10px",
    borderRadius: 20,
    background: ok ? "rgba(74,222,128,0.1)" : "rgba(107,114,128,0.1)",
    border: `1px solid ${ok ? "rgba(74,222,128,0.3)" : "rgba(107,114,128,0.2)"}`,
    color: ok ? "#4ade80" : "#6b7280",
  }}>
    {ok ? `✓ ${trueLabel}` : falseLabel}
  </span>
);

const PROFILE_META = {
  nombre:             { label: "Nombre",           type: "text" },
  edad:               { label: "Edad",              type: "number" },
  pais:               { label: "País",              type: "text" },
  ciudad:             { label: "Ciudad",            type: "text" },
  ingresos_anuales:   { label: "Ingresos/año (€)",  type: "number" },
  ocupacion:          { label: "Ocupación",         type: "text" },
  situacion_familiar: { label: "Situación familiar",type: "text" },
  ahorros:            { label: "Ahorros (€)",       type: "number" },
  gastos_mensuales:   { label: "Gastos/mes (€)",    type: "number" },
};

const LLM_PROVIDERS = [
  { value: "ollama",   label: "Ollama (local)",      needsKey: false },
  { value: "claude",   label: "Claude (Anthropic)",  needsKey: true  },
  { value: "openai",   label: "OpenAI / GPT",        needsKey: true  },
  { value: "deepseek", label: "DeepSeek (gratis)",   needsKey: true  },
  { value: "groq",     label: "Groq (gratis, rápido)", needsKey: true },
  { value: "mistral",  label: "Mistral AI",          needsKey: true  },
];

const LLM_MODELS = {
  ollama:   ["llama3.2:3b", "llama3.1:8b", "mistral:7b", "gemma3:4b"],
  claude:   ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-7"],
  openai:   ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
  deepseek: ["deepseek-chat", "deepseek-reasoner"],
  groq:     ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
  mistral:  ["mistral-small-latest", "mistral-medium-latest", "open-mixtral-8x7b"],
};

const PROVIDER_LINKS = {
  claude:   "https://console.anthropic.com/",
  openai:   "https://platform.openai.com/api-keys",
  deepseek: "https://platform.deepseek.com/",
  groq:     "https://console.groq.com/keys",
  mistral:  "https://console.mistral.ai/",
};

const PIPER_MODELS = [
  "es_ES-davefx-medium",
  "es_ES-sharvard-medium",
  "es_MX-claude-high",
];

function GmailScanner({ apiUrl }) {
  const currentYear = new Date().getFullYear();
  const [year, setYear]         = useState(currentYear);
  const [scanning, setScanning] = useState(false);
  const [result, setResult]     = useState(null);
  const [status, setStatus]     = useState(null);

  useEffect(() => {
    fetch(`${apiUrl}/api/gmail/status`)
      .then(r => r.json())
      .then(setStatus)
      .catch(() => {});
  }, [apiUrl]);

  const scan = async () => {
    setScanning(true);
    setResult(null);
    try {
      const r = await fetch(`${apiUrl}/api/gmail/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year }),
      });
      const d = await r.json();
      setResult(d);
      // Re-check status after scan (token may now exist)
      fetch(`${apiUrl}/api/gmail/status`).then(r => r.json()).then(setStatus).catch(() => {});
    } catch (e) {
      setResult({ error: e.message });
    } finally {
      setScanning(false);
    }
  };

  return (
    <div style={{ background: "#060610", borderRadius: 10, padding: "1rem", border: "1px solid #374151" }}>
      {/* Status panel */}
      {status && (
        <div style={{ marginBottom: 12, padding: "8px 12px", borderRadius: 8, background: status.setup_needed ? "rgba(239,68,68,0.08)" : "rgba(74,222,128,0.08)", border: `1px solid ${status.setup_needed ? "rgba(239,68,68,0.2)" : "rgba(74,222,128,0.2)"}`, fontSize: 12 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ color: status.setup_needed ? "#f87171" : "#4ade80" }}>
              {status.setup_needed ? "⚠" : "✓"}
            </span>
            <span style={{ color: "#9ca3af" }}>{status.hint}</span>
          </div>
          {!status.libs_ok && (
            <div style={{ marginTop: 6, fontFamily: "monospace", color: "#818cf8", fontSize: 11, background: "#0d0d1a", padding: "4px 8px", borderRadius: 4 }}>
              pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
            </div>
          )}
          {status.has_token && (
            <div style={{ marginTop: 4, color: "#6b7280" }}>Token OAuth guardado — no necesitas autorizar de nuevo</div>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
        <div>
          <label style={{ ...LABEL, marginBottom: 4 }}>Ejercicio fiscal</label>
          <select
            value={year}
            onChange={e => setYear(Number(e.target.value))}
            style={{ ...INPUT, width: 120 }}
          >
            {[currentYear, currentYear - 1, currentYear - 2, currentYear - 3].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <button
          style={{ ...BTN_PRIMARY, marginTop: 18 }}
          onClick={scan}
          disabled={scanning}
        >
          {scanning ? "Escaneando…" : "Escanear correo"}
        </button>
      </div>

      {result && !result.error && (
        <div style={{ fontSize: 13 }}>
          <div style={{ color: "#9ca3af", marginBottom: 6 }}>
            {result.emails_found} correos encontrados · {result.processed} procesados
          </div>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 8 }}>
            {[["new", "Nuevos", "#4ade80"], ["updated", "Actualizados", "#818cf8"], ["duplicate", "Ya existían", "#6b7280"]].map(([k, lbl, color]) => (
              result[k] > 0 && (
                <span key={k} style={{ fontSize: 12, color }}>
                  {result[k]} {lbl}
                </span>
              )
            ))}
          </div>
          {result.invoices?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Facturas detectadas ({result.invoices.length})
              </div>
              <div style={{ maxHeight: 180, overflowY: "auto" }}>
                {result.invoices.slice(0, 20).map((inv, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #1f2937", fontSize: 12 }}>
                    <span style={{ color: "#9ca3af", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {inv.filename || inv.vendor || "—"}
                    </span>
                    <span style={{ color: "#4b5563", marginLeft: 8 }}>{inv.date?.slice(0, 10)}</span>
                    <span style={{ color: "#f9fafb", marginLeft: 12, fontVariantNumeric: "tabular-nums" }}>
                      {inv.amount?.toFixed(2)} {inv.currency}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {result.errors?.length > 0 && (
            <div style={{ color: "#f87171", fontSize: 11, marginTop: 6 }}>
              {result.errors.length} errores — ver consola para detalles
            </div>
          )}
        </div>
      )}
      {result?.error && (
        <div style={{ color: "#f87171", fontSize: 13 }}>{result.error}</div>
      )}
    </div>
  );
}


export default function SettingsPage({ apiUrl = "http://localhost:8000", profile, onProfileUpdate }) {
  const [settings, setSettings]         = useState(null);
  const [saved, setSaved]               = useState("");
  const [profileForm, setProfileForm]   = useState({});
  const [llmForm, setLlmForm]           = useState({ provider: "ollama", model: "", api_key: "" });
  const [voiceForm, setVoiceForm]       = useState({ default_input: "text", stt_language: "es", tts_model: "es_ES-davefx-medium" });
  const [odForm, setOdForm]             = useState({ client_id: "", client_secret: "", tenant_id: "consumers" });
  const [folderInput, setFolderInput]   = useState("");
  const [activeSection, setActiveSection] = useState("profile");
  const gdriveRef = useRef(null);
  const gmailRef  = useRef(null);

  const [gmailAvailable, setGmailAvailable] = useState(false);

  useEffect(() => {
    fetch(`${apiUrl}/api/gmail/status`).then(r => r.json()).then(d => setGmailAvailable(d.available && d.libs_ok)).catch(() => {});
    fetch(`${apiUrl}/api/settings`)
      .then(r => r.json())
      .then(d => {
        setSettings(d);
        setLlmForm({
          provider: d.llm?.provider || "ollama",
          model: d.llm?.model || "",
          api_key: "",
        });
        setVoiceForm(v => ({ ...v, ...d.voice }));
      })
      .catch(() => {});
  }, [apiUrl]);

  useEffect(() => {
    if (profile) {
      const f = {};
      Object.keys(PROFILE_META).forEach(k => { f[k] = profile[k] ?? ""; });
      setProfileForm(f);
    }
  }, [profile]);

  const flash = (msg) => { setSaved(msg); setTimeout(() => setSaved(""), 2500); };

  /* ── save helpers ── */
  const saveProfile = () => {
    const updates = {};
    Object.entries(profileForm).forEach(([k, v]) => {
      updates[k] = v === "" ? null : (PROFILE_META[k].type === "number" ? Number(v) : v);
    });
    onProfileUpdate(updates);
    flash("Perfil guardado.");
  };

  const saveLlm = async () => {
    await fetch(`${apiUrl}/api/settings/preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section: "llm", updates: llmForm }),
    });
    setSettings(s => ({ ...s, llm: { provider: llmForm.provider, model: llmForm.model, has_api_key: !!llmForm.api_key } }));
    flash("LLM guardado.");
  };

  const saveVoice = async () => {
    await fetch(`${apiUrl}/api/settings/preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section: "voice", updates: voiceForm }),
    });
    flash("Preferencias de voz guardadas.");
  };

  const uploadGmail = async (file) => {
    const fd = new FormData();
    fd.append("creds_file", file);
    const r = await fetch(`${apiUrl}/api/settings/credentials/gmail`, { method: "POST", body: fd });
    const d = await r.json();
    if (d.ok) { setGmailAvailable(true); flash("Credenciales de Gmail guardadas."); }
  };

  const uploadGdrive = async (file) => {
    const fd = new FormData();
    fd.append("creds_file", file);
    const r = await fetch(`${apiUrl}/api/settings/credentials/gdrive`, { method: "POST", body: fd });
    const d = await r.json();
    if (d.ok) {
      setSettings(s => ({ ...s, credentials: { ...s.credentials, gdrive: true } }));
      flash("Credenciales de Google Drive guardadas.");
    }
  };

  const saveOnedrive = async () => {
    const r = await fetch(`${apiUrl}/api/settings/credentials/onedrive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(odForm),
    });
    const d = await r.json();
    if (d.ok) {
      setSettings(s => ({ ...s, credentials: { ...s.credentials, onedrive: true } }));
      flash("Credenciales de OneDrive guardadas.");
    }
  };

  const deleteCredential = async (service) => {
    await fetch(`${apiUrl}/api/settings/credentials/${service}`, { method: "DELETE" });
    setSettings(s => ({ ...s, credentials: { ...s.credentials, [service]: false } }));
    flash(`Credenciales de ${service} eliminadas.`);
  };

  const addFolder = async () => {
    if (!folderInput.trim()) return;
    const r = await fetch(`${apiUrl}/api/docs/add_folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: folderInput }),
    });
    const d = await r.json();
    if (d.roots) {
      setSettings(s => ({ ...s, local_drives: d.roots }));
      setFolderInput("");
      flash("Carpeta añadida.");
    }
  };

  const NAV = [
    { id: "profile", label: "Perfil" },
    { id: "llm",     label: "LLM" },
    { id: "gmail",   label: "Gmail" },
    { id: "gdrive",  label: "Google Drive" },
    { id: "onedrive",label: "OneDrive" },
    { id: "folders", label: "Carpetas locales" },
    { id: "voice",   label: "Voz" },
  ];

  const navBtn = (id, label) => (
    <button key={id} onClick={() => setActiveSection(id)} style={{
      padding: "7px 14px",
      borderRadius: 8,
      border: "none",
      background: activeSection === id ? "rgba(99,102,241,0.2)" : "transparent",
      color: activeSection === id ? "#818cf8" : "#6b7280",
      fontSize: 13,
      fontWeight: activeSection === id ? 600 : 400,
      cursor: "pointer",
    }}>{label}</button>
  );

  const selectedProvider = LLM_PROVIDERS.find(p => p.value === llmForm.provider);

  return (
    <div>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>Configuración</h1>
      {saved && (
        <div style={{ fontSize: 13, color: "#4ade80", marginBottom: 12 }}>✓ {saved}</div>
      )}

      {/* Sidebar nav */}
      <div style={{ display: "flex", gap: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 150 }}>
          {NAV.map(({ id, label }) => navBtn(id, label))}
        </div>

        <div style={{ flex: 1 }}>

          {/* ── PERFIL ── */}
          {activeSection === "profile" && (
            <div style={SECTION}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, color: "#f9fafb" }}>Perfil de usuario</h2>
              <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 16 }}>
                Aletheia usa estos datos para personalizar sus análisis. Los aprende también de tus preguntas automáticamente.
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {Object.entries(PROFILE_META).map(([k, meta]) => (
                  <div key={k}>
                    <label style={LABEL}>{meta.label}</label>
                    <input
                      type={meta.type}
                      value={profileForm[k] ?? ""}
                      onChange={e => setProfileForm(f => ({ ...f, [k]: e.target.value }))}
                      placeholder={`${meta.label}…`}
                      style={INPUT}
                    />
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
                <button style={BTN_PRIMARY} onClick={saveProfile}>Guardar perfil</button>
              </div>
            </div>
          )}

          {/* ── LLM ── */}
          {activeSection === "llm" && (
            <div style={SECTION}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, color: "#f9fafb" }}>Modelo de lenguaje</h2>

              {/* Provider pills */}
              <label style={LABEL}>Proveedor</label>
              <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                {LLM_PROVIDERS.map(p => (
                  <button key={p.value} onClick={() => setLlmForm(f => ({ ...f, provider: p.value, model: "" }))} style={{
                    padding: "6px 16px", borderRadius: 20,
                    border: `1px solid ${llmForm.provider === p.value ? "#818cf8" : "#374151"}`,
                    background: llmForm.provider === p.value ? "rgba(129,140,248,0.15)" : "transparent",
                    color: llmForm.provider === p.value ? "#818cf8" : "#9ca3af",
                    fontSize: 13, cursor: "pointer",
                    fontWeight: llmForm.provider === p.value ? 600 : 400,
                  }}>{p.label}</button>
                ))}
              </div>

              {/* Model selector */}
              <label style={LABEL}>Modelo</label>
              <select
                value={llmForm.model}
                onChange={e => setLlmForm(f => ({ ...f, model: e.target.value }))}
                style={{ ...INPUT, marginBottom: 16 }}
              >
                <option value="">— Por defecto —</option>
                {(LLM_MODELS[llmForm.provider] || []).map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>

              {/* API key (only for cloud providers) */}
              {selectedProvider?.needsKey && (
                <>
                  <label style={LABEL}>API Key</label>
                  <input
                    type="password"
                    value={llmForm.api_key}
                    onChange={e => setLlmForm(f => ({ ...f, api_key: e.target.value }))}
                    placeholder="sk-…"
                    style={{ ...INPUT, marginBottom: 4 }}
                    autoComplete="off"
                  />
                  <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
                    <span>
                      Se guarda localmente en PALACE/config/ — nunca sale de tu máquina.
                      {settings?.llm?.has_api_key && <span style={{ color: "#4ade80" }}> ✓ clave guardada</span>}
                    </span>
                    {PROVIDER_LINKS[llmForm.provider] && (
                      <a href={PROVIDER_LINKS[llmForm.provider]} target="_blank" rel="noreferrer" style={{ color: "#818cf8", whiteSpace: "nowrap" }}>
                        Obtener clave →
                      </a>
                    )}
                  </div>
                </>
              )}

              {llmForm.provider === "ollama" && (
                <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 16 }}>
                  Ollama debe estar corriendo: <code style={{ color: "#818cf8" }}>ollama serve</code>
                  <br />
                  Modelos disponibles: <code style={{ color: "#818cf8" }}>ollama list</code>
                </div>
              )}

              <button style={BTN_PRIMARY} onClick={saveLlm}>Guardar configuración LLM</button>
            </div>
          )}

          {/* ── GMAIL ── */}
          {activeSection === "gmail" && (
            <div style={SECTION}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>Gmail — Facturas y gastos</h2>
                <Badge ok={gmailAvailable} />
              </div>

              {gmailAvailable ? (
                <div>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                    Credenciales configuradas. Aletheia puede escanear tu correo para extraer facturas y gastos.
                    El primer escaneo abrirá el navegador para autorizar el acceso (solo lectura).
                  </p>
                  <GmailScanner apiUrl={apiUrl} />
                  <div style={{ marginTop: 12 }}>
                    <button style={BTN_GHOST} onClick={async () => {
                      await fetch(`${apiUrl}/api/settings/credentials/gmail`, { method: "DELETE" }).catch(() => {});
                      setGmailAvailable(false);
                      flash("Credenciales de Gmail eliminadas.");
                    }}>Eliminar credenciales</button>
                  </div>
                </div>
              ) : (
                <div>
                  <ol style={{ color: "#9ca3af", fontSize: 13, lineHeight: 1.8, marginBottom: 16 }}>
                    <li>Abre <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>console.cloud.google.com</a></li>
                    <li>Habilita la <strong style={{ color: "#f9fafb" }}>Gmail API</strong></li>
                    <li>Crea credenciales OAuth2 → descarga el fichero JSON</li>
                    <li>Súbelo aquí — el acceso es de <strong style={{ color: "#f9fafb" }}>solo lectura</strong></li>
                  </ol>
                  <input
                    ref={gmailRef}
                    type="file"
                    accept=".json"
                    style={{ display: "none" }}
                    onChange={e => { if (e.target.files[0]) uploadGmail(e.target.files[0]); }}
                  />
                  <button style={BTN_PRIMARY} onClick={() => gmailRef.current?.click()}>
                    Subir gmail_credentials.json
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── GOOGLE DRIVE ── */}
          {activeSection === "gdrive" && (
            <div style={SECTION}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>Google Drive online</h2>
                <Badge ok={settings?.credentials?.gdrive} />
              </div>

              {settings?.credentials?.gdrive ? (
                <div>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                    Credenciales configuradas. La próxima vez que uses Drive online se abrirá el navegador para autorizar (una sola vez).
                  </p>
                  <button style={BTN_GHOST} onClick={() => deleteCredential("gdrive")}>Eliminar credenciales</button>
                </div>
              ) : (
                <div>
                  <ol style={{ color: "#9ca3af", fontSize: 13, lineHeight: 1.8, marginBottom: 16 }}>
                    <li>Crea un proyecto en <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>console.cloud.google.com</a></li>
                    <li>Habilita la <strong style={{ color: "#f9fafb" }}>Google Drive API</strong></li>
                    <li>Crea credenciales OAuth2 → descarga el fichero JSON</li>
                    <li>Súbelo aquí:</li>
                  </ol>
                  <input
                    ref={gdriveRef}
                    type="file"
                    accept=".json"
                    style={{ display: "none" }}
                    onChange={e => { if (e.target.files[0]) uploadGdrive(e.target.files[0]); }}
                  />
                  <button style={BTN_PRIMARY} onClick={() => gdriveRef.current?.click()}>
                    Subir credentials.json
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── ONEDRIVE ── */}
          {activeSection === "onedrive" && (
            <div style={SECTION}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>OneDrive online</h2>
                <Badge ok={settings?.credentials?.onedrive} />
              </div>

              {settings?.credentials?.onedrive ? (
                <div>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                    App registration configurada. La primera llamada abrirá el navegador para autorizar.
                  </p>
                  <button style={BTN_GHOST} onClick={() => deleteCredential("onedrive")}>Eliminar credenciales</button>
                </div>
              ) : (
                <div>
                  <ol style={{ color: "#9ca3af", fontSize: 13, lineHeight: 1.8, marginBottom: 16 }}>
                    <li>Ve a <a href="https://portal.azure.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>portal.azure.com</a> → App registrations → New</li>
                    <li>Añade permiso <strong style={{ color: "#f9fafb" }}>Files.Read</strong> (Microsoft Graph)</li>
                    <li>Crea un Client Secret y cópialo aquí</li>
                  </ol>
                  <div style={{ display: "grid", gap: 10, marginBottom: 16 }}>
                    {[
                      ["client_id",     "Client ID",     "text"],
                      ["client_secret", "Client Secret", "password"],
                      ["tenant_id",     "Tenant ID (consumers para personal)", "text"],
                    ].map(([k, lbl, t]) => (
                      <div key={k}>
                        <label style={LABEL}>{lbl}</label>
                        <input
                          type={t}
                          value={odForm[k]}
                          onChange={e => setOdForm(f => ({ ...f, [k]: e.target.value }))}
                          placeholder={lbl}
                          style={INPUT}
                          autoComplete="off"
                        />
                      </div>
                    ))}
                  </div>
                  <button style={BTN_PRIMARY} onClick={saveOnedrive}>Guardar configuración OneDrive</button>
                </div>
              )}
            </div>
          )}

          {/* ── CARPETAS LOCALES ── */}
          {activeSection === "folders" && (
            <div style={SECTION}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, color: "#f9fafb" }}>Carpetas locales</h2>
              <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 12 }}>
                Aletheia detecta automáticamente Google Drive y OneDrive sincronizados. Añade carpetas adicionales aquí.
              </p>

              {/* Detected drives */}
              <div style={{ marginBottom: 16 }}>
                {(settings?.local_drives || []).length === 0
                  ? <p style={{ color: "#4b5563", fontSize: 13 }}>No se detectaron drives sincronizados.</p>
                  : (settings?.local_drives || []).map((d, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: "1px solid #1f2937" }}>
                      <span style={{ fontSize: 16 }}>📁</span>
                      <span style={{ flex: 1, fontSize: 13, color: "#a5b4fc" }}>{d.name}</span>
                      <span style={{ fontSize: 11, color: "#4b5563" }}>{d.path}</span>
                    </div>
                  ))
                }
              </div>

              <label style={LABEL}>Añadir carpeta personalizada</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={folderInput}
                  onChange={e => setFolderInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && addFolder()}
                  placeholder="C:\Users\…\MisDocumentos"
                  style={{ ...INPUT, flex: 1 }}
                />
                <button style={BTN_PRIMARY} onClick={addFolder}>Añadir</button>
              </div>
            </div>
          )}

          {/* ── VOZ ── */}
          {activeSection === "voice" && (
            <div style={SECTION}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, color: "#f9fafb" }}>Preferencias de voz</h2>

              <label style={LABEL}>Modo de entrada por defecto</label>
              <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                {[["text", "⌨ Texto"], ["voice", "🎙 Voz"]].map(([v, lbl]) => (
                  <button key={v} onClick={() => setVoiceForm(f => ({ ...f, default_input: v }))} style={{
                    padding: "6px 16px", borderRadius: 20,
                    border: `1px solid ${voiceForm.default_input === v ? "#818cf8" : "#374151"}`,
                    background: voiceForm.default_input === v ? "rgba(129,140,248,0.15)" : "transparent",
                    color: voiceForm.default_input === v ? "#818cf8" : "#9ca3af",
                    fontSize: 13, cursor: "pointer",
                    fontWeight: voiceForm.default_input === v ? 600 : 400,
                  }}>{lbl}</button>
                ))}
              </div>

              <label style={LABEL}>Idioma STT (Whisper)</label>
              <select
                value={voiceForm.stt_language}
                onChange={e => setVoiceForm(f => ({ ...f, stt_language: e.target.value }))}
                style={{ ...INPUT, marginBottom: 16 }}
              >
                <option value="es">Español</option>
                <option value="en">English</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="pt">Português</option>
                <option value="it">Italiano</option>
              </select>

              <label style={LABEL}>Modelo de voz Piper (TTS)</label>
              <select
                value={voiceForm.tts_model}
                onChange={e => setVoiceForm(f => ({ ...f, tts_model: e.target.value }))}
                style={{ ...INPUT, marginBottom: 16 }}
              >
                {PIPER_MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>

              <button style={BTN_PRIMARY} onClick={saveVoice}>Guardar preferencias de voz</button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
