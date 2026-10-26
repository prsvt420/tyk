import pytest
from pydantic import HttpUrl, ValidationError

from src.config.app_settings import AppSettings

DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/tyk"
CACHE_URL: str = "redis://localhost:6379/0"


@pytest.fixture(autouse=True)
def _clear_cache_settings_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep optional cache settings independent of process configuration."""
    for name in (
        "cache_short_link_ttl_seconds",
        "cache_connect_timeout_seconds",
        "cache_socket_timeout_seconds",
    ):
        monkeypatch.delenv(name=name, raising=False)
        monkeypatch.delenv(name=name.upper(), raising=False)


def test_app_settings_uses_defaults() -> None:
    """Use app defaults when optional values are omitted."""
    app_settings: AppSettings = AppSettings(
        _env_file=None,
        database_url=DATABASE_URL,
        cache_url=CACHE_URL,
    )

    assert app_settings.app_debug is False
    assert app_settings.app_title == "Тык"
    assert app_settings.app_version == "0.2.0"
    assert app_settings.log_level == "INFO"
    assert app_settings.app_description == "Сокращатель URL-адресов"
    assert app_settings.public_base_url == HttpUrl("http://127.0.0.1:8000")
    assert app_settings.database_url == DATABASE_URL
    assert app_settings.cache_url == CACHE_URL
    assert app_settings.cache_short_link_ttl_seconds == 86400
    assert app_settings.cache_connect_timeout_seconds == 0.5
    assert app_settings.cache_socket_timeout_seconds == 0.2


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
            "cache_short_link_ttl_seconds": 1800,
            "cache_connect_timeout_seconds": 0.75,
            "cache_socket_timeout_seconds": 0.4,
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
    assert app_settings.cache_short_link_ttl_seconds == 1800
    assert app_settings.cache_connect_timeout_seconds == 0.75
    assert app_settings.cache_socket_timeout_seconds == 0.4


@pytest.mark.parametrize(
    argnames=("connect_timeout", "socket_timeout", "invalid_field"),
    argvalues=[
        (0.0, 0.2, "cache_connect_timeout_seconds"),
        (-0.1, 0.2, "cache_connect_timeout_seconds"),
        (0.5, 0.0, "cache_socket_timeout_seconds"),
        (0.5, -0.1, "cache_socket_timeout_seconds"),
    ],
)
def test_app_settings_rejects_non_positive_cache_timeouts(
    connect_timeout: float,
    socket_timeout: float,
    invalid_field: str,
) -> None:
    """Reject zero and negative values for either cache timeout."""
    with pytest.raises(expected_exception=ValidationError) as exception_info:
        AppSettings(
            _env_file=None,
            database_url=DATABASE_URL,
            cache_url=CACHE_URL,
            cache_connect_timeout_seconds=connect_timeout,
            cache_socket_timeout_seconds=socket_timeout,
        )

    errors = exception_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == (invalid_field,)
    assert errors[0]["type"] == "greater_than"


@pytest.mark.parametrize(argnames="cache_ttl", argvalues=[0, -1])
def test_app_settings_rejects_non_positive_cache_ttl(
    cache_ttl: int,
) -> None:
    """Reject zero and negative short link cache lifetimes."""
    with pytest.raises(expected_exception=ValidationError) as exception_info:
        AppSettings(
            _env_file=None,
            database_url=DATABASE_URL,
            cache_url=CACHE_URL,
            cache_short_link_ttl_seconds=cache_ttl,
        )

    errors = exception_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("cache_short_link_ttl_seconds",)
    assert errors[0]["type"] == "greater_than"


def test_app_settings_reads_cache_settings_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read cache lifetime and timeout settings without a dotenv file."""
    monkeypatch.setenv(name="CACHE_SHORT_LINK_TTL_SECONDS", value="120")
    monkeypatch.setenv(name="CACHE_CONNECT_TIMEOUT_SECONDS", value="0.35")
    monkeypatch.setenv(name="CACHE_SOCKET_TIMEOUT_SECONDS", value="0.15")

    app_settings: AppSettings = AppSettings(
        _env_file=None,
        database_url=DATABASE_URL,
        cache_url=CACHE_URL,
    )

    assert app_settings.cache_short_link_ttl_seconds == 120
    assert app_settings.cache_connect_timeout_seconds == 0.35
    assert app_settings.cache_socket_timeout_seconds == 0.15
