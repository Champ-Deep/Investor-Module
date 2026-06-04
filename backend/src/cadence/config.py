from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config. Drop the two keys below into a .env and the app lights up the live
    paths automatically; with no keys it runs fully on deterministic, offline defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://cadence:cadence_dev@localhost:5436/cadence"

    # --- LLM via OpenRouter (OpenAI-compatible) — powers natural-language query parsing. ---
    # Set OPENROUTER_API_KEY to replace the heuristic parser with a real LLM. Nothing else changes.
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"

    # --- Embeddings — deterministic + offline by default (hermetic). Optional hosted upgrade. ---
    # OpenRouter does NOT serve embeddings; set OPENAI_API_KEY only if you want hosted embeddings.
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"

    # --- LakeB2B Data API — live identity/contact source. ---
    # Set LAKEB2B_API_KEY + LAKEB2B_BASE_URL and DATA_SOURCE=lakeb2b, then `make ingest`.
    lakeb2b_api_key: str | None = None
    lakeb2b_base_url: str | None = None
    data_source: str = "seed"  # seed | lakeb2b | crunchbase

    # --- Crunchbase-2015 open test data (ADR 0008). DATA_SOURCE=crunchbase, then `make ingest`. ---
    crunchbase_data_dir: str = ".data/crunchbase"
    crunchbase_min_deals: int = 5  # only import investors with at least this many deals

    activity_window_months: int = 24
    contact_sla_days: int = 180  # 90 = premium tier, 180 = standard tier
    log_level: str = "info"

    @property
    def llm_parse_provider(self) -> str:
        return "openrouter" if self.openrouter_api_key else "heuristic"

    @property
    def embeddings_provider(self) -> str:
        return "openai" if self.openai_api_key else "deterministic"

    @property
    def active_data_source(self) -> str:
        """The source that will actually be used, honouring both the selector and key presence."""
        if self.data_source == "crunchbase":
            return "crunchbase"
        if self.data_source == "lakeb2b" and self.lakeb2b_api_key:
            return "lakeb2b"
        return "seed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
