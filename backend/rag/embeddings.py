from typing import Any

import httpx

from backend.app.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY required for RAG embeddings")

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
