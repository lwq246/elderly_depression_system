"""Run 10 ingestion pipeline tests and write input/output report to Markdown."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import SKILLS_DIR, settings
from backend.rag.ingest import ingest_all
from backend.rag.inspect_index import fetch_chunks
from backend.rag.policy.chunking import chunk_markdown, load_skill_sources
from backend.rag.policy.embed_text import build_embed_text
from backend.rag.policy.validate import validate_policy_markdown
from backend.rag.store import POLICY_COLLECTION_NAME, get_policy_collection

REPORT_PATH = ROOT / "data" / "ingestion_test_results.md"

_DIRECTIVE_FIXTURE = """# Test policy

<!-- pathway: reference | retrievable: false -->
## Scope and use

Reference-only governance text that is intentionally longer than the minimum chunk size so validation passes without indexing this section into the operational RAG index for analyst retrieval.

<!-- pathway: routine | retrievable: true -->
## Routine follow-up actions

| Analyst `recommendation` | Facility action |
|--------------------------|-----------------|
| `none` | No mandatory follow-up for residents with adequate screening and no meaningful concerns identified during the session. |
"""


@dataclass
class IngestionTestResult:
    case_id: str
    title: str
    passed: bool
    input_summary: str
    output_summary: str
    details: str = ""


@dataclass
class IngestionTestRun:
    results: list[IngestionTestResult] = field(default_factory=list)
    generated_at: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total(self) -> int:
        return len(self.results)


def _policy_path(locale: str) -> Path:
    return SKILLS_DIR / "facility-policy" / f"{locale}.md"


def _run_ing01() -> IngestionTestResult:
    path = _policy_path("en-SG")
    text = path.read_text(encoding="utf-8")
    chunks = chunk_markdown(text, source=path.name, doc_type="facility_policy", locale="en-SG")
    sections = [c["metadata"]["section"] for c in chunks]
    return IngestionTestResult(
        case_id="ING-01",
        title="Chunk en-SG.md for ingest",
        passed=len(chunks) >= 5,
        input_summary=f"Source: `{path.relative_to(ROOT)}` ({len(text)} chars)",
        output_summary=f"{len(chunks)} retrievable chunks: {', '.join(sections)}",
    )


def _run_ing02() -> IngestionTestResult:
    path = _policy_path("en-AU")
    text = path.read_text(encoding="utf-8")
    chunks = chunk_markdown(text, source=path.name, doc_type="facility_policy", locale="en-AU")
    pathways = sorted({c["metadata"]["pathway"] for c in chunks})
    return IngestionTestResult(
        case_id="ING-02",
        title="Chunk en-AU.md for ingest",
        passed=len(chunks) >= 10,
        input_summary=f"Source: `{path.relative_to(ROOT)}` ({len(text)} chars)",
        output_summary=f"{len(chunks)} retrievable chunks; pathways: {', '.join(pathways)}",
    )


def _run_ing03() -> IngestionTestResult:
    path = _policy_path("en-SG")
    text = path.read_text(encoding="utf-8")
    result = validate_policy_markdown(text, locale="en-SG", path=path)
    return IngestionTestResult(
        case_id="ING-03",
        title="Validate en-SG.md pre-ingest",
        passed=result.ok,
        input_summary=f"Validator on `{path.name}`",
        output_summary="PASS" if result.ok else "FAIL: " + "; ".join(result.errors),
        details="\n".join(result.warnings) if result.warnings else "",
    )


def _run_ing04() -> IngestionTestResult:
    path = _policy_path("en-AU")
    text = path.read_text(encoding="utf-8")
    result = validate_policy_markdown(text, locale="en-AU", path=path)
    return IngestionTestResult(
        case_id="ING-04",
        title="Validate en-AU.md pre-ingest",
        passed=result.ok,
        input_summary=f"Validator on `{path.name}`",
        output_summary="PASS" if result.ok else "FAIL: " + "; ".join(result.errors),
        details="\n".join(result.warnings) if result.warnings else "",
    )


def _run_ing05() -> IngestionTestResult:
    chunks = chunk_markdown(
        _DIRECTIVE_FIXTURE,
        source="directive-fixture.md",
        doc_type="facility_policy",
        locale="en-AU",
    )
    sections = [c["metadata"]["section"] for c in chunks]
    skipped_scope = "Scope and use" not in sections
    has_routine = "Routine follow-up actions" in sections
    return IngestionTestResult(
        case_id="ING-05",
        title="Directive retrievable:false skips Scope",
        passed=skipped_scope and has_routine and len(chunks) == 1,
        input_summary="Fixture with `retrievable: false` on Scope, `true` on Routine",
        output_summary=f"Chunks indexed: {sections}",
    )


def _run_ing06() -> IngestionTestResult:
    body = "| col | val |\n|-----|-----|\n| `none` | No follow-up |\n\nNarrative prose for embedding."
    embed = build_embed_text("Routine follow-up actions", body, pathway="routine")
    no_table = "|" not in embed
    has_pathway = "escalation_pathway: routine" in embed
    return IngestionTestResult(
        case_id="ING-06",
        title="embed_text strips tables, keeps prose",
        passed=no_table and has_pathway and "Narrative prose" in embed,
        input_summary="Markdown body with table + prose line",
        output_summary=embed[:280] + ("..." if len(embed) > 280 else ""),
    )


def _run_ing07() -> IngestionTestResult:
    buf = io.StringIO()
    with redirect_stdout(buf):
        count = ingest_all(reset=True)
    log = buf.getvalue().strip()
    return IngestionTestResult(
        case_id="ING-07",
        title="Full ingest --reset into Chroma",
        passed=count > 0,
        input_summary=(
            f"Locales: `{settings.rag_index_locales}` · "
            f"embedder: `{settings.rag_local_embedding_model}`"
        ),
        output_summary=f"{count} vectors in `{POLICY_COLLECTION_NAME}`",
        details=log,
    )


def _run_ing08() -> IngestionTestResult:
    collection = get_policy_collection()
    chroma_count = collection.count()
    sources = load_skill_sources(SKILLS_DIR)
    expected = 0
    for path, meta in sources:
        if meta.get("locale") not in settings.rag_index_locale_list:
            continue
        text = path.read_text(encoding="utf-8")
        expected += len(
            chunk_markdown(
                text,
                source=str(path.relative_to(SKILLS_DIR)),
                doc_type="facility_policy",
                locale=meta["locale"],
            )
        )
    return IngestionTestResult(
        case_id="ING-08",
        title="Chroma count matches chunked policy files",
        passed=chroma_count == expected,
        input_summary=f"Expected {expected} chunks from indexed locale files",
        output_summary=f"Chroma count: {chroma_count}",
    )


def _run_ing09() -> IngestionTestResult:
    rows = fetch_chunks(doc_type="facility_policy")
    required = {"routine", "passive_safety", "active_safety"}
    pathways = {meta.get("pathway") for _, _, meta, _ in rows}
    missing = required - pathways
    return IngestionTestResult(
        case_id="ING-09",
        title="Ingested index includes required pathways",
        passed=not missing,
        input_summary=f"Required pathways: {', '.join(sorted(required))}",
        output_summary=f"Present in index: {', '.join(sorted(p for p in pathways if p))}",
        details=f"Missing: {', '.join(sorted(missing))}" if missing else "",
    )


def _run_ing10() -> IngestionTestResult:
    locale = settings.rag_index_locale_list[0] if settings.rag_index_locale_list else "en-AU"
    path = _policy_path(locale)
    text = path.read_text(encoding="utf-8")
    pre = chunk_markdown(text, source=path.name, doc_type="facility_policy", locale=locale)
    pre_map = {c["metadata"]["section"]: c["text"][:200] for c in pre}
    rows = fetch_chunks(doc_type="facility_policy", locale=locale)
    post_map = {meta.get("section"): doc[:200] for _, _, meta, doc in rows}
    matched = all(pre_map.get(sec) == post_map.get(sec) for sec in pre_map)
    return IngestionTestResult(
        case_id="ING-10",
        title=f"Round-trip {locale} chunk text matches Chroma document",
        passed=matched and len(pre_map) == len(post_map),
        input_summary=f"{len(pre_map)} pre-ingest sections from {path.name}",
        output_summary=f"{len(post_map)} documents in Chroma for {locale}",
        details="\n".join(f"- {sec}" for sec in sorted(pre_map)),
    )


def run_all() -> IngestionTestRun:
    run = IngestionTestRun(generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))
    for fn in (
        _run_ing01,
        _run_ing02,
        _run_ing03,
        _run_ing04,
        _run_ing05,
        _run_ing06,
        _run_ing07,
        _run_ing08,
        _run_ing09,
        _run_ing10,
    ):
        run.results.append(fn())
    return run


def render_markdown(run: IngestionTestRun) -> str:
    lines = [
        "# Ingestion test run",
        "",
        f"**{run.passed}/{run.total} passed** · {run.generated_at}",
        "",
        "| | |",
        "|---|---|",
        f"| Embedder | `{settings.rag_local_embedding_model}` |",
        f"| Index locales | `{settings.rag_index_locales}` |",
        f"| Chroma path | `{settings.rag_chroma_path}` |",
        "",
    ]
    for result in run.results:
        status = "PASS" if result.passed else "FAIL"
        lines.extend(
            [
                f"## {result.case_id} — {status} — {result.title}",
                "",
                "**Input**",
                f"> {result.input_summary}",
                "",
                "**Output**",
                f"> {result.output_summary}",
                "",
            ]
        )
        if result.details:
            lines.extend(["**Details**", "", "```", result.details.strip(), "```", ""])
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    run = run_all()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_markdown(run), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)} ({run.passed}/{run.total} passed)")
    if run.passed != run.total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
