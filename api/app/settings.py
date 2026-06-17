from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from the process environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: SecretStr

    @field_validator("database_url", mode="after")
    @classmethod
    def _use_psycopg_driver(cls, value: SecretStr) -> SecretStr:
        """Bare postgres URLs must use psycopg3, the only driver we install."""
        raw: str = value.get_secret_value()
        for bare in ("postgresql://", "postgres://"):
            if raw.startswith(bare):
                return SecretStr(f"postgresql+psycopg://{raw[len(bare) :]}")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings so the environment is parsed once per process."""
    return Settings()
