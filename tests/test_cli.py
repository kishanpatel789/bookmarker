from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from src.bookmarker.cli.main import (
    ContentFetchError,
    ContentSummaryError,
    InvalidContentError,
    app,
)
from src.bookmarker.core.database import DatabaseRepository

runner = CliRunner()


@pytest.fixture(autouse=True)
def db_setup(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    repo = DatabaseRepository(f"sqlite:///{db_path}")
    monkeypatch.setattr("src.bookmarker.cli.main.get_repo", lambda: repo)
    yield repo
    repo._engine.dispose()


@pytest.fixture()
def add_artifact():
    result = runner.invoke(app, ["add", "Test Article", "https://example.com"])
    return result


@pytest.fixture()
def add_another_artifact():
    result = runner.invoke(app, ["add", "Test Article 2", "https://example2.com"])
    return result


def test_add_artifact(add_artifact):
    result = add_artifact

    assert result.exit_code == 0
    assert "Artifact added with ID" in result.output
    assert "Test Article" in result.output
    assert "https://example.com" in result.output


def test_delete_artifact(add_artifact):
    result = runner.invoke(app, ["delete", "1"])

    assert result.exit_code == 0
    assert "Deleted artifact with ID 1." in result.output


def test_delete_artifact_not_found():
    result = runner.invoke(app, ["delete", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


def test_list_artifacts(add_artifact, add_another_artifact):
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Artifacts" in result.output
    assert "Test Article" in result.output
    assert "https://example.com" in result.output
    assert "Test Article 2" in result.output
    assert "https://example2.com" in result.output


def test_list_artifacts_empty():
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No artifacts found." in result.output


@patch("src.bookmarker.services.fetchers.fetch_and_store_content")
def test_fetch_content(mock_fetch_store_func, add_artifact, db_setup):
    result = runner.invoke(app, ["fetch", "1"])

    assert result.exit_code == 0
    assert "Content fetched for artifact ID 1." in result.output
    mock_fetch_store_func.assert_called_once_with(1, repo=db_setup)


def test_fetch_content_not_found():
    result = runner.invoke(app, ["fetch", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


@patch("src.bookmarker.services.fetchers.fetch_and_store_content")
def test_fetch_content_fetch_error(mock_fetch_store_func, add_artifact):
    mock_fetch_store_func.side_effect = ContentFetchError()

    result = runner.invoke(app, ["fetch", "1"])

    assert result.exit_code == 1
    assert "Error fetching content for artifact ID 1." in result.output


@patch("src.bookmarker.services.fetchers.fetch_and_store_content_many")
def test_fetch_content_many(mock_fetch_store_func, add_artifact, db_setup):
    mock_fetch_store_func.return_value = {1: "ok", 2: "ok", 3: "ok"}

    result = runner.invoke(app, ["fetch-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Fetched artifact 1 successfully." in result.output
    assert "Fetched artifact 2 successfully." in result.output
    assert "Fetched artifact 3 successfully." in result.output
    mock_fetch_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.fetchers.fetch_and_store_content_many")
def test_fetch_content_many_not_found(mock_fetch_store_func, add_artifact, db_setup):
    mock_fetch_store_func.return_value = {1: "ok", 2: "not_found", 3: "ok"}

    result = runner.invoke(app, ["fetch-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Fetched artifact 1 successfully." in result.output
    assert "Artifact 2 not found." in result.output
    assert "Fetched artifact 3 successfully." in result.output
    mock_fetch_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.fetchers.fetch_and_store_content_many")
def test_fetch_content_many_error(mock_fetch_store_func, add_artifact, db_setup):
    mock_fetch_store_func.return_value = {
        1: "ok",
        2: "fetch_error",
        3: "exception: other",
    }

    result = runner.invoke(app, ["fetch-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Fetched artifact 1 successfully." in result.output
    assert "Failed to fetch artifact 2: fetch_error" in result.output
    assert "Failed to fetch artifact 3: exception: other" in result.output
    mock_fetch_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.fetchers.fetch_and_store_content_many")
def test_fetch_content_many_timeout(mock_fetch_store_func, add_artifact, db_setup):
    mock_fetch_store_func.side_effect = TimeoutError

    result = runner.invoke(app, ["fetch-many", "1", "2", "3"])

    assert result.exit_code == 1
    assert "Exceeded time limit for bulk fetching." in result.output
    mock_fetch_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.cli.main.generate_panel")
@patch("src.bookmarker.services.summarizers.summarize_and_store_content")
def test_summarize_content(
    mock_summarize_store_func, mock_generate_panel, add_artifact, db_setup
):
    mock_summarize_store_func.return_value = add_artifact
    mock_generate_panel.return_value = "<Panel>"

    result = runner.invoke(app, ["summarize", "1"])

    assert result.exit_code == 0
    assert "Content summarized for artifact ID 1." in result.output
    assert "<Panel>" in result.output
    mock_summarize_store_func.assert_called_once_with(1, repo=db_setup)


def test_summarize_content_not_found():
    result = runner.invoke(app, ["summarize", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


@patch("src.bookmarker.services.summarizers.summarize_and_store_content")
def test_summarize_content_invalid_content_error(
    mock_summarize_store_func, add_artifact, db_setup
):
    mock_summarize_store_func.side_effect = InvalidContentError()

    result = runner.invoke(app, ["summarize", "1"])

    assert result.exit_code == 1
    assert "Artifact with ID 1 has no raw content yet." in result.output
    mock_summarize_store_func.assert_called_once_with(1, repo=db_setup)


@patch("src.bookmarker.services.summarizers.summarize_and_store_content")
def test_summarize_content_summarize_error(
    mock_summarize_store_func, add_artifact, db_setup
):
    mock_summarize_store_func.side_effect = ContentSummaryError()

    result = runner.invoke(app, ["summarize", "1"])

    assert result.exit_code == 1
    assert "Error summarizing content for artifact ID 1." in result.output
    mock_summarize_store_func.assert_called_once_with(1, repo=db_setup)


@patch("src.bookmarker.services.summarizers.summarize_and_store_content_many")
def test_summarize_content_many(mock_summarize_store_func, db_setup):
    mock_summarize_store_func.return_value = {1: "ok", 2: "ok", 3: "ok"}

    result = runner.invoke(app, ["summarize-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Summarized artifact 1 successfully." in result.output
    assert "Summarized artifact 2 successfully." in result.output
    assert "Summarized artifact 3 successfully." in result.output
    mock_summarize_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.summarizers.summarize_and_store_content_many")
def test_summarize_content_many_not_found(mock_summarize_store_func, db_setup):
    mock_summarize_store_func.return_value = {1: "ok", 2: "not_found", 3: "ok"}

    result = runner.invoke(app, ["summarize-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Summarized artifact 1 successfully." in result.output
    assert "Artifact 2 not found." in result.output
    assert "Summarized artifact 3 successfully." in result.output
    mock_summarize_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.summarizers.summarize_and_store_content_many")
def test_summarize_content_many_error(mock_summarize_store_func, db_setup):
    mock_summarize_store_func.return_value = {
        1: "ok",
        2: "summarize_error",
        3: "exception: other",
    }

    result = runner.invoke(app, ["summarize-many", "1", "2", "3"])

    assert result.exit_code == 0
    assert "Summarized artifact 1 successfully." in result.output
    assert "Failed to summarize artifact 2: summarize_error" in result.output
    assert "Failed to summarize artifact 3: exception: other" in result.output
    mock_summarize_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.services.summarizers.summarize_and_store_content_many")
def test_summarize_content_many_timeout(mock_summarize_store_func, db_setup):
    mock_summarize_store_func.return_value = {
        1: "ok",
        2: "summarize_error",
        3: "exception: other",
    }
    mock_summarize_store_func.side_effect = TimeoutError

    result = runner.invoke(app, ["summarize-many", "1", "2", "3"])

    assert result.exit_code == 1
    assert "Exceeded time limit for bulk summarizing." in result.output
    mock_summarize_store_func.assert_called_once_with([1, 2, 3], repo=db_setup)


@patch("src.bookmarker.cli.main.get_repo")
def test_show_artifact(mock_get_repo):
    mock_artifact = MagicMock(
        id=1,
        title="Test Article",
        url="https://example.com",
        content_raw="Test content",
        content_summary="Test summary.",
    )
    mock_repo = Mock()
    mock_repo.get.return_value = mock_artifact
    mock_get_repo.return_value = mock_repo

    result = runner.invoke(app, ["show", "1"])

    assert result.exit_code == 0
    assert "Test Article" in result.output
    assert "https://example" in result.output
    assert "Test summary" in result.output
    assert "Test content" not in result.output


def test_show_artifact_not_fetched(add_artifact):
    result = runner.invoke(app, ["show", "1"])

    assert result.exit_code == 0
    assert "Content has not been fetched yet." in result.output
    assert "`bookmarker fetch 1`" in result.output
    assert "`bookmarker summarize 1`" in result.output


@patch("src.bookmarker.cli.main.get_repo")
def test_show_artifact_not_summarized(mock_get_repo):
    mock_artifact = MagicMock(
        id=1,
        title="Test Article",
        url="https://example.com",
        content_raw="Test content",
        content_summary=None,
    )
    mock_repo = Mock()
    mock_repo.get.return_value = mock_artifact
    mock_get_repo.return_value = mock_repo

    result = runner.invoke(app, ["show", "1"])

    assert result.exit_code == 0
    assert "No summary yet" in result.output
    assert "`bookmarker summarize 1`" in result.output


def test_show_artifact_not_found():
    result = runner.invoke(app, ["show", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


@patch("src.bookmarker.cli.main.generate_panel")
@patch("src.bookmarker.cli.main.update_tags")
@patch("src.bookmarker.cli.main.get_repo")
def test_tag_artifact(mock_get_repo, mock_update_tags, mock_generate_panel):
    mock_artifact = MagicMock(id=1)
    mock_repo = Mock()
    mock_repo.get.return_value = mock_artifact
    mock_get_repo.return_value = mock_repo
    mock_generate_panel.return_value = "<Panel>"

    result = runner.invoke(app, ["tag", "1", "python", "cloud"])

    assert result.exit_code == 0
    assert "Updated tags successfully for artifact 1." in result.output
    assert "<Panel>" in result.output
    mock_update_tags.assert_called_once_with(
        mock_repo, 1, ["python", "cloud"], remove=False
    )


def test_tag_artifact_not_found():
    result = runner.invoke(app, ["tag", "99", "python"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output
