"""Ingest facility policy into Chroma (culture vocabulary uses local glossary only)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR, settings
from backend.rag.embeddings import embed_texts
from backend.rag.policy.chunking import chunk_markdown, load_skill_sources
from backend.rag.store import (
    POLICY_COLLECTION_NAME,
    delete_all_collections,
    delete_doc,
    get_client,
    get_policy_collection,
)


def _upsert_chunks(collection, chunks: list[dict]) -> None:
    if not chunks:
        return
    ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{**c["metadata"], "ingested_at": ingested_at} for c in chunks]
    batch_size = 16
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        batch_embeddings = embed_texts(
            [c.get("embed_text") or c["text"] for c in chunks[start:end]]
        )
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=batch_embeddings,
        )


def _doc_version_for(path: Path) -> str:
    """Version stamp from file mtime — changes when the SOP is edited."""
    return date.fromtimestamp(path.stat().st_mtime).isoformat()


def ingest_all(*, reset: bool = False, doc_ids: list[str] | None = None) -> int:
    """Ingest facility policy chunks.

    reset: drop and rebuild all collections.
    doc_ids: if given, only (re)ingest these documents — deletes their existing chunks
             first, then upserts (incremental/versioned update without a full rebuild).
    """
    client = get_client()
    if reset:
        delete_all_collections(client)

    policy_collection = get_policy_collection(client)
    policy_chunks: list[dict] = []

    for path, meta in load_skill_sources(SKILLS_DIR):
        if not path.is_file():
            print(f"SKIP missing: {path}")
            continue
        locale = meta.get("locale", "all")
        if locale not in settings.rag_index_locale_list:
            print(f"SKIP {path.name}: locale {locale} not in RAG_INDEX_LOCALES")
            continue
        doc_id = meta.get("doc_id", path.stem)
        if doc_ids and doc_id not in doc_ids:
            continue
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(SKILLS_DIR)).replace("\\", "/")
        chunks = chunk_markdown(
            text,
            source=rel,
            doc_type=meta["doc_type"],
            locale=locale,
            doc_id=doc_id,
            doc_version=_doc_version_for(path),
        )
        if doc_ids and not reset:
            # Incremental: clear this doc's old chunks before re-upserting.
            delete_doc(doc_id, collection=policy_collection)
        policy_chunks.extend(chunks)
        print(f"  {rel}: {len(chunks)} facility policy chunks ({meta['locale']})")

    if not policy_chunks:
        print("No policy chunks to ingest.")
        return 0

    _upsert_chunks(policy_collection, policy_chunks)

    policy_count = policy_collection.count()
    print(
        f"Ingested {len(policy_chunks)} policy chunks into "
        f"'{POLICY_COLLECTION_NAME}' ({policy_count} total)"
    )
    return policy_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest facility policy into Chroma RAG index")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild collections")
    parser.add_argument(
        "--doc",
        action="append",
        dest="doc_ids",
        metavar="DOC_ID",
        help="Incrementally (re)ingest only this doc_id (repeatable); deletes its old chunks first",
    )
    args = parser.parse_args()
    print(f"Chroma path: {settings.rag_chroma_path}")
    if settings.rag_embedding_backend == "local":
        print(f"Embedding backend: local ({settings.rag_local_embedding_model})")
    else:
        print(f"Embedding backend: api ({settings.rag_embedding_model})")
    ingest_all(reset=args.reset, doc_ids=args.doc_ids)


if __name__ == "__main__":
    main()
