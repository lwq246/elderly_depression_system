"""LLM summary of transcript for facility policy RAG (analyst exit only)."""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.app.llm import chat_completion
from backend.app.llm_capture import record_llm_input
from backend.app.validator import format_transcript_for_analyst

SUMMARY_SYSTEM = """You extract facility-policy retrieval tags from aged-care wellbeing screening transcripts.

Rules:
- Use facts from Resident lines only. Ignore Companion questions unless the resident answered that topic.
- Do not infer or invent concerns. Do not include resident verbatim quotes.
- Use SOP vocabulary that matches facility policy sections (recommendation, escalation, analyst flags).
- Clear denial of self-harm (e.g. "No, I do not wish to hurt myself") → passive_suicidal_thoughts: false, active_suicidal_ideation: false, not a concern.
- Passive thoughts without plan/intent → passive_suicidal_thoughts: true, escalation_pathway: passive_safety.
- Means, pills, overdose, or current intent → active_suicidal_ideation: true, escalation_pathway: active_safety.
- If safety was never addressed, set safety_discussed: false and passive/active to not_discussed.

Output exactly these lines (plain text, no markdown, no JSON):
recommendation_target: none | check_in | visit_soon | urgent
passive_suicidal_thoughts: true | false | not_discussed
active_suicidal_ideation: true | false | not_discussed
suicide_risk_flag: true | false
escalation_pathway: routine | domain_follow_up | passive_safety | active_safety
safety_discussed: true | false
domains_with_concern: none | mood, sleep, appetite, social, energy, worries (comma-separated)
domains_discussed: none | mood, sleep, appetite, social, energy, safety, worries (comma-separated)
screen_positive_pattern: true | false
safety_note: one short SOP-style phrase (no quotes from resident)"""


async def summarize_transcript_for_rag(
    transcript: list[dict[str, Any]],
    *,
    locale: str,
) -> str:
    user = (
        f"Locale: {locale}\n\n"
        "Extract policy retrieval tags for facility SOP embedding search. "
        "Use SOP terms only — no resident quotes.\n\n"
        + format_transcript_for_analyst(transcript)
    )
    record_llm_input(
        "rag_summary",
        system=SUMMARY_SYSTEM,
        user=user,
        temperature=0.1,
    )
    content = await chat_completion(
        system=SUMMARY_SYSTEM,
        user=user,
        temperature=0.1,
    )
    text = content.strip()
    limit = settings.rag_summary_max_chars
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text
