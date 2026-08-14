"""Deterministic self-harm risk detection over resident speech.

Single source of truth for "did the resident disclose a safety risk", used by:
  - the live companion — to force the safety handoff line, and
  - policy RAG retrieval — to guarantee-include the crisis sections regardless of how
    the LLM summariser tagged the session.

This is a deliberate safety backstop: a missed crisis (continuing casual screening, or
failing to retrieve the escalation protocol) is far worse than an unnecessary handoff,
so detection is biased toward triggering. It is intentionally simple and literal — it
complements, never replaces, the LLM's own judgement.
"""

from __future__ import annotations

from typing import Any

# Explicit risk language that always triggers, even with hedging around it.
_STRONG: tuple[str, ...] = (
    "taking too many",
    "take too many",
    "too many pills",
    "too many tablets",
    "overdose",
    "over dose",
    "kill myself",
    "killing myself",
    "end my life",
    "ending my life",
    "end it all",
    "make it all stop",
    "make it stop",
    "want it all to stop",
    "want it to stop",
    "want it to end",
    "better off dead",
    "wish i was dead",
    "wish i were dead",
    "did not wake",
    "didn't wake",
    "not wake up",
    "never wake up",
    "wouldn't wake",
    "would not wake",
    "wish i wasn't here",
    "wish i was not here",
    "wish i weren't here",
    "no point in living",
    "no point living",
    "not worth living",
    "don't want to be here",
    "do not want to be here",
    "don't want to live",
    "do not want to live",
    "wasn't here",
    "wasnt here",
    "weren't here",
    "werent here",
    "not here anymore",
    "wouldn't mind if i",
    "wouldnt mind if i",
)

# Cues that commonly appear inside denials ("I do not wish to hurt myself").
_AMBIGUOUS: tuple[str, ...] = (
    "hurt myself",
    "harm myself",
    "hurt my self",
    "harm my self",
)

_DENIAL: tuple[str, ...] = (
    "do not wish",
    "don't wish",
    "dont wish",
    "would not do that",
    "wouldn't do that",
    "will not do that",
    "won't do that",
    "not going to hurt",
    "not going to harm",
    "no thoughts",
    "nothing like that",
    "no safety thoughts",
    "no i do not",
    "no i don't",
)


def text_signals_safety_risk(text: str) -> bool:
    """True when a single utterance contains explicit self-harm risk language."""
    t = _normalize(text)
    if any(cue in t for cue in _STRONG):
        return True
    if any(cue in t for cue in _AMBIGUOUS):
        return not any(denial in t for denial in _DENIAL)
    return False


def _normalize(text: str) -> str:
    """Lowercase and fold curly apostrophes so STT punctuation still matches."""
    t = (text or "").lower()
    return t.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")


def transcript_signals_safety_risk(transcript: list[dict[str, Any]]) -> bool:
    """True when any resident turn in the session discloses a safety risk."""
    return any(
        turn.get("role") == "resident" and text_signals_safety_risk(turn.get("text") or "")
        for turn in transcript
    )
