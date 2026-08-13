"""Parse section-level RAG directives in facility policy markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.rag.policy.routing import (
    ALL_PATHWAYS,
    section_pathway,
)

# A section directive may name any coarse bucket; unknown tokens are ignored (the heading
# map / keyword inference then decides). Kept in sync with routing.ALL_PATHWAYS.
VALID_PATHWAYS = set(ALL_PATHWAYS)

_DIRECTIVE_RE = re.compile(r"<!--\s*(.+?)\s*-->", re.DOTALL)
_KV_RE = re.compile(r"(\w+)\s*:\s*([^|]+)")


def is_section_directive_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("<!--") and stripped.endswith("-->") and _DIRECTIVE_RE.fullmatch(stripped))


@dataclass(frozen=True)
class SectionMeta:
    pathway: str | None = None


def _parse_directive_body(body: str) -> SectionMeta:
    pathway: str | None = None
    for key, raw in _KV_RE.findall(body):
        value = raw.strip().lower()
        if key.lower() == "pathway" and value in VALID_PATHWAYS:
            pathway = value
    return SectionMeta(pathway=pathway)


def iter_directive_pathway_tokens(text: str) -> list[str]:
    """Return every raw ``pathway: X`` token declared in HTML directives (lowercased).

    Used by validation to warn when an author typos a bucket name — the token would
    otherwise be silently ignored and the section would fall back to heading inference.
    """
    tokens: list[str] = []
    for match in _DIRECTIVE_RE.finditer(text):
        for key, raw in _KV_RE.findall(match.group(1)):
            if key.lower() == "pathway":
                tokens.append(raw.strip().lower())
    return tokens


def parse_section_directive(text: str) -> SectionMeta | None:
    """Return metadata (pathway) from the first HTML comment directive in text."""
    match = _DIRECTIVE_RE.search(text)
    if not match:
        return None
    meta = _parse_directive_body(match.group(1))
    if meta.pathway is None:
        return None
    return meta


def resolve_section_pathway(section: str, content: str) -> str:
    """Resolve the pathway for a section: explicit directive wins, else heading map."""
    directive = parse_section_directive(content)
    if directive and directive.pathway is not None:
        return directive.pathway
    return section_pathway(section)


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
