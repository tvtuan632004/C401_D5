from __future__ import annotations

import os
from typing import Any

# ===== Try import Langfuse =====
try:
    from langfuse import observe, get_client, propagate_attributes
    _LANGFUSE_AVAILABLE = True
except Exception:  # pragma: no cover
    _LANGFUSE_AVAILABLE = False

    # ===== Fallbacks =====
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    def propagate_attributes(*args: Any, **kwargs: Any):
        class _DummyCtx:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return _DummyCtx()

    def get_client():
        class _DummyClient:
            def flush(self) -> None:
                return None

            def get_current_trace_id(self) -> str | None:
                return None

        return _DummyClient()


def tracing_enabled() -> bool:
    return bool(
        _LANGFUSE_AVAILABLE
        and os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
        and os.getenv("LANGFUSE_BASE_URL")
    )


def flush_traces() -> None:
    if not tracing_enabled():
        return
    try:
        get_client().flush()
    except Exception:
        pass


def get_current_trace_id() -> str | None:
    if not tracing_enabled():
        return None
    try:
        return get_client().get_current_trace_id()
    except Exception:
        return None