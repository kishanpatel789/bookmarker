from unittest.mock import Mock, patch

import pytest

import src.bookmarker.services.summarizers as core
from src.bookmarker.services.base import get_or_create_artifact
from src.bookmarker.services.summarizers import (
    ArtifactNotFoundError,
    ContentSummaryError,
    ContentSummaryExistsWarning,
    ContentType,
    summarize_and_store_content,
    summarize_and_store_content_many,
    summarize_content,
)


@pytest.fixture
def add_article(db_repo):
    artifact = get_or_create_artifact(
        db_repo,
        title="Test Article",
        url="https://example.com",
    )

    return artifact


def test_summarize_content(db_repo, add_article, monkeypatch):
    artifact = add_article
    artifact.content_raw = "This is article content."
    monkeypatch.setattr(db_repo, "get", lambda x: artifact)

    mock_summarizer = Mock()
    mock_summarizer.summarize.return_value = "This is a summary."

    result = summarize_content(artifact.id, repo=db_repo, summarizer=mock_summarizer)

    assert result == "This is a summary."
    mock_summarizer.summarize.assert_called_once_with("This is article content.")


def test_summarize_content_article_not_found(db_repo):
    mock_summarizer = Mock()
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 99 not found."):
        summarize_content(99, repo=db_repo, summarizer=mock_summarizer)
    mock_summarizer.summarize.assert_not_called()


def test_summarize_content_summary_exists():
    mock_repo = Mock()
    mock_artifact = Mock(
        id=1,
        content_raw="This is article content.",
        content_summary="This is a summary.",
    )
    mock_repo.get.return_value = mock_artifact
    mock_summarizer = Mock()

    with pytest.raises(ContentSummaryExistsWarning):
        summarize_content(1, repo=mock_repo, summarizer=mock_summarizer, refresh=False)


def test_summarize_content_summary_error(db_repo, add_article):
    artifact = add_article
    mock_summarizer = Mock()
    mock_summarizer.summarize.side_effect = ContentSummaryError()

    with pytest.raises(ContentSummaryError):
        summarize_content(artifact.id, repo=db_repo, summarizer=mock_summarizer)


@patch("src.bookmarker.services.summarizers.get_summarizer")
@patch("src.bookmarker.services.summarizers.store_content")
@patch("src.bookmarker.services.summarizers.summarize_content")
def test_summarize_and_store_content(
    mock_summarize_content, mock_store_content, mock_get_summarizer, db_repo
):
    mock_summarize_content.return_value = "Test Summary"
    mock_artifact = Mock()
    mock_store_content.return_value = mock_artifact

    result = summarize_and_store_content(
        1, repo=db_repo, summarizer=mock_get_summarizer
    )

    mock_summarize_content.assert_called_once_with(
        1, repo=db_repo, summarizer=mock_get_summarizer, refresh=False
    )
    mock_store_content.assert_called_once_with(
        db_repo, 1, "Test Summary", content_type=ContentType.SUMMARY
    )
    assert result is mock_artifact


@patch("src.bookmarker.services.summarizers.summarize_and_store_content")
def test_summarize_and_store_content_many(mock_summarize_store, db_repo):
    results = summarize_and_store_content_many([1, 2, 3], repo=db_repo, max_workers=2)

    assert all(v == "ok" for v in results.values())
    assert set(results.keys()) == {1, 2, 3}
    assert mock_summarize_store.call_count == 3


def test_summarize_and_store_content_many_not_found(monkeypatch, db_repo):
    def mock_summarize_store(artifact_id, repo, summarizer):
        if artifact_id == 2:
            raise ArtifactNotFoundError
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2] == "not_found"
    assert results[3] == "ok"


def test_summarize_and_store_content_many_summarize_error(monkeypatch, db_repo):
    def mock_summarize_store(artifact_id, repo, summarizer):
        if artifact_id == 2:
            raise ContentSummaryError
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2] == "summarize_error"
    assert results[3] == "ok"


def test_summarize_and_store_content_many_other_exception(monkeypatch, db_repo):
    def mock_summarize_store(artifact_id, repo, summarizer):
        if artifact_id == 2:
            raise ValueError("Something happened")
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many([1, 2, 3], repo=db_repo)

    assert results[1] == "ok"
    assert results[2].startswith("exception:")
    assert results[3] == "ok"


@patch("src.bookmarker.services.summarizers.summarize_and_store_content")
def test_summarize_and_store_content_many_timeout(
    mock_summarize_store, monkeypatch, db_repo, caplog
):
    mock_as_completed = Mock()
    mock_as_completed.side_effect = TimeoutError

    monkeypatch.setattr(core, "as_completed", mock_as_completed)

    with pytest.raises(TimeoutError):
        summarize_and_store_content_many([1, 2, 3], repo=db_repo)

    assert "Timeout error" in caplog.text
