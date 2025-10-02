from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.bookmarker.cli.main import ContentFetchError, app
from src.bookmarker.core.database import DatabaseRepository

runner = CliRunner()


@pytest.fixture(autouse=True)
def db_setup(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    repo = DatabaseRepository(f"sqlite:///{db_path}")
    monkeypatch.setattr("src.bookmarker.cli.main.get_repo", lambda: repo)
    yield
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


@patch("src.bookmarker.core.main.fetch_and_store_content")
def test_fetch_content(mock_fetch_store_func, add_artifact):
    result = runner.invoke(app, ["fetch", "1"])

    assert result.exit_code == 0
    assert "Content fetched for artifact ID 1." in result.output


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
