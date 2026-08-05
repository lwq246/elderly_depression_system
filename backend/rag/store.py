from pathlib import Path

import chromadb

from backend.app.config import settings

COLLECTION_NAME = "screening-facility-policy"


def get_client() -> chromadb.PersistentClient:
    path = Path(settings.rag_chroma_path)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_collection(client: chromadb.PersistentClient | None = None):
    client = client or get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def collection_count() -> int:
    try:
        return get_collection().count()
    except Exception:
        return 0
