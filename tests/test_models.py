from datetime import datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from src.bookmarker.core.models import Artifact, ArtifactTypeEnum, Tag

engine = create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="function", autouse=True)
def set_up_database():
    SQLModel.metadata.create_all(engine)


def save_to_db(obj):
    with Session(engine) as session:
        session.add(obj)
        session.commit()
        session.refresh(obj)


@pytest.fixture
def add_tag():
    tag = Tag(name="python")
    save_to_db(tag)
    return tag


@pytest.fixture
def add_another_tag():
    tag = Tag(name="cloud")
    save_to_db(tag)
    return tag


@pytest.fixture
def add_article(add_tag, add_another_tag):
    artifact = Artifact(
        title="Test Article",
        url="https://example.com",
        notes="This seems interesting",
        tags=[add_tag, add_another_tag],
    )
    save_to_db(artifact)

    return artifact


def test_create_artifact_model(add_article):
    artifact = add_article

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


def test_create_tag_model(add_tag):
    tag = add_tag

    assert tag.id is not None
    assert tag.name == "python"


def test_create_artifact_with_video_type():
    artifact = Artifact(
        title="Async Programming",
        url="https://youtube.com/watch?v=123",
        artifact_type=ArtifactTypeEnum.YOUTUBE,
    )
    save_to_db(artifact)

    assert artifact.id is not None
    assert artifact.artifact_type == ArtifactTypeEnum.YOUTUBE


def test_artifact_tag_relationship(add_article):
    tag = Tag(name="test")
    artifact = Artifact(
        title="Test Article",
        url="https://example.com",
        tags=[tag],
    )
    save_to_db(artifact)

    with Session(engine) as session:
        stmt = select(Artifact).where(Artifact.id == artifact.id)
        loaded_artifact = session.exec(stmt).one()

    assert len(loaded_artifact.tags) == 1
    assert loaded_artifact.tags[0].name == "test"


def test_updated_at_field_changes(add_article):
    artifact = add_article

    created_time = artifact.created_at
    assert artifact.updated_at is None

    with Session(engine) as session:
        db_artifact = session.get(Artifact, artifact.id)
        db_artifact.title = "New Title"
        db_artifact.updated_at = datetime.now(timezone.utc)
        session.add(db_artifact)
        session.commit()
        session.refresh(db_artifact)

        assert db_artifact.title == "New Title"
        assert db_artifact.updated_at is not None
        assert db_artifact.updated_at > created_time


def test_artifact_with_optional_fields_none():
    artifact = Artifact(
        title="Test Article",
        url="https://example.com",
    )
    save_to_db(artifact)

    assert artifact.notes is None
    assert artifact.content_raw is None
    assert artifact.content_summary is None
