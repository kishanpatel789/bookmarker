import pytest

from src.bookmarker.core.exceptions import ArtifactNotFoundError
from src.bookmarker.core.models import Artifact, ArtifactTypeEnum, Tag


@pytest.fixture
def add_article(db_repo):
    tag_python = Tag(name="python")
    tag_cloud = Tag(name="cloud")
    artifact = Artifact(
        title="Test Article",
        url="https://example.com",
        notes="This seems interesting",
        tags=[tag_python, tag_cloud],
    )
    db_repo.add(artifact)

    return artifact


@pytest.fixture
def add_another_article(db_repo):
    artifact = Artifact(
        title="Test Article 2",
        url="https://test2.example.com",
        notes="This seems interesting",
    )
    db_repo.add(artifact)

    return artifact


def test_add_artifact(add_article):
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


def test_list_artifacts(db_repo, add_article, add_another_article):
    artifacts = db_repo.list()

    assert len(artifacts) == 2
    assert any(a.id == add_article.id for a in artifacts)


def test_get_artifact(db_repo, add_article, add_another_article):
    artifact = db_repo.get(1)

    assert artifact is not None
    assert artifact.id == add_article.id
    assert artifact.url == add_article.url


def test_get_artifact_not_found(db_repo, add_article, add_another_article):
    artifact = db_repo.get(99)

    assert artifact is None


def test_get_artifact_by_url(db_repo, add_article, add_another_article):
    artifact = db_repo.get_by_url(add_article.url)

    assert artifact is not None
    assert artifact.id == add_article.id
    assert artifact.url == add_article.url


def test_get_artifact_by_url_not_found(db_repo, add_article, add_another_article):
    artifact = db_repo.get_by_url("https://doesnotexist.com")

    assert artifact is None


def test_delete_artifact(db_repo, add_article):
    db_repo.delete(add_article.id)
    artifact = db_repo.get(add_article.id)

    assert artifact is None


def test_delete_artifact_not_found(db_repo):
    with pytest.raises(ArtifactNotFoundError):
        db_repo.delete(99)


def test_store_content_raw(db_repo, add_article):
    artifact = db_repo.store_content_raw(add_article.id, "#Test header")

    assert artifact.id == 1
    assert artifact.content_raw == "#Test header"


def test_store_content_raw_not_found(db_repo, add_article):
    with pytest.raises(ArtifactNotFoundError):
        db_repo.store_content_raw(99, "#Test header")
