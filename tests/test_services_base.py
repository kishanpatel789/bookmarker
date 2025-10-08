from unittest.mock import Mock

import pytest

from src.bookmarker.services.base import (
    ContentType,
    Tag,
    get_or_create_artifact,
    store_content,
    update_tags,
)


@pytest.fixture
def add_article(db_repo):
    artifact = get_or_create_artifact(
        db_repo,
        title="Test Article",
        url="https://example.com",
    )

    return artifact


def test_add_artifact(db_repo, add_article):
    artifact = add_article

    assert artifact.id is not None
    assert artifact.title == "Test Article"
    assert artifact.url == "https://example.com"
    assert artifact.artifact_type.name == "ARTICLE"


def test_add_existing_artifact(db_repo, add_article):
    artifact1 = add_article
    artifact2 = get_or_create_artifact(
        db_repo, title="Test Article Duplicate", url="https://example.com"
    )

    assert artifact1.id == artifact2.id
    assert artifact2.title == "Test Article"
    assert len(db_repo.list()) == 1


def test_store_content_raw(db_repo, add_article):
    artifact = add_article
    updated_artifact = store_content(db_repo, artifact.id, "#Test header")

    assert updated_artifact.id == artifact.id
    assert updated_artifact.content_raw == "#Test header"


def test_store_content_summary(db_repo, add_article):
    artifact = add_article
    updated_artifact = store_content(
        db_repo, artifact.id, "Test summary", content_type=ContentType.SUMMARY
    )

    assert updated_artifact.id == artifact.id
    assert updated_artifact.content_summary == "Test summary"


def test_store_content_bad_type(db_repo, add_article):
    artifact = add_article

    with pytest.raises(ValueError):
        store_content(db_repo, artifact.id, "Test summary", content_type="bad type")


def test_update_tags_adds_tags():
    mock_repo = Mock()
    mock_artifact = Mock(id=1, tags=["python", "ai"])
    mock_repo.tag.return_value = mock_artifact

    tags = ["python", "ai"]
    result = update_tags(mock_repo, 1, tags, remove=False)

    assert result == mock_artifact
    mock_repo.tag.assert_called_once()
    called_args, called_kwargs = mock_repo.tag.call_args
    assert called_args[0] == 1
    assert all(isinstance(t, Tag) for t in called_args[1:])
    assert called_kwargs["remove"] is False
