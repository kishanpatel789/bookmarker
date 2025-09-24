import pytest

from src.bookmarker.core.database import DatabaseRepository, SQLModel, create_engine


@pytest.fixture()
def db_repo() -> DatabaseRepository:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield DatabaseRepository(engine)
    engine.dispose()
