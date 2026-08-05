"""Inspect the Chroma RAG index (supplemental reference chunks)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import settings
from backend.rag.store import COLLECTION_NAME, get_collection


def _preview(text: str, limit: int) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def inspect_index(*, section: str | None, full: bool, preview_chars: int, as_json: bool) -> int:
    collection = get_collection()
    count = collection.count()

    if count == 0:
        print(f"Collection '{COLLECTION_NAME}' is empty.")
        print(f"Chroma path: {settings.rag_chroma_path}")
        print("Run: C:/Python314/python.exe backend/rag/ingest.py --reset")
        return 1

    if section:
        result = collection.get(
            where={"section": section},
            include=["documents", "metadatas"],
            limit=1,
        )
        if not result["ids"]:
            print(f"No chunk with section={section!r}")
            return 1
        rows = list(zip(result["metadatas"], result["documents"], strict=False))
    else:
        data = collection.get(include=["metadatas", "documents"])
        rows = sorted(
            zip(data["metadatas"], data["documents"], strict=False),
            key=lambda x: x[0].get("section", ""),
        )

    if as_json:
        payload = []
        for meta, doc in rows:
            payload.append(
                {
                    "section": meta.get("section"),
                    "source": meta.get("source"),
                    "type": meta.get("type"),
                    "locale": meta.get("locale"),
                    "topic_id": meta.get("topic_id"),
                    "chars": len(doc),
                    "text": doc if full else _preview(doc, preview_chars),
                }
            )
        print(json.dumps({"collection": COLLECTION_NAME, "count": count, "chunks": payload}, indent=2))
        return 0

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Chroma path: {settings.rag_chroma_path}")
    print(f"Chunks: {count}")
    print("Note: domain rubrics are in the analyst system prompt. This index is facility SOP only.")
    print()

    for i, (meta, doc) in enumerate(rows, start=1):
        print(f"--- {i}. {meta.get('section', '(no section)')} ---")
        print(f"source:  {meta.get('source')}")
        print(f"type:    {meta.get('type')}")
        print(f"locale:  {meta.get('locale')}")
        if meta.get("topic_id"):
            print(f"topic_id: {meta.get('topic_id')}")
        print(f"chars:   {len(doc)}")
        print()
        print(doc if full else _preview(doc, preview_chars))
        print()

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Chroma supplemental RAG chunks")
    parser.add_argument("--section", help="Show one chunk by exact section heading")
    parser.add_argument("--full", action="store_true", help="Print full chunk text")
    parser.add_argument("--preview", type=int, default=200, help="Preview length when not using --full")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    raise SystemExit(
        inspect_index(
            section=args.section,
            full=args.full,
            preview_chars=args.preview,
            as_json=args.json,
        )
    )


if __name__ == "__main__":
    main()
