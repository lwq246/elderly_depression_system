from pathlib import Path

from .config import SKILLS_DIR

# Screening-relevant sections from culture-*/local-vocabulary.md (skip policy, local-light, sources).
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


def _culture_companion_path(locale: str) -> Path:
    culture_dir = SKILLS_DIR / "screening-conversation" / _culture_dir(locale)
    runtime = culture_dir / "companion-runtime.md"
    if runtime.is_file():
        return runtime
    return culture_dir / "SKILL.md"


def load_companion_system_prompt(locale: str, speech_register: str) -> str:
    culture = _culture_dir(locale)
    base_path = SKILLS_DIR / "screening-conversation" / "companion-runtime.md"
    if not base_path.is_file():
        base_path = SKILLS_DIR / "screening-conversation" / "SKILL.md"
    base = _read(base_path)
    culture_skill = _read(_culture_companion_path(locale))
    vocab_path = _local_vocabulary_path(locale)
    vocab_block = ""
    if vocab_path.is_file():
        extracted = _extract_companion_vocabulary(_read(vocab_path))
        if extracted:
            vocab_block = f"\n\n---\n\n## Local vocabulary reference\n\n{extracted}"
    register_note = (
        f"\n\n## Session setting\n\n`speech_register`: **{speech_register}**\n"
    )
    return f"{base}\n\n---\n\n{culture_skill}{vocab_block}{register_note}"


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
    analyst_locale_path = (
        SKILLS_DIR / "screening-conversation" / _culture_dir(locale) / "analyst-locale.md"
    )
    if analyst_locale_path.is_file():
        parts.append(_read(analyst_locale_path).strip())
    return "\n\n---\n\n".join(parts)


def load_greeting(locale: str, preferred_name: str | None) -> str:
    culture = _culture_dir(locale)
    template = _read(SKILLS_DIR / "screening-conversation" / culture / "greeting.txt").strip()
    if preferred_name:
        rest = template[5:].lstrip(". ") if template.lower().startswith("hello") else template
        return f"Hello, {preferred_name}. {rest}"
    return template
