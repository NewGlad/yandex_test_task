import asyncio
import logging
from subprocess import PIPE, Popen
import yaml
import pytest
from aioresponses import aioresponses
from app.app import create_app
from pathlib import Path
from asyncpg import connect
import os

logger = logging.getLogger('conftest')
pytest_plugins = 'aiohttp.pytest_plugin'


file_path = Path(__file__).parent / 'test_config.yaml'
with open(file_path, 'r') as config_file:
    test_config_dict = yaml.safe_load(config_file)


@pytest.fixture
def samples_list():
    samples_dir = Path(__file__).parent / 'test_samples/samples/'
    samples_path_list =  [os.path.join(samples_dir, item) for item in os.listdir(samples_dir) if item.endswith('.json')]
    return samples_path_list


@pytest.fixture
def one_citizen_sample():
    sample = Path(__file__).parent / 'test_samples/samples/sample_1.json'
    return sample

@pytest.fixture
def largest_sample():
    sample = Path(__file__).parent / 'test_samples/samples/sample_10000.json'
    return sample


@pytest.fixture(autouse=True)
async def db():
    """
    Фикстура для очистки данных в БД между запусками тестов
    """
    connection = await connect(test_config_dict['database_uri'])
    await connection.execute("""
        ALTER SEQUENCE citizen_info_import_id_seq RESTART WITH 1;
        TRUNCATE TABLE citizen_info CASCADE;
        TRUNCATE TABLE citizen_relation CASCADE;
    """)



@pytest.fixture
def test_cli(loop, aiohttp_client):
    """
    Базовая фикстура для старта приложения и получения aiohttp-клиента
    """
    application = create_app(config=test_config_dict)
    return loop.run_until_complete(aiohttp_client(application))


@pytest.fixture(autouse=True)
def mock_responses():
    """
    По умолчанию мокаем все запросы, кроме запросов к серверу
    """
    with aioresponses(passthrough=['http://127.0.0.1:']) as m:
        yield m
