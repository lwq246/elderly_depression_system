import json
import re
from typing import Any

import httpx

from .config import settings
from .observability import log_session_event, timed_span

FORBIDDEN_COMPANION_PATTERNS = [
    r"\bdepress(?:ion|ed)\b",
    r"\bmental illness\b",
    r"\bPHQ\b",
    r"\bGDS\b",
    r"\brisk level\b",
    r"\bscreening score\b",
    r"\buwb\b",
    r"\bresident[_ ]?id\b",
]


def check_companion_output(text: str) -> list[str]:
    errors = []
    lower = text.lower()
    for pattern in FORBIDDEN_COMPANION_PATTERNS:
        if re.search(pattern, lower, re.I):
            errors.append(f"Forbidden phrase matched: {pattern}")
    if re.search(r"[#*`|\[\]]", text):
        errors.append("Companion output must not contain markdown")
    if text.count("?") > 1:
        errors.append("Companion should ask at most one question per turn")
    return errors


def _openrouter_provider_payload() -> dict[str, Any] | None:
    provider = (settings.openrouter_provider or "").strip()
    if not provider:
        return None
    return {
        "order": [provider],
        "allow_fallbacks": settings.openrouter_allow_fallbacks,
    }


async def chat_completion(
    *,
    system: str,
    user: str,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    if not settings.use_openai:
        raise RuntimeError("OPENAI_API_KEY is required")

    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    provider = _openrouter_provider_payload()
    if provider:
        payload["provider"] = provider

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url
    if settings.openrouter_app_name:
        headers["X-Title"] = settings.openrouter_app_name
    with timed_span("llm_chat_completion", model=settings.openai_model, json_mode=json_mode) as span:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            span["status_code"] = response.status_code
            response.raise_for_status()
            data = response.json()
        log_session_event(
            "llm_chat_completion",
            model=settings.openai_model,
            json_mode=json_mode,
            status_code=span.get("status_code"),
            duration_ms=span.get("duration_ms"),
        )
    return data["choices"][0]["message"]["content"].strip()


async def parse_json_response(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)
