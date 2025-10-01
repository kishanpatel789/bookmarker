import pytest
from typer.testing import CliRunner

from src.bookmarker.cli.main import app
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


# def test_init_db():
# result = runner.invoke(app, ["init-db"])
# assert result.exit_code == 0
# assert "Database initialized." in result.output


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
