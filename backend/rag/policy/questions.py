"""LLM-generated policy lookup questions for embedding retrieval."""

from __future__ import annotations

import re

from typing import Any

from backend.app.config import settings
from backend.app.llm import chat_completion
from backend.app.llm_capture import record_llm_input
from backend.app.validator import format_transcript_for_analyst

QUESTIONS_SYSTEM = """You generate facility policy lookup questions for vector search over aged-care screening SOP documents.

The screening session has ended. Your questions retrieve operational policy — they are NOT questions to ask the resident.

Rules:
- Use facts from Resident lines only (companion lines only if the resident answered that topic).
- Use SOP vocabulary: recommendation, routine follow-up, passive safety escalation, active safety, visit_soon, check_in, duty nurse, documentation, domain follow-up, medication means, etc.
- Clear denial of self-harm → include a question about routine pathway / clear denial handling, not active escalation.
- Passive thoughts with plan denial → passive safety escalation and RN review timeframe.
- Means, pills, overdose, or current intent → active safety escalation and medication/means policy.
- If safety was not discussed, do not ask about crisis escalation unless other risk signals exist.

Output exactly 3-4 numbered lines:
1. <policy lookup question>
2. <policy lookup question>
...

No preamble, markdown, or JSON."""


def parse_policy_questions(text: str, *, max_questions: int | None = None) -> list[str]:
    """Parse numbered or bulleted policy lookup questions from LLM output."""
    limit = max_questions or settings.rag_question_count
    questions: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^(?:\d+[.)]|[-*])\s+(.+)$", stripped)
        body = match.group(1).strip() if match else stripped
        if body and body not in questions:
            questions.append(body)
        if len(questions) >= limit:
            break
    return questions


async def generate_policy_questions(
    transcript: list[dict[str, Any]],
    *,
    locale: str,
) -> list[str]:
    user = (
        f"Locale: {locale}\n\n"
        "Generate policy lookup questions to retrieve the correct facility SOP sections "
        "for this screening transcript.\n\n"
        + format_transcript_for_analyst(transcript)
    )
    record_llm_input(
        "rag_questions",
        system=QUESTIONS_SYSTEM,
        user=user,
        temperature=0.2,
    )
    content = await chat_completion(
        system=QUESTIONS_SYSTEM,
        user=user,
        temperature=0.2,
    )
    questions = parse_policy_questions(content)
    return questions[: settings.rag_question_count]
