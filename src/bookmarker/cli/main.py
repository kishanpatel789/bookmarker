import typer

from ..core.config import set_up_logging
from .base import app as base_app
from .fetchers import app as fetchers_app
from .helpers import app_callback
from .init_config import app as init_config_app
from .summarizers import app as summarizers_app

set_up_logging()

app = typer.Typer(callback=app_callback)

app.add_typer(init_config_app)
app.add_typer(base_app)
app.add_typer(fetchers_app)
app.add_typer(summarizers_app)
