from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Northstar Cloud"
    app_environment: str = "development"
    app_secret_key: str = Field(default="change-me-in-production", min_length=16)
    frontend_origin: str = "http://localhost:5174"
    database_path: str = "./data/example_usage_woobe.db"

    demo_email: str = "demo@northstar.local"
    demo_password: str = "demo123"
    demo_user_id: str = "usr_demo_001"
    demo_account_id: str = "acc_northstar_001"

    woobe_api_base_url: str = "http://localhost:8000"
    woobe_chat_surface_public_id: str = ""
    woobe_chat_surface_access_key: str = ""
    woobe_host_origin: str = "http://localhost:5174"
    woobe_request_timeout_seconds: float = 20.0

    woobe_tool_api_key: str = "replace-with-a-long-random-tool-key"


@lru_cache
def get_settings() -> Settings:
    return Settings()
