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


@app.command()
def init_db():
    """Initializes the database."""
    repo = get_repo()
    repo.create_db_and_tables()
    typer.echo("Database initialized.")


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
def add(
    ctx: typer.Context,
    title: str,
    url: str,
    artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE,
):
    """Adds an artifact with a title and URL."""
    repo = ctx.obj.repo
    artifact = get_or_create_artifact(
        repo, title=title, url=url, artifact_type=artifact_type
    )

    print(f"Artifact added: {artifact.title} - {artifact.url}")


@app.command()
def list(ctx: typer.Context):
    """Lists all artifacts."""
    repo = ctx.obj.repo
    artifacts = repo.list()
    if artifacts:
        table = Table("Title", "URL", title="Artifacts")
        for artifact in artifacts:
            table.add_row(artifact.title, artifact.url)
        ctx.obj.console.print(table)
    else:
        ctx.obj.error_console.print("No artifacts found.")
