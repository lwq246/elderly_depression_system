"""LLM conversion of raw facility policy into normalized RAG-ready markdown."""

from __future__ import annotations

from pathlib import Path

from backend.app.llm import chat_completion

_TEMPLATE_PATH = Path(__file__).resolve().parent / "template.md"

CONVERT_SYSTEM = """You convert raw aged-care facility screening SOP documents into a normalized markdown template for RAG ingestion.

Rules:
- EXTRACT ONLY from the source document. Do not invent steps, timeframes, phone numbers, or clinical advice.
- If the source omits a detail, write [CONFIGURE: brief label] — never guess.
- If passive vs active escalation is unclear, keep both sections and add <!-- UNVERIFIED: reason --> on the ambiguous line.
- Preserve locale-specific emergency numbers and service names from the source (e.g. 000, 995, Lifeline).
- Use exactly these ## section titles when the source covers that topic:
  - Scope and use
  - Routine follow-up actions
  - Domain-led follow-up (non-crisis)
  - Passive safety escalation
  - Active safety escalation
  - Crisis contacts (staff reference)
  - Documentation and handoff
- Before each ## section, add ONE HTML comment directive on its own line:
  <!-- pathway: routine | retrievable: true -->
  Valid pathways: routine, domain_follow_up, passive_safety, active_safety, reference
  Set retrievable: false for Scope and use, Documentation and handoff, and other reference-only prose.
  Set retrievable: true for operational escalation and follow-up sections.
- Output markdown only — no JSON wrapper, no code fences around the full document.
- Include a top-level # title and a "Locale: en-AU" or "Locale: en-SG" line near the top.
- Keep tables where they help nurses (recommendation mapping, escalation steps, contacts).
- Map analyst JSON field names (`recommendation`, `passive_suicidal_thoughts`, etc.) when the source uses them."""


def load_template() -> str:
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


async def convert_policy_markdown(
    source_text: str,
    *,
    locale: str,
    site_name: str = "Facility",
) -> str:
    template = load_template()
    user = (
        f"Target locale: {locale}\n"
        f"Site name: {site_name}\n\n"
        "Use this normalized template structure and directive format:\n\n"
        f"{template}\n\n"
        "---\n\n"
        "Convert the following raw facility policy into the template format. "
        "Extract only — do not add content not supported by the source.\n\n"
        f"{source_text.strip()}"
    )
    content = await chat_completion(
        system=CONVERT_SYSTEM,
        user=user,
        temperature=0.1,
    )
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
