"""Configuration loaded once from environment variables.

Keeping configuration in one Pydantic model makes the effective runtime inputs
visible and validated. Copy `.env.example` to `.env` to override defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All knobs that are useful while learning from the traces."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"
    trace_directory: Path = Path("traces")
    trace_capture_content: bool = True
    otel_exporter_otlp_traces_endpoint: str | None = None
    max_agent_turns: int = Field(default=8, ge=2, le=30)


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-in-practice settings object per process."""

    return Settings()
