import typer

from .init_config import app as init_config_app

app = typer.Typer()

app.add_typer(init_config_app)

try:
    from .base import app as base_app
    from .fetchers import app as fetchers_app
    from .helpers import app_callback
    from .summarizers import app as summarizers_app

    app.add_typer(base_app, name="manage", callback=app_callback)
    app.add_typer(fetchers_app)
    app.add_typer(summarizers_app)
except FileNotFoundError:
    # fallback in case config file is not found; still allow init to work
    pass
