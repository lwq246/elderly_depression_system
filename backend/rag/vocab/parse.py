"""Parse culture ``local-vocabulary.md`` glossary tables into canonical term records.

Only the sections that actually list terms residents *say* are parsed — those are the
ones the companion needs to recognise. Policy/mode/address tables are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Section headings (matched by prefix) whose tables hold resident-facing terms.
GLOSSARY_HEADING_PREFIXES: tuple[str, ...] = (
    "Words residents often use",
    "Singlish particles",
    "Australian daily-life words",
)

_BOLD = re.compile(r"\*\*|`")
_PARENS = re.compile(r"\([^)]*\)")
_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass
class VocabRecord:
    locale: str
    canonical: str
    aliases: list[str] = field(default_factory=list)
    meaning: str = ""
    reflect: str = ""
    section: str = ""

    @property
    def id(self) -> str:
        return f"{self.locale}::{_slug(self.section)}::{_slug(self.canonical)}"

    @property
    def document(self) -> str:
        return f"{self.canonical} — {self.meaning}" if self.meaning else self.canonical

    @property
    def embed_text(self) -> str:
        # Embed canonical + all aliases + meaning + reflection so paraphrases land nearby.
        parts = [self.canonical, *self.aliases, self.meaning, self.reflect]
        return " ".join(p for p in parts if p).strip()

    def metadata(self) -> dict[str, str]:
        return {
            "locale": self.locale,
            "canonical": self.canonical,
            "aliases": "|".join(self.aliases),
            "meaning": self.meaning,
            "reflect": self.reflect,
            "section": self.section,
        }


def _slug(text: str) -> str:
    return _SLUG.sub("-", text.strip().lower()).strip("-") or "term"


def _clean(cell: str) -> str:
    return _BOLD.sub("", cell).strip()


def _is_separator_row(cells: list[str]) -> bool:
    return all(set(c) <= {"-", ":", " "} and c for c in cells)


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _aliases_from_term_cell(term_cell: str) -> tuple[str, list[str]]:
    """Return (display canonical, lowercased alias list) from a term cell.

    A cell like ``**knackered** / **worn out** / **buggered** (mild)`` yields
    canonical ``knackered`` and aliases ``[knackered, worn out, buggered]``.
    """
    cleaned = _clean(term_cell)
    variants = [v.strip() for v in cleaned.split("/") if v.strip()]
    display: list[str] = []
    aliases: list[str] = []
    for v in variants:
        no_parens = _PARENS.sub("", v).strip()
        if not no_parens:
            continue
        display.append(no_parens)
        aliases.append(no_parens.lower())
    if not display:
        return "", []
    # Dedupe aliases preserving order.
    seen: set[str] = set()
    uniq = [a for a in aliases if not (a in seen or seen.add(a))]
    return display[0], uniq


def _iter_sections(md: str):
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("## "):
            heading = lines[i][3:].strip()
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                body.append(lines[i])
                i += 1
            yield heading, body
        else:
            i += 1


def parse_vocabulary_markdown(md: str, locale: str) -> list[VocabRecord]:
    records: list[VocabRecord] = []
    seen_ids: set[str] = set()
    for heading, body in _iter_sections(md):
        if not any(heading.startswith(p) for p in GLOSSARY_HEADING_PREFIXES):
            continue
        rows = [l for l in body if l.strip().startswith("|")]
        if len(rows) < 2:
            continue
        # rows[0] is the header, rows[1] is the --- separator; data starts after.
        for row in rows[1:]:
            cells = _split_row(row)
            if _is_separator_row(cells) or len(cells) < 2:
                continue
            canonical, aliases = _aliases_from_term_cell(cells[0])
            if not canonical:
                continue
            meaning = _clean(cells[1])
            reflect = _clean(cells[2]) if len(cells) >= 3 else ""
            rec = VocabRecord(
                locale=locale,
                canonical=canonical,
                aliases=aliases,
                meaning=meaning,
                reflect=reflect,
                section=heading,
            )
            if rec.id in seen_ids:
                continue
            seen_ids.add(rec.id)
            records.append(rec)
    return records
