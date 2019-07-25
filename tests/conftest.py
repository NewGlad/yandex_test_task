import asyncio
import logging
from subprocess import PIPE, Popen

import pytest
from aioresponses import aioresponses
from app import create_app

logger = logging.getLogger('conftest')

pytest_plugins = 'aiohttp.pytest_plugin'


@pytest.fixture
def test_cli(loop, aiohttp_client):
    """
    Базовая фикстура для старта приложения и получения aiohttp-клиента
    """
    return loop.run_until_complete(aiohttp_client(create_app()))


@pytest.fixture(autouse=True)
def mock_responses():
    """
    По умолчанию мокаем все запросы, кроме запросов к серверу
    """
    with aioresponses(passthrough=['http://127.0.0.1:']) as m:
        yield m
