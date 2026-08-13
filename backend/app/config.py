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
    # RAG — analyst facility policy (ingest.py) and companion culture vocabulary
    # (vocab/ingest.py). Vocabulary is retrieved per companion turn (literal alias match +
    # semantic) and re-injected at the end of the prompt so it is never "forgotten" in long
    # sessions. The analyst still inlines the glossary (single-shot call, nothing to forget).
    rag_enabled: bool = False
    rag_chroma_path: str = str(DATA_DIR / "rag" / "chroma")
    rag_top_k: int = 3
    # Analyst facility-policy retrieval breadth (kept separate from rag_top_k so general
    # domain sections aren't starved; safety sections are guaranteed on top of this).
    rag_policy_top_k: int = 6
    # "Filter then rank": restrict the broad semantic lane to the non-safety ('general')
    # chunks before cosine. Safety sections still enter via the deterministic
    # guarantee-include, so they are unaffected. OFF by default — only worth enabling once
    # the corpus is large enough that ranking everything gets noisy.
    rag_policy_pathway_filter: bool = False
    # Two-stage retrieve: fetch a wider candidate pool, then rerank down to rag_policy_top_k.
    # ON: the broad lane fetches rag_policy_candidate_pool rows and passes them through
    # rerank_chunks(). NOTE: with rag_policy_reranker_model empty the rerank is an identity
    # pass (wider fetch, no reordering) — set a model below to make it actually rerank.
    rag_policy_rerank: bool = True
    # Candidate breadth for the rerank stage; also the hard cap so fetch latency stays flat
    # as the corpus grows (ignored when rag_policy_rerank is off).
    rag_policy_candidate_pool: int = 30
    # Cross-encoder model for reranking (e.g. "BAAI/bge-reranker-base"). Empty = the hook is
    # present but a no-op (identity), so enabling the model later is a pure config change.
    rag_policy_reranker_model: str = ""
    # Max culture-vocabulary terms re-injected into the companion prompt per turn
    rag_vocab_top_k: int = 5
    # Analyst-exit vocab retrieval. OFF: the analyst inlines the full glossary (default).
    # ON: at exit the analyst retrieves only the terms the resident actually SPOKE — a single
    # literal (Aho-Corasick) pass over the full transcript — and injects just those. High
    # recall for used terms, smaller prompt, no paraphrase noise. Requires rag_enabled and an
    # ingested vocab collection; with either missing the analyst gets no vocab, so keep OFF
    # until vocabulary is ingested.
    rag_analyst_vocab_retrieval: bool = False
    # Companion vocab retrieval lanes: literal alias match (Aho-Corasick) is always on.
    # The semantic (cosine) lane is OFF by default — on an English companion model it mostly
    # re-teaches meanings the model already knows and adds noise. Enable only if you switch to
    # a multilingual embedder or a weaker companion model that needs the gloss spelled out.
    rag_vocab_semantic: bool = False
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
    # Record full LLM system/user prompts on session (test/debug; off in production)
    capture_llm_inputs: bool = False

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
