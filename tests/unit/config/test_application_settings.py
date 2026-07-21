from pydantic import HttpUrl

from src.config.application_settings import ApplicationSettings

DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/tyk"


def test_application_settings_uses_defaults() -> None:
    """Use application defaults when optional values are omitted."""
    application_settings: ApplicationSettings = (
        ApplicationSettings.model_validate(obj={"database_url": DATABASE_URL})
    )

    assert application_settings.app_debug is False
    assert application_settings.app_title == "Тык"
    assert application_settings.app_version == "0.1.0"
    assert application_settings.log_level == "INFO"
    assert application_settings.app_description == "Сокращатель URL-адресов"
    assert application_settings.public_base_url == HttpUrl(
        "http://127.0.0.1:8000"
    )
    assert application_settings.database_url == DATABASE_URL


def test_application_settings_accepts_overrides() -> None:
    """Accept explicitly provided application settings."""
    application_settings: ApplicationSettings = (
        ApplicationSettings.model_validate(
            obj={
                "app_debug": True,
                "app_title": "Test application",
                "app_version": "1.2.3",
                "log_level": "DEBUG",
                "app_description": "Test description",
                "public_base_url": "https://example.com",
                "database_url": DATABASE_URL,
            }
        )
    )

    assert application_settings.app_debug is True
    assert application_settings.app_title == "Test application"
    assert application_settings.app_version == "1.2.3"
    assert application_settings.log_level == "DEBUG"
    assert application_settings.app_description == "Test description"
    assert application_settings.public_base_url == HttpUrl(
        "https://example.com"
    )
    assert application_settings.database_url == DATABASE_URL
