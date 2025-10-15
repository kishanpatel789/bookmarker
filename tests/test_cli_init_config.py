import pytest
from typer.testing import CliRunner

import src.bookmarker.cli.init_config as init_mod
from src.bookmarker.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def use_temp_home(monkeypatch, tmp_path):
    """
    Redirect DEFAULT_PROJECT_HOME and CONFIG_PATH to a temp dir
    so tests don't touch the user's real ~/.bookmarker folder.
    """
    fake_home = tmp_path / ".bookmarker"
    monkeypatch.setattr(init_mod, "DEFAULT_PROJECT_HOME", fake_home)
    monkeypatch.setattr(init_mod, "DEFAULT_DB_PATH", fake_home / "bookmarker.sqlite")
    monkeypatch.setattr(init_mod, "CONFIG_PATH", fake_home / "config.env")
    return fake_home


def test_init_config_creates_new_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(init_mod.Confirm, "ask", lambda *a, **k: True)
    monkeypatch.setattr(
        init_mod.Prompt,
        "ask",
        lambda prompt, **kwargs: {
            "[bold]Enter your OpenAI API key[/]": "fake-key",
            "[bold]Enter your preferred OpenAI model name[/]": "gpt-5-nano",
        }[prompt],
    )

    result = runner.invoke(app, ["init"])

    config_text = (tmp_path / ".bookmarker" / "config.env").read_text()

    assert result.exit_code == 0
    assert "Bookmarker is ready to use" in result.stdout
    assert "DATABASE_URL=sqlite" in config_text
    assert "OPENAI_API_KEY=fake-key" in config_text


def test_init_config_uses_custom_database_url(monkeypatch, tmp_path):
    monkeypatch.setattr(init_mod.Confirm, "ask", lambda *a, **k: False)

    responses = {
        "[bold]Enter your DATABASE_URL[/] (e.g. sqlite:///path/to/db.sqlite or postgres://...)": "postgres://user:pass@localhost/db",
        "[bold]Enter your OpenAI API key[/]": "abc123",
        "[bold]Enter your preferred OpenAI model name[/]": "gpt-4-turbo",
    }
    monkeypatch.setattr(
        init_mod.Prompt, "ask", lambda prompt, **kwargs: responses[prompt]
    )

    result = runner.invoke(app, ["init"])

    config_file = tmp_path / ".bookmarker" / "config.env"
    text = config_file.read_text()

    assert result.exit_code == 0
    assert "postgres://user:pass@localhost/db" in text
    assert "OPENAI_MODEL_NAME=gpt-4-turbo" in text


def test_init_config_reuses_existing_directory(monkeypatch, tmp_path):
    existing = tmp_path / ".bookmarker"
    existing.mkdir()
    (existing / "config.env").write_text("old config\n")

    monkeypatch.setattr(init_mod.Confirm, "ask", lambda *a, **k: True)
    monkeypatch.setattr(
        init_mod.Prompt,
        "ask",
        lambda prompt, **kwargs: {
            "[bold]Enter your OpenAI API key[/]": "new-key",
            "[bold]Enter your preferred OpenAI model name[/]": "gpt-5-nano",
        }[prompt],
    )

    result = runner.invoke(app, ["init"])
    assert "Using existing directory" in result.stdout
    assert result.exit_code == 0
