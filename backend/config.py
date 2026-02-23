from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    model: str = "gpt-4o"
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    # Agent
    max_context_tokens: int = 8000

    # Memory
    checkpoint_db_path: str = "db/checkpoints.db"

    # MCP
    mcp_timeout: float = 10.0

    # Logging
    log_level: str = "DEBUG"
    log_dir: str = "logs"

    # CORS（JSON 数组格式，如 '["http://localhost:5173"]'）
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
