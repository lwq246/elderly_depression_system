"""Convert a raw facility policy (PDF or text) into RAG-ready facility-policy markdown.

This bridges an uploaded policy into the *facility-policy* flow (unlike ingest_toolkit.py,
which targets the separate toolkit collection). Pipeline:

    PDF/text  ->  extract text  ->  LLM reformat (convert.py)  ->  coverage guard
              ->  write .cursor/skills/facility-policy/<locale>.md

It intentionally stops at writing markdown so a human can review the converted file before
ingesting. Run the normal ingest afterwards:

    C:/Python314/python.exe backend/rag/policy/convert_file.py "C:/path/policy.pdf" --locale en-AU
    C:/Python314/python.exe backend/rag/ingest.py --reset

Use --text for an already-extracted .txt/.md source (skips PDF parsing).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR
from backend.rag.policy.chunking import iter_policy_sections
from backend.rag.policy.convert import (
    check_conversion_coverage,
    convert_policy_markdown,
    format_coverage_report,
)

VALID_LOCALES = ("en-AU", "en-SG")


def extract_text(path: Path) -> str:
    """Extract source text: parse a PDF with pypdf, else read the file as UTF-8 text."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return path.read_text(encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a PDF/text facility policy into facility-policy markdown."
    )
    parser.add_argument("source", type=Path, help="Source policy file (.pdf, .txt, or .md)")
    parser.add_argument(
        "--locale",
        required=True,
        choices=VALID_LOCALES,
        help="Policy locale; also the output filename stem ingest uses.",
    )
    parser.add_argument("--site-name", default="Facility", help="Facility name for the header")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output markdown path (default: .cursor/skills/facility-policy/<locale>.md)",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite the output file if it already exists"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write even if the content-coverage guard fails (lossy conversion)",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"Source not found: {args.source}")
        return 1

    out_path = args.out or (SKILLS_DIR / "facility-policy" / f"{args.locale}.md")
    if out_path.exists() and not args.overwrite:
        print(f"Refusing to overwrite existing {out_path} (pass --overwrite to replace).")
        return 1

    print(f"[1/4] Extracting {args.source.name} ...")
    source = extract_text(args.source)
    if not source.strip():
        print("  No text extracted (scanned/image PDF?). Provide a text source with --text.")
        return 1
    print(f"  {len(source)} chars")

    print("[2/4] Converting via LLM ...")
    converted = await convert_policy_markdown(
        source, locale=args.locale, site_name=args.site_name
    )
    coverage = check_conversion_coverage(source, converted)
    print(format_coverage_report(coverage))
    if not coverage.ok and not args.force:
        print(
            "\nAborting: conversion dropped content (LLM sampling is nondeterministic). "
            "Re-run for a clean pass, or use --force to write anyway. Nothing was written."
        )
        return 1

    print("[3/4] Section preview ...")
    for s in iter_policy_sections(converted, locale=args.locale):
        print(f"    [{s['pathway']}|{s['char_count']}c] {s['section']}")

    print(f"[4/4] Writing {out_path} ...")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(converted, encoding="utf-8")
    print(
        f"Wrote {out_path}.\nReview it, then ingest with:\n"
        f"    C:/Python314/python.exe backend/rag/ingest.py --reset"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
