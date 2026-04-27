"""Almacenamiento de decisiones vividas - FASE 3."""

import json
import os
from typing import List, Dict, Any
from .models import DecisionMemoryNode
from datetime import datetime

DB_PATH = "memory/data/decision_log.json"

def _load() -> List[Dict[str, Any]]:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: List[Dict[str, Any]]):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_node(node: DecisionMemoryNode):
    data = _load()
    node_dict = node.__dict__.copy()
    node_dict['timestamp'] = datetime.utcnow().isoformat()
    data.append(node_dict)
    _save(data)

def get_all() -> List[Dict[str, Any]]:
    return _load()

def find_similar(question: str, domain: str, limit: int = 5) -> List[Dict[str, Any]]:
    data = _load()
    results = []
    q_words = set(question.lower().split())
    for item in data:
        score = 0
        if item["domain"] == domain:
            score += 2
        item_words = set(item["question"].lower().split())
        overlap = len(q_words & item_words)
        score += overlap
        if score > 0:
            results.append((score, item))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:limit]]

def update_outcome(node_id: str, real_outcome: str, delta: str):
    data = _load()
    for item in data:
        if item["id"] == node_id:
            item["real_outcome"] = real_outcome
            item["delta"] = delta
            break
    _save(data)
