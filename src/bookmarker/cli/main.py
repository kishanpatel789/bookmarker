from typing import Annotated, NamedTuple

import typer
from rich.console import Console, Group
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
from ..core.models import Artifact
from ..services.base import (
    ArtifactTypeEnum,
    get_or_create_artifact,
    update_tags,
)

app = typer.Typer()


class AppConfig(NamedTuple):
    repo: DatabaseRepository
    console: Console
    error_console: Console


def get_config(ctx: typer.Context) -> AppConfig:
    return ctx.obj


def generate_panel(artifact: Artifact) -> Panel:
    """Generate a rich panel for displaying a artifact."""

    title_text = Text(artifact.title, style="bold")

    body_elements = []
    if len(artifact.tags) > 0:
        body_elements.append(
            Text(
                " ".join(f"#{tag.name}" for tag in artifact.tags),
                style="dim",
                justify="center",
            )
        )

    if artifact.content_summary is None:
        if artifact.content_raw is None:
            summary = (
                "Content has not been fetched yet.\n"
                f"Run `bookmarker fetch {artifact.id}`.\n"
                f"Then run `bookmarker summarize {artifact.id}`."
            )
        else:
            summary = f"No summary yet. Run `bookmarker summarize {artifact.id}`"
    else:
        summary = escape(artifact.content_summary)
    summary_text = Text(summary, justify="left")
    summary_padding = Padding(summary_text, (1, 2))
    body_elements.append(summary_padding)

    body = Group(*body_elements)

    panel = Panel.fit(
        body,
        title=title_text,
        subtitle=artifact.url,
        subtitle_align="right",
        border_style="cyan",
    )

    return panel


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
def add_artifact(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="The name of the artifact")],
    url: Annotated[str, typer.Argument(help="The URL of the artifact")],
    artifact_type: Annotated[
        ArtifactTypeEnum, typer.Option(help="The type of the artifact")
    ] = ArtifactTypeEnum.ARTICLE,
):
    """Add an artifact with a title and URL."""
    config = get_config(ctx)
    artifact = get_or_create_artifact(
        config.repo, title=title, url=url, artifact_type=artifact_type
    )
    config.console.print(
        f"[green]Artifact added with ID {artifact.id}:[/] {artifact.title} - {artifact.url}"
    )


@app.command(name="delete")
def delete_artifact(
    ctx: typer.Context,
    artifact_id: Annotated[
        int, typer.Argument(help="The ID of the artifact to delete")
    ],
):
    """Delete an artifact."""
    config = get_config(ctx)
    try:
        config.repo.delete(artifact_id)
        config.console.print(f"[green]Deleted artifact with ID {artifact_id}.[/]")
    except ArtifactNotFoundError:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_artifacts(ctx: typer.Context):
    """List all artifacts."""
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
def fetch_content(
    ctx: typer.Context,
    artifact_id: Annotated[
        int, typer.Argument(help="The ID of the artifact content to fetch")
    ],
):
    """Fetch content for the specified artifact ID."""
    from ..services.fetchers import fetch_and_store_content

    config = get_config(ctx)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Fetching...", total=None)
            fetch_and_store_content(artifact_id, repo=config.repo)
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


@app.command(name="fetch-many")
def fetch_content_many(
    ctx: typer.Context,
    artifact_ids: Annotated[
        list[int],
        typer.Argument(help="The IDs of the artifact content to fetch (e.g. `1 2 3`)"),
    ],
):
    """Fetch multiple artifacts concurrently."""
    from ..services.fetchers import fetch_and_store_content_many

    config = get_config(ctx)
    bulk_fetch_timed_out = False
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(
            "Fetching multiple artifacts...", total=len(artifact_ids)
        )
        try:
            results = fetch_and_store_content_many(artifact_ids, repo=config.repo)
        except TimeoutError:
            bulk_fetch_timed_out = True
        finally:
            progress.update(task, completed=len(artifact_ids))

    # throw console error outside progress context manager for cleaner output
    if bulk_fetch_timed_out:
        config.error_console.print(
            "[red]Exceeded time limit for bulk fetching. Try fetching fewer artifacts.[/]"
        )
        raise typer.Exit(code=1)

    for aid, status in results.items():
        if status == "ok":
            config.console.print(f"[green]Fetched artifact {aid} successfully.[/]")
        elif status == "not_found":
            config.error_console.print(f"[red]Artifact {aid} not found.[/]")
        else:
            config.error_console.print(
                f"[red]Failed to fetch artifact {aid}: {status}[/]"
            )


@app.command(name="summarize")
def summarize_content(
    ctx: typer.Context,
    artifact_id: Annotated[
        int, typer.Argument(help="The ID of the artifact content to summarize")
    ],
):
    """Summarize content for the specified artifact ID."""
    from ..services.summarizers import summarize_and_store_content

    config = get_config(ctx)
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Summarizing...", total=None)
            artifact = summarize_and_store_content(artifact_id, repo=config.repo)
        config.console.print(
            f"[green]Content summarized for artifact ID {artifact_id}.[/]"
        )
        if artifact is not None:
            panel = generate_panel(artifact)
            config.console.print(panel)
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


@app.command(name="summarize-many")
def summarize_content_many(
    ctx: typer.Context,
    artifact_ids: Annotated[
        list[int],
        typer.Argument(
            help="The IDs of the artifact content to summarize (e.g. `1 2 3`)"
        ),
    ],
):
    """Summarize multiple artifacts concurrently."""
    from ..services.summarizers import summarize_and_store_content_many

    config = get_config(ctx)
    bulk_summarize_timed_out = False
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(
            "Summarizing multiple artifacts...", total=len(artifact_ids)
        )
        try:
            results = summarize_and_store_content_many(artifact_ids, repo=config.repo)
        except TimeoutError:
            bulk_summarize_timed_out = True
        finally:
            progress.update(task, completed=len(artifact_ids))

    # throw console error outside progress context manager for cleaner output
    if bulk_summarize_timed_out:
        config.error_console.print(
            "[red]Exceeded time limit for bulk summarizing. Try summarizing fewer artifacts.[/]"
        )
        raise typer.Exit(code=1)

    for aid, status in results.items():
        if status == "ok":
            config.console.print(f"[green]Summarized artifact {aid} successfully.[/]")
        elif status == "not_found":
            config.error_console.print(f"[red]Artifact {aid} not found.[/]")
        else:
            config.error_console.print(
                f"[red]Failed to summarize artifact {aid}: {status}[/]"
            )


@app.command(name="show")
def show_artifact(
    ctx: typer.Context,
    artifact_id: Annotated[int, typer.Argument(help="The ID of the artifact to show")],
):
    """Show details for the specified artifact ID."""
    config = get_config(ctx)
    artifact = config.repo.get(artifact_id)
    if artifact is None:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)

    panel = generate_panel(artifact)
    config.console.print(panel)


@app.command(name="tag")
def tag_artifact(
    ctx: typer.Context,
    artifact_id: Annotated[int, typer.Argument(help="The ID of artifact to update")],
    tags: Annotated[list[str], typer.Argument(help="Tags to add or remove")],
    remove: Annotated[
        bool, typer.Option("--remove", help="Remove tag instead of adding")
    ] = False,
):
    """Add or remove tags from an artifact."""
    config = get_config(ctx)
    try:
        artifact = update_tags(config.repo, artifact_id, tags, remove=remove)
        config.console.print(
            f"[green]Updated tags successfully for artifact {artifact_id}.[/]"
        )
        panel = generate_panel(artifact)
        config.console.print(panel)
    except ArtifactNotFoundError:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)
