"""Validate normalized facility policy markdown before RAG ingest."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from backend.rag.policy.chunking import iter_policy_sections
from backend.rag.policy.routing import PATHWAY_ACTIVE, PATHWAY_PASSIVE

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
