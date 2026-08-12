"""Culture vocabulary retrieval for companion per-turn context.

Local glossary (data.py) + boundary-aware literal match (matcher.py) — no Chroma or
embeddings. The single compiled matcher is shared with normalize.py.
"""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.rag.vocab.matcher import find_matches, term_in_text

_VOCAB_SECTION = "Words residents often use"


def _term_in_resident_text(term: str, resident_text: str) -> bool:
    """True when the culture term appears in the resident message (word-boundary aware)."""
    return term_in_text(term, resident_text)


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
    """Glossary terms in the message as rows (longest match wins, nested terms dropped)."""
    return [
        _vocab_row(term=term, meaning=meaning, locale=locale)
        for term, meaning in find_matches(resident_text, locale)
    ]


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
