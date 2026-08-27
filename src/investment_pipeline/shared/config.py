"""Environment-backed runtime configuration."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineConfig(BaseSettings):
    """Configuration shared by the CLI and pipeline stages."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    openai_reasoning_effort: str | None = None
    request_timeout_seconds: float = Field(default=60, gt=0)
    max_candidates: int = Field(default=20, ge=10, le=20)
    output_dir: Path = Path("outputs")
