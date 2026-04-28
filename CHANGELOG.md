## [v1.1.0] - LLMRouter v1 (2024-10-XX)

### Added
- Centralized LLMRouter with LOCAL (Ollama) → CACHE → MEMORY/PALACE → PROVIDER → CACHE flow
- core/llm/providers/: ollama.py, mock.py, online.py (placeholder)
- core/llm/cache.py: In-memory LLMCache with task+prompt hashing
- core/llm/selector.py: Auto-detect Ollama availability
- core/llm/prompts.py: Centralized prompts + _enrich with memory/palace
- core/llm/router.py: generate(task, prompt, context, temp) singleton

### Changed
- agents/explorer.py, simulator.py: Direct ollama → router.generate()
- core/orchestrator.py: Removed enrich() calls (internal now)
- ai/ollama_client.py, ai/prompts.py: Deprecated, marked legacy

### Technical
- Contract intact (no schema changes)
- Palace/memory integrated as context enrichment
- Fallback to mock on Ollama failure
- Cache avoids repeated calls

Run `python run.py` or `cli.py` to test full pipeline.

---
Previous changelog unchanged.

