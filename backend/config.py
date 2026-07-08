"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── LLM Settings ───────────────────────────────────────────────────────
    llm_provider: str = "zai"
    llm_model: str = "glm-4.7-flash"
    
    # ── ZAI API ────────────────────────────────────────────────────────────
    zai_api_key: str = ""            # auto-selected if empty

    # Search Configuration
    # Supported: "google" | "tavily" | "duckduckgo"
    search_engine: str = "tavily"
    tavily_api_key: str = ""
    max_search_results: int = 5

    # Database
    database_url: str = "sqlite+aiosqlite:///./zylabs.db"

    # App
    app_name: str = "ZyLabs AI Research Copilot"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Workflow
    max_retries: int = 2
    quality_threshold: float = 0.65

    @property
    def effective_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        if self.llm_provider == "openai":
            return "gpt-4o-mini"
        if self.llm_provider == "openrouter":
            return "z-ai/glm-5.2"
        return "gemini-2.0-flash"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
