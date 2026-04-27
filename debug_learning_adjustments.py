import json
import requests

BASE_URL = "http://127.0.0.1:8000"

payload = {
    "domain": "finanzas",
    "question": "Quiero evaluar dejar trabajo",
    "memory": ["sin datos de ingresos", "sin datos de gastos"],
    "constraints": [],
}

resp = requests.post(f"{BASE_URL}/simulate", json=payload, timeout=120)
print("status:", resp.status_code)

data = resp.json()
result = data

explorer = result.get("pipeline", {}).get("explorer", {})
guardian = result.get("pipeline", {}).get("guardian", {})
learning = (
    result.get("trace", {})
    .get("system_adjustments", {})
    .get("learning_adjustments", [])
)

print("\n=== EXPLORER ===")
print(json.dumps(explorer, ensure_ascii=False, indent=2))

print("\n=== GUARDIAN ===")
print(json.dumps(guardian, ensure_ascii=False, indent=2))

print("\n=== LEARNING ADJUSTMENTS ===")
print(json.dumps(learning, ensure_ascii=False, indent=2))

print("\n=== RAW TRACE KEYS ===")
print(list(result.get("trace", {}).keys()))
