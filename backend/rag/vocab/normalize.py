"""Replace culture-specific resident wording with general meanings for analyst reading."""

from __future__ import annotations

from backend.rag.vocab.matcher import normalize_text


def normalize_resident_text(text: str, locale: str) -> str:
    """Return resident text with culture terms replaced by general meanings.

    Raw ``text`` is preserved on the transcript turn; this is for analyst reading only.
    Uses the shared boundary-aware matcher, so ``flat`` is only replaced as a word.
    """
    return normalize_text(text, locale)
