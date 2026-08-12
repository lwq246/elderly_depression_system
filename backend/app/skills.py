from pathlib import Path

from .config import SKILLS_DIR


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Skill file not found: {path}")
    return path.read_text(encoding="utf-8")


def _culture_dir(locale: str) -> str:
    return "culture-en-SG" if locale == "en-SG" else "culture-en-AU"


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


def load_companion_system_prompt(
    locale: str,
    *,
    vocabulary_context: str = "",
) -> str:
    culture = _culture_dir(locale)
    base_path = SKILLS_DIR / "screening-conversation" / "SKILL.md"
    base = _read(base_path)
    culture_skill = _read(_culture_companion_path(locale))
    vocab_block = ""
    if vocabulary_context.strip():
        vocab_block = (
            "\n\n---\n\n## Retrieved local vocabulary (this turn)\n\n"
            "Use these meanings to understand the resident. Do not treat as clinical "
            "terms, and do not force these words into your own reply.\n\n"
            + vocabulary_context.strip()
        )
    return f"{base}\n\n---\n\n{culture_skill}{vocab_block}"


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
    return "\n\n---\n\n".join(parts)


def load_greeting(locale: str, preferred_name: str | None) -> str:
    template = _GREETINGS.get(locale, _GREETINGS["en-SG"])
    if preferred_name:
        rest = template[5:].lstrip(". ") if template.lower().startswith("hello") else template
        return f"Hello, {preferred_name}. {rest}"
    return template
