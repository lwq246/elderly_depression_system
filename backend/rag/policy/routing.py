"""Parse RAG summary tags and map to policy chunk pathways for filtered retrieval."""

from __future__ import annotations

from typing import Any

# Pathway labels stored on Chroma chunk metadata at ingest.
PATHWAY_ROUTINE = "routine"
PATHWAY_DOMAIN = "domain_follow_up"
PATHWAY_PASSIVE = "passive_safety"
PATHWAY_ACTIVE = "active_safety"
PATHWAY_REFERENCE = "reference"

SECTION_PATHWAY: dict[str, str] = {
    "Routine follow-up actions": PATHWAY_ROUTINE,
    "Domain-led follow-up (non-crisis)": PATHWAY_DOMAIN,
    "Passive safety escalation": PATHWAY_PASSIVE,
    "Active safety escalation": PATHWAY_ACTIVE,
    "Medication and means safety": PATHWAY_ACTIVE,
    "Crisis contacts (staff reference)": PATHWAY_ACTIVE,
}


def section_pathway(section: str) -> str:
    return SECTION_PATHWAY.get(section, PATHWAY_REFERENCE)


def parse_policy_summary(summary: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for line in summary.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        tags[key.strip().lower()] = value.strip()
    return tags


def _is_false(value: str) -> bool:
    return value.lower() in {"false", "no", "none", "not_discussed", "denied", "clear_denial"}


def _is_true(value: str) -> bool:
    return value.lower() in {"true", "yes"}


def pathways_for_summary(tags: dict[str, str]) -> list[str] | None:
    """Return pathway filter candidates, or None to search all chunks."""
    if not tags:
        return None

    pathway = tags.get("escalation_pathway", "").lower()
    passive = tags.get("passive_suicidal_thoughts", "").lower()
    active = tags.get("active_suicidal_ideation", "").lower()
    recommendation = tags.get("recommendation_target", "").lower()

    if pathway == PATHWAY_ACTIVE or _is_true(active):
        return [PATHWAY_ACTIVE]

    if pathway == PATHWAY_PASSIVE or _is_true(passive):
        return [PATHWAY_PASSIVE, PATHWAY_ROUTINE]

    if pathway == PATHWAY_DOMAIN or (
        recommendation in {"check_in", "visit_soon"}
        and _is_false(passive)
        and _is_false(active)
        and tags.get("domains_with_concern", "none").lower() not in {"", "none"}
    ):
        return [PATHWAY_DOMAIN, PATHWAY_ROUTINE]

    if pathway == PATHWAY_ROUTINE or recommendation in {"none", "check_in"}:
        if _is_false(passive) and _is_false(active):
            return [PATHWAY_ROUTINE, PATHWAY_DOMAIN]

    return None


def pathways_from_transcript_heuristic(transcript: list[dict[str, Any]]) -> list[str] | None:
    """Fallback when summary tags are missing — scan resident text for crisis cues."""
    resident_text = " ".join(
        (t.get("text") or "").lower() for t in transcript if t.get("role") == "resident"
    )
    if not resident_text.strip():
        return None

    has_denial = any(
        phrase in resident_text
        for phrase in (
            "do not wish to hurt",
            "don't wish to hurt",
            "no plan",
            "will not do that",
            "no safety thoughts",
            "nothing like that",
        )
    )

    if any(cue in resident_text for cue in ("pill", "overdose", "taking too many")):
        return [PATHWAY_ACTIVE, PATHWAY_PASSIVE]

    passive_cues = (
        "wish i did not wake",
        "wish i wasn't here",
        "better off dead",
        "wish not to wake",
    )
    if any(cue in resident_text for cue in passive_cues):
        return [PATHWAY_PASSIVE, PATHWAY_ROUTINE]

    if any(
        cue in resident_text for cue in ("kill myself", "end my life", "hurt myself")
    ):
        if has_denial:
            return [PATHWAY_ROUTINE, PATHWAY_DOMAIN]
        return [PATHWAY_ACTIVE, PATHWAY_PASSIVE]

    if "burden" in resident_text and not has_denial:
        return [PATHWAY_PASSIVE, PATHWAY_ROUTINE]

    return None
