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
  { value: "ollama",      label: "Ollama (local)",           needsKey: false },
  { value: "openrouter",  label: "OpenRouter ✦ gratis",      needsKey: true  },
  { value: "groq",        label: "Groq ✦ gratis",            needsKey: true  },
  { value: "deepseek",    label: "DeepSeek ✦ gratis",        needsKey: true  },
  { value: "claude",      label: "Claude (Anthropic)",       needsKey: true  },
  { value: "openai",      label: "OpenAI / GPT",             needsKey: true  },
  { value: "mistral",     label: "Mistral AI",               needsKey: true  },
];

const LLM_MODELS = {
  ollama:      ["llama3.2:3b", "llama3.1:8b", "mistral:7b", "gemma3:4b"],
  openrouter:  [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "mistralai/mistral-7b-instruct:free",
    "microsoft/phi-4-reasoning-plus:free",
  ],
  groq:        ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
  deepseek:    ["deepseek-chat", "deepseek-reasoner"],
  claude:      ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-7"],
  openai:      ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
  mistral:     ["mistral-small-latest", "mistral-medium-latest", "open-mixtral-8x7b"],
};

const PROVIDER_LINKS = {
  openrouter: "https://openrouter.ai/keys",
  claude:     "https://console.anthropic.com/",
  openai:     "https://platform.openai.com/api-keys",
  deepseek:   "https://platform.deepseek.com/",
  groq:       "https://console.groq.com/keys",
  mistral:    "https://console.mistral.ai/",
};

const PROVIDER_FREE_NOTE = {
  openrouter: "20+ modelos gratuitos con una sola clave — openrouter.ai (registro gratis)",
  groq:       "Tier gratuito: hasta 6000 req/día — console.groq.com",
  deepseek:   "Muy económico — platform.deepseek.com",
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
  const [systemForm, setSystemForm]     = useState({ use_v3_modes: false });
  const [calStatus, setCalStatus]       = useState(null);
  const [calAuthing, setCalAuthing]     = useState(false);
  const [tgStatus, setTgStatus]         = useState(null);
  const [tgForm, setTgForm]             = useState({ token: "", allowed_user_ids: "", admin_user_id: "" });
  const [tgSaving, setTgSaving]         = useState(false);
  const gdriveRef = useRef(null);
  const gmailRef  = useRef(null);

  const [gmailAvailable, setGmailAvailable] = useState(false);

  // LLM test / discover state
  const [ollamaStatus, setOllamaStatus]   = useState(null); // null | { ok, models, error }
  const [ollamaModels, setOllamaModels]   = useState([]);   // real installed models
  const [llmTesting, setLlmTesting]       = useState(false);
  const [llmActivating, setLlmActivating] = useState(null); // "ollama" | provider name
  const [discovering, setDiscovering]     = useState(false);
  const [discoverResult, setDiscoverResult] = useState(null); // { providers, configured, total }
  const [routingPolicy, setRoutingPolicy] = useState("fastest");
  const [rankingLoading, setRankingLoading] = useState(false);
  const [rankingResult, setRankingResult] = useState(null);

  useEffect(() => {
    const handler = (e) => setActiveSection(e.detail);
    window.addEventListener("aletheia:settings-section", handler);
    return () => window.removeEventListener("aletheia:settings-section", handler);
  }, []);

  useEffect(() => {
    fetch(`${apiUrl}/api/gmail/status`).then(r => r.json()).then(d => setGmailAvailable(d.available && d.libs_ok)).catch(() => {});
    fetch(`${apiUrl}/api/calendar/status`).then(r => r.json()).then(setCalStatus).catch(() => {});
    fetch(`${apiUrl}/api/settings/telegram/status`).then(r => r.json()).then(d => {
      setTgStatus(d);
      if (d.configured) {
        setTgForm(f => ({
          ...f,
          allowed_user_ids: (d.allowed_user_ids || []).join(", "),
          admin_user_id: d.admin_user_id ?? "",
        }));
      }
    }).catch(() => {});
    fetch(`${apiUrl}/api/settings`)
      .then(r => r.json())
      .then(d => {
        setSettings(d);
        setLlmForm({
          provider: d.llm?.provider || "ollama",
          model: d.llm?.model || "",
          api_key: "",
        });
        setRoutingPolicy(d.llm?.routing_policy || "fastest");
        setVoiceForm(v => ({ ...v, ...d.voice }));
        if (d.system) setSystemForm(d.system);
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

  const authorizeCalendar = async () => {
    setCalAuthing(true);
    try {
      const r = await fetch(`${apiUrl}/api/calendar/auth`, { method: "POST" });
      const d = await r.json();
      if (d.ok) {
        flash("Google Calendar autorizado correctamente.");
        fetch(`${apiUrl}/api/calendar/status`).then(r => r.json()).then(setCalStatus).catch(() => {});
      } else {
        flash(`Error: ${d.error}`);
      }
    } catch (e) {
      flash(`Error de conexión: ${e.message}`);
    } finally {
      setCalAuthing(false);
    }
  };

  const saveTelegram = async () => {
    setTgSaving(true);
    try {
      const ids = tgForm.allowed_user_ids.split(",").map(s => s.trim()).filter(Boolean);
      const r = await fetch(`${apiUrl}/api/settings/telegram`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: tgForm.token,
          allowed_user_ids: ids,
          admin_user_id: tgForm.admin_user_id || null,
        }),
      });
      const d = await r.json();
      if (d.ok) {
        flash("Configuración de Telegram guardada.");
        fetch(`${apiUrl}/api/settings/telegram/status`).then(r => r.json()).then(setTgStatus).catch(() => {});
      } else {
        flash(`Error: ${d.error}`);
      }
    } finally {
      setTgSaving(false);
    }
  };

  const deleteTelegram = async () => {
    await fetch(`${apiUrl}/api/settings/telegram`, { method: "DELETE" });
    setTgStatus({ configured: false });
    setTgForm({ token: "", allowed_user_ids: "", admin_user_id: "" });
    flash("Configuración de Telegram eliminada.");
  };

  const saveSystem = async () => {
    const r = await fetch(`${apiUrl}/api/settings/preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ section: "system", updates: systemForm }),
    });
    const d = await r.json();
    if (d.system) setSystemForm(d.system);
    flash("Configuración del sistema guardada.");
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

  // Probe Ollama when entering the LLM section
  useEffect(() => {
    if (activeSection !== "llm") return;
    fetch(`${apiUrl}/api/llm/ollama/models`)
      .then(r => r.json())
      .then(d => {
        setOllamaStatus({ ok: d.ok, models: d.models, error: d.ok ? null : "Ollama no responde" });
        if (d.ok && d.models.length > 0) setOllamaModels(d.models);
      })
      .catch(() => setOllamaStatus({ ok: false, models: [], error: "Sin conexión con Ollama" }));
  }, [activeSection, apiUrl]);

  const runDiscover = async () => {
    setDiscovering(true);
    try {
      const r = await fetch(`${apiUrl}/api/llm/discover`);
      const d = await r.json();
      setDiscoverResult(d);
    } catch (e) {
      flash(`Error al descubrir: ${e.message}`);
    } finally {
      setDiscovering(false);
    }
  };

  const saveRoutingPolicy = async () => {
    try {
      await fetch(`${apiUrl}/api/settings/preferences`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "llm", updates: { routing_policy: routingPolicy } }),
      });
      flash(`Política guardada: ${routingPolicy}`);
    } catch (e) {
      flash(`Error guardando política: ${e.message}`);
    }
  };

  const refreshCatalogAndRanking = async (policy = routingPolicy) => {
    setRankingLoading(true);
    try {
      await fetch(`${apiUrl}/api/llm/refresh_catalog`, { method: "POST" });
      const r = await fetch(`${apiUrl}/api/llm/ranking?policy=${encodeURIComponent(policy)}`);
      const d = await r.json();
      setRankingResult(d);
    } catch (e) {
      flash(`Error actualizando ranking: ${e.message}`);
    } finally {
      setRankingLoading(false);
    }
  };

  const testLlm = async (targetProvider) => {
    setLlmTesting(true);
    try {
      const r = await fetch(`${apiUrl}/api/llm/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: targetProvider, api_key: llmForm.api_key }),
      });
      const d = await r.json();
      flash(d.ok ? `✓ ${targetProvider}: ${d.note || "conexión OK"}` : `Error: ${d.error}`);
    } catch (e) {
      flash(`Error: ${e.message}`);
    } finally {
      setLlmTesting(false);
    }
  };

  const activateLlm = async (targetProvider, model, api_key) => {
    setLlmActivating(targetProvider);
    try {
      const updates = { provider: targetProvider, model: model || "" };
      if (api_key) updates.api_key = api_key; // never overwrite a saved key with an empty string
      await fetch(`${apiUrl}/api/settings/preferences`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section: "llm", updates }),
      });
      setSettings(s => ({ ...s, llm: { provider: targetProvider, model, has_api_key: !!api_key || !!s?.llm?.has_api_key } }));
      setLlmForm(f => ({ ...f, provider: targetProvider, model: model || "" }));
      flash(`Proveedor activo: ${targetProvider}`);
    } finally {
      setLlmActivating(null);
    }
  };

  const NAV = [
    { id: "profile",  label: "Perfil" },
    { id: "llm",      label: "LLM" },
    { id: "gmail",    label: "Gmail" },
    { id: "gdrive",   label: "Google Drive" },
    { id: "calendar", label: "Calendario" },
    { id: "onedrive", label: "OneDrive" },
    { id: "folders",  label: "Carpetas locales" },
    { id: "voice",    label: "Voz" },
    { id: "telegram", label: "Telegram" },
    { id: "system",   label: "Sistema" },
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
          {activeSection === "llm" && (() => {
            const activeProvider = settings?.llm?.provider || llmForm.provider;
            const cloudProviders = LLM_PROVIDERS.filter(p => p.needsKey);
            const isCloudActive  = activeProvider !== "ollama";

            const cardStyle = (active) => ({
              background: "#060610",
              border: `1px solid ${active ? "#818cf8" : "#1f2937"}`,
              borderRadius: 12,
              padding: "1.25rem",
              marginBottom: 16,
              position: "relative",
            });

            const activeBadge = (
              <span style={{
                position: "absolute", top: 12, right: 12,
                fontSize: 10, padding: "2px 8px", borderRadius: 20,
                background: "rgba(74,222,128,0.12)", border: "1px solid rgba(74,222,128,0.3)",
                color: "#4ade80", fontWeight: 700, letterSpacing: "0.06em",
              }}>ACTIVO</span>
            );

            return (
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>Modelo de lenguaje</h2>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      style={{ ...BTN_GHOST, fontSize: 12, display: "flex", alignItems: "center", gap: 6, opacity: discovering ? 0.6 : 1 }}
                      onClick={runDiscover}
                      disabled={discovering}
                    >
                      <span style={{ fontSize: 14 }}>🔍</span>
                      {discovering ? "Descubriendo…" : "Descubrir disponibles"}
                    </button>
                    <button
                      style={{ ...BTN_GHOST, fontSize: 12, opacity: rankingLoading ? 0.6 : 1 }}
                      onClick={() => refreshCatalogAndRanking(routingPolicy)}
                      disabled={rankingLoading}
                    >
                      {rankingLoading ? "Actualizando…" : "Actualizar listado"}
                    </button>
                  </div>
                </div>

                <div style={{ background: "#060610", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem", marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                    Política de routing
                  </div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
                    <select
                      value={routingPolicy}
                      onChange={e => setRoutingPolicy(e.target.value)}
                      style={{ ...INPUT, maxWidth: 220 }}
                    >
                      <option value="fastest">Más rápido (fastest)</option>
                      <option value="most_reliable">Más fiable (most_reliable)</option>
                    </select>
                    <button style={{ ...BTN_PRIMARY, fontSize: 12 }} onClick={saveRoutingPolicy}>
                      Guardar política
                    </button>
                    <button style={{ ...BTN_GHOST, fontSize: 12 }} onClick={() => refreshCatalogAndRanking(routingPolicy)}>
                      Ver ranking
                    </button>
                  </div>

                  {rankingResult?.ranking && (
                    <div>
                      <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 6 }}>
                        Ranking actual — política: <span style={{ color: "#818cf8" }}>{rankingResult.policy}</span>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        {rankingResult.ranking.slice(0, 5).map((p, i) => (
                          <div key={p.provider} style={{
                            display: "flex", alignItems: "center", gap: 8,
                            border: "1px solid #1f2937", borderRadius: 8, padding: "6px 10px",
                            background: p.available ? "rgba(74,222,128,0.04)" : "transparent",
                          }}>
                            <span style={{ width: 18, color: "#6b7280", fontSize: 12 }}>#{i + 1}</span>
                            <span style={{ flex: 1, color: p.available ? "#f9fafb" : "#6b7280", fontSize: 13 }}>{p.provider}</span>
                            <span style={{ fontSize: 11, color: "#9ca3af" }}>{p.latency_ms}ms</span>
                            <span style={{ fontSize: 11, color: "#9ca3af" }}>{Math.round((p.reliability || 0) * 100)}%</span>
                            <span style={{ fontSize: 10, color: p.available ? "#4ade80" : "#f87171" }}>
                              {p.available ? "● disponible" : "○ no disponible"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* ── Panel de descubrimiento ── */}
                {discoverResult && (
                  <div style={{ background: "#060610", border: "1px solid #1f2937", borderRadius: 12, padding: "1rem", marginBottom: 16 }}>
                    <div style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                      {discoverResult.configured} de {discoverResult.total} proveedores disponibles
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {discoverResult.providers.map(p => (
                        <div key={p.provider} style={{
                          display: "flex", alignItems: "center", gap: 10,
                          padding: "8px 12px", borderRadius: 8,
                          background: p.active ? "rgba(99,102,241,0.08)" : "transparent",
                          border: `1px solid ${p.ok ? "rgba(74,222,128,0.15)" : "#1f2937"}`,
                        }}>
                          <span style={{ fontSize: 13, color: p.ok ? "#4ade80" : "#4b5563", flexShrink: 0 }}>
                            {p.ok ? "●" : "○"}
                          </span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <span style={{ fontSize: 13, fontWeight: 600, color: p.ok ? "#f9fafb" : "#4b5563" }}>{p.label}</span>
                              {p.free && p.ok && (
                                <span style={{ fontSize: 9, padding: "1px 6px", borderRadius: 10, background: "rgba(74,222,128,0.12)", color: "#4ade80", border: "1px solid rgba(74,222,128,0.2)" }}>GRATIS</span>
                              )}
                              {p.active && (
                                <span style={{ fontSize: 9, padding: "1px 6px", borderRadius: 10, background: "rgba(99,102,241,0.15)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.2)" }}>ACTIVO</span>
                              )}
                            </div>
                            <div style={{ fontSize: 11, color: "#4b5563", marginTop: 1 }}>{p.use_for}</div>
                          </div>
                          {p.ok && !p.active && (
                            <button
                              style={{ ...BTN_GHOST, fontSize: 11, padding: "4px 10px", flexShrink: 0, opacity: llmActivating === p.provider ? 0.6 : 1 }}
                              onClick={() => activateLlm(p.provider, "", "")}
                              disabled={llmActivating === p.provider}
                            >
                              {llmActivating === p.provider ? "…" : "Activar"}
                            </button>
                          )}
                          {!p.ok && p.needs_key && (
                            <span style={{ fontSize: 11, color: "#374151", flexShrink: 0 }}>sin clave</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── LOCAL (Ollama) ── */}
                <div style={cardStyle(!isCloudActive)}>
                  {!isCloudActive && activeBadge}
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 18 }}>🏠</span>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#f9fafb" }}>LOCAL — Ollama</div>
                      <div style={{ fontSize: 11, color: "#6b7280" }}>Privado, sin coste, requiere GPU o CPU potente</div>
                    </div>
                    {(() => {
                      const ollamaOk      = ollamaStatus?.ok;
                      const ollamaLoading = ollamaStatus === null;
                      const statusColor   = ollamaOk ? "#4ade80" : (ollamaLoading ? "#6b7280" : "#f87171");
                      const statusBg      = ollamaOk ? "rgba(74,222,128,0.1)"  : "rgba(248,113,113,0.1)";
                      const statusBorder  = ollamaOk ? "rgba(74,222,128,0.3)"  : "rgba(248,113,113,0.25)";
                      const statusLabel   = ollamaLoading ? "comprobando…" : (ollamaOk ? "● conectado" : "● sin conexión");
                      return (
                        <span style={{ marginLeft: "auto", fontSize: 11, padding: "2px 8px", borderRadius: 20, background: statusBg, border: `1px solid ${statusBorder}`, color: statusColor }}>
                          {statusLabel}
                        </span>
                      );
                    })()}
                  </div>

                  <label style={LABEL}>Modelo</label>
                  <select
                    value={isCloudActive ? "" : (llmForm.model || "")}
                    onChange={e => setLlmForm(f => ({ ...f, provider: "ollama", model: e.target.value }))}
                    style={{ ...INPUT, marginBottom: 12 }}
                  >
                    <option value="">— Por defecto —</option>
                    {(ollamaModels.length > 0 ? ollamaModels : LLM_MODELS.ollama).map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>

                  <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 12 }}>
                    Ollama debe estar corriendo: <code style={{ color: "#818cf8" }}>ollama serve</code>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      style={{ ...BTN_GHOST, fontSize: 12 }}
                      onClick={() => {
                        setOllamaStatus(null);
                        fetch(`${apiUrl}/api/llm/ollama/models`)
                          .then(r => r.json())
                          .then(d => {
                            setOllamaStatus({ ok: d.ok, models: d.models, error: d.ok ? null : "Ollama no responde" });
                            if (d.ok && d.models.length > 0) setOllamaModels(d.models);
                          })
                          .catch(() => setOllamaStatus({ ok: false, models: [], error: "Sin conexión" }));
                      }}
                    >
                      Probar
                    </button>
                    <button
                      style={{ ...BTN_PRIMARY, fontSize: 12, opacity: llmActivating === "ollama" ? 0.6 : 1 }}
                      onClick={() => activateLlm("ollama", llmForm.provider === "ollama" ? llmForm.model : "", "")}
                      disabled={llmActivating === "ollama"}
                    >
                      {llmActivating === "ollama" ? "Activando…" : "Activar LOCAL"}
                    </button>
                  </div>
                </div>

                {/* ── ONLINE (Cloud) ── */}
                <div style={cardStyle(isCloudActive)}>
                  {isCloudActive && activeBadge}
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                    <span style={{ fontSize: 18 }}>☁️</span>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#f9fafb" }}>ONLINE — Cloud</div>
                      <div style={{ fontSize: 11, color: "#6b7280" }}>Máxima capacidad, requiere API key</div>
                    </div>
                  </div>

                  {/* Provider pills */}
                  <label style={LABEL}>Proveedor</label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
                    {cloudProviders.map(p => (
                      <button key={p.value}
                        onClick={() => setLlmForm(f => ({ ...f, provider: p.value, model: "" }))}
                        style={{
                          padding: "5px 14px", borderRadius: 20, fontSize: 12, cursor: "pointer",
                          border: `1px solid ${llmForm.provider === p.value ? "#818cf8" : "#374151"}`,
                          background: llmForm.provider === p.value ? "rgba(129,140,248,0.15)" : "transparent",
                          color: llmForm.provider === p.value ? "#818cf8" : "#9ca3af",
                          fontWeight: llmForm.provider === p.value ? 600 : 400,
                          outline: (isCloudActive && activeProvider === p.value) ? "2px solid rgba(74,222,128,0.4)" : "none",
                        }}
                      >{p.label}</button>
                    ))}
                  </div>

                  {/* Free provider note */}
                  {PROVIDER_FREE_NOTE[llmForm.provider] && (
                    <div style={{ fontSize: 11, color: "#4ade80", padding: "6px 10px", borderRadius: 6, background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.15)", marginBottom: 12 }}>
                      ✦ {PROVIDER_FREE_NOTE[llmForm.provider]}
                    </div>
                  )}

                  {/* Model */}
                  <label style={LABEL}>Modelo</label>
                  <select
                    value={llmForm.provider !== "ollama" ? llmForm.model : ""}
                    onChange={e => setLlmForm(f => ({ ...f, model: e.target.value }))}
                    style={{ ...INPUT, marginBottom: 12 }}
                  >
                    <option value="">— Por defecto —</option>
                    {(LLM_MODELS[llmForm.provider] || []).map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>

                  {/* API Key */}
                  <label style={LABEL}>API Key</label>
                  <input
                    type="password"
                    value={llmForm.api_key}
                    onChange={e => setLlmForm(f => ({ ...f, api_key: e.target.value }))}
                    placeholder="sk-…"
                    style={{ ...INPUT, marginBottom: 4 }}
                    autoComplete="off"
                  />
                  <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 12, display: "flex", gap: 12, alignItems: "center" }}>
                    <span>
                      Guardada localmente — nunca sale de tu máquina.
                      {isCloudActive && settings?.llm?.has_api_key && <span style={{ color: "#4ade80" }}> ✓ clave guardada</span>}
                    </span>
                    {PROVIDER_LINKS[llmForm.provider] && (
                      <a href={PROVIDER_LINKS[llmForm.provider]} target="_blank" rel="noreferrer"
                        style={{ color: "#818cf8", whiteSpace: "nowrap", fontSize: 11 }}>
                        Obtener clave →
                      </a>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      style={{ ...BTN_GHOST, fontSize: 12, opacity: llmTesting ? 0.6 : 1 }}
                      onClick={() => testLlm(llmForm.provider)}
                      disabled={llmTesting || llmForm.provider === "ollama"}
                    >
                      {llmTesting ? "Probando…" : "Probar clave"}
                    </button>
                    <button
                      style={{ ...BTN_PRIMARY, fontSize: 12, opacity: llmActivating === llmForm.provider ? 0.6 : 1 }}
                      onClick={() => activateLlm(llmForm.provider, llmForm.model, llmForm.api_key)}
                      disabled={llmActivating === llmForm.provider || llmForm.provider === "ollama"}
                    >
                      {llmActivating === llmForm.provider ? "Activando…" : "Activar CLOUD"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })()}

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

          {/* ── CALENDARIO ── */}
          {activeSection === "calendar" && (
            <div style={SECTION}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>Google Calendar</h2>
                <Badge
                  ok={calStatus?.authorized}
                  trueLabel="Autorizado"
                  falseLabel={calStatus?.has_credentials ? "Pendiente autorizar" : "Sin credenciales"}
                />
              </div>

              {/* Reutiliza credenciales de Drive */}
              {calStatus?.using_drive_creds && (
                <div style={{ fontSize: 12, color: "#818cf8", padding: "8px 12px", borderRadius: 8, background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", marginBottom: 14 }}>
                  Usando las credenciales de Google Drive. Solo necesitas autorizar Calendar.
                </div>
              )}

              {!calStatus?.has_credentials && (
                <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                  <p style={{ marginBottom: 8 }}>Primero configura Google Drive (sube <code style={{ color: "#818cf8" }}>credentials.json</code>) o sube un fichero específico para Calendar.</p>
                  <ol style={{ color: "#9ca3af", lineHeight: 1.8 }}>
                    <li>Abre <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>console.cloud.google.com</a></li>
                    <li>Habilita la <strong style={{ color: "#f9fafb" }}>Google Calendar API</strong> en tu proyecto</li>
                    <li>Configura Google Drive aquí arriba (mismas credenciales)</li>
                  </ol>
                </div>
              )}

              {calStatus?.has_credentials && !calStatus?.authorized && (
                <div style={{ marginBottom: 16 }}>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 12 }}>
                    Las credenciales están listas. Pulsa el botón para abrir el navegador y autorizar el acceso a tu calendario (solo lectura y escritura en tu cuenta).
                  </p>
                  <button
                    style={{ ...BTN_PRIMARY, opacity: calAuthing ? 0.6 : 1 }}
                    onClick={authorizeCalendar}
                    disabled={calAuthing}
                  >
                    {calAuthing ? "Abriendo navegador…" : "Autorizar Google Calendar"}
                  </button>
                </div>
              )}

              {calStatus?.authorized && (
                <div>
                  <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                    Aletheia puede leer y crear eventos en tu calendario. Puedes preguntar cosas como "¿Qué tengo hoy?" o "Crea una reunión el lunes a las 10h".
                  </p>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      style={{ ...BTN_GHOST }}
                      onClick={authorizeCalendar}
                      disabled={calAuthing}
                    >
                      {calAuthing ? "Reautorizando…" : "Reautorizar"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── TELEGRAM ── */}
          {activeSection === "telegram" && (
            <div style={SECTION}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 700, color: "#f9fafb", margin: 0 }}>Bot de Telegram</h2>
                <Badge ok={tgStatus?.configured} trueLabel="Configurado" falseLabel="Sin configurar" />
              </div>

              <p style={{ fontSize: 13, color: "#9ca3af", marginBottom: 16 }}>
                Permite chatear con Aletheia desde tu móvil y recibir notificaciones proactivas de HESTIA.
              </p>

              {/* Setup steps */}
              {!tgStatus?.configured && (
                <div style={{ background: "#060610", borderRadius: 10, padding: "1rem", border: "1px solid #374151", marginBottom: 16 }}>
                  <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.08em" }}>Paso 1 — Crear el bot</div>
                  <ol style={{ color: "#9ca3af", fontSize: 13, lineHeight: 2, margin: 0, paddingLeft: 18 }}>
                    <li>Abre Telegram y busca <strong style={{ color: "#f9fafb" }}>@BotFather</strong></li>
                    <li>Envía <code style={{ color: "#818cf8" }}>/newbot</code> y sigue las instrucciones</li>
                    <li>Copia el token que te dé (formato: <code style={{ color: "#818cf8" }}>1234567890:ABC…</code>)</li>
                  </ol>
                </div>
              )}

              {/* Token input */}
              <label style={LABEL}>Token del bot</label>
              <input
                type="password"
                value={tgForm.token}
                onChange={e => setTgForm(f => ({ ...f, token: e.target.value }))}
                placeholder="1234567890:ABCdefGHI..."
                style={{ ...INPUT, marginBottom: 14 }}
                autoComplete="off"
              />

              <label style={LABEL}>Tu ID de usuario (para notificaciones proactivas)</label>
              <input
                type="text"
                value={tgForm.admin_user_id}
                onChange={e => setTgForm(f => ({ ...f, admin_user_id: e.target.value }))}
                placeholder="123456789"
                style={{ ...INPUT, marginBottom: 4 }}
              />
              <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 14 }}>
                Envía <code style={{ color: "#818cf8" }}>/myid</code> a tu bot para obtener tu ID.
              </div>

              <label style={LABEL}>IDs permitidos (separados por comas — vacío = cualquiera)</label>
              <input
                type="text"
                value={tgForm.allowed_user_ids}
                onChange={e => setTgForm(f => ({ ...f, allowed_user_ids: e.target.value }))}
                placeholder="123456789, 987654321"
                style={{ ...INPUT, marginBottom: 16 }}
              />

              <div style={{ display: "flex", gap: 8 }}>
                <button style={{ ...BTN_PRIMARY, opacity: tgSaving ? 0.6 : 1 }} onClick={saveTelegram} disabled={tgSaving}>
                  {tgSaving ? "Guardando…" : "Guardar configuración"}
                </button>
                {tgStatus?.configured && (
                  <button style={BTN_GHOST} onClick={deleteTelegram}>Eliminar</button>
                )}
              </div>

              {tgStatus?.configured && (
                <div style={{ marginTop: 16, fontSize: 12, color: "#6b7280", padding: "10px 14px", borderRadius: 8, background: "#060610", border: "1px solid #374151" }}>
                  <div style={{ marginBottom: 4 }}>Para arrancar el bot:</div>
                  <code style={{ color: "#818cf8" }}>python start.py --telegram</code>
                  {tgStatus.admin_user_id && (
                    <div style={{ marginTop: 6 }}>Notificaciones → ID: <strong style={{ color: "#f9fafb" }}>{tgStatus.admin_user_id}</strong></div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── SISTEMA ── */}
          {activeSection === "system" && (
            <div style={SECTION}>
              <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, color: "#f9fafb" }}>Sistema</h2>
              <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 20 }}>
                Opciones avanzadas del motor cognitivo de Aletheia.
              </p>

              {/* v3 modes toggle */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px", background: "#060610", borderRadius: 10, border: "1px solid #374151", marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#f9fafb", marginBottom: 2 }}>
                    Modos cognitivos 3.0
                  </div>
                  <div style={{ fontSize: 12, color: "#6b7280" }}>
                    Activa el motor de 11 modos (OBSERVER, ANALYTICAL, STRATEGIC…). Si está desactivado usa el pipeline v1.
                  </div>
                </div>
                <button
                  onClick={() => setSystemForm(f => ({ ...f, use_v3_modes: !f.use_v3_modes }))}
                  style={{
                    width: 48, height: 26, borderRadius: 13, border: "none", cursor: "pointer",
                    background: systemForm.use_v3_modes ? "rgba(99,102,241,0.8)" : "#374151",
                    position: "relative", flexShrink: 0, transition: "background 0.2s",
                  }}
                  title={systemForm.use_v3_modes ? "Desactivar modos 3.0" : "Activar modos 3.0"}
                >
                  <span style={{
                    display: "block", width: 20, height: 20, borderRadius: "50%", background: "#fff",
                    position: "absolute", top: 3,
                    left: systemForm.use_v3_modes ? 25 : 3,
                    transition: "left 0.2s",
                  }} />
                </button>
              </div>

              {systemForm.use_v3_modes && (
                <div style={{ fontSize: 12, color: "#818cf8", padding: "8px 12px", borderRadius: 8, background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", marginBottom: 12 }}>
                  Motor 3.0 activo — OBSERVER enrutará cada mensaje al modo cognitivo más adecuado.
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button style={BTN_PRIMARY} onClick={saveSystem}>Guardar configuración del sistema</button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
