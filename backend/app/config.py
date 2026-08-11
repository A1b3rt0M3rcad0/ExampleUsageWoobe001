from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_environment: str = "development"
    app_secret_key: str = Field(default="change-me-in-production", min_length=16)
    frontend_origin: str = "http://localhost:5174"
    public_store_base_url: str = "http://localhost:5174"
    database_path: str = "./data/mercury_commerce.db"
    admin_email: str = "admin@mercury.demo"
    admin_password: str = "demo123"
    admin_user_id: str = "usr_merchant_001"
    merchant_id: str = "merchant_mercury_001"
    woobe_api_base_url: str = "http://localhost:8000"
    woobe_host_origin: str = "http://localhost:5174"
    woobe_request_timeout_seconds: float = 20.0
    woobe_store_chat_surface_public_id: str = ""
    woobe_store_chat_surface_access_key: str = ""
    woobe_admin_chat_surface_public_id: str = ""
    woobe_admin_chat_surface_access_key: str = ""
    woobe_store_tool_api_key: str = "replace-with-a-long-random-store-tool-key"
    woobe_admin_tool_api_key: str = "replace-with-a-long-random-admin-tool-key"

    @property
    def store_surface_configured(self) -> bool:
        return self.woobe_store_chat_surface_public_id.startswith("csf_") and "replace_me" not in self.woobe_store_chat_surface_public_id and self.woobe_store_chat_surface_access_key.startswith("woobe_surface_") and "replace_me" not in self.woobe_store_chat_surface_access_key

    @property
    def admin_surface_configured(self) -> bool:
        return self.woobe_admin_chat_surface_public_id.startswith("csf_") and "replace_me" not in self.woobe_admin_chat_surface_public_id and self.woobe_admin_chat_surface_access_key.startswith("woobe_surface_") and "replace_me" not in self.woobe_admin_chat_surface_access_key

@lru_cache
def get_settings() -> Settings:
    return Settings()
