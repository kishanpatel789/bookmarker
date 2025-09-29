import typer

app = typer.Typer()


@app.command()
def hello():
    """Prints Hello, World!"""
    typer.echo("Hello, World!")
