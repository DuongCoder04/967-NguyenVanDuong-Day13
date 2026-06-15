from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import observe, get_client, propagate_attributes
except Exception:
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    def propagate_attributes(**kwargs: Any) -> None:
        return None

    class _DummyClient:
        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    _dummy = _DummyClient()

    def get_client() -> _DummyClient:
        return _dummy


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
