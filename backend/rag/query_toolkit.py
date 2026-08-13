"""Query or dump the standalone mental-health toolkit collection (`screening-mh-toolkit`).

    C:/Python314/python.exe backend/rag/query_toolkit.py "how do I respond to a resident with low mood?"
    C:/Python314/python.exe backend/rag/query_toolkit.py "referral options" -k 5 --all
    C:/Python314/python.exe backend/rag/query_toolkit.py --dump          # every chunk, no query
    C:/Python314/python.exe backend/rag/query_toolkit.py --dump --full   # with full text
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.rag.query import query_collection
from backend.rag.store import get_toolkit_collection


def _dump(full: bool) -> int:
    """Fetch every chunk (no vector search, no similarity threshold), in insertion order."""
    collection = get_toolkit_collection()
    data = collection.get(include=["documents", "metadatas"])
    ids = data["ids"]
    if not ids:
        print("Collection is empty.")
        print("Ingest first: C:/Python314/python.exe backend/rag/ingest_toolkit.py")
        return 1

    print(f"{len(ids)} chunks in '{collection.name}'\n")
    for chunk_id, meta, doc in zip(ids, data["metadatas"], data["documents"], strict=False):
        meta = meta or {}
        print(f"=== {chunk_id} ===")
        print(f"section : {meta.get('section')}")
        print(f"pathway : {meta.get('pathway')}  |  child_index: {meta.get('child_index')}")
        print(doc if full else doc[:600] + ("..." if len(doc) > 600 else ""))
        print()
    return 0


def _search(query: str, top_k: int, apply_threshold: bool, full: bool) -> int:
    rows = query_collection(
        query,
        doc_type="mh_toolkit",
        top_k=top_k,
        apply_similarity_threshold=apply_threshold,
    )
    if not rows:
        print("No matches (collection empty or below similarity threshold).")
        print("Ingest first: C:/Python314/python.exe backend/rag/ingest_toolkit.py")
        return 1

    for i, row in enumerate(rows, start=1):
        meta = row["metadata"]
        sim = row["cosine_similarity"]
        sim_str = f"{sim:.3f}" if sim is not None else "n/a"
        print(f"--- {i}. {meta.get('section')} (similarity={sim_str}, pathway={meta.get('pathway')}) ---")
        text = row["text"]
        print(text if full else text[:600] + ("..." if len(text) > 600 else ""))
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Query or dump the MH-in-RACF toolkit collection")
    parser.add_argument("query", nargs="?", help="Natural-language query (omit when using --dump)")
    parser.add_argument("-k", "--top-k", type=int, default=3, help="Number of results")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ignore the similarity threshold (show best matches regardless of score)",
    )
    parser.add_argument("--full", action="store_true", help="Print full section text")
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Print every chunk in the collection (no query needed)",
    )
    args = parser.parse_args()

    if args.dump:
        return _dump(full=args.full)
    if not args.query:
        parser.error("provide a query, or use --dump to print all chunks")
    return _search(args.query, args.top_k, apply_threshold=not args.all, full=args.full)


if __name__ == "__main__":
    raise SystemExit(main())
