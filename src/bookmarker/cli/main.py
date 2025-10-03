from typing import NamedTuple

import typer
from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ..core.database import DatabaseRepository, get_repo
from ..core.exceptions import (
    ArtifactNotFoundError,
    ContentFetchError,
    ContentSummaryError,
    InvalidContentError,
)
from ..core.main import (
    ArtifactTypeEnum,
    fetch_and_store_content,
    get_or_create_artifact,
    summarize_and_store_content,
)
from ..core.summarizers import get_summarizer

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
    config.console.print(
        f"[green]Artifact added with ID {artifact.id}:[/] {artifact.title} - {artifact.url}"
    )


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


@app.command(name="fetch")
def fetch_content(ctx: typer.Context, artifact_id: int):
    """Fetches content for the specified artifact ID."""
    config = get_config(ctx)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Fetching...", total=None)
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


@app.command(name="summarize")
def summarize_content(ctx: typer.Context, artifact_id: int):
    """Fetches content for the specified artifact ID."""
    config = get_config(ctx)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Summarizing...", total=None)
            summarizer = get_summarizer()
            summarize_and_store_content(config.repo, summarizer, artifact_id)
        config.console.print(
            f"[green]Content summarized for artifact ID {artifact_id}.[/]"
        )
    except ArtifactNotFoundError:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)
    except InvalidContentError:
        config.error_console.print(
            f"Artifact with ID {artifact_id} has no raw content yet.\n"
            f"Run `bookmarker fetch {artifact_id}` first."
        )
        raise typer.Exit(code=1)
    except ContentSummaryError:
        config.error_console.print(
            f"Error summarizing content for artifact ID {artifact_id}."
        )
        raise typer.Exit(code=1)


@app.command(name="show")
def show_artifact(ctx: typer.Context, artifact_id: int):
    """Show details for the specified artifact ID."""
    config = get_config(ctx)
    artifact = config.repo.get(artifact_id)
    if artifact is None:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)
    if artifact.content_raw is None and artifact.content_summary is None:
        summary = (
            "Content has not been fetched yet.\n"
            f"Run `bookmarker fetch {artifact.id}`.\n"
            f"Then run `bookmarker summarize {artifact.id}`."
        )
    elif artifact.content_summary is None:
        summary = f"No summary yet. Run `bookmarker summarize {artifact.id}`"
    else:
        summary = escape(artifact.content_summary)
    text = Text(summary, justify="left")
    body = Padding(text, (1, 2))
    panel = Panel.fit(
        body,
        title=f"[bold]{artifact.title}[/]",
        subtitle=artifact.url,
        subtitle_align="right",
        border_style="cyan",
    )
    config.console.print(panel)
