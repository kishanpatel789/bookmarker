from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

DEFAULT_PROJECT_HOME = Path.home() / ".bookmarker"
DEFAULT_DB_PATH = DEFAULT_PROJECT_HOME / "bookmarker.sqlite"
CONFIG_PATH = DEFAULT_PROJECT_HOME / "config.env"

app = typer.Typer(help="Initialize Bookmarker configuration")


@app.command(name="init")
def init_config():
    """Initialize local configuration (database and AI summarizer)"""
    console = Console()

    # set up project directory
    if not DEFAULT_PROJECT_HOME.exists():
        DEFAULT_PROJECT_HOME.mkdir(parents=True)
        console.print(f"Created directory: '{DEFAULT_PROJECT_HOME}'.")
    else:
        console.print(f"Using existing directory: '{DEFAULT_PROJECT_HOME}'.")

    # define database config
    console.print("\n🛠️ [bold cyan]Database Setup[/]")
    use_default_db = Confirm.ask(
        f"[bold]Would you like to create a database at[/] '{DEFAULT_DB_PATH}'?"
    )
    if use_default_db:
        database_url = f"sqlite:///{DEFAULT_DB_PATH}"
    else:
        database_url = Prompt.ask(
            "[bold]Enter your DATABASE_URL[/] (e.g. sqlite:///path/to/db.sqlite or postgres://...)"
        )

    # define openai config
    console.print("\n🤖 [bold cyan]Summarizer Config[/]")
    openai_api_key = Prompt.ask("[bold]Enter your OpenAI API key[/]")
    openai_model_name = Prompt.ask(
        "[bold]Enter your preferred OpenAI model name[/]", default="gpt-5-nano"
    )

    # write config file
    content = [
        f"DATABASE_URL={database_url}",
        "DEBUG=False",
        "SUMMARIZER_BACKEND=openai",
        f"OPENAI_API_KEY={openai_api_key}",
        f"OPENAI_MODEL_NAME={openai_model_name}",
        "TIMEOUT_MULTITHREADING=15",
    ]
    CONFIG_PATH.write_text("\n".join(content) + "\n")

    console.print(f"\n✅ Configuration saved at: {CONFIG_PATH}")
    console.print("You can edit this file anytime to adjust your settings.")
    console.print(
        "\n🎉 [green]Bookmarker is ready to use![/] Run `[bold magenta3]bookmarker --help[/]` to see available commands."
    )
