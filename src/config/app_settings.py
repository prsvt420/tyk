from typing import ClassVar, Literal

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """App settings."""

    app_debug: bool = False
    app_title: str = "Тык"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        "INFO"
    )
    app_description: str = "Сокращатель URL-адресов"
    public_base_url: HttpUrl = HttpUrl("http://127.0.0.1:8000")
    cache_url: str
    database_url: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


app_settings: AppSettings = AppSettings()
