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

    # Groq AI
    # NOTE: Do NOT hardcode API keys here. Set `GROQ_API_KEY` in your
    # environment (Railway/GCP/AWS) or in a local `.env` file that is
    # excluded from version control. Default to empty string.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Session store
    session_store_path: str = "data/sessions.json"
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
    # Load settings from environment / .env first
    s = Settings()

    # Backwards-compat: some deployments (e.g. Railway) use ACCESS_TOKEN
    # as the name for the WhatsApp bearer token. Accept that as a fallback
    # so users don't need to rename env vars immediately.
    import os

    if not s.whatsapp_token:
        s.whatsapp_token = os.getenv("ACCESS_TOKEN", "")

    # Backwards-compat: old env files may still use OPENAI_API_KEY for the
    # Groq key. Accept that as fallback if GROQ_API_KEY is not set.
    if not s.GROQ_API_KEY:
        s.GROQ_API_KEY = os.getenv("OPENAI_API_KEY", "")

    return s
