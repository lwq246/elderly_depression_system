import re
from typing import Any

REQUIRED_TOPIC_IDS = [
    "mood_spirits",
    "interest_activities",
    "energy",
    "meals_appetite",
    "sleep_rest",
    "social_connection",
    "emotional_weight",
    "safety_check",
    "coping_strengths",
]

CONFIDENCE = {"low", "medium", "high"}
RECOMMENDATIONS = {"none", "check_in", "visit_soon", "urgent"}
INDICATOR_DOMAINS = {"emotional", "behavioural", "physical", "elderly_specific", "safety"}
SEVERITIES = {"none", "mild", "moderate", "notable", "severe"}

_EVIDENCE_REF_RE = re.compile(r"^\[?R(\d+)\]?$", re.IGNORECASE)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def resident_lines_from_transcript(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [t for t in transcript if t.get("role") == "resident"]


def is_evidence_ref(value: str) -> bool:
    return bool(_EVIDENCE_REF_RE.match((value or "").strip()))


def resolve_evidence_refs(report: dict[str, Any], transcript: list[dict[str, Any]]) -> list[str]:
    """Replace R1-style evidence refs with raw resident line text. Returns errors for invalid refs."""
    errors: list[str] = []
    topics = report.get("transcript_topics")
    if not isinstance(topics, list):
        return errors

    resident_lines = resident_lines_from_transcript(transcript)
    for topic in topics:
        if not isinstance(topic, dict):
            continue
        evidence = (topic.get("evidence") or "").strip()
        match = _EVIDENCE_REF_RE.match(evidence)
        if not match:
            continue
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(resident_lines):
            topic["evidence"] = resident_lines[idx]["text"]
        else:
            errors.append(f"Invalid evidence reference: {evidence}")
    return errors


def resident_text_from_transcript(transcript: list[dict[str, Any]]) -> str:
    parts = [t["text"] for t in transcript if t.get("role") == "resident"]
    return "\n".join(parts)


def evidence_in_transcript(evidence: str, transcript: list[dict[str, Any]]) -> bool:
    if not evidence:
        return True
    resident_only = resident_text_from_transcript(transcript)
    hay = normalize_text(resident_only)
    needle = normalize_text(evidence)
    return needle in hay


def validate_analyst_report(report: dict[str, Any], transcript: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ["Report must be a JSON object"]

    for field in (
        "estimate_confidence",
        "suicide_risk_flag",
        "passive_suicidal_thoughts",
        "active_suicidal_ideation",
        "transcript_topics",
        "indicators",
        "explanation",
        "recommendation",
    ):
        if field not in report:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    if report["estimate_confidence"] not in CONFIDENCE:
        errors.append("Invalid estimate_confidence")

    if report["recommendation"] not in RECOMMENDATIONS:
        errors.append("Invalid recommendation")

    for flag in ("suicide_risk_flag", "passive_suicidal_thoughts", "active_suicidal_ideation"):
        if not isinstance(report[flag], bool):
            errors.append(f"{flag} must be boolean")

    topics = report.get("transcript_topics")
    if not isinstance(topics, list):
        errors.append("transcript_topics must be a list")
        return errors

    topic_ids = [t.get("topic_id") for t in topics if isinstance(t, dict)]
    if sorted(topic_ids) != sorted(REQUIRED_TOPIC_IDS):
        errors.append("transcript_topics must include all 9 topic_id values exactly once")

    for topic in topics:
        if not isinstance(topic, dict):
            errors.append("Each transcript topic must be an object")
            continue
        discussed = topic.get("discussed")
        concern = topic.get("concern")
        evidence = topic.get("evidence", "")
        if discussed is False and concern is True:
            errors.append(f"{topic.get('topic_id')}: concern cannot be true when discussed is false")
        if concern and evidence and not evidence_in_transcript(evidence, transcript):
            errors.append(f"Evidence not found in resident transcript: {evidence!r}")
        if concern and discussed and not evidence:
            errors.append(f"{topic.get('topic_id')}: concern true requires evidence")

    indicators = report.get("indicators")
    if not isinstance(indicators, list):
        errors.append("indicators must be a list")
    else:
        for ind in indicators:
            if ind.get("domain") not in INDICATOR_DOMAINS:
                errors.append(f"Invalid indicator domain: {ind.get('domain')}")
            if ind.get("severity") not in SEVERITIES:
                errors.append(f"Invalid indicator severity: {ind.get('severity')}")

    has_safety_flag = (
        report.get("active_suicidal_ideation")
        or report.get("passive_suicidal_thoughts")
        or report.get("suicide_risk_flag")
    )
    if report.get("recommendation") == "urgent" and not has_safety_flag:
        errors.append("recommendation urgent requires a safety flag in the report")

    if report.get("active_suicidal_ideation") and report.get("recommendation") != "urgent":
        errors.append("active_suicidal_ideation true requires recommendation urgent")

    return errors


def format_transcript_for_analyst(transcript: list[dict[str, Any]]) -> str:
    from backend.rag.vocab.retrieve import format_vocab_matches_for_analyst

    lines = []
    resident_idx = 0
    for turn in transcript:
        if turn["role"] == "companion":
            lines.append(f"**Companion:** {turn['text']}")
            continue
        resident_idx += 1
        raw = turn["text"]
        block = f"**Resident [R{resident_idx}]:** {raw}"
        vocab_block = format_vocab_matches_for_analyst(turn.get("vocab_matches") or [])
        if vocab_block:
            block += f"\n\n{vocab_block}"
        lines.append(block)
    return "\n\n".join(lines)

