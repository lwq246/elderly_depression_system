"""Convert raw facility policy to RAG-ready markdown via LLM, then validate."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import DATA_DIR
from backend.rag.policy.convert import (
    check_conversion_coverage,
    convert_policy_markdown,
    format_coverage_report,
)
from backend.rag.policy.validate import format_validation_report, validate_policy_markdown

DEFAULT_DRAFTS_DIR = DATA_DIR / "policy_drafts"


def _read_input(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    return path.read_text(encoding="utf-8")


def _write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


async def _run_convert(args: argparse.Namespace) -> int:
    source = _read_input(args.input)
    converted = await convert_policy_markdown(
        source,
        locale=args.locale,
        site_name=args.site_name,
    )

    out_path = args.output
    if out_path is None:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        out_path = DEFAULT_DRAFTS_DIR / f"{args.locale}-{stamp}.md"

    _write_output(out_path, converted)
    print(f"Wrote draft: {out_path}")

    coverage = check_conversion_coverage(source, converted)
    print(format_coverage_report(coverage))

    exit_code = 0 if coverage.ok else 1
    if args.validate:
        result = validate_policy_markdown(converted, locale=args.locale, path=out_path)
        print(format_validation_report(result))
        if not result.ok:
            exit_code = 1
    return exit_code


def _run_validate(args: argparse.Namespace) -> int:
    text = _read_input(args.input)
    result = validate_policy_markdown(text, locale=args.locale, path=args.input)
    print(format_validation_report(result))
    return 0 if result.ok else 1


def _run_approve(args: argparse.Namespace) -> int:
    from backend.app.config import SKILLS_DIR

    text = _read_input(args.input)
    result = validate_policy_markdown(text, locale=args.locale, path=args.input)
    print(format_validation_report(result))
    if not result.ok:
        return 1

    dest = args.dest or (SKILLS_DIR / "facility-policy" / f"{args.locale}.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _write_output(dest, text)
    print(f"Approved policy copied to: {dest}")
    print("Re-ingest with: python backend/rag/ingest.py --reset")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert raw facility policy to RAG-ready markdown (LLM) and validate"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    convert_p = sub.add_parser("convert", help="LLM-convert raw policy to normalized markdown")
    convert_p.add_argument("--input", "-i", type=Path, required=True, help="Raw policy file")
    convert_p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help=f"Output draft path (default: {DEFAULT_DRAFTS_DIR}/<locale>-<timestamp>.md)",
    )
    convert_p.add_argument(
        "--locale",
        "-l",
        required=True,
        choices=["en-AU", "en-SG"],
        help="Target locale",
    )
    convert_p.add_argument(
        "--site-name",
        default="Facility",
        help="Facility name for the document title",
    )
    convert_p.add_argument(
        "--validate",
        action="store_true",
        help="Run validator on the converted draft",
    )

    validate_p = sub.add_parser("validate", help="Validate a normalized policy draft")
    validate_p.add_argument("--input", "-i", type=Path, required=True, help="Policy markdown file")
    validate_p.add_argument("--locale", "-l", default=None, choices=["en-AU", "en-SG"])

    approve_p = sub.add_parser(
        "approve",
        help="Validate draft and copy to facility-policy for ingest (human approval step)",
    )
    approve_p.add_argument("--input", "-i", type=Path, required=True, help="Approved policy draft")
    approve_p.add_argument(
        "--locale",
        "-l",
        required=True,
        choices=["en-AU", "en-SG"],
        help="Target locale filename (en-AU.md / en-SG.md)",
    )
    approve_p.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Override destination (default: .cursor/skills/facility-policy/<locale>.md)",
    )

    args = parser.parse_args()
    if args.command == "convert":
        raise SystemExit(asyncio.run(_run_convert(args)))
    if args.command == "validate":
        raise SystemExit(_run_validate(args))
    if args.command == "approve":
        raise SystemExit(_run_approve(args))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
