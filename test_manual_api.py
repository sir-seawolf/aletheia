"""
Tests manuales reproducibles para la API de Aletheia.

Ejecutar contra el servidor corriendo:
    python run.py
    python test_manual_api.py

O ejecutar directamente (inicia servidor en subprocess):
    python test_manual_api.py --start-server
"""

import sys
import json
import requests
import subprocess
import time
import os

BASE_URL = "http://127.0.0.1:8000"

# Payloads de prueba
PROFILE_A_PAYLOAD = {
    "domain": "finanzas",
    "question": "¿Puedo dejar mi trabajo en 9 meses?",
    "memory": [
        "Ahorros actuales: 12000€",
        "Gastos mensuales: 1200€",
        "Sin ingresos alternativos"
    ]
}

PROFILE_B_PAYLOAD = {
    "domain": "finanzas",
    "question": "¿Puedo dejar mi trabajo en 9 meses?",
    "memory": [
        "Ahorros actuales: 12000€",
        "Gastos mensuales: 1200€",
        "Sin ingresos alternativos"
    ],
    "user_profile": {
        "verbosity_preference": "alta",
        "structure_preference": "narrativa",
        "abstraction_capacity": "alta"
    }
}


def check_root_endpoint():
    """Valida que el endpoint raíz incluya status: running."""
    resp = requests.get(f"{BASE_URL}/", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    assert data.get("system") == "Aletheia", f"system mismatch: {data}"
    assert data.get("status") == "running", f"status not running: {data}"
    print(f"[PASS] Root endpoint: {json.dumps(data, ensure_ascii=False)}")
    return data


def run_simulate(payload: dict, label: str) -> dict:
    """Ejecuta POST /simulate y valida estructura base."""
    print(f"\n[TEST] Running {label}...")
    resp = requests.post(
        f"{BASE_URL}/simulate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # Validar estructura mínima
    assert "domain" in data, "Missing 'domain'"
    assert "risk" in data, "Missing 'risk'"
    assert "pipeline" in data, "Missing 'pipeline'"
    assert "final_output" in data, "Missing 'final_output'"
    assert "meta" in data, "Missing 'meta'"

    # Validar pipeline steps
    pipeline = data["pipeline"]
    assert "explore" in pipeline, "Missing 'explore' in pipeline"
    assert "simulate" in pipeline, "Missing 'simulate' in pipeline"
    assert "validate" in pipeline, "Missing 'validate' in pipeline"

    # Validar meta
    meta = data["meta"]
    assert "steps_executed" in meta, "Missing 'steps_executed'"
    assert "timestamp" in meta, "Missing 'timestamp'"
    assert meta.get("version", "").startswith("0.3"), f"Unexpected version: {meta.get('version')}"

    print(f"[PASS] {label} structure OK")
    print(f"       Steps: {meta['steps_executed']}")
    print(f"       Risk: {json.dumps(data['risk'], ensure_ascii=False)}")
    return data


def compare_profiles(result_a: dict, result_b: dict):
    """Compara salidas de Profile A vs Profile B."""
    print("\n[COMPARE] Profile A vs Profile B")

    # B debe tener final_output (igual que A)
    assert "final_output" in result_a
    assert "final_output" in result_b

    # Verificar que B tiene user_profile en la request (ya lo sabemos por payload)
    # En la respuesta, ambos tienen la misma estructura base
    # Lo diferencial es cómo el pipeline procesó — aquí solo logueamos diferencias observables

    sim_a = result_a["pipeline"]["simulate"]
    sim_b = result_b["pipeline"]["simulate"]

    scenarios_a = sim_a.get("scenarios", [])
    scenarios_b = sim_b.get("scenarios", [])

    print(f"  Profile A scenarios: {len(scenarios_a)}")
    print(f"  Profile B scenarios: {len(scenarios_b)}")

    # En riesgo alto (finanzas), ambos deben tener >= 2 escenarios
    if result_a["risk"].get("level") == "high":
        assert len(scenarios_a) >= 2, f"Profile A expected >=2 scenarios, got {len(scenarios_a)}"
        assert len(scenarios_b) >= 2, f"Profile B expected >=2 scenarios, got {len(scenarios_b)}"
        print("  [PASS] Both have >= 2 scenarios (high risk)")

    # Guardian validations
    val_a = result_a["pipeline"]["validate"]
    val_b = result_b["pipeline"]["validate"]
    print(f"  Profile A valid: {val_a.get('valid')} | issues: {val_a.get('issues')}")
    print(f"  Profile B valid: {val_b.get('valid')} | issues: {val_b.get('issues')}")


def main():
    start_server = "--start-server" in sys.argv
    server_proc = None

    if start_server:
        print("[INFO] Starting server in background...")
        env = os.environ.copy()
        server_proc = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        time.sleep(3)  # Esperar arranque

    try:
        # Test 0: Root endpoint
        check_root_endpoint()

        # Test 1: Profile A (sin user_profile)
        result_a = run_simulate(PROFILE_A_PAYLOAD, "Profile A (no profile)")

        # Test 2: Profile B (con user_profile)
        result_b = run_simulate(PROFILE_B_PAYLOAD, "Profile B (with profile)")

        # Test 3: Comparación
        compare_profiles(result_a, result_b)

        print("\n✅ Todos los tests manuales de la API pasaron.")

        # Guardar resultados para análisis manual
        with open("test_result_profile_a.json", "w", encoding="utf-8") as f:
            json.dump(result_a, f, ensure_ascii=False, indent=2)
        with open("test_result_profile_b.json", "w", encoding="utf-8") as f:
            json.dump(result_b, f, ensure_ascii=False, indent=2)
        print("📁 Resultados guardados en test_result_profile_a.json y test_result_profile_b.json")

    except requests.exceptions.ConnectionError:
        print("[FAIL] No se pudo conectar a la API. ¿Está corriendo el servidor en 127.0.0.1:8000?")
        sys.exit(1)
    except AssertionError as e:
        print(f"[FAIL] Assertion error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Error inesperado: {e}")
        sys.exit(1)
    finally:
        if server_proc:
            print("[INFO] Stopping background server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()


if __name__ == "__main__":
    main()

