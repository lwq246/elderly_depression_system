"""Ingest a standalone reference PDF (RASA 'Mental Health in RACF' toolkit) into its own
Chroma collection (`screening-mh-toolkit`).

Kept separate from facility-policy so it never mixes into analyst policy retrieval and is
not wiped by `ingest.py --reset`. Re-running replaces this doc's chunks (idempotent).

    C:/Python314/python.exe backend/rag/ingest_toolkit.py
    C:/Python314/python.exe backend/rag/ingest_toolkit.py --pdf "C:/path/to/file.pdf"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader

from backend.rag.ingest import _upsert_chunks
from backend.rag.policy.chunking import chunk_markdown, iter_policy_sections
from backend.rag.policy.convert import (
    check_conversion_coverage,
    convert_policy_markdown,
    format_coverage_report,
)
from backend.rag.store import TOOLKIT_COLLECTION_NAME, get_toolkit_collection

DEFAULT_PDF = Path(r"C:\Users\leewe\Downloads\Mental-Health-RACF-Toolkit_RASA_Final.pdf")
DOC_ID = "mh-racf-toolkit"
LOCALE = "en-AU"


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest the MH-in-RACF toolkit PDF into Chroma")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="Source PDF path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ingest even if the content-coverage guard fails (lossy conversion)",
    )
    args = parser.parse_args()

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}")
        return 1

    collection = get_toolkit_collection()

    print(f"[1/4] Extracting {args.pdf.name} ...")
    source = extract_pdf(args.pdf)
    print(f"  {len(source)} chars")

    print("[2/4] Converting via LLM ...")
    converted = await convert_policy_markdown(source, locale=LOCALE, site_name="RASA Toolkit")
    coverage = check_conversion_coverage(source, converted)
    print(format_coverage_report(coverage))
    if not coverage.ok and not args.force:
        print(
            "\nAborting: conversion dropped content (LLM sampling is nondeterministic). "
            "Re-run to get a clean pass, or use --force to ingest anyway. "
            "Existing chunks were left untouched."
        )
        return 1

    print("[3/4] Chunking ...")
    for s in iter_policy_sections(converted, locale=LOCALE):
        print(f"    [{s['pathway']}|{s['char_count']}c] {s['section']}")
    chunks = chunk_markdown(
        converted,
        source=f"toolkit/{DOC_ID}.md",
        doc_type="mh_toolkit",
        locale=LOCALE,
        doc_id=DOC_ID,
        doc_version="rasa-final",
    )

    print("[4/4] Embedding + upserting (idempotent replace) ...")
    collection.delete(where={"doc_id": DOC_ID})  # clear prior version first
    _upsert_chunks(collection, chunks)
    print(
        f"Ingested {len(chunks)} chunks into '{TOOLKIT_COLLECTION_NAME}' "
        f"({collection.count()} total)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
