## 🧠 ALETHEIA KERNEL — RUTA ACTUAL (LOCKED)

* Palace v1 activo (6 áreas, append-only)
* Pipeline contractual estable (orchestrator → agents → contract_lock)
* Memory simple operativo
* Falta capa LLM unificada (Ollama / online / mock)
* Objetivo: integrar LLM sin romper contrato ni flujo

---

## 📌 INFORMACIÓN QUE NECESITO (SOLO ESTO)

### 1) 🔌 Dónde se llama hoy a la “IA”

* ¿Qué funciones generan lenguaje/inteligencia actualmente?
* Archivos exactos donde hay:

  * prompts
  * llamadas HTTP
  * llamadas a Ollama (si existen)
  * lógica “simulada” de LLM

---

### 2) 🧠 Estado real de Ollama en tu PC

* ¿Está instalado?
* URL local (ej: `http://localhost:11434`)
* modelos disponibles (`ollama list` salida)

---

### 3) 🌐 Si existe capa online

* ¿Hay OpenAI / API / backend externo?
* Archivo donde se gestiona (si existe)

---

### 4) 🔁 Flujo exacto actual del Orchestrator

* `core/orchestrator.py` versión real (la última)
* Cómo pasan datos entre:

  * explorer → simulator → guardian

---

### 5) 📦 Context object (CRÍTICO)

* Clase `Context` completa (donde está definida)
* Qué campos reales tiene ahora mismo

---

### 6) 🧩 contract_lock.py real

* versión actual completa
* REQUIRED_FIELDS actuales exactos

---

## ⚡ CON ESO PUEDO:

* Insertar Ollama SIN romper contrato
* Crear LLMRouter limpio (offline/online/fallback)
* Mantener pipeline intacto
* Evitar duplicaciones o bypass del sistema

---

Cuando me pases eso, ya no “supongo nada”.
