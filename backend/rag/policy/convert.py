"""LLM reformat of raw facility policy into RAG-ready markdown (content-preserving).

This is a FORMATTING pass, not a summarizer: every sentence and number in the source
must survive. `check_conversion_coverage` guards against silent content loss.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.app.llm import chat_completion

# Converted content must retain at least this fraction of the source text length.
MIN_CONTENT_RATIO = 0.9

CONVERT_SYSTEM = """You reformat an aged-care facility screening SOP into clean markdown for RAG chunking. This is a FORMATTING pass only.

Absolute rules (content preservation):
- PRESERVE ALL CONTENT VERBATIM. Do not summarize, shorten, drop, merge away, or reword any sentence, number, timeframe, phone number, or service name. Every fact in the source must appear in the output.
- Do NOT invent or add new content. If a detail seems missing, leave it out — never guess.

Formatting you MAY do:
- Ensure one top-level '# title' and a 'Locale: en-AU' or 'Locale: en-SG' line near the top (add only if absent; keep an existing one).
- Normalize heading levels: '##' for main sections, '###' for subsections, using the source's own wording. If a block of text has no heading, add a short heading built from that block's own words.
- Add blank lines around paragraphs, lists, and tables so sections chunk cleanly. Split very long paragraphs at natural sentence boundaries (no wording changes).
- Keep tables as markdown tables.
- Before each '##' section add ONE directive line on its own line:
  <!-- pathway: <routine|domain_follow_up|passive_safety|active_safety|reference> | retrievable: <true|false> -->
  Choose the pathway by the section's purpose. Set retrievable: false only for reference/background prose (scope, documentation, governance); set retrievable: true for operational follow-up and escalation content.
- Output markdown only — no JSON, no code fences around the whole document."""


async def convert_policy_markdown(
    source_text: str,
    *,
    locale: str,
    site_name: str = "Facility",
) -> str:
    user = (
        f"Target locale: {locale}\n"
        f"Site name: {site_name}\n\n"
        "Reformat the following facility policy for RAG chunking. Preserve every "
        "sentence and number verbatim; only adjust structure and add directives.\n\n"
        f"{source_text.strip()}"
    )
    content = await chat_completion(system=CONVERT_SYSTEM, user=user, temperature=0.1)
    return _strip_code_fences(content.strip())


def _strip_code_fences(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


_DIRECTIVE_LINE_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_NUMBER_RE = re.compile(r"\d[\d ]*\d|\d")


def _content_length(text: str) -> int:
    """Whitespace-insensitive length of the meaningful text (directives removed)."""
    without_directives = _DIRECTIVE_LINE_RE.sub("", text)
    return len("".join(without_directives.split()))


def _numbers(text: str) -> set[str]:
    """Digit runs (phones, timeframes) normalized without internal spaces."""
    return {match.replace(" ", "") for match in _NUMBER_RE.findall(text)}


@dataclass
class CoverageResult:
    ok: bool
    content_ratio: float
    missing_numbers: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def check_conversion_coverage(source_text: str, converted_text: str) -> CoverageResult:
    """Deterministic guard that the reformat did not silently drop content."""
    src_len = _content_length(source_text) or 1
    ratio = _content_length(converted_text) / src_len

    missing = sorted(_numbers(source_text) - _numbers(converted_text))

    errors: list[str] = []
    if ratio < MIN_CONTENT_RATIO:
        errors.append(
            f"content shrank to {ratio:.0%} of source (min {MIN_CONTENT_RATIO:.0%}) "
            "— reformat may have dropped content"
        )
    if missing:
        errors.append(
            "source numbers missing from output (timeframes/phone numbers?): "
            + ", ".join(missing)
        )
    return CoverageResult(
        ok=not errors, content_ratio=ratio, missing_numbers=missing, errors=errors
    )


def format_coverage_report(result: CoverageResult) -> str:
    lines = [
        "Conversion coverage: " + ("PASS" if result.ok else "FAIL"),
        f"Content retained: {result.content_ratio:.0%}",
    ]
    for msg in result.errors:
        lines.append(f"ERROR: {msg}")
    return "\n".join(lines)
