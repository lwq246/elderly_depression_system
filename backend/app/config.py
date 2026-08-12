from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT_DIR / ".cursor" / "skills"
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "openai/gpt-4o-mini"
    # Optional OpenRouter attribution headers (recommended by OpenRouter)
    openrouter_site_url: str = ""
    openrouter_app_name: str = "Elderly Depression Screening"
    # Pin OpenRouter to a provider slug (e.g. deepinfra). See openrouter.ai/docs/guides/routing/provider-selection
    openrouter_provider: str = ""
    openrouter_allow_fallbacks: bool = True
    database_path: str = str(DATA_DIR / "screening.db")
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    companion_history_turns: int = 12
    # RAG — analyst facility policy (ingest.py); companion vocab uses local glossary literal match
    rag_enabled: bool = False
    rag_chroma_path: str = str(DATA_DIR / "rag" / "chroma")
    rag_top_k: int = 3
    # Min cosine similarity for Chroma retrieval (cosine space: similarity = 1 - distance)
    rag_min_similarity: float = 0.35
    # Embedding backend: local (sentence-transformers) or api (OpenRouter/OpenAI)
    rag_embedding_backend: str = "local"
    rag_local_embedding_model: str = "BAAI/bge-base-en-v1.5"
    rag_embedding_model: str = "openai/text-embedding-3-small"
    rag_use_llm_summary: bool = True
    rag_summary_max_chars: int = 800
    # Parent/child chunking: sections split into overlapping child windows for embedding; full parent text returned
    rag_child_max_chars: int = 1200
    rag_child_overlap_chars: int = 200
    # Default facility/tenant id stamped on chunks when a source declares none
    rag_default_facility_id: str = "default"
    # Comma-separated facility-policy locales to ingest (e.g. en-AU only)
    rag_index_locales: str = "en-AU"
    # Companion per-turn vocabulary RAG tuning (backend/rag/vocab/data.py → Chroma)
    rag_vocab_top_k: int = 20
    rag_vocab_locales: str = "en-SG,en-AU"
    # Record full LLM system/user prompts on session (test/debug; off in production)
    capture_llm_inputs: bool = False

    @property
    def rag_index_locale_list(self) -> list[str]:
        return [x.strip() for x in self.rag_index_locales.split(",") if x.strip()]

    @property
    def rag_vocab_locale_list(self) -> list[str]:
        return [x.strip() for x in self.rag_vocab_locales.split(",") if x.strip()]

    @property
    def use_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
