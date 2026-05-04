# Aletheia CEL v1.1 - Cognitive Execution Layer Active

## 🎯 Status: PRODUCTION READY

**FASE 2 CEL COMPLETE: ACO + LLMRouter fused → Cognitive Executive. Ruta actualizada! v1.1.0**

## 🚀 Quick Start (Windows/PowerShell)

### 🎯 ONE-CLICK LAUNCHER (New!)
```
double-click launcher.bat
```
**Menu**: 1=DEMO (DEV/testing), 2=REAL (PROD/live), 3=Tests/Status.
Auto: pip/npm install, tests, reset DB, API+UI servers, opens browsers (localhost:8000/docs ^& 3000).

### 📋 Manual (Original):
```
cd d:/Proyectos/aletheia-core/aletheia
pip install -r requirements.txt pytest click uvicorn
python cli.py reset
python cli.py status  # Health check
python cli.py test    # 7/7 PASS
python cli.py start --mode DEV  # Kernel + API
```


**Test API:**
```
Invoke-RestMethod "http://127.0.0.1:8000/api/simulate" -Method POST -ContentType "application/json" -Body (@{domain="finanzas"; question="¿Dejo trabajo?"} | ConvertTo-Json)
```

**Docs:** http://127.0.0.1:8000/docs

## Arquitectura actual vs roadmap
**Funciona hoy v1.1 (PRODUCCIÓN):**
- Pipeline base (orchestrator + agents + guardian)
- ACO v1 middleware
- LLM Router + Cache + Palace

**DISEÑADO (esqueleros):**
- ACO v2 engine, v3 meta

**ROADMAP:**
- ACO v4+, FSSL, CBL, CGD, CFC (Sprint 4+)

## Limitaciones conocidas
- LLMCacheV2.get() signature: requires context=dict (known bug from inconsistent calls)
- Context.__init__() user_id via **kwargs (minor)
- Pydantic V1 warnings (ignore)

## 🧠 Architecture Layers (All Delivered)

### CAPA 1 - Contract Lock
```
core/contracts/contract_lock.py
- validate_final_report()
- normalize_report() 
- freeze_contract_version()
```
**ALL DecisionReport pass here.**

### CAPA 2 - CEL Orchestrator (New!)
```
 /api/simulate → ACO → **CEL (cognitive fusion)** → explorer → simulator → guardian → lock → memory
```
ACO policy → CEL (memory/palace/cost) → router.generate → augmented input

### CAPA 3 - Bootstrap System
```
python cli.py start
- system_init.py: memory/LLM/contract
- runtime.py: FastAPI lightweight
- healthcheck.py: /health full status
```

### CAPA 4 - System Tests
```
tests/system/
- test_contract_lock.py: fails invalid
- test_contract_integrity.py: broken agents blocked
- test_memory_regression.py: consistent evolution
- test_full_pipeline.py: end-to-end mock
```

### CAPA 5 - Clean Modes
```
config/modes.py
DEV/TEST/PROD - verbose/deterministic/safe
```

## 🔧 Known (Non-Critical)

1. **Pydantic V1 warnings**: Migrate V2 post-v1.0
2. **Orchestrator legacy**: Complex OK (API router primary)

## 📊 Verified
- [x] python cli.py test → 7/7 PASS
- [x] python cli.py status → Healthy
- [x] API /simulate → DecisionReport locked
- [x] No startup crashes
- [x] CLI stable

**¡Kernel v1.0 mission accomplished!** 🚀
