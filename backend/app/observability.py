"""Observability shims (Logfire removed).

These are intentionally no-ops so call sites (`configure_observability`,
`log_session_event`, `timed_span`) stay unchanged if a tracing backend is
reintroduced later.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI


def configure_observability(app: FastAPI) -> None:
    return None


def log_session_event(event: str, **fields: Any) -> None:
    return None


@contextmanager
def timed_span(name: str, **fields: Any) -> Iterator[dict[str, Any]]:
    """Yield a mutable dict for span attributes. No-op without a tracing backend."""
    payload: dict[str, Any] = {}
    yield payload
