from functools import lru_cache
from typing import Any, List

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    app_name: str = "AI Finance Backend"
    debug: bool = False
    database_url: str | None = None
    jwt_secret: str | None = None
    supabase_url: str | None = None
    supabase_key: str | None = None
    env_name: str = "dev"
    allowed_origins: List[str] = []

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and v.strip().startswith("["):
            import json

            return json.loads(v)
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: str):
            if field_name == "allowed_origins":
                return raw_value
            return super().parse_env_var(field_name, raw_value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
