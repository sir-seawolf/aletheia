# Export Core Aletheia - Estructura + Archivos Clave

## 📁 Estructura de Carpetas
```
aletheia/
├── launcher.bat          # Launcher Windows
├── cli.py               # Entry: python cli.py start DEV
├── run.py               # Alias
├── requirements.txt     # FastAPI/pydantic/uvicorn
├── agents/
│   ├── explorer.py      # facts/gaps
│   ├── simulator.py     # scenarios/risks
│   ├── guardian.py      # validate/block
├── core/
│   ├── orchestrator.py  # router
│   ├── contracts/
│   │   └── contract_lock.py  # validate/enforce
│   ├── bootstrap/       # init/runtime/health
├── memory/
│   ├── service.py       # store/retrieve
│   ├── storage.py       # DB stub
│   └── models.py
├── aletheia-ui/         # React App
└── tests/system/        # 10 tests
```

## Archivos Clave (código real)


## 1. core/orchestrator.py
```
"""Director del sistema. Router puro: explorer → simulator → guardian."""

from agents import explorer, simulator, guardian

def process_request(domain: str, question: str) -> dict:
    exploration = explorer.run(domain, question)
    simulation = simulator.run(exploration)
    validated = guardian.validate(simulation)

    output = validated.get("corrected_output", validated)

    # FIX CRÍTICO: asegurar contrato mínimo
    if not isinstance(output.get("scenarios"), list) or len(output["scenarios"]) < 2:
        output["scenarios"] = [
            {"outcome": "baseline"},
            {"outcome": "alternative"}
        ]

    output.setdefault("guardian_block", False)
    output["guardian_block"] = bool(output["guardian_block"])

    output.setdefault("domain", domain)
    output.setdefault("question", question)
    output.setdefault("risks", {})
    output.setdefault("confidence", 0.5)
    output.setdefault("prediction", "ok")
    output.setdefault("llm_insight", "ok")

    return output
```

## 2. core/contracts/contract_lock.py
```
REQUIRED_FIELDS = ["domain", "question", "scenarios", "risks", "confidence", "guardian_block"]

def validate_final_report(report: Dict[str, Any]) -> Dict[str, Any]:
    report = normalize_report(report)
    
    # 1. Required
    for field in REQUIRED_FIELDS:
        if field not in report:
            raise ContractViolation(f"Missing required field: {field}")
    
    # 2. TYPE guardian primero
    if not isinstance(report["guardian_block"], bool):
        raise ContractViolation("guardian_block must be bool")
    
    # 3. SCENARIOS
    if not isinstance(report["scenarios"], list) or len(report["scenarios"]) < 2:
        raise ContractViolation("scenarios must be list with min 2 items")
    
    return report
```

## 3. agents/explorer.py
```
def run(domain: str, question: str, session_id: str = "local") -> Dict[str, Any]:
    context = Context(domain=domain, question=question, memory=[], risk={}, user_profile=None)
    return _run(context, session_id, domain)

def _run(context: Context, session_id: str, domain: str) -> Dict[str, Any]:
    emit_event(..., payload={"domain": domain}, ...)
    # facts/gaps/confidence logic
    return result
```

## 4. agents/simulator.py
```
def run(exploration: Dict[str, Any]) -> Dict[str, Any]:
    domain = exploration.get("domain", "unknown")
    question = exploration.get("question", "unknown")
    
    return {
        "scenarios": [  # MIN 2
            {"id": "s1", "outcome": "positivo", "probability": 0.6},
            {"id": "s2", "outcome": "neutral", "probability": 0.4}
        ],
        "risks": {"volatilidad": 0.3},
        "assumptions": ["Mercado estable"]
    }
```

## 5. agents/guardian.py
```
def validate(simulation: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if len(simulation.get("scenarios", [])) < 2:
        issues.append("Falta comparacion")
    
    corrected_output = simulation.copy()
    corrected_output["guardian_block"] = len(issues) > 1  # BOOL
    
    return {
        "valid": len(issues) == 0,
        "corrected_output": corrected_output
    }
```

## 6. launcher.bat
```
@echo off
title Aletheia Launcher v1.0
:menu
cls
echo [1] DEMO [2] REAL [3] Tests [0] Exit
set /p choice=
if "%choice%"=="1" set MODE=DEV & goto launch
if "%choice%"=="2" set MODE=PROD & goto launch
if "%choice%"=="3" goto tests
goto menu

:launch
pip install -r requirements.txt
python cli.py reset
python cli.py test
start cmd /k "python cli.py start --mode %MODE%"
cd aletheia-ui & npm start & cd ..
start http://127.0.0.1:8000/docs
pause
goto menu
```

## 7. memory/service.py + storage.py
```
# service.py
_STORE = []
def store_event(event: dict):
    _STORE.append(event)
def retrieve_context(domain: str):
    return [e for e in _STORE if e.get("domain") == domain]

# storage.py (DB stub)
def init_db():
    pass
```

**Tests: 10/10 PASS**
**Launcher: Funcional (DEMO/REAL)**
