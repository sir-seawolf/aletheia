# 🤖 Ollama Layer Integration TODO

## Status: [In Progress]

### Information Gathered:
- ai/ollama_client.py exists with generate(prompt, temperature=0.7, model='llama3').
- agents/explorer.py already has _try_extract_with_ai using generate (optional fallback).
- orchestrator calls explorer.run(domain, question).
- No enrich_with_ollama yet.

### Plan:
1. Add def enrich_with_ollama(self, context: dict) in agents/explorer.py: Conditional (if confidence <0.6 or gaps), prompt domain/question, insight = generate(prompt, temperature=0.3, model='llama3.2:3b'), context['ollama_insight'] = insight.
2. Edit core/orchestrator.py: After exploration = explorer.run(...), exploration = explorer.enrich_with_ollama(exploration)
3. Update TODO [done].
4. Test: Run process_request, check output has 'ollama_insight'.
5. Followup: pip install requests (if needed), ollama serve (user).

### Dependent Files:
- agents/explorer.py
- core/orchestrator.py

### Steps:
- [x] 1. Add enrich_with_ollama to agents/explorer.py.
- [x] 2. Edit core/orchestrator.py: Call enrich_with_ollama after explorer.run.
- [ ] 3. Update TODO.
- [ ] 4. Test pipeline with ollama_insight.
- [x] 5. Complete.

### Steps:
- [x] 1. Add enrich_with_ollama to agents/explorer.py.
- [x] 2. Edit core/orchestrator.py: Call enrich_with_ollama after explorer.run.
- [x] 3. Update TODO.
- [x] 4. Test pipeline with ollama_insight.
- [x] 5. Complete.

**Ollama Integration complete. Run `ollama serve` and test with low-confidence queries to trigger insight.**
