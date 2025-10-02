from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from src.bookmarker.cli.main import (
    ContentFetchError,
    ContentSummaryError,
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
    assert "Artifact added:" in result.output
    assert "Test Article" in result.output
    assert "https://example.com" in result.output


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


@patch("src.bookmarker.cli.main.fetch_and_store_content")
def test_fetch_content(mock_fetch_store_func, add_artifact, db_setup):
    result = runner.invoke(app, ["fetch", "1"])

    assert result.exit_code == 0
    assert "Content fetched for artifact ID 1." in result.output
    mock_fetch_store_func.assert_called_once_with(db_setup, 1)


def test_fetch_content_not_found():
    result = runner.invoke(app, ["fetch", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


@patch("src.bookmarker.cli.main.fetch_and_store_content")
def test_fetch_content_fetch_error(mock_fetch_store_func, add_artifact):
    mock_fetch_store_func.side_effect = ContentFetchError()

    result = runner.invoke(app, ["fetch", "1"])

    assert result.exit_code == 1
    assert "Error fetching content for artifact ID 1." in result.output


@patch("src.bookmarker.cli.main.get_summarizer")
@patch("src.bookmarker.cli.main.summarize_and_store_content")
def test_summarize_content(
    mock_summarize_store_func, mock_get_summarizer, add_artifact, db_setup
):
    mock_summarizer = Mock()
    mock_get_summarizer.return_value = mock_summarizer
    result = runner.invoke(app, ["summarize", "1"])

    assert result.exit_code == 0
    assert "Content summarized for artifact ID 1." in result.output
    mock_summarize_store_func.assert_called_once_with(db_setup, mock_summarizer, 1)


def test_summarize_content_not_found():
    result = runner.invoke(app, ["summarize", "99"])

    assert result.exit_code == 1
    assert "Artifact with ID 99 not found." in result.output


@patch("src.bookmarker.cli.main.get_summarizer")
@patch("src.bookmarker.cli.main.summarize_and_store_content")
def test_summarize_content_summarize_error(
    mock_summarize_store_func, mock_get_summarizer, add_artifact, db_setup
):
    mock_summarize_store_func.side_effect = ContentSummaryError()
    mock_summarizer = Mock()
    mock_get_summarizer.return_value = mock_summarizer

    result = runner.invoke(app, ["summarize", "1"])

    assert result.exit_code == 1
    assert "Error summarizing content for artifact ID 1." in result.output
    mock_summarize_store_func.assert_called_once_with(db_setup, mock_summarizer, 1)
