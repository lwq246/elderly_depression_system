"""Facility policy markdown chunking for Chroma ingest."""

from pathlib import Path

import re

from backend.rag.policy.embed_text import build_embed_text
from backend.rag.policy.routing import ALL_PATHWAYS, STATUS_ACTIVE
from backend.rag.policy.section_meta import (
    is_section_directive_line,
    resolve_section_pathway,
    strip_section_directives,
)

MERGE_INTRO_INTO = "Scope and use"


def _topic_id_from_heading(heading: str) -> str | None:
    match = re.match(r"^([a-z_]+)\s*—", heading.strip())
    return match.group(1) if match else None


def _base_metadata(
    *,
    locale: str,
    section: str,
    pathway: str,
    doc_id: str,
    facility_id: str,
    doc_version: str,
    doc_type: str,
    parent_id: str,
    child_index: int,
) -> dict[str, str | int]:
    meta: dict[str, str | int] = {
        "locale": locale,
        "section": section,
        "pathway": pathway,
        "doc_id": doc_id,
        "facility_id": facility_id,
        "doc_version": doc_version,
        "status": STATUS_ACTIVE,
        "doc_type": doc_type,
        "parent_id": parent_id,
        "child_index": child_index,
    }
    topic_id = _topic_id_from_heading(section)
    if topic_id:
        meta["topic_id"] = topic_id
    return meta


def _split_into_children(body: str, *, max_chars: int, overlap_chars: int) -> list[str]:
    """Split a section body into overlapping windows on paragraph/line boundaries."""
    if len(body) <= max_chars:
        return [body]

    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    windows: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            windows.append(current)
            tail = current[-overlap_chars:] if overlap_chars else ""
            current = f"{tail}\n\n{para}".strip() if tail else para
    if current:
        windows.append(current)

    # A single paragraph can still exceed max_chars; hard-split those windows.
    final: list[str] = []
    for window in windows:
        if len(window) <= max_chars:
            final.append(window)
            continue
        start = 0
        step = max(1, max_chars - overlap_chars)
        while start < len(window):
            final.append(window[start : start + max_chars])
            start += step
    return final or [body]


def _make_child_chunks(
    *,
    doc_id: str,
    facility_id: str,
    doc_version: str,
    doc_type: str,
    locale: str,
    section: str,
    text: str,
    pathway: str,
    max_chars: int,
    overlap_chars: int,
) -> list[dict]:
    body = strip_section_directives(text.strip())
    if not body:
        return []
    parent_id = f"{doc_id}:{section}"
    children = _split_into_children(body, max_chars=max_chars, overlap_chars=overlap_chars)
    chunks: list[dict] = []
    for index, child_body in enumerate(children):
        chunks.append(
            {
                # Deterministic id — stable across re-ingest for versioned replace.
                "id": f"{parent_id}:{index}",
                "parent_id": parent_id,
                # Full parent section text is returned to the analyst on any child hit.
                "text": body,
                "embed_text": build_embed_text(section, child_body, pathway=pathway),
                "metadata": _base_metadata(
                    locale=locale,
                    section=section,
                    pathway=pathway,
                    doc_id=doc_id,
                    facility_id=facility_id,
                    doc_version=doc_version,
                    doc_type=doc_type,
                    parent_id=parent_id,
                    child_index=index,
                ),
            }
        )
    return chunks


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    heading = "Introduction"
    body_lines: list[str] = []
    pending_directive: list[str] = []

    def flush() -> None:
        if not body_lines:
            return
        sections[heading] = "\n".join(body_lines).strip()

    for line in text.splitlines():
        if is_section_directive_line(line):
            pending_directive.append(line)
            continue
        if line.startswith("### "):
            flush()
            heading = line[4:].strip()
            body_lines = pending_directive + [line]
            pending_directive = []
        elif line.startswith("## "):
            flush()
            heading = line[3:].strip()
            body_lines = pending_directive + [line]
            pending_directive = []
        else:
            body_lines.append(line)

    flush()
    return sections


def iter_policy_sections(
    text: str,
    *,
    locale: str = "all",
) -> list[dict]:
    """Return all ## sections with resolved pathway (for validation)."""
    sections = _split_sections(text)
    intro = sections.pop("Introduction", "")

    if MERGE_INTRO_INTO in sections and intro:
        sections[MERGE_INTRO_INTO] = f"{intro}\n\n{sections[MERGE_INTRO_INTO]}".strip()

    rows: list[dict] = []
    for heading, content in sections.items():
        pathway = resolve_section_pathway(heading, content)
        body = strip_section_directives(content.strip())
        rows.append(
            {
                "section": heading,
                "locale": locale,
                "pathway": pathway,
                "char_count": len(body),
            }
        )
    return rows


def chunk_markdown(
    text: str,
    *,
    source: str,
    doc_type: str,
    locale: str = "all",
    doc_id: str | None = None,
    facility_id: str | None = None,
    doc_version: str = "unversioned",
    max_chars: int | None = None,
    overlap_chars: int | None = None,
) -> list[dict]:
    """Split markdown on ## headings, then into overlapping child windows per section.

    Each child is embedded separately (better recall on long sections) but carries the
    full parent section text, so any child hit returns the whole section to the analyst.
    """
    from backend.app.config import settings

    doc_id = doc_id or _doc_id_from_source(source)
    facility_id = facility_id or settings.rag_default_facility_id
    max_chars = max_chars if max_chars is not None else settings.rag_child_max_chars
    overlap_chars = overlap_chars if overlap_chars is not None else settings.rag_child_overlap_chars

    sections = _split_sections(text)
    intro = sections.pop("Introduction", "")

    if MERGE_INTRO_INTO in sections and intro:
        sections[MERGE_INTRO_INTO] = f"{intro}\n\n{sections[MERGE_INTRO_INTO]}".strip()

    chunks: list[dict] = []
    for heading, content in sections.items():
        pathway = resolve_section_pathway(heading, content)
        # Every chunk must carry exactly one valid coarse bucket. resolve_section_pathway
        # always returns one, so this only fires if the taxonomy is edited inconsistently.
        if pathway not in ALL_PATHWAYS:
            raise ValueError(
                f"section '{heading}' resolved to invalid pathway {pathway!r}; "
                f"expected one of {sorted(ALL_PATHWAYS)}"
            )
        chunks.extend(
            _make_child_chunks(
                doc_id=doc_id,
                facility_id=facility_id,
                doc_version=doc_version,
                doc_type=doc_type,
                locale=locale,
                section=heading,
                text=content,
                pathway=pathway,
                max_chars=max_chars,
                overlap_chars=overlap_chars,
            )
        )
    return chunks


def _doc_id_from_source(source: str) -> str:
    """Stable document id from a source path (e.g. 'facility-policy/en-AU.md' -> 'en-AU')."""
    stem = Path(source).stem
    return stem or source


def load_skill_sources(skills_dir: Path) -> list[tuple[Path, dict[str, str]]]:
    policy_dir = skills_dir / "facility-policy"
    sources: list[tuple[Path, dict[str, str]]] = []
    for path in sorted(policy_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        sources.append(
            (
                path,
                {
                    "doc_type": "facility_policy",
                    "locale": path.stem,
                    "doc_id": path.stem,
                },
            )
        )
    return sources
