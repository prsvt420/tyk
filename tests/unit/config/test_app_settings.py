from pydantic import HttpUrl

from src.config.app_settings import AppSettings

DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/tyk"
CACHE_URL: str = "redis://localhost:6379/0"


def test_app_settings_uses_defaults() -> None:
    """Use app defaults when optional values are omitted."""
    app_settings: AppSettings = AppSettings.model_validate(
        obj={"database_url": DATABASE_URL, "cache_url": CACHE_URL}
    )

    assert app_settings.app_debug is False
    assert app_settings.app_title == "Тык"
    assert app_settings.app_version == "0.1.0"
    assert app_settings.log_level == "INFO"
    assert app_settings.app_description == "Сокращатель URL-адресов"
    assert app_settings.public_base_url == HttpUrl("http://127.0.0.1:8000")
    assert app_settings.database_url == DATABASE_URL
    assert app_settings.cache_url == CACHE_URL


def test_app_settings_accepts_overrides() -> None:
    """Accept explicitly provided app settings."""
    app_settings: AppSettings = AppSettings.model_validate(
        obj={
            "app_debug": True,
            "app_title": "Test app",
            "app_version": "1.2.3",
            "log_level": "DEBUG",
            "app_description": "Test description",
            "public_base_url": "https://example.com",
            "database_url": DATABASE_URL,
            "cache_url": "redis://cache:6380/2",
        }
    )

    assert app_settings.app_debug is True
    assert app_settings.app_title == "Test app"
    assert app_settings.app_version == "1.2.3"
    assert app_settings.log_level == "DEBUG"
    assert app_settings.app_description == "Test description"
    assert app_settings.public_base_url == HttpUrl("https://example.com")
    assert app_settings.database_url == DATABASE_URL
    assert app_settings.cache_url == "redis://cache:6380/2"
