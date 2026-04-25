import sys
import os

# Limpiar DB de test previos para evitar interferencias
try:
    os.remove("memory/data/aletheia.db")
except FileNotFoundError:
    pass

# Test 1: Context.summary()
from core.context import Context
ctx = Context(domain="test", risk={"level": "high"}, memory=["a", "b"], question="Should I invest?")
summary = ctx.summary()
assert "test" in summary
assert "high" in summary
assert "memory=2" in summary
print("[PASS] Context.summary():", summary)

# Test 2: Orchestrator schemas exist
from core.orchestrator import EXPLORATION_SCHEMA, SIMULATION_SCHEMA
assert EXPLORATION_SCHEMA["facts"] == list
assert SIMULATION_SCHEMA["scenarios"] == list
print("[PASS] Orchestrator schemas defined")

# Test 3: Guardian tightened validations
from agents.guardian import validate

# High risk + <2 scenarios + no assumptions → 2 issues
result = validate(
    {"scenarios": [{"type": "x"}], "risks": ["r1"], "assumptions": []},
    {"level": "high"}
)
issues = result["issues"]
assert "Falta comparación de escenarios en riesgo alto" in issues
assert "No hay supuestos explícitos" in issues
print("[PASS] Guardian tightened validations:", issues)

# Test 4: API root endpoint exists
from api.main import root
resp = root()
assert resp["system"] == "Aletheia"
assert "local-first cognitive engine" in resp["mode"]
print("[PASS] API root endpoint:", resp)

# Test 5: Scenario description prompt exists and produces text
from ai.prompts import scenario_description_prompt
prompt = scenario_description_prompt("test q", ["fact1"], "optimistic")
assert "test q" in prompt
assert "fact1" in prompt
assert "optimistic" in prompt
print("[PASS] Scenario description prompt generated")

# ============================================
# NUEVOS TESTS: Memory Layer
# ============================================

# Test 6: MemoryItem model
from memory.models import MemoryItem
from datetime import datetime

item = MemoryItem(
    type="fact",
    content="SQLite es una base de datos embebida",
    domain="tecnologia",
    confidence=0.95,
    created_at=datetime.now(),
)
assert item.type == "fact"
assert item.domain == "tecnologia"
assert item.id is None  # antes de guardar
print("[PASS] MemoryItem created:", item.content)

# Test 7: Save and retrieve from storage
from memory.storage import save_memory, get_by_domain, get_all

saved_id = save_memory(item)
assert saved_id > 0
item.id = saved_id
print("[PASS] save_memory returned id:", saved_id)

memories = get_by_domain("tecnologia")
assert len(memories) >= 1
assert any(m.content == item.content for m in memories)
print("[PASS] get_by_domain retrieved memory:", len(memories), "items")

# Test 8: Service layer retrieve_context
from memory.service import retrieve_context, store_event

context_contents = retrieve_context("tecnologia")
assert isinstance(context_contents, list)
assert all(isinstance(c, str) for c in context_contents)
assert item.content in context_contents
print("[PASS] retrieve_context returned list of strings:", context_contents)

# Test 9: Service layer store_event
event_id = store_event("¿Debería aprender Rust?", "carrera", confidence=0.8)
assert event_id > 0
print("[PASS] store_event persisted event with id:", event_id)

event_memories = get_by_domain("carrera")
assert any(m.content == "¿Debería aprender Rust?" for m in event_memories)
print("[PASS] Event found in DB via get_by_domain")

# Test 10: Orchestrator auto-retrieves memory and stores event after execution
from core.orchestrator import process_request

# Primero guardamos un hecho en el dominio 'aprendizaje'
from memory.storage import save_memory
fact = MemoryItem(
    type="fact",
    content="El aprendizaje distribuido mejora la retención",
    domain="aprendizaje",
    confidence=0.9,
    created_at=datetime.now(),
)
save_memory(fact)

# Ejecutamos sin pasar memory_data → debe auto-recuperar
result = process_request(
    domain="aprendizaje",
    question="¿Cómo mejoro mi retención?",
    memory_data=None,  # auto-recuperación
)
assert "final_output" in result
assert result["domain"] == "aprendizaje"
# Verificar que la pregunta se guardó como evento
events = get_by_domain("aprendizaje")
assert any(m.content == "¿Cómo mejoro mi retención?" and m.type == "event" for m in events)
print("[PASS] Orchestrator auto-retrieved memory and stored event")

print("\n✅ Todos los tests pasaron.")

