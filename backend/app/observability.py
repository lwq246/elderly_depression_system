"""Logfire observability — PHI-safe: no transcript text, names, or LLM prompts."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI

from .config import settings

_SENSITIVE_KEYS = frozenset(
    {
        "text",
        "content",
        "transcript",
        "message",
        "messages",
        "system",
        "user",
        "preferred_name",
        "room_id",
        "opening_message",
        "greeting",
        "body",
        "reply",
    }
)


def _scrub_callback(match: Any) -> str | None:
    key = (getattr(match, "key", None) or "").lower()
    path = (getattr(match, "path", None) or "").lower()
    if key in _SENSITIVE_KEYS or any(part in path for part in _SENSITIVE_KEYS):
        return "[redacted]"
    return None


def _fastapi_request_attributes_mapper(_request: Any, attributes: dict[str, Any]) -> dict[str, Any]:
    """Drop validated endpoint args on success — avoids logging resident message text."""
    if attributes.get("errors"):
        return {"errors": attributes["errors"]}
    return {}


def configure_observability(app: FastAPI) -> None:
    if not settings.logfire_enabled:
        return

    import logfire

    kwargs: dict[str, Any] = {
        "send_to_logfire": settings.logfire_send_to,
        "scrubbing": logfire.ScrubbingOptions(callback=_scrub_callback),
    }
    if settings.logfire_token:
        kwargs["token"] = settings.logfire_token
    if settings.logfire_service_name:
        kwargs["service_name"] = settings.logfire_service_name

    logfire.configure(**kwargs)
    excluded = [url.strip() for url in settings.logfire_excluded_urls.split(",") if url.strip()]
    logfire.instrument_fastapi(
        app,
        excluded_urls=excluded,
        request_attributes_mapper=_fastapi_request_attributes_mapper,
    )
    logfire.instrument_httpx()


def log_session_event(event: str, **fields: Any) -> None:
    if not settings.logfire_enabled:
        return

    import logfire

    allowed = {
        "session_id",
        "resident_id",
        "locale",
        "turn_count",
        "vocab_match_count",
        "companion_warning_count",
        "companion_ms",
        "analyst_ms",
        "validation_error_count",
        "recommendation",
        "suicide_risk_flag",
        "passive_suicidal_thoughts",
        "active_suicidal_ideation",
        "json_mode",
        "model",
        "status_code",
        "duration_ms",
    }
    safe = {key: value for key, value in fields.items() if key in allowed and value is not None}
    logfire.info(event, **safe)


@contextmanager
def timed_span(name: str, **fields: Any) -> Iterator[dict[str, Any]]:
    """Record duration_ms on exit. Yields a mutable dict for extra span attributes."""
    if not settings.logfire_enabled:
        payload: dict[str, Any] = {}
        yield payload
        return

    import logfire

    started = time.perf_counter()
    payload = dict(fields)
    with logfire.span(name, **payload):
        yield payload
    payload["duration_ms"] = round((time.perf_counter() - started) * 1000)
