"""Culture vocabulary retrieval for companion per-turn context.

Local glossary (data.py) + literal substring match — no Chroma or embeddings.
"""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.rag.vocab.data import VOCABULARY_TERMS

_VOCAB_SECTION = "Words residents often use"


def _term_in_resident_text(term: str, resident_text: str) -> bool:
    """True when the culture term appears in the resident message."""
    needle = term.strip().lower()
    if not needle:
        return False
    return needle in resident_text.lower()


def _vocab_row(*, term: str, meaning: str, locale: str) -> dict[str, Any]:
    return {
        "text": meaning,
        "metadata": {
            "term": term,
            "locale": locale,
            "section": _VOCAB_SECTION,
        },
    }


def _literal_vocabulary_matches(resident_text: str, *, locale: str) -> list[dict[str, Any]]:
    """Glossary terms in the message, longest first; shorter nested terms removed."""
    haystack = resident_text.strip().lower()
    if not haystack:
        return []

    seen_terms: set[str] = set()
    rows: list[dict[str, Any]] = []
    for variants, meaning in VOCABULARY_TERMS.get(locale, []):
        general = meaning.strip()
        if not general:
            continue
        for variant in variants:
            term = variant.strip().lower()
            if not term or term in seen_terms:
                continue
            if term not in haystack:
                continue
            seen_terms.add(term)
            rows.append(_vocab_row(term=term, meaning=general, locale=locale))

    rows.sort(key=lambda row: len((row.get("metadata") or {}).get("term", "")), reverse=True)
    return _drop_shorter_substring_matches(rows)


def _drop_shorter_substring_matches(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep longest matches only — drop shorter terms contained in a longer match."""
    kept: list[dict[str, Any]] = []
    kept_terms: list[str] = []
    for row in rows:
        term = ((row.get("metadata") or {}).get("term") or "").strip().lower()
        if not term:
            continue
        if any(term in longer for longer in kept_terms):
            continue
        kept.append(row)
        kept_terms.append(term)
    return kept


def format_vocabulary_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata") or {}
        term = meta.get("term", "")
        if not term:
            continue
        meaning = chunk.get("text", "")
        parts.append(f"### Vocabulary {i} — {term}\n{term} → {meaning}")
    return "\n\n".join(parts)


def vocab_matches_from_hits(hits: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Compact term/meaning pairs stored on each resident turn for the analyst."""
    matches: list[dict[str, str]] = []
    for chunk in hits:
        meta = chunk.get("metadata") or {}
        term = (meta.get("term") or "").strip()
        meaning = (chunk.get("text") or "").strip()
        if term and meaning:
            matches.append({"term": term, "meaning": meaning})
    return matches


def format_vocab_matches_for_analyst(matches: list[dict[str, str]]) -> str:
    if not matches:
        return ""
    lines = [f"- {m['term']} → {m['meaning']}" for m in matches]
    return "Local vocabulary (matched this turn):\n" + "\n".join(lines)


def retrieve_vocabulary_literal_hits(
    resident_text: str,
    *,
    locale: str,
) -> list[dict[str, Any]]:
    """All literal glossary matches for the locale (before top_k cap)."""
    return _literal_vocabulary_matches(resident_text, locale=locale)


def retrieve_vocabulary_chroma_hits(
    resident_text: str,
    *,
    locale: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Alias for tests/reports: all literal matches (legacy name from Chroma era)."""
    _ = top_k
    return retrieve_vocabulary_literal_hits(resident_text, locale=locale)


def retrieve_vocabulary_for_companion(
    resident_text: str,
    *,
    locale: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Retrieve culture vocabulary for the companion via local glossary literal match."""
    k = top_k or settings.rag_vocab_top_k
    hits = _literal_vocabulary_matches(resident_text, locale=locale)
    return hits[:k] if k else hits
