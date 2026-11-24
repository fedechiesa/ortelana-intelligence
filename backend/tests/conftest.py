import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
OPERATOR = {"Authorization": "Bearer demo-operator-local"}
SUPERVISOR = {"Authorization": "Bearer demo-supervisor-local"}


@pytest.fixture
def settings(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'business.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(ROOT / "backend/alembic.ini"))
    command.upgrade(config, "head")
    return Settings(
        database_url=url,
        data_dir=ROOT / "data",
        checkpoint_path=str(tmp_path / "checkpoints.db"),
        data_mode="demo",
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as instance:
        yield instance


@pytest.fixture(scope="module")
def postgres_client():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated database ending in _test")
    from sqlalchemy.engine import make_url

    if not (make_url(url).database or "").endswith("_test"):
        pytest.fail("Refusing to run integration tests on a non-test database")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(Config(str(ROOT / "backend/alembic.ini")), "head")
        with TestClient(
            create_app(Settings(database_url=url, data_dir=ROOT / "data", data_mode="demo"))
        ) as c:
            yield c
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
