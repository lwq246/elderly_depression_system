"""Capture LLM prompts for test/debug — enabled via CAPTURE_LLM_INPUTS or request header."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

from fastapi import Request

from .config import settings

_capture_enabled: ContextVar[bool] = ContextVar("capture_llm_inputs", default=False)
_capture_session_id: ContextVar[str | None] = ContextVar("capture_session_id", default=None)


def capture_enabled_for_request(request: Request | None) -> bool:
    if settings.capture_llm_inputs:
        return True
    if request is None:
        return False
    return request.headers.get("x-capture-llm-inputs", "").strip().lower() in ("1", "true", "yes")


@contextmanager
def llm_capture_scope(session_id: str, *, enabled: bool) -> Iterator[None]:
    token_enabled = _capture_enabled.set(enabled)
    token_session = _capture_session_id.set(session_id if enabled else None)
    try:
        yield
    finally:
        _capture_enabled.reset(token_enabled)
        _capture_session_id.reset(token_session)


def record_llm_input(
    call: str,
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float | None = None,
    json_mode: bool = False,
    attempt: int = 1,
    turn_index: int | None = None,
) -> None:
    if not _capture_enabled.get():
        return
    session_id = _capture_session_id.get()
    if not session_id:
        return

    from .db import append_llm_input

    record: dict[str, Any] = {
        "call": call,
        "attempt": attempt,
        "model": model or settings.openai_model,
        "temperature": temperature,
        "json_mode": json_mode,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if turn_index is not None:
        record["turn_index"] = turn_index
    append_llm_input(session_id, record)
