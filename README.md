# Aletheia

## 🧭 What makes Aletheia different?

Most AI systems try to give answers.

Aletheia does something else:

→ It reveals structure  
→ It exposes uncertainty  
→ It simulates consequences  

It is designed for thinking, not responding.

**Personal cognitive system for decision-making**

Aletheia is a local-first cognitive system designed to help you think better, not faster.

It combines structured memory, contextual reasoning, and scenario simulation to support complex decisions in areas like finance, career, and personal development.

---

## 🧠 What is Aletheia?

Aletheia is not a chatbot.

It is a **cognitive architecture** that:

- Stores personal knowledge in structured form
- Retrieves relevant context
- Simulates possible futures
- Highlights risks and uncertainty
- Helps you reason before acting

> It does not decide for you. It reveals.

---

## 🎯 Core Principles

- **Human autonomy first** → final decisions are always yours  
- **Evidence over opinion** → grounded in stored data  
- **Transparency** → shows assumptions and uncertainty  
- **Local-first** → your data stays on your machine  
- **Simulation over answers** → explores possibilities, not conclusions  

---

## 🧩 System Architecture

```
User Input
↓
Orchestrator
↓
Explorer → retrieves context
↓
Simulator → generates scenarios
↓
Guardian → enforces risk rules
↓
Structured Response
```

## 🧠 Cognitive Modes

Aletheia adapts its behavior based on decision risk:

- Low risk → exploratory, creative
- Medium risk → structured reasoning
- High risk → conservative, multi-scenario analysis

The system does not behave the same in all contexts.
---

## ⚙️ Components

### Core
- Orchestrator (flow control)
- Risk Engine (domain-based risk classification)
- Context Builder (memory preparation)

### Agents
- **Explorer** → retrieves relevant data
- **Simulator** → generates future scenarios
- **Guardian** → validates output based on risk

### Memory (MVP)
- Structured notes (facts, ideas, goals, events)
- In-memory or simple storage (SQLite planned)

### AI Layer
- Local inference via **Ollama**
- Optional cloud integration (future phase)

## 🔬 Decision Flow

1. Classify domain and risk
2. Retrieve relevant memory
3. Build contextual representation
4. Simulate multiple scenarios
5. Validate output based on risk rules
6. Return structured insight

No single-answer outputs in high-risk domains.

---

## 🔥 Current Features (MVP)

- Domain-based reasoning (finance, career, etc.)
- Risk-aware simulation
- Scenario generation (optimistic / conservative)
- Local AI execution (Ollama)
- Simple API endpoint for simulation

## 🧠 Design Philosophy

Aletheia is built on a simple idea:

Clarity emerges when:
- information is structured
- contradictions are visible
- assumptions are explicit

The system is designed to expose, not to simplify.
---

## 🚀 Getting Started

### 1. Requirements

- Python 3.10+
- Ollama running locally

Install Ollama:
https://ollama.com

Pull a model (example):
```bash
ollama pull llama3
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn requests
```

### 3. Run the system
```bash
python run.py
```

API will be available at:

http://127.0.0.1:8000

### 4. Example request

POST /simulate

```json
{
  "domain": "finanzas",
  "question": "¿Puedo dejar mi trabajo en 9 meses?",
  "memory": [
    "Ahorros actuales: 12000€",
    "Gastos mensuales: 1200€",
    "Sin ingresos alternativos"
  ]
}
```

### 5. Example response
- Multiple scenarios
- Risks
- Assumptions
- Open questions

---

## ⚠️ What Aletheia is NOT

❌ Not a decision-maker
❌ Not an autonomous agent
❌ Not a financial advisor
❌ Not a productivity tool

---

## 🧠 Roadmap

**Phase 1 (current)**
- Core architecture
- Simulation flow
- Local AI

**Phase 2**
- Persistent memory (SQLite + embeddings)
- Improved retrieval
- Structured outputs

**Phase 3**
- Digital twin evolution
- Hybrid AI (local + cloud)
- UI (Memory Palace interface)

**Phase 4**
- MCP integration
- Advanced reasoning pipelines
- Full knowledge graph

---

## 🔐 Privacy

Aletheia is designed as a local-first system.

- Data stays on your machine
- No cloud dependency required
- Optional external APIs (future)

---

## 💡 Philosophy

Aletheia comes from ancient Greek:

"Truth as unveiling"

This system is built around that idea:

Not to give answers,
but to reveal what is already there, hidden in complexity.

---

## 👤 Author

Miguel Pascual Caballero
Docente · Programador · Orientador

---

## 📌 Status

🚧 Early development (MVP)
- Architecture-first approach
- Actively evolving

---

## 🤝 Contributions

Currently a personal project, but ideas, feedback and discussion are welcome.

---

## 🧭 Final Note

Aletheia is an attempt to build something rare:

A system where intelligence is not the goal —
but clarity is.

## 🧪 Quick demo

Run:

curl -X POST http://127.0.0.1:8000/simulate \
-H "Content-Type: application/json" \
-d '{ ... }'

