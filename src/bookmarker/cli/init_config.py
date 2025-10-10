from pathlib import Path

import typer

DEFAULT_PROJECT_HOME = Path.home() / ".bookmarker"
DEFAULT_DB_PATH = DEFAULT_PROJECT_HOME / "bookmarker.sqlite"
CONFIG_PATH = DEFAULT_PROJECT_HOME / "config.env"

app = typer.Typer(help="Initialize Bookmarker configuration")


@app.command(name="init")
def init_config():
    """Initialize local configuration"""
    print("TODO: Implement local config setup")
