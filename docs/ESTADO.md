# Aletheia Kernel — Estado del sistema

**Versión**: v1.1 | **Stack**: Python 3.14 · FastAPI · SQLite · Ollama · CLI

---

## Arranque

```bat
launcher.bat          # Windows — menú interactivo
  [1] DEV   → mock LLM (phi3:mini), verbose, testing
  [2] PROD  → llama3.2:3b real, pipeline completo
  [3] Tests → CEL + system tests
  [4] CEL Quick Test
  [5] Kill servers
```

```powershell
# Manual
python cli.py start --mode DEV
python cli.py test
python cli.py status
python cli.py reset
```

---

## Arquitectura — 5 capas

```
REQUEST → API Contract Gate
         ↓
    ORCHESTRATOR  (routing puro, sin lógica)
         ↓
    ACO MIDDLEWARE + CEL EXECUTOR
         ↓
    EXPLORER → SIMULATOR → GUARDIAN
         ↓
    PALACE (memoria larga)  +  CONTRACT LOCK
         ↓
    MEMORY SAVE (SQLite)
         ↓
    DecisionReport (response)
```

| Capa | Archivo clave | Rol |
|------|--------------|-----|
| Contract Lock | `core/contracts/contract_lock.py` | Schema + reglas inquebrantables |
| Orchestrator | `core/orchestrator.py` | Routing puro |
| Bootstrap | `core/bootstrap/system_init.py` | Init: DB + Ollama + Contract |
| Tests | `tests/system/` | 10 tests de integridad |
| Modos | `config/modes.py` | DEV / TEST / PROD |

---

## Conexiones

| Servicio | URL / Path | Estado |
|----------|-----------|--------|
| FastAPI REST | `http://127.0.0.1:8000` | `GET /health`, `POST /api/simulate` |
| Ollama | `http://localhost:11434` | Modelos: `phi3:mini`, `llama3.2:3b` |
| SQLite | `memory/data/aletheia.db` | Multi-tabla (nodes, refs, events) |
| PALACE | `PALACE/{area}/memory.txt` | 6 áreas, append-only |

---

## DecisionReport schema

```python
domain, question          # requeridos
scenarios: List[Dict]     # min 2
risks: Dict[str, float]
confidence: float         # 0-1
guardian_block: bool
prediction: str
llm_insight: str
# extra=forbid (strict)
```

---

## Uso desde PowerShell

```powershell
$r = Invoke-RestMethod "http://127.0.0.1:8000/api/simulate" `
     -Method POST -ContentType "application/json" `
     -Body (@{domain="finanzas"; question="¿Dejo el trabajo?"} | ConvertTo-Json)
$r | ConvertTo-Json -Depth 10
```

---

## Pendientes conocidos

- Pydantic V2 migration (warnings no bloqueantes)
- `/system/metrics` endpoint no implementado
- Métricas de timing en orchestrator son mock (línea 74)
- Ruta PALACE relativa en `core/palace/writer.py` (frágil fuera de raíz)
