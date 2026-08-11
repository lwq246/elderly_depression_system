"""Build compact embedding strings for facility policy chunks."""

from __future__ import annotations

import re

from backend.rag.policy.routing import section_pathway

_TABLE_ROW = re.compile(r"^\|")
_TABLE_SEP = re.compile(r"^\|[-:\s|]+\|$")
_MAX_EMBED_CHARS = 1500


def build_embed_text(section: str, body: str, *, pathway: str | None = None) -> str:
    """SOP-aligned compact text for vector search; full markdown stays in chunk text."""
    pathway = pathway or section_pathway(section)
    parts = [
        f"Facility policy section: {section}",
        f"escalation_pathway: {pathway}",
    ]

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if _TABLE_ROW.match(stripped) or _TABLE_SEP.match(stripped):
            continue
        parts.append(stripped)

    compact = " ".join(parts)
    if len(compact) > _MAX_EMBED_CHARS:
        return compact[: _MAX_EMBED_CHARS - 3] + "..."
    return compact
