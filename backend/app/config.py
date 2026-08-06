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
    # RAG — analyst facility policy + companion culture vocabulary (run backend/rag/ingest.py first)
    rag_enabled: bool = False
    rag_chroma_path: str = str(DATA_DIR / "rag" / "chroma")
    rag_top_k: int = 3
    rag_query_max_chars: int = 4000
    # Min cosine similarity for Chroma retrieval (cosine space: similarity = 1 - distance)
    rag_min_similarity: float = 0.35
    rag_embedding_model: str = "openai/text-embedding-3-small"
    rag_use_llm_summary: bool = True
    rag_summary_max_chars: int = 800
    # Comma-separated facility-policy locales to ingest (e.g. en-AU only)
    rag_index_locales: str = "en-AU"
    # Companion per-turn vocabulary RAG tuning (backend/rag/vocab/data.py → Chroma)
    rag_vocab_top_k: int = 5
    rag_vocab_locales: str = "en-SG,en-AU"

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
