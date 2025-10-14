from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.exceptions import (
    ArtifactNotFoundError,
    ContentSummaryError,
    ContentSummaryExistsWarning,
    InvalidAPIKeyError,
    InvalidContentError,
)
from .helpers import generate_panel, get_config

app = typer.Typer()


@app.command(name="summarize")
def summarize_content(
    ctx: typer.Context,
    artifact_id: Annotated[
        int, typer.Argument(help="The ID of the artifact content to summarize")
    ],
    refresh: Annotated[bool, typer.Option(help="Force summary refresh")] = False,
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
            artifact = summarize_and_store_content(
                artifact_id, repo=config.repo, refresh=refresh
            )
        config.console.print(
            f"[green]Content summarized for artifact ID {artifact_id}.[/]"
        )
        if artifact is not None:
            panel = generate_panel(artifact)
            config.console.print(panel)
    except ArtifactNotFoundError:
        config.error_console.print(f"Artifact with ID {artifact_id} not found.")
        raise typer.Exit(code=1)
    except ContentSummaryExistsWarning:
        config.error_console.print(
            f"Artifact with ID {artifact_id} already has summary.\n"
            "Use `--refresh` option to get a new summary."
        )
    except InvalidContentError:
        config.error_console.print(
            f"Artifact with ID {artifact_id} has no raw content yet.\n"
            f"Run `bookmarker fetch {artifact_id}` first."
        )
        raise typer.Exit(code=1)
    except InvalidAPIKeyError as e:
        config.error_console.print(f"Invalid API key: {e}")
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
