from typing import NamedTuple

import typer
from rich.console import Console
from rich.table import Table

from ..core.main import (
    ArtifactNotFoundError,
    ArtifactTypeEnum,
    ContentFetchError,
    DatabaseRepository,
    fetch_and_store_content,
    get_or_create_artifact,
    get_repo,
)

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
    repo.create_db_and_tables()
    app_config = AppConfig(
        repo=repo,
        console=Console(),
        error_console=Console(stderr=True, style="bold red"),
    )
    ctx.obj = app_config


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
        table = Table(title="Artifacts")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Type")
        table.add_column("Fetched", justify="center")
        table.add_column("Summarized", justify="center")
        table.add_column("URL")
        for artifact in artifacts:
            table.add_row(
                str(artifact.id),
                artifact.title,
                artifact.artifact_type.value,
                ":white_heavy_check_mark:" if artifact.content_raw else ":x:",
                ":white_heavy_check_mark:" if artifact.content_summary else ":x:",
                artifact.url,
            )
        ctx.obj.console.print(table)
    else:
        ctx.obj.error_console.print("No artifacts found.")


@app.command()
def fetch(ctx: typer.Context, artifact_id: int):
    """Fetches content for the specified artifact ID."""
    config = get_config(ctx)
    try:
        fetch_and_store_content(config.repo, artifact_id)
        config.console.print(
            f"[green]Content fetched for artifact ID {artifact_id}.[/]"
        )
    except ArtifactNotFoundError:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)
    except ContentFetchError:
        config.error_console.print(
            f"Error fetching content for artifact ID {artifact_id}."
        )
        raise typer.Exit(code=1)
