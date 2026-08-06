"""LLM summary of transcript for facility policy RAG (analyst exit only)."""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.app.llm import chat_completion
from backend.app.validator import format_transcript_for_analyst

SUMMARY_SYSTEM = """You summarize aged-care wellbeing screening transcripts for facility policy retrieval only.

Rules:
- Use facts from Resident lines only. Ignore Companion questions unless the resident answered that topic.
- For each domain below, state what the resident said OR write "not discussed". Do not infer or invent concerns.
- Do not treat a clear denial (e.g. "No safety thoughts") as a concern.

Output 4-7 plain-text lines:
- Mood/spirits: <resident quote or not discussed>
- Sleep: <resident quote or not discussed>
- Appetite/meals: <resident quote or not discussed>
- Social/activities/energy: <resident quote or not discussed>
- Passive safety: <quote or none / not discussed>; note plan/intent denial if stated
- Active safety: <quote or none / not discussed> (intent, plan, means, pills, overdose)
- Likely follow-up level: none, check_in, visit_soon, or urgent (based only on resident evidence above)

No diagnosis. No markdown bullets. No JSON."""


async def summarize_transcript_for_rag(
    transcript: list[dict[str, Any]],
    *,
    locale: str,
) -> str:
    user = (
        f"Locale: {locale}\n\n"
        "Summarize for facility SOP retrieval. Only include domains the resident explicitly "
        "addressed; write not discussed for all others.\n\n"
        + format_transcript_for_analyst(transcript)
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
