from pathlib import Path

from .config import SKILLS_DIR

# Screening-relevant sections pulled from culture-*/local-vocabulary.md and inlined into
# the companion prompt (skip policy / local-light / sources — those are not runtime guidance).
_COMPANION_VOCAB_SECTION_HEADINGS = (
    "Words residents often use",
    "Singlish particles",
    "Mixed language",
    "CALD caution",
    "Men's / stoic presentation",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Skill file not found: {path}")
    return path.read_text(encoding="utf-8")


def _culture_dir(locale: str) -> str:
    return "culture-en-SG" if locale == "en-SG" else "culture-en-AU"


def _local_vocabulary_path(locale: str) -> Path:
    return SKILLS_DIR / "screening-conversation" / _culture_dir(locale) / "local-vocabulary.md"


def _extract_vocab_sections(vocab_md: str, section_headings: tuple[str, ...]) -> str:
    lines = vocab_md.splitlines()
    sections: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            heading = line[3:].strip()
            if any(heading.startswith(title) for title in section_headings):
                block = [line]
                i += 1
                while i < len(lines) and not lines[i].startswith("## "):
                    block.append(lines[i])
                    i += 1
                sections.append("\n".join(block).strip())
                continue
        i += 1
    return "\n\n".join(sections)


def _extract_companion_vocabulary(vocab_md: str) -> str:
    return _extract_vocab_sections(vocab_md, _COMPANION_VOCAB_SECTION_HEADINGS)


_GREETINGS: dict[str, str] = {
    "en-SG": (
        "Hello. Good to see you. I am here for a friendly check-in. "
        "Would it be okay if we chat a little about how you have been lately? "
        "Nothing formal — just a short conversation."
    ),
    "en-AU": (
        "Hello. I pop in for a quiet yarn now and then. "
        "Would it be alright if we talked a bit about how you have been going lately? "
        "Nothing formal — just a friendly check-in."
    ),
}


def _culture_companion_path(locale: str) -> Path:
    # Use the full SKILL.md (documentation form) for the companion prompt.
    culture_dir = SKILLS_DIR / "screening-conversation" / _culture_dir(locale)
    return culture_dir / "SKILL.md"


def load_companion_system_prompt(locale: str) -> str:
    base_path = SKILLS_DIR / "screening-conversation" / "SKILL.md"
    base = _read(base_path)
    culture_skill = _read(_culture_companion_path(locale))

    # Inline the full companion-relevant local vocabulary for this locale so the model always
    # has the whole lexicon in context (no per-turn retrieval).
    vocab_ref = ""
    vocab_path = _local_vocabulary_path(locale)
    if vocab_path.is_file():
        extracted = _extract_companion_vocabulary(_read(vocab_path))
        if extracted:
            vocab_ref = f"\n\n---\n\n## Local vocabulary reference\n\n{extracted}"

    return f"{base}\n\n---\n\n{culture_skill}{vocab_ref}"


def _extract_domain_criteria(reference_md: str) -> str:
    start = reference_md.find("## Domain criteria")
    if start == -1:
        return ""
    end = reference_md.find("\n## Indicator domains", start)
    if end == -1:
        return reference_md[start:].strip()
    return reference_md[start:end].strip()


def load_analyst_system_prompt(locale: str = "en-SG") -> str:
    skill = _read(SKILLS_DIR / "elderly-depression-detection" / "SKILL.md")
    reference = _read(SKILLS_DIR / "elderly-depression-detection" / "reference.md")
    examples_path = SKILLS_DIR / "elderly-depression-detection" / "examples.md"
    domains = _extract_domain_criteria(reference)
    parts = [skill]
    if domains:
        parts.append(domains)
    if examples_path.is_file():
        parts.append("## Reference examples\n\n" + _read(examples_path).strip())

    # Inline the full local vocabulary for the locale (same approach as the companion) so the
    # analyst can interpret culture-specific terms — no per-turn vocabulary retrieval needed.
    vocab_path = _local_vocabulary_path(locale)
    if vocab_path.is_file():
        extracted = _extract_companion_vocabulary(_read(vocab_path))
        if extracted:
            parts.append(
                "## Local vocabulary reference\n\n"
                "Culture-specific terms the resident may use. Use only to interpret meaning; "
                "evidence must cite resident line references (R1, R2, ...), never this glossary.\n\n"
                + extracted
            )
    return "\n\n---\n\n".join(parts)


def load_greeting(locale: str, preferred_name: str | None) -> str:
    template = _GREETINGS.get(locale, _GREETINGS["en-SG"])
    if preferred_name:
        rest = template[5:].lstrip(". ") if template.lower().startswith("hello") else template
        return f"Hello, {preferred_name}. {rest}"
    return template
