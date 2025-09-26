from unittest.mock import Mock, create_autospec, patch

import pytest

from src.bookmarker.core.exceptions import ArtifactNotFoundError
from src.bookmarker.core.main import (
    FETCHERS,
    get_and_store_content,
    get_content,
    get_or_create_artifact,
    store_content,
)
from src.bookmarker.core.models import ArtifactTypeEnum


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


def test_get_article_content_with_mocked_fetcher(db_repo, add_article, monkeypatch):
    artifact = add_article

    mock_fetcher = create_autospec(FETCHERS[ArtifactTypeEnum.ARTICLE], instance=True)
    mock_fetcher.fetch.return_value = "Test Content"
    mock_class = Mock(return_value=mock_fetcher)

    monkeypatch.setitem(FETCHERS, ArtifactTypeEnum.ARTICLE, mock_class)

    content = get_content(db_repo, artifact.id)

    assert content == "Test Content"
    mock_fetcher.fetch.assert_called_once_with(artifact.url)


def test_get_content_article_not_found(db_repo):
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 99 not found."):
        get_content(db_repo, artifact_id=99)


def test_store_content(db_repo, add_article):
    artifact = add_article
    updated_artifact = store_content(db_repo, artifact.id, "#Test header")

    assert updated_artifact.id == artifact.id
    assert updated_artifact.content_raw == "#Test header"


@patch("src.bookmarker.core.main.store_content")
@patch("src.bookmarker.core.main.get_content")
def test_get_and_store_content(mock_get_content, mock_store_content, db_repo):
    mock_get_content.return_value = "Test Content"
    mock_artifact = Mock()
    mock_store_content.return_value = mock_artifact

    result = get_and_store_content(db_repo, 1)

    mock_get_content.assert_called_once_with(db_repo, 1)
    mock_store_content.assert_called_once_with(
        db_repo, 1, "Test Content", content_type="raw"
    )
    assert result is mock_artifact
