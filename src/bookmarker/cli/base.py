from typing import Annotated

import typer
from rich.table import Table

from ..core.exceptions import (
    ArtifactNotFoundError,
)
from ..services.base import (
    ArtifactTypeEnum,
    get_or_create_artifact,
    update_tags,
)
from .helpers import generate_panel, get_config

app = typer.Typer()


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
