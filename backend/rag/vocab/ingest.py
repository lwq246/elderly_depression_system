"""Ingest culture local vocabulary into the Chroma vocab collection.

    python backend/rag/vocab/ingest.py --reset

Processes both culture locales (en-SG, en-AU) regardless of RAG_INDEX_LOCALES — that
setting scopes facility-policy ingest only. One record per canonical term.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR, settings
from backend.rag.embeddings import embed_texts
from backend.rag.store import VOCAB_COLLECTION_NAME, get_client, get_vocab_collection
from backend.rag.vocab.parse import VocabRecord, parse_vocabulary_markdown

VOCAB_LOCALES: tuple[str, ...] = ("en-SG", "en-AU")


def _culture_dir(locale: str) -> str:
    return "culture-en-SG" if locale == "en-SG" else "culture-en-AU"


def _vocab_path(locale: str) -> Path:
    return SKILLS_DIR / "screening-conversation" / _culture_dir(locale) / "local-vocabulary.md"


def _load_records() -> list[VocabRecord]:
    records: list[VocabRecord] = []
    for locale in VOCAB_LOCALES:
        path = _vocab_path(locale)
        if not path.is_file():
            print(f"SKIP missing: {path}")
            continue
        recs = parse_vocabulary_markdown(path.read_text(encoding="utf-8"), locale)
        print(f"  {path.name}: {len(recs)} terms ({locale})")
        records.extend(recs)
    return records


def _upsert(collection, records: list[VocabRecord]) -> None:
    ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    batch = 16
    for start in range(0, len(records), batch):
        chunk = records[start : start + batch]
        embeddings = embed_texts([r.embed_text for r in chunk])
        collection.upsert(
            ids=[r.id for r in chunk],
            documents=[r.document for r in chunk],
            metadatas=[{**r.metadata(), "ingested_at": ingested_at} for r in chunk],
            embeddings=embeddings,
        )


def ingest_vocab(*, reset: bool = False) -> int:
    client = get_client()
    if reset:
        try:
            client.delete_collection(VOCAB_COLLECTION_NAME)
        except Exception:
            pass

    collection = get_vocab_collection(client)
    records = _load_records()
    if not records:
        print("No vocabulary records to ingest.")
        return 0

    _upsert(collection, records)
    total = collection.count()
    print(f"Ingested {len(records)} vocab terms into '{VOCAB_COLLECTION_NAME}' ({total} total)")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest culture vocabulary into Chroma")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the vocab collection")
    args = parser.parse_args()
    print(f"Chroma path: {settings.rag_chroma_path}")
    if settings.rag_embedding_backend == "local":
        print(f"Embedding backend: local ({settings.rag_local_embedding_model})")
    else:
        print(f"Embedding backend: api ({settings.rag_embedding_model})")
    ingest_vocab(reset=args.reset)


if __name__ == "__main__":
    main()
