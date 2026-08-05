from typing import Any

from .config import settings
from .llm import chat_completion, check_companion_output
from .skills import load_companion_system_prompt


def build_companion_user_message(
    *,
    preferred_name: str | None,
    locale: str,
    speech_register: str,
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
        f"- locale: {locale}\n"
        f"- speech_register: {speech_register}\n\n"
        f"Conversation so far:\n" + "\n".join(lines) + "\n\n"
        "Reply with the next companion spoken line only. No markdown."
    )


async def generate_companion_reply(
    *,
    preferred_name: str | None,
    locale: str,
    speech_register: str,
    transcript: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    system = load_companion_system_prompt(locale, speech_register)
    user = build_companion_user_message(
        preferred_name=preferred_name,
        locale=locale,
        speech_register=speech_register,
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
