"""HestiaEngine — unified entry point for HESTIA strategic layer.

STATUS: IMPLEMENTED (Hestia v1)
"""

import json
from collections import Counter
from typing import Any, Dict, List, Optional

from core.hestia.memory import HestiaMemory
from core.hestia.analyzer import HestiaAnalyzer


class HestiaEngine:

    def __init__(self):
        self.memory = HestiaMemory()
        self.analyzer = HestiaAnalyzer()

    def trigger_analysis(self, hours_back: int = 24,
                         goal_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        result = self.analyzer.analyze(hours_back=hours_back, goal_ids=goal_ids)
        self.memory.save_analysis({
            "timestamp": result.get("timestamp"),
            "hours_analyzed": hours_back,
            "goal_ids": result.get("goal_ids", []),
            "analysis": result,
            "alignment_score": result.get("alignment_score", 0.5),
            "verdict": result.get("verdict", ""),
        })
        clean = {k: v for k, v in result.items() if k != "goals_used"}
        clean["goals_used"] = [g.get("title") for g in result.get("goals_used", [])]
        return clean

    def status(self) -> Dict[str, Any]:
        goals = self.memory.get_active_goals()
        obs_24h = self.memory.get_observations(24)
        last = self.memory.get_last_analysis()

        all_flags: list[str] = []
        for obs in obs_24h:
            try:
                all_flags.extend(json.loads(obs.get("flags", "[]")))
            except Exception:
                pass
        top_flags = dict(Counter(all_flags).most_common(5))

        return {
            "active_goals": [
                {
                    "title": g["title"],
                    "progress": (
                        f"{g.get('current_value', 0)}/"
                        f"{g.get('target_value', '?')} {g.get('target_unit', '')}"
                    ),
                    "priority": g.get("priority", 1),
                }
                for g in goals
            ],
            "observations_last_24h": len(obs_24h),
            "top_flags": top_flags,
            "last_analysis": last["timestamp"] if last else None,
            "last_verdict": last["verdict"] if last else None,
            "last_alignment_score": last["alignment_score"] if last else None,
        }

    def add_goal(self, goal: Dict[str, Any]) -> int:
        return self.memory.save_goal(goal)

    def update_goal_progress(self, goal_id: int,
                             current_value: float,
                             notes: Optional[str] = None) -> None:
        updates: Dict[str, Any] = {"current_value": current_value}
        if notes is not None:
            updates["notes"] = notes
        self.memory.update_goal(goal_id, updates)

    def edit_goal(self, goal_id: int, updates: Dict[str, Any]) -> None:
        self.memory.update_goal(goal_id, updates)


hestia = HestiaEngine()
