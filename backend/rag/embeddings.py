from __future__ import annotations

from typing import Any

import httpx

from backend.app.config import settings

_local_sentence_transformer: Any | None = None


def _get_sentence_transformer_model() -> Any:
    global _local_sentence_transformer
    if _local_sentence_transformer is None:
        from sentence_transformers import SentenceTransformer

        _local_sentence_transformer = SentenceTransformer(settings.rag_local_embedding_model)
    return _local_sentence_transformer


def _embed_via_local(texts: list[str]) -> list[list[float]]:
    model = _get_sentence_transformer_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [row.tolist() for row in vectors]


def _embed_via_api(texts: list[str]) -> list[list[float]]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY required for API RAG embeddings")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url
    if settings.openrouter_app_name:
        headers["X-Title"] = settings.openrouter_app_name

    payload: dict[str, Any] = {
        "model": settings.rag_embedding_model,
        "input": texts,
    }
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{settings.openai_base_url.rstrip('/')}/embeddings",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    ordered = sorted(data["data"], key=lambda row: row["index"])
    return [row["embedding"] for row in ordered]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.rag_embedding_backend == "local":
        return _embed_via_local(texts)
    return _embed_via_api(texts)
