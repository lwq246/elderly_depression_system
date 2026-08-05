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
    openai_model: str = "qwen/qwen3-14b"
    # Optional OpenRouter attribution headers (recommended by OpenRouter)
    openrouter_site_url: str = ""
    openrouter_app_name: str = "Elderly Depression Screening"
    # Pin OpenRouter to a provider slug (e.g. deepinfra). See openrouter.ai/docs/guides/routing/provider-selection
    openrouter_provider: str = ""
    openrouter_allow_fallbacks: bool = True
    database_path: str = str(DATA_DIR / "screening.db")
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    companion_history_turns: int = 12
    # RAG (analyst only) — set RAG_ENABLED=true after running backend/rag/ingest.py
    rag_enabled: bool = False
    rag_chroma_path: str = str(DATA_DIR / "rag" / "chroma")
    rag_top_k: int = 3
    rag_query_max_chars: int = 4000
    rag_max_distance: float = 0.65
    rag_embedding_model: str = "openai/text-embedding-3-small"
    rag_use_llm_summary: bool = True
    rag_summary_max_chars: int = 800
    # Comma-separated facility-policy locales to ingest (e.g. en-AU only)
    rag_index_locales: str = "en-AU"

    @property
    def rag_index_locale_list(self) -> list[str]:
        return [x.strip() for x in self.rag_index_locales.split(",") if x.strip()]

    @property
    def use_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
