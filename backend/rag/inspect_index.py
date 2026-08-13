"""Inspect the Chroma RAG index (supplemental reference chunks)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import settings
from backend.rag.store import (
    POLICY_COLLECTION_NAME,
    collection_counts,
    get_policy_collection,
)


def _preview(text: str, limit: int) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def _build_where(
    *,
    locale: str | None,
    section: str | None,
    term: str | None,
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if locale:
        clauses.append({"locale": locale})
    if section:
        clauses.append({"section": section})
    if term:
        clauses.append({"term": term})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _fetch_from_collection(
    collection,
    *,
    collection_name: str,
    locale: str | None = None,
    section: str | None = None,
    term: str | None = None,
) -> list[tuple[str, str, dict[str, Any], str]]:
    where = _build_where(locale=locale, section=section, term=term)
    kwargs: dict[str, Any] = {"include": ["metadatas", "documents"]}
    if where:
        kwargs["where"] = where
    data = collection.get(**kwargs)
    rows = [
        (collection_name, chunk_id, meta, doc)
        for chunk_id, meta, doc in zip(
            data["ids"],
            data["metadatas"],
            data["documents"],
            strict=False,
        )
    ]
    rows.sort(
        key=lambda row: (
            row[2].get("locale", ""),
            row[2].get("term", ""),
            row[2].get("section", ""),
        )
    )
    return rows


def fetch_chunks(
    *,
    doc_type: str | None = None,
    locale: str | None = None,
    section: str | None = None,
    term: str | None = None,
) -> list[tuple[str, str, dict[str, Any], str]]:
    """Return (collection_name, id, metadata, document) rows."""
    rows: list[tuple[str, str, dict[str, Any], str]] = []
    if doc_type in (None, "facility_policy"):
        rows.extend(
            _fetch_from_collection(
                get_policy_collection(),
                collection_name=POLICY_COLLECTION_NAME,
                locale=locale,
                section=section,
                term=term,
            )
        )
    return rows


def inspect_index(
    *,
    doc_type: str | None,
    locale: str | None,
    section: str | None,
    term: str | None,
    full: bool,
    preview_chars: int,
    as_json: bool,
) -> int:
    counts = collection_counts()
    if counts["total"] == 0:
        print("Chroma collections are empty.")
        print(f"Chroma path: {settings.rag_chroma_path}")
        print(f"  {POLICY_COLLECTION_NAME}: 0")
        print("Run: C:/Python314/python.exe backend/rag/ingest.py --reset")
        return 1

    rows = fetch_chunks(doc_type=doc_type, locale=locale, section=section, term=term)
    if not rows:
        print("No chunks matched the filters.")
        return 1

    if as_json:
        payload = []
        for collection_name, chunk_id, meta, doc in rows:
            payload.append(
                {
                    "collection": collection_name,
                    "id": chunk_id,
                    "section": meta.get("section"),
                    "locale": meta.get("locale"),
                    "term": meta.get("term"),
                    "topic_id": meta.get("topic_id"),
                    "text": doc if full else _preview(doc, preview_chars),
                }
            )
        print(
            json.dumps(
                {
                    "path": settings.rag_chroma_path,
                    "collections": {
                        POLICY_COLLECTION_NAME: counts["policy"],
                    },
                    "matched": len(payload),
                    "chunks": payload,
                },
                indent=2,
            )
        )
        return 0

    print(f"Chroma path: {settings.rag_chroma_path}")
    print(f"  {POLICY_COLLECTION_NAME}: {counts['policy']} chunks")
    print(f"Matched: {len(rows)}")
    print()

    for i, (collection_name, chunk_id, meta, doc) in enumerate(rows, start=1):
        label = meta.get("term") or meta.get("section", "(no section)")
        print(f"--- {i}. {label} ---")
        print(f"collection: {collection_name}")
        print(f"id:         {chunk_id}")
        print(f"locale:     {meta.get('locale')}")
        if meta.get("term"):
            print(f"term:       {meta.get('term')}")
        if meta.get("topic_id"):
            print(f"topic_id:   {meta.get('topic_id')}")
        print()
        print(doc if full else _preview(doc, preview_chars))
        print()

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Chroma RAG chunks")
    parser.add_argument(
        "--type",
        dest="doc_type",
        choices=("facility_policy",),
        help="Which collection to show",
    )
    parser.add_argument("--locale", help="Locale filter (e.g. en-SG, en-AU)")
    parser.add_argument("--section", help="Exact section heading filter")
    parser.add_argument("--term", help="Vocabulary term filter (e.g. sian)")
    parser.add_argument("--full", action="store_true", help="Print full chunk text")
    parser.add_argument("--preview", type=int, default=200, help="Preview length when not using --full")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    raise SystemExit(
        inspect_index(
            doc_type=args.doc_type,
            locale=args.locale,
            section=args.section,
            term=args.term,
            full=args.full,
            preview_chars=args.preview,
            as_json=args.json,
        )
    )


if __name__ == "__main__":
    main()
