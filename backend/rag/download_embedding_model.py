"""Download / verify the local RAG embedding model (sentence-transformers / Hugging Face)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import settings
from backend.rag.embeddings import embed_texts


def main() -> int:
    model = settings.rag_local_embedding_model
    print(f"Loading local embedding model: {model}")
    vectors = embed_texts(["sian", "I feel very tired lately"])
    print(f"OK — {len(vectors)} vectors, dimension {len(vectors[0])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
