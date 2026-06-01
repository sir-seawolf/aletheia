"""
In-process notification queue.

Modules (HESTIA, proactive_engine, etc.) push notifications here.
The Telegram bot polls /api/notifications/poll to drain them.

Queue is per-user and in-memory — clears on server restart.
That's fine: notifications are ephemeral by nature.
"""

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

_MAX_PER_USER = 50

_queues: dict[str, deque] = {}


@dataclass
class Notification:
    text: str
    source: str        # "hestia" | "proactive" | "system"
    ts: str = ""

    def __post_init__(self):
        if not self.ts:
            self.ts = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


def push(text: str, source: str = "system", user_id: str = "default") -> None:
    """Enqueue a notification for a user."""
    q = _queues.setdefault(user_id, deque(maxlen=_MAX_PER_USER))
    q.append(Notification(text=text, source=source))


def push_all(text: str, source: str = "system") -> None:
    """Push to every registered user."""
    for uid in list(_queues.keys()):
        push(text, source, uid)


def poll(user_id: str = "default") -> list[dict]:
    """Drain and return all pending notifications for a user."""
    q = _queues.get(user_id)
    if not q:
        return []
    out = [n.to_dict() for n in q]
    q.clear()
    return out


def register(user_id: str) -> None:
    """Ensure a user has a queue (call on first contact)."""
    _queues.setdefault(user_id, deque(maxlen=_MAX_PER_USER))


def registered_users() -> list[str]:
    return list(_queues.keys())
