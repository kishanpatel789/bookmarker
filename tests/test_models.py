import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.bookmarker.core.models import Artifact, ArtifactTypeEnum, Tag

engine = create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="function", autouse=True)
def set_up_database():
    SQLModel.metadata.create_all(engine)


def save_to_db(artifact):
    with Session(engine) as session:
        session.add(artifact)
        session.commit()
        session.refresh(artifact)


def test_create_artifact_model():
    tag_python = Tag(name="python")
    tag_cloud = Tag(name="cloud")

    artifact = Artifact(
        title="Test Article",
        url="https://example.com",
        notes="This seems interesting",
        tags=[tag_python, tag_cloud],
    )
    save_to_db(artifact)

    assert artifact.id is not None
    assert artifact.title == "Test Article"
    assert artifact.url == "https://example.com"
    assert artifact.artifact_type == ArtifactTypeEnum.ARTICLE
    assert artifact.notes == "This seems interesting"
    assert len(artifact.tags) == 2
    assert artifact.content_raw is None
    assert artifact.content_summary is None
    assert artifact.created_at is not None
    assert artifact.updated_at is None
