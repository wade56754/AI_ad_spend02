from functools import lru_cache
from typing import List, Union

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "AI Finance Backend"
    debug: bool = False
    database_url: str
    allowed_origins: List[str] = ["*"]

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            items = [origin.strip() for origin in value.split(",")]
            return [origin for origin in items if origin]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()



