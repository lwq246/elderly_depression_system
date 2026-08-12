"""Parse RAG summary tags and map to policy chunk pathways for filtered retrieval."""

from __future__ import annotations

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

    # Screen-positive pattern (5+ concern domains) → at least domain-led follow-up,
    # even if the recommendation tag is conservative. Safety branches above win first.
    if _is_true(tags.get("screen_positive_pattern", "")):
        return [PATHWAY_DOMAIN, PATHWAY_ROUTINE]

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
