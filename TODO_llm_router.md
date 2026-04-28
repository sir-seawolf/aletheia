# LLMRouter Integration Complete

- [x] core/llm/router.py created (mode auto/offline/mock, _ollama_available)
- [x] core/llm/__init__.py exports LLMRouter
- [x] orchestrator.py: router = LLMRouter(); enrich("exploration", exploration); enrich("simulation", simulation)
- [x] explorer.py: enrich_with_ollama deprecated
- [x] simulator.py: LLM calls → router placeholders
- [x] Test pipeline with ollama serve

Status: Pipeline centralizado, no roturas.

Next: Prompts central ai/prompts.py
