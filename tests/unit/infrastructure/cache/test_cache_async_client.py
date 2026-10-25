import sys
from importlib import import_module
from types import ModuleType
from unittest.mock import patch

import pytest
from redis.asyncio import Redis as AsyncRedis

import src.infrastructure as infrastructure_package
from src.config import app_settings


def test_cache_async_client_uses_configured_url_and_enables_decoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configure an async Redis pool without opening a connection."""
    with patch.dict(in_dict=sys.modules), monkeypatch.context() as context:
        context.setattr(
            target=app_settings,
            name="cache_url",
            value="redis://cache.example:6380/2",
        )
        context.setattr(
            target=app_settings,
            name="cache_connect_timeout_seconds",
            value=0.35,
        )
        context.setattr(
            target=app_settings,
            name="cache_socket_timeout_seconds",
            value=0.15,
        )
        context.setattr(
            target=infrastructure_package,
            name="cache",
            value=None,
            raising=False,
        )
        sys.modules.pop("src.infrastructure.cache", None)
        sys.modules.pop("src.infrastructure.cache.cache_async_client", None)
        cache_package: ModuleType = import_module(
            name="src.infrastructure.cache"
        )
        cache_module: ModuleType = import_module(
            name="src.infrastructure.cache.cache_async_client"
        )
        cache_async_client: AsyncRedis = cache_module.cache_async_client

        assert (
            cache_async_client.connection_pool.connection_kwargs["host"]
            == "cache.example"
        )
        assert (
            cache_async_client.connection_pool.connection_kwargs["port"]
            == 6380
        )
        assert cache_async_client.connection_pool.connection_kwargs["db"] == 2
        assert (
            cache_async_client.connection_pool.connection_kwargs[
                "decode_responses"
            ]
            is True
        )
        assert (
            cache_async_client.connection_pool.connection_kwargs[
                "socket_connect_timeout"
            ]
            == 0.35
        )
        assert (
            cache_async_client.connection_pool.connection_kwargs[
                "socket_timeout"
            ]
            == 0.15
        )
        assert cache_package.cache_async_client is cache_async_client
