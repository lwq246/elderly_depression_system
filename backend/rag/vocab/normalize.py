"""Replace culture-specific resident wording with general meanings for analyst reading."""

from __future__ import annotations

import re

from backend.rag.vocab.data import VOCABULARY_TERMS


def _replacement_pairs(locale: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for variants, meaning in VOCABULARY_TERMS.get(locale, []):
        general = meaning.strip()
        if not general:
            continue
        for term in variants:
            needle = term.strip()
            if needle:
                pairs.append((needle, general))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def normalize_resident_text(text: str, locale: str) -> str:
    """Return resident text with culture terms replaced by general meanings.

    Raw ``text`` is preserved on the transcript turn; this is for analyst reading only.
    """
    if not text.strip():
        return text

    result = text
    for term, meaning in _replacement_pairs(locale):
        result = re.sub(re.escape(term), meaning, result, flags=re.IGNORECASE)
    return result
