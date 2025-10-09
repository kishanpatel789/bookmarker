from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.exceptions import (
    ArtifactNotFoundError,
    ContentFetchError,
)
from .helpers import get_config

app = typer.Typer()


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
