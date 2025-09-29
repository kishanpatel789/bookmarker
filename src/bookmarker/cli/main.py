import typer

from ..core.database import get_repo
from ..core.main import ArtifactTypeEnum, get_or_create_artifact

app = typer.Typer()


@app.command()
def init_db():
    """Initializes the database."""
    repo = get_repo()
    repo.create_db_and_tables()
    typer.echo("Database initialized.")


@app.callback()
def init(ctx: typer.Context):
    repo = get_repo()
    ctx.obj = repo


@app.command()
def add(
    ctx: typer.Context,
    title: str,
    url: str,
    artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE,
):
    """Adds an artifact with a title and URL."""
    repo = ctx.obj
    artifact = get_or_create_artifact(
        repo, title=title, url=url, artifact_type=artifact_type
    )

    print(f"Artifact added: {artifact.title} - {artifact.url}")


@app.command()
def list(ctx: typer.Context):
    """Lists all artifacts."""
    repo = ctx.obj
    artifacts = repo.list()
    for artifact in artifacts:
        print(f"{artifact.id}: {artifact.title} - {artifact.url}")
