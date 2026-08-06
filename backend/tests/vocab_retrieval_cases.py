"""Synthetic cases for live culture-vocabulary retrieval (Chroma + embeddings).

Run (from repo root):
  C:/Python314/python.exe backend/tests/vocab_retrieval_cases.py

Or:
  scripts\\run-vocab-retrieval-tests.cmd

Requires: ingest first, OPENAI_API_KEY in .env
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.vocab.retrieve import (
    retrieve_vocabulary_chroma_hits,
    retrieve_vocabulary_for_companion,
)

DEFAULT_REPORT_DIR = ROOT / "data" / "test-results"


@dataclass(frozen=True)
class VocabRetrievalCase:
    case_id: str
    locale: str
    text: str
    must_include: tuple[str, ...] = ()
    must_exclude: tuple[str, ...] = ()
    note: str = ""

    def evaluate(self, rows: list[dict[str, Any]]) -> tuple[bool, str]:
        terms = {(r.get("metadata") or {}).get("term", "").lower() for r in rows}
        terms.discard("")

        missing = [t for t in self.must_include if t.lower() not in terms]
        forbidden = [t for t in self.must_exclude if t.lower() in terms]

        if missing:
            return False, f"missing terms {missing}; got {sorted(terms)}"
        if forbidden:
            return False, f"forbidden terms {forbidden}; got {sorted(terms)}"
        if self.must_include or self.must_exclude:
            return True, f"ok: {sorted(terms)}"
        if terms:
            return False, f"expected no hits; got {sorted(terms)}"
        return True, "ok: no hits"


VOCAB_RETRIEVAL_CASES: list[VocabRetrievalCase] = [
    VocabRetrievalCase(
        "SG-01",
        "en-SG",
        "Very sian lately, no strength at all.",
        must_include=("sian", "no strength"),
    ),
    VocabRetrievalCase(
        "SG-02",
        "en-SG",
        "Cannot sleep also, sleep very poor.",
        must_include=("cannot sleep", "sleep very poor"),
    ),
    VocabRetrievalCase(
        "SG-03",
        "en-SG",
        "My heart very heavy, very worried about my children.",
        must_include=("heart very heavy", "worried"),
    ),
    VocabRetrievalCase(
        "SG-04",
        "en-SG",
        "Everything buay tahan lately, very sian.",
        must_include=("buay tahan", "sian"),
    ),
    VocabRetrievalCase(
        "SG-05",
        "en-SG",
        "Don't feel like eating, no appetite.",
        must_include=("don't feel like eating", "no appetite"),
    ),
    VocabRetrievalCase(
        "SG-06",
        "en-SG",
        "I feel breathless when I walk, a bit panting.",
        must_include=("breathless", "panting"),
    ),
    VocabRetrievalCase(
        "AU-01",
        "en-AU",
        "Been feeling a bit crook and flat this week.",
        must_include=(),
        note="crook/flat in text but outside chroma top-k — expect empty retrieved",
    ),
    VocabRetrievalCase(
        "AU-01b",
        "en-AU",
        "Feel crook today, been knackered all week.",
        must_include=("crook", "knackered"),
        note="short message — terms rank in chroma top-k",
    ),
    VocabRetrievalCase(
        "AU-02",
        "en-AU",
        "Had crappy sleep and not sleeping well.",
        must_include=("crappy sleep", "not sleeping"),
    ),
    VocabRetrievalCase(
        "AU-03",
        "en-AU",
        "She'll be right, I suppose.",
        must_include=("she'll be right",),
    ),
    VocabRetrievalCase(
        "AU-04",
        "en-AU",
        "Been knackered, off your food for days.",
        must_include=("knackered", "off your food"),
    ),
    VocabRetrievalCase(
        "AU-05",
        "en-AU",
        "Keeping to yourself, a bit quiet in the room.",
        must_include=("keeping to yourself", "a bit quiet"),
    ),
    VocabRetrievalCase(
        "AU-06",
        "en-AU",
        "Feeling a bit lonely, doing it tough lately.",
        must_include=("lonely", "doing it tough"),
    ),
    VocabRetrievalCase(
        "NEG-01",
        "en-AU",
        "I have been feeling sad and tired lately.",
        must_include=(),
        must_exclude=("crook", "flat", "knackered"),
        note="generic English - no culture terms in message",
    ),
    VocabRetrievalCase(
        "NEG-02",
        "en-SG",
        "I feel crook today.",
        must_exclude=("crook",),
        note="AU term in SG session - should not retrieve",
    ),
    # Longer resident turns — culture terms buried in conversational filler
    VocabRetrievalCase(
        "LONG-SG-01",
        "en-SG",
        (
            "You know ah, these few weeks I wake up already very tired. My children all busy "
            "with work, rarely visit. At night cannot sleep also, sleep very poor until morning "
            "still no strength. Sometimes my heart very heavy thinking about old times. "
            "Everything buay tahan lately, very sian."
        ),
        must_include=(
            "cannot sleep",
            "sleep very poor",
            "no strength",
            "heart very heavy",
            "buay tahan",
            "sian",
        ),
        note="long SG ramble with 6 culture terms",
    ),
    VocabRetrievalCase(
        "LONG-SG-02",
        "en-SG",
        (
            "The nurse asked me how I am. I said okay lah but actually don't feel like eating "
            "for many days already, no appetite at all. Also very worried about money and "
            "medication, a bit breathless when I walk to the toilet, panting after that."
        ),
        must_include=(
            "don't feel like eating",
            "no appetite",
            "worried",
            "breathless",
            "panting",
        ),
        note="long SG with appetite + anxiety + breath terms",
    ),
    VocabRetrievalCase(
        "LONG-AU-01",
        "en-AU",
        (
            "I've been telling myself she'll be right but honestly I've been knackered for weeks. "
            "Had crappy sleep every night, not sleeping more than a few hours. They say I'm "
            "keeping to yourself — well I've been a bit quiet in my room. Doing it tough lately, "
            "feeling a bit flat and a bit crook."
        ),
        must_include=(
            "she'll be right",
            "knackered",
            "crappy sleep",
            "not sleeping",
            "a bit quiet",
            "doing it tough",
        ),
        note="long AU ramble — chroma top-k; keeping to yourself/flat/crook rank outside top-10",
    ),
    VocabRetrievalCase(
        "LONG-NEG-01",
        "en-AU",
        (
            "I've had a difficult few weeks. I don't enjoy things the way I used to and I feel "
            "exhausted most mornings. My family lives interstate so I don't see them often. "
            "The staff are kind but I still feel low and unmotivated. Sleep has been broken "
            "and I have little interest in meals."
        ),
        must_exclude=("crook", "flat", "knackered", "crappy sleep", "doing it tough"),
        note="long generic English — should not retrieve culture terms",
    ),
]


def _rows_to_dicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        meta = row.get("metadata") or {}
        sim = row.get("cosine_similarity")
        out.append(
            {
                "term": meta.get("term", ""),
                "meaning": row.get("text", ""),
                "cosine_similarity": round(sim, 4) if sim is not None else None,
                "locale": meta.get("locale", ""),
            }
        )
    return out


def _format_retrieved_line(row: dict[str, Any]) -> str:
    sim = row.get("cosine_similarity")
    if sim is not None:
        return f"{row['term']} -> {row['meaning']}  (cosine_sim={sim:.4f})"
    return f"{row['term']} -> {row['meaning']}  (cosine_sim=n/a)"


def _format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.3f} s"


def run_vocab_retrieval_cases(
    cases: list[VocabRetrievalCase] | None = None,
) -> list[dict[str, Any]]:
    """Run cases and return structured results (for console, JSON, Markdown)."""
    structured: list[dict[str, Any]] = []
    for case in cases or VOCAB_RETRIEVAL_CASES:
        started = time.perf_counter()
        chroma_hits = retrieve_vocabulary_chroma_hits(case.text, locale=case.locale)
        rows = retrieve_vocabulary_for_companion(case.text, locale=case.locale)
        ok, detail = case.evaluate(rows)
        elapsed_s = time.perf_counter() - started
        structured.append(
            {
                "case_id": case.case_id,
                "locale": case.locale,
                "text": case.text,
                "note": case.note,
                "must_include": list(case.must_include),
                "must_exclude": list(case.must_exclude),
                "pass": ok,
                "check": detail,
                "elapsed_s": round(elapsed_s, 4),
                "elapsed": _format_elapsed(elapsed_s),
                "chroma_hits": _rows_to_dicts(chroma_hits),
                "retrieved": _rows_to_dicts(rows),
            }
        )
    return structured


def print_results(results: list[dict[str, Any]]) -> None:
    passed = sum(1 for r in results if r["pass"])
    total_s = sum(r.get("elapsed_s", 0) for r in results)
    print(f"Culture vocab retrieval — {passed}/{len(results)} passed ({_format_elapsed(total_s)} total)\n")
    print("=" * 72)
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['case_id']}  locale={r['locale']}  time={r.get('elapsed', '?')}")
        print(f"  text: {r['text']!r}")
        if r.get("note"):
            print(f"  note: {r['note']}")
        if r["must_include"]:
            print(f"  expect include: {r['must_include']}")
        if r["must_exclude"]:
            print(f"  expect exclude: {r['must_exclude']}")
        chroma = r.get("chroma_hits") or []
        if chroma:
            print("  chroma (top-k from vector DB):")
            for i, row in enumerate(chroma, start=1):
                print(f"    {i}. {_format_retrieved_line(row)}")
        else:
            print("  chroma (top-k from vector DB): (none)")
        retrieved = r["retrieved"]
        if retrieved:
            print("  retrieved (after literal filter):")
            for i, row in enumerate(retrieved, start=1):
                print(f"    {i}. {_format_retrieved_line(row)}")
        else:
            print("  retrieved (after literal filter): (none)")
        print(f"  check: {r['check']}")
        print("-" * 72)
    print(f"\nSUMMARY: {passed}/{len(results)} passed in {_format_elapsed(total_s)}")


def write_markdown_report(results: list[dict[str, Any]], path: Path) -> None:
    passed = sum(1 for r in results if r["pass"])
    total_s = sum(r.get("elapsed_s", 0) for r in results)
    lines = [
        "# Culture vocab retrieval test report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Result: **{passed}/{len(results)} passed**",
        f"- Total time: **{_format_elapsed(total_s)}**",
        "",
    ]
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        lines.append(f"## [{status}] {r['case_id']} ({r['locale']}) — {r.get('elapsed', '?')}")
        lines.append("")
        lines.append(f"**Text:** {r['text']}")
        if r.get("note"):
            lines.append(f"**Note:** {r['note']}")
        if r["must_include"]:
            lines.append(f"**Must include:** {', '.join(r['must_include'])}")
        if r["must_exclude"]:
            lines.append(f"**Must exclude:** {', '.join(r['must_exclude'])}")
        lines.append("")
        lines.append("**Chroma (top-k from vector DB):**")
        lines.append("")
        lines.append("| # | term | meaning | cosine_sim |")
        lines.append("|---|------|---------|------------|")
        if r.get("chroma_hits"):
            for i, row in enumerate(r["chroma_hits"], start=1):
                sim = row.get("cosine_similarity")
                lines.append(
                    f"| {i} | {row['term']} | {row['meaning']} | "
                    f"{sim if sim is not None else ''} |"
                )
        else:
            lines.append("| - | *(none)* | | |")
        lines.append("")
        lines.append("**Retrieved (after literal filter):**")
        lines.append("")
        lines.append("| # | term | meaning | cosine_sim |")
        lines.append("|---|------|---------|------------|")
        if r["retrieved"]:
            for i, row in enumerate(r["retrieved"], start=1):
                sim = row.get("cosine_similarity")
                lines.append(
                    f"| {i} | {row['term']} | {row['meaning']} | "
                    f"{sim if sim is not None else ''} |"
                )
        else:
            lines.append("| - | *(none)* | | |")
        lines.append("")
        lines.append(f"**Check:** {r['check']}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json_report(results: list[dict[str, Any]], path: Path) -> None:
    total_s = sum(r.get("elapsed_s", 0) for r in results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
        "total_elapsed_s": round(total_s, 4),
        "total_elapsed": _format_elapsed(total_s),
        "cases": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _select_cases(case_ids: list[str] | None) -> list[VocabRetrievalCase]:
    if not case_ids:
        return VOCAB_RETRIEVAL_CASES
    by_id = {c.case_id: c for c in VOCAB_RETRIEVAL_CASES}
    missing = [cid for cid in case_ids if cid not in by_id]
    if missing:
        known = ", ".join(sorted(by_id))
        raise SystemExit(f"Unknown case id(s): {', '.join(missing)}. Known: {known}")
    return [by_id[cid] for cid in case_ids]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run synthetic culture-vocab retrieval cases against live Chroma index",
    )
    parser.add_argument(
        "--case",
        metavar="ID",
        action="append",
        help="Run one case only (repeatable), e.g. --case SG-01 --case AU-02",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write report files under data/test-results/",
    )
    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory for vocab-retrieval-report.md and .json (default: data/test-results)",
    )
    args = parser.parse_args()

    from backend.app.config import settings
    from backend.rag.store import get_vocab_collection

    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY required for embeddings (set in .env)")
        return 2
    if get_vocab_collection().count() == 0:
        print("ERROR: vocab index empty. Run first:")
        print("  C:/Python314/python.exe backend/rag/ingest.py --reset")
        return 2

    cases = _select_cases(args.case)
    results = run_vocab_retrieval_cases(cases)
    print_results(results)

    if not args.no_report:
        report_dir = Path(args.report_dir)
        md_path = report_dir / "vocab-retrieval-report.md"
        json_path = report_dir / "vocab-retrieval-report.json"
        write_markdown_report(results, md_path)
        write_json_report(results, json_path)
        print(f"\nReport saved:")
        print(f"  {md_path}")
        print(f"  {json_path}")

    passed = sum(1 for r in results if r["pass"])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
