from unittest.mock import Mock, create_autospec, patch

import pytest

import src.bookmarker.services.fetchers as core
from src.bookmarker.core.models import ArtifactTypeEnum
from src.bookmarker.services.base import get_or_create_artifact
from src.bookmarker.services.fetchers import (
    FETCHERS,
    ArtifactNotFoundError,
    ContentFetchError,
    ContentType,
    fetch_and_store_content,
    fetch_and_store_content_many,
    fetch_content,
)


@pytest.fixture
def add_article(db_repo):
    artifact = get_or_create_artifact(
        db_repo,
        title="Test Article",
        url="https://example.com",
    )

    return artifact


def test_fetch_article_content_with_mocked_fetcher(db_repo, add_article, monkeypatch):
    artifact = add_article

    mock_fetcher = create_autospec(FETCHERS[ArtifactTypeEnum.ARTICLE], instance=True)
    mock_fetcher.fetch.return_value = "Test Content"
    mock_class = Mock(return_value=mock_fetcher)

    monkeypatch.setitem(FETCHERS, ArtifactTypeEnum.ARTICLE, mock_class)

    content = fetch_content(artifact.id, repo=db_repo)

    assert content == "Test Content"
    mock_fetcher.fetch.assert_called_once_with(artifact.url)


def test_fetch_content_article_not_found(db_repo):
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 99 not found."):
        fetch_content(99, repo=db_repo)


def test_fetch_content_fetch_error(db_repo, add_article, monkeypatch):
    artifact = add_article
    mock_fetcher = create_autospec(FETCHERS[ArtifactTypeEnum.ARTICLE], instance=True)
    mock_fetcher.fetch.side_effect = ContentFetchError()
    mock_class = Mock(return_value=mock_fetcher)
    monkeypatch.setitem(FETCHERS, ArtifactTypeEnum.ARTICLE, mock_class)

    with pytest.raises(ContentFetchError):
        fetch_content(artifact.id, repo=db_repo)


@patch("src.bookmarker.services.fetchers.store_content")
@patch("src.bookmarker.services.fetchers.fetch_content")
def test_fetch_and_store_content(mock_fetch_content, mock_store_content, db_repo):
    mock_fetch_content.return_value = "Test Content"
    mock_artifact = Mock()
    mock_store_content.return_value = mock_artifact

    result = fetch_and_store_content(1, repo=db_repo)

    mock_fetch_content.assert_called_once_with(1, repo=db_repo)
    mock_store_content.assert_called_once_with(
        db_repo, 1, "Test Content", content_type=ContentType.RAW
    )
    assert result is mock_artifact


@patch("src.bookmarker.services.fetchers.fetch_and_store_content")
def test_fetch_and_store_content_many(mock_fetch_store, db_repo):
    results = fetch_and_store_content_many([1, 2, 3], repo=db_repo, max_workers=2)

    assert all(v == "ok" for v in results.values())
    assert set(results.keys()) == {1, 2, 3}
    assert mock_fetch_store.call_count == 3


def test_fetch_and_store_content_many_not_found(monkeypatch, db_repo):
    def mock_fetch_store(artifact_id, repo):
        if artifact_id == 2:
            raise ArtifactNotFoundError
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2] == "not_found"
    assert results[3] == "ok"


def test_fetch_and_store_content_many_fetch_error(monkeypatch, db_repo):
    def mock_fetch_store(artifact_id, repo):
        if artifact_id == 2:
            raise ContentFetchError
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2] == "fetch_error"
    assert results[3] == "ok"


def test_fetch_and_store_content_many_other_exception(monkeypatch, db_repo):
    def mock_fetch_store(artifact_id, repo):
        if artifact_id == 2:
            raise ValueError("Something happened")
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2].startswith("exception:")
    assert results[3] == "ok"


@patch("src.bookmarker.services.fetchers.fetch_and_store_content")
def test_fetch_and_store_content_many_timeout(
    mock_fetch_store, monkeypatch, db_repo, caplog
):
    mock_as_completed = Mock()
    mock_as_completed.side_effect = TimeoutError

    monkeypatch.setattr(core, "as_completed", mock_as_completed)

    with pytest.raises(TimeoutError):
        fetch_and_store_content_many([1, 2, 3], repo=db_repo)

    assert "Timeout error" in caplog.text
