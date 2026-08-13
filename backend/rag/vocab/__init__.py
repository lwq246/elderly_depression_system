"""Culture local vocabulary RAG (companion).

Stores one Chroma record per canonical term (aliases + meaning + locale metadata) and
retrieves the relevant terms per companion turn — literal alias match (deterministic,
guarantees exact dialect tokens) unioned with semantic search (paraphrases) — so the
vocabulary is re-injected at the salient end of the prompt every turn instead of being
inlined once and forgotten over a long session.

    parse.py     local-vocabulary.md tables -> canonical term records
    ingest.py    embed + upsert records into the vocab collection (CLI)
    retrieve.py  per-turn literal + semantic retrieval + prompt block formatting
"""
