import time
from pathlib import Path
from typing import Generator

import pytest
import redis
import requests
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, clear_mappers, sessionmaker
from tenacity import retry, stop_after_delay

from app.adapters.orm import metadata, start_mappers

from ..config import get_api_url, get_postgres_uri, get_redis_host_and_port


@pytest.fixture
def in_memory_db() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture
def sqlite_session(sqlite_session_factory):
    return sqlite_session_factory()


@pytest.fixture
def session(in_memory_db) -> Generator[Session, None, None]:
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine: Engine):
    return engine.connect()


@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up():
    return requests.get(get_api_url())


@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**get_redis_host_and_port())
    return r.ping()


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(get_postgres_uri())
    wait_for_postgres_to_come_up(engine=engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)
    clear_mappers()


@pytest.fixture
def postgres_session(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


@pytest.fixture
def restart_api():
    (Path(__file__).parent.parent / "main.py").touch()

    time.sleep(0.5)
    wait_for_webapp_to_come_up()


@pytest.fixture
def restart_redis_pubsub():
    wait_for_redis_to_come_up()
    import shutil
    import subprocess

    if not shutil.which("docker compose"):
        print("skipping restart, assumes running in container")
        return

    subprocess.run(["docker", "compose", "restart", "-t", "0", "redis_pubsub"])
