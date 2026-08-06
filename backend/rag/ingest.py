"""Ingest facility policy and culture vocabulary into Chroma."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR, settings
from backend.rag.embeddings import embed_texts
from backend.rag.policy.chunking import chunk_markdown, load_skill_sources
from backend.rag.store import (
    POLICY_COLLECTION_NAME,
    VOCAB_COLLECTION_NAME,
    delete_all_collections,
    get_client,
    get_policy_collection,
    get_vocab_collection,
)
from backend.rag.vocab.chunking import build_vocabulary_chunks, vocab_embedding_input


def _embedding_input(chunk: dict) -> str:
    if "embed_text" in chunk:
        return vocab_embedding_input(chunk)
    return chunk["text"]


def _upsert_chunks(collection, chunks: list[dict], *, id_offset: int = 0) -> None:
    if not chunks:
        return
    ids = [f"{c['id']}#{id_offset + i}" for i, c in enumerate(chunks)]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    batch_size = 16
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        batch_embeddings = embed_texts([_embedding_input(c) for c in chunks[start:end]])
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=batch_embeddings,
        )


def ingest_all(*, reset: bool = False) -> int:
    client = get_client()
    if reset:
        delete_all_collections(client)

    policy_chunks: list[dict] = []
    vocab_chunks: list[dict] = []

    for path, meta in load_skill_sources(SKILLS_DIR):
        if not path.is_file():
            print(f"SKIP missing: {path}")
            continue
        locale = meta.get("locale", "all")
        if locale not in settings.rag_index_locale_list:
            print(f"SKIP {path.name}: locale {locale} not in RAG_INDEX_LOCALES")
            continue
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(SKILLS_DIR)).replace("\\", "/")
        chunks = chunk_markdown(
            text,
            source=rel,
            doc_type=meta["doc_type"],
            locale=meta.get("locale", "all"),
        )
        policy_chunks.extend(chunks)
        print(f"  {rel}: {len(chunks)} facility policy chunks ({meta['locale']})")

    for locale in settings.rag_vocab_locale_list:
        locale_chunks = [
            c
            for c in build_vocabulary_chunks(locales=[locale])
        ]
        vocab_chunks.extend(locale_chunks)
        print(f"  culture-vocabulary/{locale}: {len(locale_chunks)} vocabulary chunks ({locale})")

    if not policy_chunks and not vocab_chunks:
        print("No chunks to ingest.")
        return 0

    policy_collection = get_policy_collection(client)
    vocab_collection = get_vocab_collection(client)

    _upsert_chunks(policy_collection, policy_chunks, id_offset=0)
    _upsert_chunks(vocab_collection, vocab_chunks, id_offset=1000)

    policy_count = policy_collection.count()
    vocab_count = vocab_collection.count()
    total = policy_count + vocab_count
    print(
        f"Ingested {len(policy_chunks)} policy + {len(vocab_chunks)} vocabulary chunks "
        f"into '{POLICY_COLLECTION_NAME}' ({policy_count}) and "
        f"'{VOCAB_COLLECTION_NAME}' ({vocab_count}); {total} total"
    )
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest facility policy and vocabulary into Chroma RAG index")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild collections")
    args = parser.parse_args()
    print(f"Chroma path: {settings.rag_chroma_path}")
    print(f"Embedding model: {settings.rag_embedding_model}")
    ingest_all(reset=args.reset)


if __name__ == "__main__":
    main()
