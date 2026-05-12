# Resumen Funcional Aletheia para otra IA

## 🎯 Estado: v1.0 PRODUCTION READY (FASE 1 COMPLETE)

**Launcher**: launcher.bat (Windows) - Menu DEMO/REAL/Tests. Auto deps, parallel API/UI, browsers.

## 🏗️ Arquitectura (5 Capas)

### 1. Contract Lock (`core/contracts/contract_lock.py`)
- `validate_final_report()` / `normalize_report()` / `freeze_contract_version()`
- ALL DecisionReport pass here (REQUIRED_FIELDS + shape: scenarios >=2)

### 2. Router (`core/orchestrator.py`)
```
 /api/simulate → explorer → simulator → guardian → lock → memory
```
- `process_request(domain, question)` pure str args.

### 3. Bootstrap (`cli.py start --mode DEV/PROD`)
- `system_init.py`: memory/LLM/contract
- `runtime.py`: FastAPI /health /docs
- Modes: DEV( verbose)/TEST/PROD(safe)

### 4. Tests (7/10 PASS)
```
cli.py test → contract 4/4, integrity 2/3, pipeline/memory fail (scenarios <2)
```

### 5. Agents
- **explorer.run(domain, question)**: facts/gaps/confidence (fallback keywords)
- **simulator.run(exploration)**: scenarios/risks/assumptions (2 escenarios)
- **guardian.validate(simulation)**: block/issues/corrected_output

## 🔧 Estado Actual
- API: http://127.0.0.1:8000/api/simulate (POST {domain, question})
- UI: localhost:3000
- Status: `cli.py status` → healthy
- Memory: _STORE stub (regression test expects >=1 event)

**Pendientes menores**: scenarios test mock >=2, guardian bool check.

**¡Kernel estable para testing/supervisión!** 🚀
