from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .observability import configure_observability
from .routes.sessions import residents_router, router as sessions_router
## C:\Python314\python.exe -m uvicorn backend.app.main:app --reload --port 8000
app = FastAPI(
    title="Elderly Depression Screening API",
    description="UWB-triggered screening sessions with companion + analyst pipeline",
    version="0.1.0",
)

configure_observability(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(residents_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    rag_chunks = 0
    rag_policy_chunks = 0
    if settings.rag_enabled:
        try:
            from backend.rag.store import collection_counts

            counts = collection_counts()
            rag_chunks = counts["total"]
            rag_policy_chunks = counts["policy"]
        except Exception:
            rag_chunks = -1

    return {
        "status": "ok",
        "llm_configured": settings.use_openai,
        "model": settings.openai_model if settings.use_openai else None,
        "openrouter_provider": settings.openrouter_provider or None,
        "rag_enabled": settings.rag_enabled,
        "rag_use_llm_summary": settings.rag_use_llm_summary,
        "rag_chunks": rag_chunks,
        "rag_policy_chunks": rag_policy_chunks,
    }
