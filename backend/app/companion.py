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
    "you're feeling",
    "you feel a",
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


_SAFETY_QUESTION_MARKERS: tuple[str, ...] = (
    "weren't here",
    "werent here",
    "not being here",
    "not wanting to be here",
    "not here anymore",
    "hurt yourself",
    "ending your life",
    "better if you weren't",
    "better if you werent",
)


def _fold(text: str) -> str:
    t = (text or "").lower()
    return t.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")


def _is_handoff_line(text: str) -> bool:
    t = _fold(text)
    return "care team will" in t and ("chat with you" in t or "speak with you" in t)


def _companion_already_handed_off(transcript: list[dict[str, Any]]) -> bool:
    return any(_is_handoff_line(line) for line in _companion_lines(transcript))


def _last_companion_asked_safety(transcript: list[dict[str, Any]]) -> bool:
    for turn in reversed(transcript):
        if turn.get("role") == "companion":
            t = _fold(turn.get("text") or "")
            return any(m in t for m in _SAFETY_QUESTION_MARKERS)
    return False


def _closing_after_handoff(preferred_name: str | None) -> str:
    name = preferred_name or "there"
    return f"Thank you for chatting with me today. Take care, {name}."


def _resident_affirmed_safety(text: str) -> bool:
    t = _fold(text).strip()
    return t.startswith(("yes", "yeah", "yep", "sometimes", "i do", "i have"))


def _style_directive(transcript: list[dict[str, Any]]) -> str:
    """Per-turn nudge: no full recap; stay 1–2 follow-ups, then shift domain."""
    resident = _latest_resident_text(transcript)
    n_resident = sum(1 for t in transcript if t.get("role") == "resident")
    parts = [
        "Style for THIS turn:",
        "- Do not recap or list everything they just said. Pick ONE detail and respond to that.",
        "- Stay close to their words. Do not invent labels (burden, emptiness, uselessness).",
        "- Do not begin with \"It sounds like\", \"Sounds like\", or \"You're feeling\".",
        "- Keep it to 1–3 short spoken sentences.",
        "- End with exactly one open question so they have a cue to speak "
        "(unless you are handing off to the care team).",
        "- Ask at most ONE safety question this session. If they already answered "
        "yes, sometimes, or a death wish: do not ask again — only thank them and "
        "say the care team will come. If they already heard the care-team line, "
        "do not speak except a short goodbye.",
    ]
    if len(resident.split()) <= 4:
        parts.append(
            "- Their last reply was very short — do not interpret feelings from it. "
            "Acknowledge briefly and ask one simple question about how they have been."
        )
    elif n_resident >= 4:
        parts.append(
            "- You have stayed with this topic long enough. THIS turn: one short "
            "acknowledgement, then announce a NEW screening domain they have not covered "
            "(sleep, meals, energy, or visitors). If they have spoken of loneliness, "
            "emptiness, pointlessness, or missing someone badly, and you have not already "
            "asked a safety question, use a gentle safety check instead. "
            "Example: \"I'd like to ask about sleep now. How have your nights been lately?\""
        )
    elif n_resident >= 2:
        parts.append(
            "- This is still a follow-up on what they just raised (at most two). "
            "Next turns should move to another domain — do not start a long thread on "
            "the same song, memory, or person."
        )
    return "\n".join(parts)


def _repetition_issues(reply: str, transcript: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    low = reply.strip().lower()
    if any(low.startswith(b) for b in _BANNED_OPENERS):
        issues.append(
            'Do not open with "It sounds like" / "Sounds like" / "You\'re feeling" — vary your opening.'
        )
    prior_openers = {o for o in (_opener(l) for l in _companion_lines(transcript)) if o}
    this_opener = _opener(reply)
    if this_opener and this_opener in prior_openers:
        issues.append(f'You already opened a turn with "{this_opener}…" this session — start differently.')
    return issues


def _vocab_block_for(locale: str, utterance: str) -> str:
    """Retrieve the locale vocabulary relevant to this utterance and format it for the prompt.

    Returns a leading-newline block appended at the END of the companion user message so the
    terms stay salient every turn (anti-forgetting). No-ops if the vocab collection is empty
    or retrieval fails — the companion must never break because of the glossary.
    """
    if not utterance.strip():
        return ""
    try:
        from backend.rag.vocab.retrieve import format_vocab_block, retrieve_relevant_vocab

        block = format_vocab_block(retrieve_relevant_vocab(locale, utterance))
        return f"\n\n{block}" if block else ""
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
    # After the care-team handoff: no more screening — only the exit closing.
    if _companion_already_handed_off(transcript):
        return _closing_after_handoff(preferred_name), []

    latest = _latest_resident_text(transcript)
    # Explicit risk language, or a yes after we already asked safety once → hand off.
    if text_signals_safety_risk(latest) or (
        _last_companion_asked_safety(transcript) and _resident_affirmed_safety(latest)
    ):
        return _SAFETY_HANDOFF.get(locale, _SAFETY_HANDOFF["en-SG"]), []

    system = load_companion_system_prompt(locale)
    user = build_companion_user_message(
        preferred_name=preferred_name,
        locale=locale,
        transcript=transcript,
    )
    user += "\n\n" + _style_directive(transcript)
    user += _vocab_block_for(locale, _latest_resident_text(transcript))
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
