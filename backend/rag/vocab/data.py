"""Culture vocabulary — locale-specific terms for companion literal-match retrieval.

Generic English symptom words are intentionally excluded; the LLM handles those.
en-SG: backend/rag/vocab/data_en_sg.py
en-AU: backend/rag/vocab/data_en_au.py
"""

from __future__ import annotations

from backend.rag.vocab.data_en_au import VOCABULARY_TERMS_EN_AU
from backend.rag.vocab.data_en_sg import VOCABULARY_TERMS_EN_SG

# locale → list of (variant terms, single general meaning)
VOCABULARY_TERMS: dict[str, list[tuple[list[str], str]]] = {
    "en-SG": VOCABULARY_TERMS_EN_SG,
    "en-AU": VOCABULARY_TERMS_EN_AU,
}


def vocabulary_locales() -> list[str]:
    return list(VOCABULARY_TERMS.keys())
