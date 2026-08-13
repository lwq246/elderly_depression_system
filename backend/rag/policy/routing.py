"""Parse RAG summary tags and map to policy chunk pathways for filtered retrieval."""

from __future__ import annotations

# Pathway labels stored on every chunk's metadata at ingest. Only the safety pathways are
# meaningful: they are pinned by heading and drive the crisis guarantee-include in
# retrieve.py. Everything else is labelled 'general' and retrieved purely by cosine (the
# non-safety label only matters when the pathway filter is on, and then only as
# "safety vs everything else").
PATHWAY_PASSIVE = "passive_safety"
PATHWAY_ACTIVE = "active_safety"
PATHWAY_GENERAL = "general"

# Version/lifecycle status stamped on every chunk. Ingest replaces a doc's chunks on
# re-ingest, so everything currently in the index is the active version; retrieval filters
# on this so a superseded version can never surface if one is ever retained.
STATUS_ACTIVE = "active"

SAFETY_PATHWAYS = frozenset({PATHWAY_PASSIVE, PATHWAY_ACTIVE})
NON_SAFETY_PATHWAYS = frozenset({PATHWAY_GENERAL})
ALL_PATHWAYS = SAFETY_PATHWAYS | NON_SAFETY_PATHWAYS

# Explicit heading -> pathway overrides. Safety sections are pinned here so a reworded body
# can never demote a crisis protocol; every other section defaults to 'general'.
SECTION_PATHWAY: dict[str, str] = {
    "Passive safety escalation": PATHWAY_PASSIVE,
    "Active safety escalation": PATHWAY_ACTIVE,
    "Medication and means safety": PATHWAY_ACTIVE,
    "Environmental safety (access to means)": PATHWAY_ACTIVE,
    "Crisis contacts (staff reference)": PATHWAY_ACTIVE,
}


def section_pathway(section: str) -> str:
    """Resolve a heading: safety sections are pinned, everything else is 'general'."""
    return SECTION_PATHWAY.get(section, PATHWAY_GENERAL)


def parse_policy_summary(summary: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for line in summary.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        tags[key.strip().lower()] = value.strip()
    return tags


def _is_true(value: str) -> bool:
    return value.lower() in {"true", "yes"}


def pathways_for_summary(tags: dict[str, str]) -> list[str] | None:
    """Return the safety pathway(s) the summary implies, or None.

    Derived purely from the two safety booleans (active takes precedence over passive).
    Only the safety pathways matter: retrieval searches all chunks broadly and merely
    *guarantee-includes* the crisis sections when a safety cue is present. All non-safety
    sections are labelled 'general' and retrieved purely by relevance, so there is nothing
    to route for them.
    """
    if not tags:
        return None

    if _is_true(tags.get("active_suicidal_ideation", "")):
        return [PATHWAY_ACTIVE]

    if _is_true(tags.get("passive_suicidal_thoughts", "")):
        return [PATHWAY_PASSIVE]

    return None
