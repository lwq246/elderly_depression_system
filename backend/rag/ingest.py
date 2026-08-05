"""Ingest facility policy docs into Chroma for analyst RAG."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR, settings
from backend.rag.chunking import chunk_markdown, load_skill_sources
from backend.rag.embeddings import embed_texts
from backend.rag.store import COLLECTION_NAME, get_client, get_collection


def ingest_all(*, reset: bool = False) -> int:
    client = get_client()
    if reset:
        for name in ("screening-rubric", "screening-policy", COLLECTION_NAME):
            try:
                client.delete_collection(name)
            except Exception:
                pass

    collection = get_collection(client)
    all_chunks: list[dict] = []

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
        all_chunks.extend(chunks)
        print(f"  {rel}: {len(chunks)} facility policy chunks ({meta['locale']})")

    if not all_chunks:
        print("No chunks to ingest.")
        return 0

    if reset:
        collection = get_collection(client)

    ids = [f"{c['id']}#{i}" for i, c in enumerate(all_chunks)]
    documents = [c["text"] for c in all_chunks]
    metadatas = [c["metadata"] for c in all_chunks]

    batch_size = 16
    for start in range(0, len(all_chunks), batch_size):
        end = start + batch_size
        batch_embeddings = embed_texts(documents[start:end])
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=batch_embeddings,
        )

    count = collection.count()
    print(f"Ingested {len(all_chunks)} chunks into collection '{COLLECTION_NAME}' ({count} total)")
    return len(all_chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest facility policy docs into Chroma RAG index")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the collection")
    args = parser.parse_args()
    print(f"Chroma path: {settings.rag_chroma_path}")
    print(f"Embedding model: {settings.rag_embedding_model}")
    ingest_all(reset=args.reset)


if __name__ == "__main__":
    main()
