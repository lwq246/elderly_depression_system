"""Compiled culture-vocabulary matcher — single source of truth for retrieve + normalize.

One precompiled, boundary-aware regex per locale replaces the old per-turn loops.
Matching is:
- case-insensitive,
- boundary-aware (``sian`` no longer matches inside ``Asian``; ``wind`` not in ``window``),
- longest-match-wins (``very sian`` beats ``sian``; ``a bit flat`` beats ``flat``),
- non-overlapping (finditer/sub consume the longest phrase, so nested shorter terms drop).
"""

from __future__ import annotations

import re
from functools import lru_cache

from backend.rag.vocab.data import VOCABULARY_TERMS

# Treat apostrophe as part of a word so contractions ("she'll", "i'm") stay atomic
# and a term is never matched flush against a letter/digit/underscore/apostrophe.
_LEFT_BOUNDARY = r"(?<![\w'])"
_RIGHT_BOUNDARY = r"(?![\w'])"


@lru_cache(maxsize=None)
def _compiled(locale: str) -> tuple[re.Pattern[str] | None, dict[str, str]]:
    """Return (compiled alternation regex, {variant_lower: meaning}) for a locale."""
    meanings: dict[str, str] = {}
    variants: list[str] = []
    for variant_list, meaning in VOCABULARY_TERMS.get(locale, []):
        general = meaning.strip()
        if not general:
            continue
        for variant in variant_list:
            term = variant.strip().lower()
            if not term or term in meanings:
                continue
            meanings[term] = general
            variants.append(term)

    if not variants:
        return None, {}

    # Longest first so the alternation prefers the longer phrase at any start position.
    variants.sort(key=len, reverse=True)
    alternation = "|".join(re.escape(term) for term in variants)
    pattern = re.compile(
        rf"{_LEFT_BOUNDARY}(?:{alternation}){_RIGHT_BOUNDARY}",
        re.IGNORECASE,
    )
    return pattern, meanings


def find_matches(text: str, locale: str) -> list[tuple[str, str]]:
    """Ordered, de-duplicated ``(term, meaning)`` pairs found in ``text``."""
    haystack = (text or "").strip()
    if not haystack:
        return []
    pattern, meanings = _compiled(locale)
    if pattern is None:
        return []

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in pattern.finditer(haystack):
        term = match.group(0).lower()
        if term in seen:
            continue
        seen.add(term)
        out.append((term, meanings[term]))
    return out


def normalize_text(text: str, locale: str) -> str:
    """Replace every culture term in ``text`` with its general meaning."""
    if not (text or "").strip():
        return text
    pattern, meanings = _compiled(locale)
    if pattern is None:
        return text
    return pattern.sub(lambda m: meanings[m.group(0).lower()], text)


def term_in_text(term: str, text: str) -> bool:
    """True when a single culture ``term`` appears in ``text`` with word boundaries."""
    needle = (term or "").strip().lower()
    haystack = (text or "")
    if not needle or not haystack.strip():
        return False
    pattern = re.compile(
        rf"{_LEFT_BOUNDARY}{re.escape(needle)}{_RIGHT_BOUNDARY}",
        re.IGNORECASE,
    )
    return pattern.search(haystack) is not None
