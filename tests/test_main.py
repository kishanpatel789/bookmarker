import pytest

from src.bookmarker.core.database import DatabaseRepository, SQLModel, create_engine
from src.bookmarker.core.main import add_artifact


@pytest.fixture()
def db_repo() -> DatabaseRepository:
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    return DatabaseRepository(engine)


def test_add_artifact(db_repo):
    breakpoint()
    artifact = add_artifact(db_repo, title="Test Article", url="https://example.com")

    assert artifact.id is not None
    assert artifact.title == "Test Article"
    assert artifact.url == "https://example.com"
    assert artifact.artifact_type.name == "ARTICLE"
