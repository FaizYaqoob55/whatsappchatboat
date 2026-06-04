from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # WhatsApp
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "mera_secret_verify_token_123"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Business
    business_name: str = "My Online Store"
    business_description: str = "We sell quality products online in Pakistan"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def whatsapp_api_url(self) -> str:
        return (
            f"https://graph.facebook.com/v19.0/"
            f"{self.whatsapp_phone_number_id}/messages"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
