from typing import NamedTuple

import typer
from rich.console import Console
from rich.table import Table

from ..core.database import DatabaseRepository, get_repo
from ..core.main import ArtifactTypeEnum, get_or_create_artifact

app = typer.Typer()


class AppConfig(NamedTuple):
    repo: DatabaseRepository
    console: Console
    error_console: Console


def get_config(ctx: typer.Context) -> AppConfig:
    return ctx.obj


@app.callback()
def init(ctx: typer.Context):
    repo = get_repo()
    app_config = AppConfig(
        repo=repo,
        console=Console(),
        error_console=Console(stderr=True, style="bold red"),
    )
    ctx.obj = app_config


@app.command()
def init_db(ctx: typer.Context):
    """Initializes the database."""
    config = get_config(ctx)
    try:
        config.repo.create_db_and_tables()
        config.console.print("[green]Database initialized.[/]")
    except Exception as e:
        config.error_console.print(f"Error initializing DB: {e}")


@app.command(name="add")
def add_artifacts(
    ctx: typer.Context,
    title: str,
    url: str,
    artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE,
):
    """Adds an artifact with a title and URL."""
    config = get_config(ctx)
    artifact = get_or_create_artifact(
        config.repo, title=title, url=url, artifact_type=artifact_type
    )
    config.console.print(f"[green]Artifact added:[/] {artifact.title} - {artifact.url}")


@app.command(name="list")
def list_artifacts(ctx: typer.Context):
    """Lists all artifacts."""
    config = get_config(ctx)
    artifacts = config.repo.list()
    if artifacts:
        table = Table("Title", "URL", title="Artifacts")
        for artifact in artifacts:
            table.add_row(artifact.title, artifact.url)
        ctx.obj.console.print(table)
    else:
        ctx.obj.error_console.print("No artifacts found.")
