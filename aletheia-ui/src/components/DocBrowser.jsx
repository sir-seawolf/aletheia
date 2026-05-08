/**
 * DocBrowser — browse/search local Drive & OneDrive folders,
 * upload files, and send documents to the cognitive pipeline.
 *
 * Props:
 *   apiUrl: string
 *   onResult(result): called when the pipeline returns
 *   domain: string
 */
import { useState, useEffect, useRef } from "react";

const CARD = {
  background: "#0d0d1a",
  border: "1px solid #1f2937",
  borderRadius: 12,
  padding: "1rem 1.25rem",
  marginBottom: 12,
};

export default function DocBrowser({ apiUrl = "http://localhost:8000", onResult, domain = "general" }) {
  const [roots, setRoots] = useState({ local: [], gdrive_online: false, onedrive_online: false });
  const [browsePath, setBrowsePath] = useState("");
  const [browseItems, setBrowseItems] = useState([]);
  const [browseParent, setBrowseParent] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileText, setFileText] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [tab, setTab] = useState("browse");  // browse | search | upload | web | online | artifacts
  const [artifacts, setArtifacts]     = useState([]);
  const [artYear, setArtYear]         = useState(new Date().getFullYear());
  const [artSummary, setArtSummary]   = useState(null);
  const [gmailReady, setGmailReady]   = useState(null);
  const [scanning, setScanning]       = useState(false);
  const [scanResult, setScanResult]   = useState(null);
  // Web tools
  const [webQuery, setWebQuery]       = useState("");
  const [webResults, setWebResults]   = useState([]);
  const [urlInput, setUrlInput]       = useState("");
  const [urlResult, setUrlResult]     = useState(null);
  const [addFolderPath, setAddFolderPath] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetch(`${apiUrl}/api/docs/roots`)
      .then(r => r.json())
      .then(setRoots)
      .catch(() => {});
    fetch(`${apiUrl}/api/gmail/status`)
      .then(r => r.json())
      .then(d => setGmailReady(d.available))
      .catch(() => setGmailReady(false));
  }, [apiUrl]);

  /* ── Browse ──────────────────────────────────────────────────────── */
  async function browse(path) {
    setLoading(true);
    try {
      const r = await fetch(`${apiUrl}/api/docs/browse?path=${encodeURIComponent(path)}`);
      const d = await r.json();
      if (d.error) { setStatus(d.error); return; }
      setBrowsePath(d.path || "");
      setBrowseParent(d.parent || "");
      setBrowseItems(d.items || d.roots?.map(rt => ({ type: "dir", name: rt.name, path: rt.path })) || []);
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { browse(""); }, []);

  async function openItem(item) {
    if (item.type === "dir") {
      browse(item.path);
    } else {
      await loadFile(item.path);
    }
  }

  async function loadFile(path) {
    setLoading(true);
    setStatus("Extrayendo texto…");
    try {
      const r = await fetch(`${apiUrl}/api/docs/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      const d = await r.json();
      if (d.ok === false) { setStatus(d.error); return; }
      setSelectedFile({ name: d.name, path: d.path, size_kb: d.size_kb });
      setFileText(d.text || "");
      setStatus(`Documento cargado: ${d.name}`);
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ── Search ──────────────────────────────────────────────────────── */
  async function runSearch() {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setSearchResults([]);
    try {
      const r = await fetch(`${apiUrl}/api/docs/search?q=${encodeURIComponent(searchQuery)}`);
      const d = await r.json();
      setSearchResults(d.results || []);
      if ((d.results || []).length === 0) setStatus("Sin resultados.");
      else setStatus("");
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ── Upload ──────────────────────────────────────────────────────── */
  async function uploadFile(file) {
    setLoading(true);
    setStatus(`Subiendo ${file.name}…`);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("domain", domain);
      if (question) fd.append("question", question);
      const r = await fetch(`${apiUrl}/api/docs/upload`, { method: "POST", body: fd });
      const d = await r.json();
      setStatus(`Procesado: ${file.name}`);
      if (onResult) onResult(d);
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ── Send loaded doc to pipeline ─────────────────────────────────── */
  async function analyzeLoaded() {
    if (!fileText) return;
    setLoading(true);
    setStatus("Analizando…");
    try {
      const r = await fetch(`${apiUrl}/api/docs/ingest_text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: fileText, domain, question }),
      });
      const d = await r.json();
      setStatus("Análisis completo.");
      if (onResult) onResult(d);
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  }

  /* ── Add custom folder ───────────────────────────────────────────── */
  async function addFolder() {
    if (!addFolderPath.trim()) return;
    const r = await fetch(`${apiUrl}/api/docs/add_folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: addFolderPath }),
    });
    const d = await r.json();
    if (d.error) { setStatus(d.error); return; }
    setRoots(prev => ({ ...prev, local: d.roots }));
    setAddFolderPath("");
    browse("");
  }

  const scanGmail = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const r = await fetch(`${apiUrl}/api/gmail/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year: artYear }),
      });
      const d = await r.json();
      setScanResult(d);
      if (!d.error) await loadArtifacts(artYear);
    } catch (e) {
      setScanResult({ error: e.message });
    } finally {
      setScanning(false);
    }
  };

  const runWebSearch = async () => {
    if (!webQuery.trim()) return;
    setLoading(true);
    setWebResults([]);
    try {
      const r = await fetch(`${apiUrl}/api/search?q=${encodeURIComponent(webQuery)}&max_results=8`);
      const d = await r.json();
      setWebResults(d.results || []);
      if (!d.results?.length) setStatus("Sin resultados.");
    } catch (e) { setStatus(e.message); }
    finally { setLoading(false); }
  };

  const ingestUrl = async () => {
    const url = urlInput.trim();
    if (!url) return;
    setLoading(true);
    setUrlResult(null);
    setStatus("Leyendo página…");
    try {
      const r = await fetch(`${apiUrl}/api/docs/ingest_url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, domain }),
      });
      const d = await r.json();
      setUrlResult(d);
      setStatus(d.ok ? `Página guardada: ${d.title}` : `Error: ${d.error}`);
      if (d.ok && d.analysis && onResult) onResult({ llm_insight: d.analysis, domain, question: url });
    } catch (e) { setStatus(e.message); }
    finally { setLoading(false); }
  };

  const loadArtifacts = async (year) => {
    setLoading(true);
    try {
      const params = year ? `&date_from=${year}-01-01&date_to=${year}-12-31` : "";
      const [artR, sumR] = await Promise.all([
        fetch(`${apiUrl}/api/artifacts?domain=finanzas&limit=200${params}`).then(r => r.json()),
        fetch(`${apiUrl}/api/artifacts/financial_summary?year=${year || 0}`).then(r => r.json()),
      ]);
      setArtifacts(Array.isArray(artR) ? artR : []);
      setArtSummary(sumR);
    } catch (e) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  };

  const tabStyle = (t) => ({
    padding: "6px 14px",
    border: "none",
    background: tab === t ? "rgba(99,102,241,0.2)" : "transparent",
    color: tab === t ? "#818cf8" : "#6b7280",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 13,
    fontWeight: tab === t ? 600 : 400,
  });

  const fileIcon = (suffix) => {
    const map = { ".pdf": "📄", ".docx": "📝", ".doc": "📝", ".csv": "📊", ".json": "🗂", ".md": "📋", ".txt": "📃" };
    return map[suffix] || "📄";
  };

  return (
    <div style={{ color: "#f9fafb" }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
        {[["browse", "Explorar"], ["search", "Buscar"], ["upload", "Subir archivo"], ["web", "Web"], ["online", "Online"], ["artifacts", "Artefactos"]].map(([t, l]) => (
          <button key={t} style={tabStyle(t)} onClick={() => setTab(t)}>{l}</button>
        ))}
      </div>

      {status && (
        <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 10 }}>{status}</div>
      )}

      {/* ── BROWSE tab ── */}
      {tab === "browse" && (
        <div>
          {browsePath && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <button onClick={() => browse(browseParent)} style={{ background: "transparent", border: "1px solid #374151", color: "#9ca3af", borderRadius: 6, padding: "3px 10px", cursor: "pointer", fontSize: 12 }}>
                ← Atrás
              </button>
              <span style={{ fontSize: 12, color: "#4b5563", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {browsePath}
              </span>
            </div>
          )}

          {browseItems.length === 0 && !loading && (
            <div style={{ color: "#6b7280", fontSize: 13 }}>
              No se detectaron drives locales. Añade una carpeta abajo.
            </div>
          )}

          <div style={{ maxHeight: 280, overflowY: "auto" }}>
            {browseItems.map((item, i) => (
              <div
                key={i}
                onClick={() => openItem(item)}
                style={{
                  padding: "8px 12px",
                  borderRadius: 8,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 13,
                  color: item.type === "dir" ? "#a5b4fc" : "#e5e7eb",
                  background: "transparent",
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => e.currentTarget.style.background = "#1f2937"}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}
              >
                <span>{item.type === "dir" ? "📁" : fileIcon(item.suffix)}</span>
                <span style={{ flex: 1 }}>{item.name}</span>
                {item.size_kb && <span style={{ color: "#4b5563", fontSize: 11 }}>{item.size_kb} KB</span>}
              </div>
            ))}
          </div>

          {/* Add folder */}
          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <input
              value={addFolderPath}
              onChange={e => setAddFolderPath(e.target.value)}
              placeholder="Añadir carpeta personalizada (ruta completa)…"
              style={{ flex: 1, padding: "6px 10px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 12, outline: "none" }}
            />
            <button onClick={addFolder} style={{ padding: "6px 14px", background: "#374151", border: "none", borderRadius: 8, color: "#9ca3af", cursor: "pointer", fontSize: 12 }}>
              Añadir
            </button>
          </div>
        </div>
      )}

      {/* ── SEARCH tab ── */}
      {tab === "search" && (
        <div>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && runSearch()}
              placeholder="Buscar en todos los drives…"
              style={{ flex: 1, padding: "8px 12px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 13, outline: "none" }}
            />
            <button onClick={runSearch} disabled={loading} style={{ padding: "8px 16px", background: "#4f46e5", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", fontSize: 13 }}>
              Buscar
            </button>
          </div>
          {searchResults.map((r, i) => (
            <div key={i} style={{ ...CARD, cursor: "pointer" }} onClick={() => loadFile(r.path)}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{fileIcon(r.suffix)} {r.name}</span>
                <span style={{ color: "#4b5563", fontSize: 11 }}>{r.size_kb} KB · {r.match}</span>
              </div>
              {r.excerpt && <div style={{ fontSize: 12, color: "#6b7280" }}>{r.excerpt}</div>}
            </div>
          ))}
        </div>
      )}

      {/* ── UPLOAD tab ── */}
      {tab === "upload" && (
        <div>
          {/* Bank statement upload */}
          <div style={{ marginBottom: 16, padding: "12px 16px", background: "#060610", border: "1px solid #1f2937", borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 8, fontWeight: 600 }}>🏦 Extracto bancario (CSV / XLSX / OFX)</div>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.ofx,.qfx"
              style={{ display: "none" }}
              id="bank-upload"
              onChange={async e => {
                const file = e.target.files[0];
                if (!file) return;
                setLoading(true);
                setStatus(`Procesando extracto: ${file.name}…`);
                try {
                  const fd = new FormData();
                  fd.append("file", file);
                  fd.append("domain", domain);
                  const r = await fetch(`${apiUrl}/api/docs/bank_statement`, { method: "POST", body: fd });
                  const d = await r.json();
                  if (d.ok) {
                    setStatus(`✓ ${d.count} transacciones de ${d.bank} · neto ${d.net?.toFixed(2)} €`);
                  } else {
                    setStatus(`Error: ${d.error}`);
                  }
                } catch (ex) { setStatus(ex.message); }
                finally { setLoading(false); }
              }}
            />
            <label htmlFor="bank-upload" style={{ padding: "7px 16px", background: "#374151", borderRadius: 8, color: "#d1d5db", fontSize: 13, cursor: "pointer", display: "inline-block" }}>
              Subir extracto
            </label>
          </div>

          <div
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: "2px dashed #374151",
              borderRadius: 12,
              padding: "2rem",
              textAlign: "center",
              cursor: "pointer",
              color: "#6b7280",
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            {loading ? "Procesando…" : "Haz clic o arrastra un archivo aquí"}
            <br />
            <span style={{ fontSize: 11 }}>PDF, DOCX, TXT, MD, CSV, JSON</span>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md,.csv,.json,.rst"
            style={{ display: "none" }}
            onChange={e => { if (e.target.files[0]) uploadFile(e.target.files[0]); }}
          />
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Pregunta opcional sobre el documento… (deja vacío para análisis automático)"
            rows={2}
            style={{ width: "100%", padding: "8px 12px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 13, resize: "vertical", boxSizing: "border-box", outline: "none" }}
          />
        </div>
      )}

      {/* ── WEB tab ── */}
      {tab === "web" && (
        <div>
          {/* Web search */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 8, fontWeight: 600 }}>🔍 Búsqueda web (DuckDuckGo)</div>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <input
                value={webQuery}
                onChange={e => setWebQuery(e.target.value)}
                onKeyDown={e => e.key === "Enter" && runWebSearch()}
                placeholder="Buscar en internet…"
                style={{ flex: 1, padding: "8px 12px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 13, outline: "none" }}
              />
              <button onClick={runWebSearch} disabled={loading || !webQuery.trim()} style={{ padding: "8px 16px", background: "#4f46e5", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", fontSize: 13 }}>
                Buscar
              </button>
            </div>
            <div style={{ maxHeight: 220, overflowY: "auto" }}>
              {webResults.map((r, i) => (
                r.error ? (
                  <div key={i} style={{ color: "#f87171", fontSize: 13 }}>{r.error}</div>
                ) : (
                  <div key={i} style={{ ...CARD, marginBottom: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>
                      <a href={r.url} target="_blank" rel="noreferrer" style={{ color: "#818cf8", textDecoration: "none" }}>
                        {r.title}
                      </a>
                    </div>
                    <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 4 }}>{r.url}</div>
                    {r.snippet && <div style={{ fontSize: 12, color: "#9ca3af" }}>{r.snippet.slice(0, 160)}</div>}
                    <div style={{ marginTop: 6, display: "flex", gap: 6 }}>
                      <button
                        onClick={() => { setUrlInput(r.url); ingestUrl(); }}
                        style={{ fontSize: 11, padding: "2px 8px", background: "transparent", border: "1px solid #374151", borderRadius: 6, color: "#6b7280", cursor: "pointer" }}
                      >
                        Leer e ingestar
                      </button>
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>

          {/* URL ingestion */}
          <div>
            <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 8, fontWeight: 600 }}>🌐 Leer página web por URL</div>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <input
                value={urlInput}
                onChange={e => setUrlInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && ingestUrl()}
                placeholder="https://..."
                style={{ flex: 1, padding: "8px 12px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 13, outline: "none", fontFamily: "monospace" }}
              />
              <button onClick={ingestUrl} disabled={loading || !urlInput.trim()} style={{ padding: "8px 16px", background: "#059669", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", fontSize: 13 }}>
                Leer
              </button>
            </div>
            {urlResult && (
              <div style={{ ...CARD, borderColor: urlResult.ok ? "#059669" : "#ef4444" }}>
                {urlResult.ok ? (
                  <>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{urlResult.title}</div>
                    <div style={{ fontSize: 11, color: "#4b5563", marginBottom: 6 }}>{urlResult.chars} caracteres · guardado como artefacto</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{urlResult.excerpt?.slice(0, 300)}…</div>
                  </>
                ) : (
                  <div style={{ color: "#f87171", fontSize: 13 }}>{urlResult.error}</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── ONLINE tab ── */}
      {tab === "online" && (
        <div>
          <div style={{ ...CARD }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Google Drive</div>
            {roots.gdrive_online
              ? <span style={{ color: "#4ade80", fontSize: 13 }}>✓ Credenciales configuradas</span>
              : (
                <div style={{ fontSize: 12, color: "#9ca3af" }}>
                  Coloca <code>gdrive_credentials.json</code> en <code>PALACE/config/</code> para acceso online.
                  <br />
                  <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>
                    Google Cloud Console →
                  </a>
                </div>
              )
            }
          </div>
          <div style={{ ...CARD }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>OneDrive</div>
            {roots.onedrive_online
              ? <span style={{ color: "#4ade80", fontSize: 13 }}>✓ Credenciales configuradas</span>
              : (
                <div style={{ fontSize: 12, color: "#9ca3af" }}>
                  Coloca <code>onedrive_config.json</code> en <code>PALACE/config/</code> para acceso online.
                  <br />
                  <a href="https://portal.azure.com/" target="_blank" rel="noreferrer" style={{ color: "#818cf8" }}>
                    Azure App Registrations →
                  </a>
                </div>
              )
            }
          </div>
        </div>
      )}

      {/* ── ARTIFACTS tab ── */}
      {tab === "artifacts" && (
        <div>
          {/* Year selector + action bar */}
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
            <select
              value={artYear}
              onChange={e => setArtYear(Number(e.target.value))}
              style={{ padding: "6px 10px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 13, outline: "none" }}
            >
              {[0, new Date().getFullYear(), new Date().getFullYear()-1, new Date().getFullYear()-2].map(y => (
                <option key={y} value={y}>{y === 0 ? "Todos los años" : y}</option>
              ))}
            </select>
            <button
              onClick={() => loadArtifacts(artYear || null)}
              disabled={loading || scanning}
              style={{ padding: "6px 16px", background: "#374151", border: "none", borderRadius: 8, color: "#d1d5db", cursor: "pointer", fontSize: 13 }}
            >
              {loading ? "Cargando…" : "Actualizar"}
            </button>
            {gmailReady && (
              <button
                onClick={scanGmail}
                disabled={scanning || loading}
                style={{ padding: "6px 16px", background: scanning ? "#374151" : "linear-gradient(135deg,#4f46e5,#7c3aed)", border: "none", borderRadius: 8, color: "#fff", cursor: scanning ? "not-allowed" : "pointer", fontSize: 13, fontWeight: 600 }}
              >
                {scanning ? "Escaneando correo…" : "✉ Escanear Gmail"}
              </button>
            )}
            {gmailReady === false && (
              <span style={{ fontSize: 12, color: "#6b7280" }}>
                Gmail no configurado —{" "}
                <span style={{ color: "#818cf8", cursor: "pointer", textDecoration: "underline" }}
                  onClick={() => window.dispatchEvent(new CustomEvent("aletheia:nav", { detail: "settings" }))}>
                  Configurar →
                </span>
              </span>
            )}
          </div>

          {/* Scan result feedback */}
          {scanResult && !scanResult.error && (
            <div style={{ ...CARD, borderColor: "#4ade80", marginBottom: 12, fontSize: 13 }}>
              <div style={{ color: "#4ade80", fontWeight: 600, marginBottom: 4 }}>✓ Escaneo completado</div>
              <div style={{ color: "#9ca3af" }}>
                {scanResult.processed} correos revisados · {scanResult.new} nuevos · {scanResult.updated} actualizados · {scanResult.duplicate} ya existían
              </div>
              {scanResult.invoices?.length > 0 && (
                <div style={{ color: "#f9fafb", marginTop: 4 }}>
                  {scanResult.invoices.length} facturas/gastos detectados · Total:{" "}
                  <strong>{scanResult.invoices.reduce((s, i) => s + (i.amount || 0), 0).toFixed(2)} €</strong>
                </div>
              )}
            </div>
          )}
          {scanResult?.error && (
            <div style={{ ...CARD, borderColor: "#ef4444", marginBottom: 12, fontSize: 13, color: "#f87171" }}>
              {scanResult.error}
            </div>
          )}

          {/* Financial summary */}
          {artSummary && artSummary.count > 0 && (
            <div style={{ ...CARD, borderColor: "#4f46e5", marginBottom: 12 }}>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em" }}>Total</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#f9fafb" }}>{artSummary.total?.toFixed(2)} €</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em" }}>IVA</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#818cf8" }}>{artSummary.total_vat?.toFixed(2)} €</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em" }}>Documentos</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#4ade80" }}>{artSummary.count}</div>
                </div>
              </div>
              {artSummary.by_month && Object.keys(artSummary.by_month).length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>Por mes</div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {Object.entries(artSummary.by_month).map(([month, amount]) => (
                      <div key={month} style={{ background: "#111827", borderRadius: 6, padding: "4px 10px", fontSize: 12 }}>
                        <span style={{ color: "#6b7280" }}>{month}</span>
                        <span style={{ color: "#f9fafb", marginLeft: 6 }}>{amount.toFixed(0)} €</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {artifacts.length === 0 && !loading && !scanning && (
            <div style={{ ...CARD, borderStyle: "dashed", borderColor: "#374151", textAlign: "center", padding: "2rem" }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
              {gmailReady ? (
                <>
                  <div style={{ color: "#9ca3af", fontSize: 14, marginBottom: 16 }}>
                    No hay documentos almacenados todavía.
                    <br />
                    Escanea tu correo para importar facturas y gastos automáticamente.
                  </div>
                  <button
                    onClick={scanGmail}
                    disabled={scanning}
                    style={{ padding: "10px 24px", background: "linear-gradient(135deg,#4f46e5,#7c3aed)", border: "none", borderRadius: 10, color: "#fff", fontWeight: 700, fontSize: 14, cursor: "pointer" }}
                  >
                    ✉ Escanear Gmail {artYear}
                  </button>
                  <div style={{ marginTop: 12, fontSize: 12, color: "#4b5563" }}>
                    o arrastra un PDF/DOCX al tab "Subir archivo"
                  </div>
                </>
              ) : (
                <>
                  <div style={{ color: "#9ca3af", fontSize: 14, marginBottom: 16 }}>
                    Conecta Gmail para importar facturas automáticamente,<br />o sube documentos manualmente.
                  </div>
                  <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
                    <button
                      onClick={() => setTab("upload")}
                      style={{ padding: "8px 20px", background: "#374151", border: "none", borderRadius: 8, color: "#d1d5db", fontSize: 13, cursor: "pointer" }}
                    >
                      Subir documento
                    </button>
                    <button
                      onClick={() => window.dispatchEvent(new CustomEvent("aletheia:nav", { detail: "settings" }))}
                      style={{ padding: "8px 20px", background: "linear-gradient(135deg,#4f46e5,#7c3aed)", border: "none", borderRadius: 8, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" }}
                    >
                      Configurar Gmail →
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Artifact list */}
          <div style={{ maxHeight: 320, overflowY: "auto" }}>
            {artifacts.length === 0 && (loading || scanning) && (
              <div style={{ color: "#6b7280", fontSize: 13, padding: "1rem" }}>
                {scanning ? "Escaneando correo…" : "Cargando artefactos…"}
              </div>
            )}
            {artifacts.map((a, i) => {
              const fin = a.financial || {};
              return (
                <div key={i} style={{ ...CARD, cursor: "pointer" }} onClick={() => loadFile(a.text_path)}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>
                        {a.type === "invoice" ? "🧾" : a.type === "email_excerpt" ? "✉️" : "📄"}{" "}
                        {a.filename || a.id.slice(0, 12)}
                        {a.version > 1 && <span style={{ marginLeft: 6, fontSize: 10, color: "#818cf8" }}>v{a.version}</span>}
                      </div>
                      <div style={{ fontSize: 11, color: "#4b5563", marginTop: 2 }}>
                        {a.source?.split(":")[0]} · {a.source_date?.slice(0, 10) || "sin fecha"}
                      </div>
                      {fin.vendor && <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 2 }}>{fin.vendor}</div>}
                    </div>
                    {fin.amount > 0 && (
                      <div style={{ textAlign: "right", marginLeft: 12 }}>
                        <div style={{ fontWeight: 700, color: "#f9fafb" }}>{fin.amount?.toFixed(2)} {fin.currency || "€"}</div>
                        {fin.vat > 0 && <div style={{ fontSize: 11, color: "#6b7280" }}>IVA: {fin.vat?.toFixed(2)}</div>}
                      </div>
                    )}
                  </div>
                  {fin.concept && (
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>{fin.concept}</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected file preview + analyze button */}
      {selectedFile && (
        <div style={{ ...CARD, marginTop: 16, borderColor: "#4f46e5" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>📄 {selectedFile.name}</span>
            <span style={{ color: "#4b5563", fontSize: 11 }}>{selectedFile.size_kb} KB</span>
          </div>
          <div style={{ fontSize: 12, color: "#6b7280", maxHeight: 80, overflow: "hidden", marginBottom: 10 }}>
            {fileText.slice(0, 300)}…
          </div>
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Pregunta sobre el documento… (opcional)"
            rows={2}
            style={{ width: "100%", padding: "6px 10px", background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb", fontSize: 12, resize: "vertical", boxSizing: "border-box", outline: "none", marginBottom: 8 }}
          />
          <button
            onClick={analyzeLoaded}
            disabled={loading}
            style={{ padding: "8px 20px", background: "linear-gradient(135deg,#4f46e5,#7c3aed)", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600 }}
          >
            {loading ? "Analizando…" : "Analizar con Aletheia"}
          </button>
        </div>
      )}
    </div>
  );
}
