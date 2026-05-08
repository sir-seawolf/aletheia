from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from .classifier import classify
from core.memory.emotional_tagger import tag as emotion_tag


def json_serializable(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not JSON serializable")


def build_entry(output: Dict[str, Any], domain: str) -> Dict[str, Any]:
    content_str = json.dumps(output, default=json_serializable, ensure_ascii=False)
    emotion = emotion_tag(content_str)
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "areas": [],
        "type": "insight",
        "content": content_str,
        "tags": [domain],
        "source": "system",
        "emotion": emotion.label,
        "valence": str(emotion.valence),
        "arousal": str(emotion.arousal),
    }


def write_to_palace(areas: List[str], entry: Dict[str, Any]) -> None:
    for area in areas:
        path = Path(f"PALACE/{area}/memory.txt")
        lines = [
            "---ENTRY---",
            f"timestamp: {entry['timestamp']}",
            f"areas: {', '.join(entry['areas'])}",
            f"type: {entry['type']}",
            f"content: {entry['content']}",
            f"tags: {', '.join(entry['tags'])}",
            f"source: {entry['source']}",
            f"emotion: {entry.get('emotion', 'neutro')}",
            f"valence: {entry.get('valence', '0.0')}",
            f"arousal: {entry.get('arousal', '0.0')}",
            "---END---"
        ]
        block = "\n".join(lines) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(block)


def attach_to_palace(output: Dict[str, Any]) -> None:
    domain = output.get("domain", "unknown")
    entry = build_entry(output, domain)
    content = entry["content"]
    areas = classify(content)
    entry["areas"] = areas
    if areas:
        write_to_palace(areas, entry)
