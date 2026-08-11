"""Parse section-level RAG directives in facility policy markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.rag.policy.routing import (
    PATHWAY_ACTIVE,
    PATHWAY_DOMAIN,
    PATHWAY_PASSIVE,
    PATHWAY_REFERENCE,
    PATHWAY_ROUTINE,
    section_pathway,
)

VALID_PATHWAYS = {
    PATHWAY_ROUTINE,
    PATHWAY_DOMAIN,
    PATHWAY_PASSIVE,
    PATHWAY_ACTIVE,
    PATHWAY_REFERENCE,
}

_DIRECTIVE_RE = re.compile(r"<!--\s*(.+?)\s*-->", re.DOTALL)
_KV_RE = re.compile(r"(\w+)\s*:\s*([^|]+)")


def is_section_directive_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("<!--") and stripped.endswith("-->") and _DIRECTIVE_RE.fullmatch(stripped))


@dataclass(frozen=True)
class SectionMeta:
    pathway: str | None = None
    retrievable: bool | None = None


def _parse_directive_body(body: str) -> SectionMeta:
    pathway: str | None = None
    retrievable: bool | None = None

    if re.search(r"\breference\b.*\bnot retrieved\b", body, re.I):
        retrievable = False
        pathway = PATHWAY_REFERENCE

    for key, raw in _KV_RE.findall(body):
        value = raw.strip().lower()
        if key.lower() == "pathway":
            if value in VALID_PATHWAYS:
                pathway = value
        elif key.lower() == "retrievable":
            retrievable = value in {"true", "yes", "1"}

    return SectionMeta(pathway=pathway, retrievable=retrievable)


def parse_section_directive(text: str) -> SectionMeta | None:
    """Return metadata from the first HTML comment directive in text."""
    match = _DIRECTIVE_RE.search(text)
    if not match:
        return None
    meta = _parse_directive_body(match.group(1))
    if meta.pathway is None and meta.retrievable is None:
        return None
    return meta


def resolve_section_meta(
    section: str,
    content: str,
    *,
    default_retrievable: bool = True,
) -> tuple[str, bool]:
    """Resolve pathway and retrievable flag for a section body."""
    directive = parse_section_directive(content)
    pathway = section_pathway(section)
    retrievable = default_retrievable

    if directive:
        if directive.pathway is not None:
            pathway = directive.pathway
        if directive.retrievable is not None:
            retrievable = directive.retrievable

    if pathway == PATHWAY_REFERENCE and directive is None:
        # Unmarked reference headings stay out of RAG when explicitly named.
        pass

    return pathway, retrievable


def strip_section_directives(text: str) -> str:
    """Remove HTML comment directives from section content shown to the analyst."""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            if _DIRECTIVE_RE.fullmatch(stripped):
                continue
        lines.append(line)
    return "\n".join(lines).strip()
