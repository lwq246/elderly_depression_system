import re
from typing import Any

from .config import settings
from .llm import chat_completion, check_companion_output
from .llm_capture import record_llm_input
from .safety import text_signals_safety_risk
from .skills import load_companion_system_prompt

# Fixed opener stems the model overuses turn after turn (the "mirroring" complaint).
_BANNED_OPENERS: tuple[str, ...] = (
    "it sounds like",
    "so it sounds like",
    "sounds like",
    "it seems like",
    "so it seems",
)

# Locale-specific handoff lines (kept in sync with culture-*/companion-runtime.md).
_SAFETY_HANDOFF: dict[str, str] = {
    "en-AU": (
        "Thank you for telling me. Someone from the care team will come and have a "
        "chat with you soon."
    ),
    "en-SG": (
        "Thank you for sharing that with me. A member of the care team will come and "
        "speak with you shortly."
    ),
}


def _latest_resident_text(transcript: list[dict[str, Any]]) -> str:
    for turn in reversed(transcript):
        if turn.get("role") == "resident":
            return (turn.get("text") or "").strip()
    return ""


def _opener(text: str, words: int = 4) -> str:
    """First few words, normalised — used to detect repeated opening phrasing."""
    normalised = re.sub(r"[^a-z0-9 ]", "", (text or "").strip().lower())
    return " ".join(normalised.split()[:words])


def _companion_lines(transcript: list[dict[str, Any]]) -> list[str]:
    return [t.get("text", "") for t in transcript if t.get("role") == "companion" and t.get("text")]


def _last_companion_asked_question(transcript: list[dict[str, Any]]) -> bool:
    for turn in reversed(transcript):
        if turn.get("role") == "companion":
            return (turn.get("text") or "").strip().endswith("?")
    return False


def _style_directive(transcript: list[dict[str, Any]]) -> str:
    """Deterministic per-turn nudge that breaks the repeated-opener / question-every-turn rut."""
    used_openers = sorted({o for o in (_opener(l) for l in _companion_lines(transcript)) if o})
    parts = [
        "Style for THIS turn:",
        "- Lead with a reflection written as a statement, not a question. Do not begin with "
        "\"It sounds like\", \"So it sounds like\", or \"Sounds like\".",
        "- Go a little deeper into what they just said — name the feeling or meaning underneath, "
        "not just a summary of their words.",
    ]
    if used_openers:
        joined = "; ".join(f'"{o}…"' for o in used_openers)
        parts.append(f"- Openers you have ALREADY used this session (do NOT reuse or echo): {joined}")
    if _last_companion_asked_question(transcript):
        parts.append(
            "- Your previous turn asked a question, so THIS turn reflect only — no question. "
            "Stay with what they just said instead of moving to a new topic."
        )
    else:
        parts.append("- You may ask at most one open, exploring question if it fits — otherwise just reflect.")
    return "\n".join(parts)


def _repetition_issues(reply: str, transcript: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    low = reply.strip().lower()
    if any(low.startswith(b) for b in _BANNED_OPENERS):
        issues.append('Do not open with "It sounds like" / "Sounds like" — vary your opening.')
    prior_openers = {o for o in (_opener(l) for l in _companion_lines(transcript)) if o}
    this_opener = _opener(reply)
    if this_opener and this_opener in prior_openers:
        issues.append(f'You already opened a turn with "{this_opener}…" this session — start differently.')
    return issues


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
    # Safety-critical short-circuit: if the resident's latest turn discloses self-harm
    # risk, deliver the handoff line deterministically instead of trusting the LLM.
    if text_signals_safety_risk(_latest_resident_text(transcript)):
        return _SAFETY_HANDOFF.get(locale, _SAFETY_HANDOFF["en-SG"]), []

    system = load_companion_system_prompt(locale)
    user = build_companion_user_message(
        preferred_name=preferred_name,
        locale=locale,
        transcript=transcript,
    )
    user += "\n\n" + _style_directive(transcript)
    turn_index = sum(1 for turn in transcript if turn.get("role") == "resident")

    for attempt in range(2):
        record_llm_input(
            "companion",
            system=system,
            user=user,
            temperature=0.5,
            attempt=attempt + 1,
            turn_index=turn_index,
        )
        reply = await chat_completion(system=system, user=user, temperature=0.5)
        warnings = check_companion_output(reply) + _repetition_issues(reply, transcript)
        if not warnings:
            return reply, warnings
        user += (
            "\n\nYour previous reply had these problems: "
            + "; ".join(warnings)
            + ". Regenerate a compliant spoken reply."
        )

    return reply, warnings
