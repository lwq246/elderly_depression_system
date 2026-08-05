from typing import Any

from .config import settings
from .llm import chat_completion, parse_json_response
from .skills import load_analyst_system_prompt
from .validator import format_transcript_for_analyst, validate_analyst_report


async def _analyst_system_prompt(transcript: list[dict[str, Any]], locale: str) -> str:
    system = load_analyst_system_prompt(locale)
    if not settings.rag_enabled:
        return system

    try:
        from backend.rag.retrieve import format_rag_context, retrieve_for_analyst

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

    return system


async def run_analyst(
    transcript: list[dict[str, Any]],
    *,
    locale: str = "en-SG",
) -> tuple[dict[str, Any], list[str]]:
    system = await _analyst_system_prompt(transcript, locale)
    user = (
        "Analyze this screening transcript and respond with JSON only.\n\n"
        + format_transcript_for_analyst(transcript)
    )

    last_errors: list[str] = []
    for attempt in range(3):
        content = await chat_completion(system=system, user=user, temperature=0.2, json_mode=True)
        report = await parse_json_response(content)
        errors = validate_analyst_report(report, transcript)
        if not errors:
            return report, []
        last_errors = errors
        user += (
            "\n\nValidation failed:\n- "
            + "\n- ".join(errors)
            + "\n\nFix the JSON. Evidence must be verbatim resident quotes."
        )

    report = await parse_json_response(
        await chat_completion(system=system, user=user, temperature=0.1, json_mode=True)
    )
    return report, validate_analyst_report(report, transcript)
