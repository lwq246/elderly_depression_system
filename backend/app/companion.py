from typing import Any

from .config import settings
from .llm import chat_completion, check_companion_output
from .skills import load_companion_system_prompt


def _latest_resident_text(transcript: list[dict[str, Any]]) -> str:
    for turn in reversed(transcript):
        if turn.get("role") == "resident":
            return (turn.get("text") or "").strip()
    return ""


def _companion_vocabulary_context(locale: str, transcript: list[dict[str, Any]]) -> str:
    if not settings.rag_enabled:
        return ""
    resident_text = _latest_resident_text(transcript)
    if not resident_text:
        return ""
    try:
        from backend.rag.vocab.retrieve import format_vocabulary_context, retrieve_vocabulary_for_companion

        chunks = retrieve_vocabulary_for_companion(resident_text, locale=locale)
        if not chunks:
            return ""
        return format_vocabulary_context(chunks)
    except Exception:
        return ""


def build_companion_user_message(
    *,
    preferred_name: str | None,
    locale: str,
    transcript: list[dict[str, Any]],
) -> str:
    history = transcript[-settings.companion_history_turns :]
    lines = []
    for turn in history:
        speaker = "Companion" if turn["role"] == "companion" else "Resident"
        lines.append(f"{speaker}: {turn['text']}")
    name_line = preferred_name or "(name lookup failed — use generic greeting)"
    return (
        f"Session context:\n"
        f"- preferred_name: {name_line}\n"
        f"- locale: {locale}\n\n"
        f"Conversation so far:\n" + "\n".join(lines) + "\n\n"
        "Reply with the next companion spoken line only. No markdown."
    )


async def generate_companion_reply(
    *,
    preferred_name: str | None,
    locale: str,
    transcript: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    system = load_companion_system_prompt(
        locale,
        vocabulary_context=_companion_vocabulary_context(locale, transcript),
    )
    user = build_companion_user_message(
        preferred_name=preferred_name,
        locale=locale,
        transcript=transcript,
    )

    for attempt in range(2):
        reply = await chat_completion(system=system, user=user, temperature=0.5)
        warnings = check_companion_output(reply)
        if not warnings:
            return reply, warnings
        user += (
            "\n\nYour previous reply violated rules: "
            + "; ".join(warnings)
            + ". Regenerate a compliant spoken reply."
        )

    return reply, warnings
