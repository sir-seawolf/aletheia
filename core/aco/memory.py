from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime

class ACOMemory:
    def __init__(self, path: str = "aco_memory.json"):
        self.path = Path(path)
        self.log: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return []

    def _save(self):
        self.path.write_text(json.dumps(self.log, indent=2))

    def record_metric(self, metric: Dict[str, Any]):
        self.log.append({**metric, "timestamp": str(datetime.now())})
        self._save()

    def record(self, record: Dict[str, Any]):
        self.log.append(record)
        self._save()

    def stats(self, filter_key: str = None, filter_value: str = None) -> Dict[str, Any]:
        filtered = self.log
        if filter_key and filter_value:
            filtered = [r for r in self.log if r.get(filter_key) == filter_value]
        return {
            "total": len(filtered),
            "avg_dqs": sum(r.get("dqs", 0) for r in filtered) / max(len(filtered), 1)
        }

