"""Build culture vocabulary chunk records (for tests/tools — not ingested into Chroma)."""

from __future__ import annotations

from backend.rag.vocab.data import VOCABULARY_TERMS, vocabulary_locales


def _make_term_chunk(
    *,
    source: str,
    locale: str,
    term: str,
    meaning: str,
) -> dict:
    general = meaning.strip()
    return {
        "id": f"{source}:term:{term}",
        "text": general,
        "metadata": {
            "locale": locale,
            "section": "Words residents often use",
            "term": term,
        },
        "embed_text": term,
    }


def chunk_local_vocabulary(*, source: str, locale: str) -> list[dict]:
    """Build term-only RAG chunks for a culture locale."""
    chunks: list[dict] = []
    seen_terms: set[str] = set()

    for variants, meaning in VOCABULARY_TERMS.get(locale, []):
        for term in variants:
            key = term.strip().lower()
            if not key or key in seen_terms:
                continue
            seen_terms.add(key)
            chunks.append(
                _make_term_chunk(
                    source=source,
                    locale=locale,
                    term=key,
                    meaning=meaning,
                )
            )

    return chunks


def build_vocabulary_chunks(*, locales: list[str] | None = None) -> list[dict]:
    """Build all vocabulary chunks from in-code locale definitions."""
    chunks: list[dict] = []
    for locale in locales or vocabulary_locales():
        source = f"culture-vocabulary/{locale}"
        chunks.extend(chunk_local_vocabulary(source=source, locale=locale))
    return chunks


def vocab_embedding_input(chunk: dict) -> str:
    """Text sent to the embedding model for this vocabulary chunk."""
    return chunk.get("embed_text") or chunk["text"]
