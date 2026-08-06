from pathlib import Path

import chromadb

from backend.app.config import settings

POLICY_COLLECTION_NAME = "screening-facility-policy"
VOCAB_COLLECTION_NAME = "screening-culture-vocabulary"
# Legacy single-collection name (pre-split); deleted on ingest --reset.
LEGACY_COLLECTION_NAME = POLICY_COLLECTION_NAME

_COSINE = {"hnsw:space": "cosine"}


def get_client() -> chromadb.PersistentClient:
    path = Path(settings.rag_chroma_path)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_policy_collection(client: chromadb.PersistentClient | None = None):
    client = client or get_client()
    return client.get_or_create_collection(
        name=POLICY_COLLECTION_NAME,
        metadata=_COSINE,
    )


def get_vocab_collection(client: chromadb.PersistentClient | None = None):
    client = client or get_client()
    return client.get_or_create_collection(
        name=VOCAB_COLLECTION_NAME,
        metadata=_COSINE,
    )


def get_collection_for_type(doc_type: str):
    if doc_type == "culture_vocabulary":
        return get_vocab_collection()
    if doc_type == "facility_policy":
        return get_policy_collection()
    raise ValueError(f"Unknown doc_type: {doc_type}")


def delete_all_collections(client: chromadb.PersistentClient | None = None) -> None:
    client = client or get_client()
    for name in (
        "screening-rubric",
        "screening-policy",
        POLICY_COLLECTION_NAME,
        VOCAB_COLLECTION_NAME,
    ):
        try:
            client.delete_collection(name)
        except Exception:
            pass


def collection_counts() -> dict[str, int]:
    try:
        policy = get_policy_collection().count()
        vocab = get_vocab_collection().count()
    except Exception:
        return {"policy": 0, "vocabulary": 0, "total": 0}
    return {"policy": policy, "vocabulary": vocab, "total": policy + vocab}


def collection_count() -> int:
    return collection_counts()["total"]
