from unittest.mock import Mock, create_autospec, patch

import pytest

import src.bookmarker.core.main as core
from src.bookmarker.core.main import (
    FETCHERS,
    ArtifactNotFoundError,
    ContentFetchError,
    ContentSummaryError,
    ContentType,
    fetch_and_store_content,
    fetch_and_store_content_many,
    fetch_content,
    get_or_create_artifact,
    store_content,
    summarize_and_store_content,
    summarize_and_store_content_many,
    summarize_content,
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


def test_fetch_article_content_with_mocked_fetcher(db_repo, add_article, monkeypatch):
    artifact = add_article

    mock_fetcher = create_autospec(FETCHERS[ArtifactTypeEnum.ARTICLE], instance=True)
    mock_fetcher.fetch.return_value = "Test Content"
    mock_class = Mock(return_value=mock_fetcher)

    monkeypatch.setitem(FETCHERS, ArtifactTypeEnum.ARTICLE, mock_class)

    content = fetch_content(db_repo, artifact.id)

    assert content == "Test Content"
    mock_fetcher.fetch.assert_called_once_with(artifact.url)


def test_fetch_content_article_not_found(db_repo):
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 99 not found."):
        fetch_content(db_repo, artifact_id=99)


def test_fetch_content_fetch_error(db_repo, add_article, monkeypatch):
    artifact = add_article
    mock_fetcher = create_autospec(FETCHERS[ArtifactTypeEnum.ARTICLE], instance=True)
    mock_fetcher.fetch.side_effect = ContentFetchError()
    mock_class = Mock(return_value=mock_fetcher)
    monkeypatch.setitem(FETCHERS, ArtifactTypeEnum.ARTICLE, mock_class)

    with pytest.raises(ContentFetchError):
        fetch_content(db_repo, artifact.id)


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


@patch("src.bookmarker.core.main.store_content")
@patch("src.bookmarker.core.main.fetch_content")
def test_fetch_and_store_content(mock_fetch_content, mock_store_content, db_repo):
    mock_fetch_content.return_value = "Test Content"
    mock_artifact = Mock()
    mock_store_content.return_value = mock_artifact

    result = fetch_and_store_content(db_repo, 1)

    mock_fetch_content.assert_called_once_with(db_repo, 1)
    mock_store_content.assert_called_once_with(
        db_repo, 1, "Test Content", content_type=ContentType.RAW
    )
    assert result is mock_artifact


@patch("src.bookmarker.core.main.fetch_and_store_content")
def test_fetch_and_store_content_many(mock_fetch_store, db_repo):
    results = fetch_and_store_content_many(db_repo, [1, 2, 3], max_workers=2)

    assert all(v == "ok" for v in results.values())
    assert set(results.keys()) == {1, 2, 3}
    assert mock_fetch_store.call_count == 3


def test_fetch_and_store_content_many_not_found(monkeypatch, db_repo):
    def mock_fetch_store(repo, artifact_id):
        if artifact_id == 2:
            raise ArtifactNotFoundError
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many(db_repo, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2] == "not_found"
    assert results[3] == "ok"


def test_fetch_and_store_content_many_fetch_error(monkeypatch, db_repo):
    def mock_fetch_store(repo, artifact_id):
        if artifact_id == 2:
            raise ContentFetchError
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many(db_repo, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2] == "fetch_error"
    assert results[3] == "ok"


def test_fetch_and_store_content_many_other_exception(monkeypatch, db_repo):
    def mock_fetch_store(repo, artifact_id):
        if artifact_id == 2:
            raise ValueError("Something happened")
        return None

    monkeypatch.setattr(core, "fetch_and_store_content", mock_fetch_store)

    results = fetch_and_store_content_many(db_repo, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2].startswith("exception:")
    assert results[3] == "ok"


@patch("src.bookmarker.core.main.fetch_and_store_content")
def test_fetch_and_store_content_many_timeout(
    mock_fetch_store, monkeypatch, db_repo, caplog
):
    mock_as_completed = Mock()
    mock_as_completed.side_effect = TimeoutError

    monkeypatch.setattr(core, "as_completed", mock_as_completed)

    with pytest.raises(TimeoutError):
        fetch_and_store_content_many(db_repo, [1, 2, 3])

    assert "Timeout error" in caplog.text


def test_summarize_content(db_repo, add_article, monkeypatch):
    artifact = add_article
    artifact.content_raw = "This is article content."
    monkeypatch.setattr(db_repo, "get", lambda x: artifact)

    mock_summarizer = Mock()
    mock_summarizer.summarize.return_value = "This is a summary."

    result = summarize_content(db_repo, mock_summarizer, artifact.id)

    assert result == "This is a summary."
    mock_summarizer.summarize.assert_called_once_with("This is article content.")


def test_summarize_content_article_not_found(db_repo):
    mock_summarizer = Mock()
    with pytest.raises(ArtifactNotFoundError, match="Artifact with ID 99 not found."):
        summarize_content(db_repo, mock_summarizer, artifact_id=99)
    mock_summarizer.summarize.assert_not_called()


def test_summarize_content_summary_error(db_repo, add_article):
    artifact = add_article
    mock_summarizer = Mock()
    mock_summarizer.summarize.side_effect = ContentSummaryError()

    with pytest.raises(ContentSummaryError):
        summarize_content(db_repo, mock_summarizer, artifact.id)


@patch("src.bookmarker.core.summarizers.get_summarizer")
@patch("src.bookmarker.core.main.store_content")
@patch("src.bookmarker.core.main.summarize_content")
def test_summarize_and_store_content(
    mock_summarize_content, mock_store_content, mock_get_summarizer, db_repo
):
    mock_summarize_content.return_value = "Test Summary"
    mock_artifact = Mock()
    mock_store_content.return_value = mock_artifact

    result = summarize_and_store_content(db_repo, mock_get_summarizer, 1)

    mock_summarize_content.assert_called_once_with(db_repo, mock_get_summarizer, 1)
    mock_store_content.assert_called_once_with(
        db_repo, 1, "Test Summary", content_type=ContentType.SUMMARY
    )
    assert result is mock_artifact


# NEW STUFF BELOW
@patch("src.bookmarker.core.main.summarize_and_store_content")
def test_summarize_and_store_content_many(mock_summarize_store, db_repo):
    mock_summarizer = Mock()
    results = summarize_and_store_content_many(
        db_repo, mock_summarizer, [1, 2, 3], max_workers=2
    )

    assert all(v == "ok" for v in results.values())
    assert set(results.keys()) == {1, 2, 3}
    assert mock_summarize_store.call_count == 3


def test_summarize_and_store_content_many_not_found(monkeypatch, db_repo):
    mock_summarizer = Mock()

    def mock_summarize_store(repo, summarizer, artifact_id):
        if artifact_id == 2:
            raise ArtifactNotFoundError
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many(db_repo, mock_summarizer, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2] == "not_found"
    assert results[3] == "ok"


def test_summarize_and_store_content_many_summarize_error(monkeypatch, db_repo):
    mock_summarizer = Mock()

    def mock_summarize_store(repo, summarizer, artifact_id):
        if artifact_id == 2:
            raise ContentSummaryError
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many(db_repo, mock_summarizer, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2] == "summarize_error"
    assert results[3] == "ok"


def test_summarize_and_store_content_many_other_exception(monkeypatch, db_repo):
    mock_summarizer = Mock()

    def mock_summarize_store(repo, summarizer, artifact_id):
        if artifact_id == 2:
            raise ValueError("Something happened")
        return None

    monkeypatch.setattr(core, "summarize_and_store_content", mock_summarize_store)

    results = summarize_and_store_content_many(db_repo, mock_summarizer, [1, 2, 3])

    assert results[1] == "ok"
    assert results[2].startswith("exception:")
    assert results[3] == "ok"


@patch("src.bookmarker.core.main.summarize_and_store_content")
def test_summarize_and_store_content_many_timeout(
    mock_summarize_store, monkeypatch, db_repo, caplog
):
    mock_summarizer = Mock()
    mock_as_completed = Mock()
    mock_as_completed.side_effect = TimeoutError

    monkeypatch.setattr(core, "as_completed", mock_as_completed)

    with pytest.raises(TimeoutError):
        summarize_and_store_content_many(db_repo, mock_summarizer, [1, 2, 3])

    assert "Timeout error" in caplog.text
