from typing import ClassVar, Literal

from pydantic import Field, HttpUrl
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
    cache_short_link_ttl_seconds: int = Field(default=86400, gt=0)
    cache_connect_timeout_seconds: float = Field(default=0.5, gt=0)
    cache_socket_timeout_seconds: float = Field(default=0.2, gt=0)
    database_url: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


app_settings: AppSettings = AppSettings()
