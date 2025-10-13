import os

import pytest

from src.bookmarker.core.database import DatabaseRepository


@pytest.fixture()
def db_repo():
    repo = DatabaseRepository(database_url="sqlite:///:memory:", echo=True)
    repo.create_db_and_tables()
    yield repo
    repo._engine.dispose()


@pytest.fixture(autouse=True, scope="session")
def set_env():
    os.environ["BOOKMARKER_ENV"] = "dev"
