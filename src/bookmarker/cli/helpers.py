from typing import NamedTuple

import typer
from rich.console import Console, Group
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.text import Text

from ..core.database import DatabaseRepository, get_repo
from ..core.models import Artifact


class AppConfig(NamedTuple):
    repo: DatabaseRepository | None
    console: Console
    error_console: Console


def app_callback(ctx: typer.Context) -> None:
    console = Console()
    error_console = Console(stderr=True, style="bold red")

    if ctx.invoked_subcommand == "init":
        app_config = AppConfig(
            repo=None,
            console=console,
            error_console=error_console,
        )
    else:
        try:
            repo = get_repo()
            repo.create_db_and_tables()
        except RuntimeError as e:
            error_console.print(e)
            console.print("Run [green]`bookmarker init`[/] to set up config file.")
            raise typer.Exit(1)

        app_config = AppConfig(
            repo=repo,
            console=console,
            error_console=error_console,
        )

    ctx.obj = app_config


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
