"""
Application configuration using pydantic-settings.
Reads from .env file automatically.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Report Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "change-me"

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ── Groq API (Chapter Report Text Generation) ─────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_MAX_TOKENS: int = 4096

    # ── Hugging Face API (Diagram & Image Generation) ─────────────────────────
    HF_API_KEY: str = ""
    HF_IMAGE_MODEL: str = "Maelstrome/mermaid-gemmma-7b"

    # ── Storage Directories ───────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./storage/chromadb"
    UPLOAD_DIR: str = "./storage/uploads"
    DIAGRAMS_DIR: str = "./storage/diagrams"
    MAX_FILE_SIZE_MB: int = 50


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
