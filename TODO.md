# UI Revision — Coherencia, Velocidad y Botones LLM

**Status:** 🔄 EN CURSO — reanudar aquí

---

## Completado en esta sesión

### Fixes de rendimiento (ACT completado)

- [x] `core/bootstrap/runtime.py` — `/api/status`: `requests.get()` síncrono envuelto en `run_in_executor` (ya no bloquea el event loop)
- [x] `core/config/preferences.py` — `load()` con caché en memoria TTL 5s; se invalida en `save()`
- [x] `core/bootstrap/runtime.py` — `init_db()` eliminado del loop de `/api/status` (ya se llama en startup)
- [x] `aletheia-ui/src/App.js` — `<main>` tiene `marginRight: panelOpen ? 300 : 40` → el ThinkingPanel ya no solapa el contenido

---

## Pendiente — reanudar aquí

### Backend (`core/bootstrap/runtime.py`)

- [x] **Fix nav de voz** en `setup_status()` — `"nav": "settings", "section": "voice"`
- [x] **`POST /api/llm/test`** — prueba conexión al proveedor activo
- [x] **`GET /api/llm/ollama/models`** — lista modelos instalados en Ollama en tiempo real

### Frontend

- [x] **`SettingsPage.jsx` — Sección LLM rediseñada** con tarjetas LOCAL (Ollama) y ONLINE (Cloud)
- [x] **`Sidebar.jsx` — Eliminado `"dashboard"` de VIEWS**
- [x] **`App.js` — Código muerto eliminado** + chip LLM mejorado (`LOCAL` / `CLOUD · proveedor`)

---

## Contexto de diseño

- Stack UI: React + inline styles (sin Tailwind en producción)
- Paleta: bg `#060610`, surface `#0d0d1a`, border `#1f2937`, accent `#818cf8`, verde `#4ade80`, amarillo `#fbbf24`, rojo `#f87171`
- API base: `REACT_APP_API_URL` o `http://localhost:8000`
- Proveedor activo en `PALACE/config/preferences.json` → sección `llm.provider`
- Para activar proveedor: `PATCH /api/settings/preferences` con `{ section: "llm", updates: { provider, model, api_key } }`
