"""
TraceContext — async-safe propagation of the active TraceBuilder.

Uses Python's contextvars.ContextVar so the trace flows automatically through
asyncio tasks and thread executors without explicit parameter passing.

All subsystems (LLMRouter, FatigueEngine, ModeRegistry, MemoryBus) call
get_trace() and, if a builder is active, write their contribution to it.
The pattern is always "best-effort": if no trace is active, or if writing
fails, execution continues normally — tracing never breaks the pipeline.

Usage in a request handler:
    with begin_trace(session_id, domain, message) as tb:
        # ... run pipeline ...
        trace = tb.finish(output=reply, confidence=0.8)
    trace_store.save(trace)
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator, Optional

from core.tracing.trace import TraceBuilder

_current: ContextVar[Optional[TraceBuilder]] = ContextVar("_current_trace", default=None)


def get_trace() -> Optional[TraceBuilder]:
    """Return the active TraceBuilder for this async context, or None."""
    return _current.get()


def set_trace(tb: Optional[TraceBuilder]) -> None:
    _current.set(tb)


@contextmanager
def begin_trace(
    session_id: str,
    domain: str,
    question: str,
    source: str = "v1_pipeline",
) -> Generator[TraceBuilder, None, None]:
    """
    Context manager that installs a TraceBuilder for the duration of a block.
    Restores the previous trace (or None) on exit — safe for nested calls.

        with begin_trace(session_id, domain, message) as tb:
            reply = run_pipeline(...)
            trace = tb.finish(reply, confidence=0.8)
        trace_store.save(trace)
    """
    tb = TraceBuilder(session_id=session_id, domain=domain, question=question, source=source)
    token = _current.set(tb)
    try:
        yield tb
    finally:
        _current.reset(token)


# ── Convenience writers (no-op when no trace is active) ─────────────────────

def trace_routing(provider: str, tier: str, reasoning: str) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.set_routing(provider, tier, reasoning)
        except Exception:
            pass


def trace_mode(mode_id: str, routing_reason: Optional[str] = None) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.set_mode(mode_id, routing_reason)
        except Exception:
            pass


def trace_fatigue(before: float, after: float) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.set_fatigue(before, after)
        except Exception:
            pass


def trace_memory(source: str, count: int = 0) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.add_memory_source(source)
            if count:
                tb.set_memory_count(tb.memory_items_used + count)
        except Exception:
            pass


def trace_tokens(n: int) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.add_tokens(n)
        except Exception:
            pass


def trace_error(msg: str) -> None:
    tb = get_trace()
    if tb:
        try:
            tb.set_error(msg)
        except Exception:
            pass
