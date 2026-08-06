"""Facility policy markdown chunking for Chroma ingest."""

from pathlib import Path

import re

MIN_CHUNK_CHARS = 150
MERGE_INTRO_INTO = "Scope and use"


def _topic_id_from_heading(heading: str) -> str | None:
    match = re.match(r"^([a-z_]+)\s*—", heading.strip())
    return match.group(1) if match else None


def _base_metadata(
    *,
    locale: str,
    section: str,
) -> dict[str, str]:
    meta: dict[str, str] = {
        "locale": locale,
        "section": section,
    }
    topic_id = _topic_id_from_heading(section)
    if topic_id:
        meta["topic_id"] = topic_id
    return meta


def _make_chunk(
    *,
    source: str,
    doc_type: str,
    locale: str,
    section: str,
    text: str,
) -> dict | None:
    body = text.strip()
    if len(body) < MIN_CHUNK_CHARS:
        return None
    return {
        "id": f"{source}:{section}",
        "text": body,
        "metadata": _base_metadata(
            locale=locale,
            section=section,
        ),
    }


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    heading = "Introduction"
    body_lines: list[str] = []

    def flush() -> None:
        if not body_lines:
            return
        sections[heading] = "\n".join(body_lines).strip()

    for line in text.splitlines():
        if line.startswith("### "):
            flush()
            heading = line[4:].strip()
            body_lines = [line]
        elif line.startswith("## "):
            flush()
            heading = line[3:].strip()
            body_lines = [line]
        else:
            body_lines.append(line)

    flush()
    return sections


def chunk_markdown(
    text: str,
    *,
    source: str,
    doc_type: str,
    locale: str = "all",
) -> list[dict]:
    """Split markdown on ## headings — one chunk per section."""
    sections = _split_sections(text)
    intro = sections.pop("Introduction", "")

    if MERGE_INTRO_INTO in sections and intro:
        sections[MERGE_INTRO_INTO] = f"{intro}\n\n{sections[MERGE_INTRO_INTO]}".strip()

    chunks: list[dict] = []
    for heading, content in sections.items():
        chunk = _make_chunk(
            source=source,
            doc_type=doc_type,
            locale=locale,
            section=heading,
            text=content,
        )
        if chunk:
            chunks.append(chunk)
    return chunks


def load_skill_sources(skills_dir: Path) -> list[tuple[Path, dict[str, str]]]:
    policy_dir = skills_dir / "facility-policy"
    sources: list[tuple[Path, dict[str, str]]] = []
    for path in sorted(policy_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        sources.append((path, {"doc_type": "facility_policy", "locale": path.stem}))
    return sources
