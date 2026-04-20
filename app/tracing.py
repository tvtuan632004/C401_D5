from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import observe, get_client, propagate_attributes
except Exception:  # pragma: no cover
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
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
        and os.getenv("LANGFUSE_BASE_URL")
    )


def flush_traces() -> None:
    try:
        get_client().flush()
    except Exception:
        pass