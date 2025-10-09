import typer

from .base import app as base_app
from .fetchers import app as fetchers_app
from .helpers import app_callback
from .summarizers import app as summarizers_app

app = typer.Typer(callback=app_callback)

app.add_typer(base_app)
app.add_typer(fetchers_app)
app.add_typer(summarizers_app)
