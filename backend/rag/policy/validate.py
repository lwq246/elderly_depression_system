"""Validate normalized facility policy markdown before RAG ingest."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from backend.rag.policy.chunking import iter_policy_sections
from backend.rag.policy.routing import ALL_PATHWAYS, PATHWAY_ACTIVE, PATHWAY_PASSIVE
from backend.rag.policy.section_meta import iter_directive_pathway_tokens

REQUIRED_PATHWAYS = {PATHWAY_PASSIVE, PATHWAY_ACTIVE}
VALID_LOCALES = {"en-AU", "en-SG"}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    indexed_sections: list[str] = field(default_factory=list)


def _infer_locale(text: str, path: Path | None) -> str | None:
    for line in text.splitlines()[:20]:
        stripped = line.strip()
        if stripped.lower().startswith("locale:"):
            return stripped.split(":", 1)[1].strip()
    if path:
        stem = path.stem.lower()
        if stem in VALID_LOCALES:
            return stem
    return None


def validate_policy_markdown(
    text: str,
    *,
    locale: str | None = None,
    path: Path | None = None,
) -> ValidationResult:
    """Check converted policy is ready for human approval and RAG ingest."""
    errors: list[str] = []
    warnings: list[str] = []

    resolved_locale = locale or _infer_locale(text, path)
    if not resolved_locale:
        errors.append("locale missing — set --locale or add 'Locale: en-AU' near the top")
    elif resolved_locale not in VALID_LOCALES:
        errors.append(f"unsupported locale: {resolved_locale} (expected en-AU or en-SG)")

    sections = iter_policy_sections(text, locale=resolved_locale or "all")
    if not sections:
        errors.append("no ## sections found")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    indexed_names = [s["section"] for s in sections]
    pathways = {s["pathway"] for s in sections}

    missing_required = REQUIRED_PATHWAYS - pathways
    for pathway in sorted(missing_required):
        errors.append(f"missing required pathway: {pathway}")

    # Every section must resolve to exactly one valid coarse bucket — no chunk is ingested
    # without one (the ingest layer also hard-fails on this).
    for section in sections:
        if section["pathway"] not in ALL_PATHWAYS:
            errors.append(
                f"section '{section['section']}' has invalid/missing pathway: "
                f"{section['pathway']!r} (expected one of {sorted(ALL_PATHWAYS)})"
            )

    # Surface typo'd directive tokens (e.g. `<!-- pathway: refrence -->`) that would be
    # silently ignored and fall back to heading inference.
    for token in iter_directive_pathway_tokens(text):
        if token not in ALL_PATHWAYS:
            warnings.append(
                f"unknown pathway directive '{token}' ignored — "
                f"expected one of {sorted(ALL_PATHWAYS)}"
            )

    if "UNVERIFIED" in text:
        warnings.append("document contains UNVERIFIED markers — review before ingest")

    if "[CONFIGURE:" in text:
        warnings.append("document contains [CONFIGURE: ...] placeholders — fill in before ingest")

    return ValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        indexed_sections=indexed_names,
    )


def format_validation_report(result: ValidationResult) -> str:
    lines = ["Policy validation: " + ("PASS" if result.ok else "FAIL")]
    if result.indexed_sections:
        lines.append(f"Indexed sections ({len(result.indexed_sections)}): "
                     + ", ".join(result.indexed_sections))
    for msg in result.errors:
        lines.append(f"ERROR: {msg}")
    for msg in result.warnings:
        lines.append(f"WARN: {msg}")
    return "\n".join(lines)
