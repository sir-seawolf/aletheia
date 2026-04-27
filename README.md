# Aletheia Kernel v1.0 - Cognitive Decision Engine

## 🎯 Status: PRODUCTION READY

**FASE 1 COMPLETE: Contract enforced, pipeline stabilized, tests blinded. v1.0.0**

## 🚀 Quick Start (Windows/PowerShell)

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

## 🧠 Architecture Layers (All Delivered)

### CAPA 1 - Contract Lock
```
core/contracts/contract_lock.py
- validate_final_report()
- normalize_report() 
- freeze_contract_version()
```
**ALL DecisionReport pass here.**

### CAPA 2 - Simple Orchestrator Router
```
 /api/simulate → explorer → simulator → guardian → lock → memory
```
No validation/trace/fallback in orchestrator.

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
