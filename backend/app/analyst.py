from typing import Any

from .config import settings
from .llm import chat_completion, parse_json_response
from .llm_capture import record_llm_input
from .skills import load_analyst_system_prompt
from .validator import (
    format_transcript_for_analyst,
    resolve_evidence_refs,
    validate_analyst_report,
)


async def _analyst_system_prompt(transcript: list[dict[str, Any]], locale: str) -> str:
    system = load_analyst_system_prompt(locale)
    if not settings.rag_enabled:
        return system

    try:
        from backend.rag.policy.retrieve import format_rag_context, retrieve_for_analyst

        result = await retrieve_for_analyst(transcript, locale=locale)
        if result.chunks:
            system += (
                "\n\n---\n\n## Retrieved facility policy (operational SOP)\n"
                "Use to align analyst recommendations with facility follow-up and escalation steps. "
                "Domain criteria are already in the system prompt above. "
                "Do NOT treat as resident quotes. Evidence must come from the transcript only.\n\n"
                + format_rag_context(result.chunks)
            )
    except Exception:
        pass

    if settings.rag_analyst_vocab_retrieval:
        system += _analyst_vocab_block(transcript, locale)

    return system


def _analyst_vocab_block(transcript: list[dict[str, Any]], locale: str) -> str:
    """Literal vocab over the full transcript — only terms the resident actually used."""
    try:
        from backend.rag.vocab.retrieve import retrieve_vocab_for_analyst

        from .validator import resident_text_from_transcript

        terms = retrieve_vocab_for_analyst(locale, resident_text_from_transcript(transcript))
        if not terms:
            return ""
        lines = [
            f"- {t.canonical} — {t.meaning}" if t.meaning else f"- {t.canonical}" for t in terms
        ]
        return (
            "\n\n---\n\n## Local vocabulary reference (terms used this session)\n\n"
            "Culture-specific terms the resident actually used, for interpretation only. "
            "Evidence must cite resident line references (R1, R2, ...), never this glossary.\n\n"
            + "\n".join(lines)
        )
    except Exception:
        return ""


async def run_analyst(
    transcript: list[dict[str, Any]],
    *,
    locale: str = "en-SG",
) -> tuple[dict[str, Any], list[str]]:
    system = await _analyst_system_prompt(transcript, locale)
    user = (
        "Analyze this screening transcript and respond with JSON only.\n"
        "Resident lines are verbatim and labelled [R1], [R2], ... "
        "The 'Local vocabulary reference' in the system prompt explains culture-specific terms — "
        "use it for interpretation; evidence must still cite R1, R2, ... not the glossary text.\n"
        "For each topic with concern, set evidence to the resident line reference only "
        '(e.g. "R1", "R2") — not a direct quote.\n\n'
        + format_transcript_for_analyst(transcript)
    )

    last_errors: list[str] = []
    for attempt in range(3):
        record_llm_input(
            "analyst",
            system=system,
            user=user,
            temperature=0.2,
            json_mode=True,
            attempt=attempt + 1,
        )
        content = await chat_completion(system=system, user=user, temperature=0.2, json_mode=True)
        report = await parse_json_response(content)
        ref_errors = resolve_evidence_refs(report, transcript)
        errors = ref_errors + validate_analyst_report(report, transcript)
        if not errors:
            return report, []
        last_errors = errors
        user += (
            "\n\nValidation failed:\n- "
            + "\n- ".join(errors)
            + "\n\nFix the JSON. Evidence must be a resident line reference (R1, R2, ...)."
        )

    record_llm_input(
        "analyst",
        system=system,
        user=user,
        temperature=0.1,
        json_mode=True,
        attempt=4,
    )
    report = await parse_json_response(
        await chat_completion(system=system, user=user, temperature=0.1, json_mode=True)
    )
    ref_errors = resolve_evidence_refs(report, transcript)
    return report, ref_errors + validate_analyst_report(report, transcript)
