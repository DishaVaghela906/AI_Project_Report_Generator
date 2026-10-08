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

    # ── LLM Provider Configuration ──────────────────────────────────────────────
    # Options: "groq", "huggingface", "openrouter", "ollama"
    LLM_PROVIDER: str = "groq"
    LLM_MAX_TOKENS: int = 4096  # Allows full 4k token generation for complete academic chapters

    # Groq (Recommended — super fast, 120B model support with high token quota)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"  # 120B parameter model: no truncation, high token limit

    # Hugging Face Inference API
    HF_API_KEY: str = ""
    HF_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"  # options: Qwen/Qwen2.5-72B-Instruct, Qwen/Qwen2.5-Coder-32B-Instruct, Qwen/Qwen2.5-7B-Instruct

    # OpenRouter API
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "qwen/qwen-2.5-72b-instruct"

    # Ollama (Local fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"

    # ── Chapter API Keys (pool — optional override per chapter) ─────────────────
    CHAPTER_1_API_KEY: str = "default"
    CHAPTER_2_API_KEY: str = "default"
    CHAPTER_3_API_KEY: str = "default"
    CHAPTER_4_API_KEY: str = "default"
    CHAPTER_5_API_KEY: str = "default"
    CHAPTER_6_API_KEY: str = "default"

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./storage/chromadb"

    # ── File Upload ───────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_FILE_SIZE_MB: int = 50

    @property
    def chapter_api_keys(self) -> dict[int, str]:
        """Returns a mapping of chapter number → API key."""
        return {
            1: self.CHAPTER_1_API_KEY,
            2: self.CHAPTER_2_API_KEY,
            3: self.CHAPTER_3_API_KEY,
            4: self.CHAPTER_4_API_KEY,
            5: self.CHAPTER_5_API_KEY,
            6: self.CHAPTER_6_API_KEY,
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
