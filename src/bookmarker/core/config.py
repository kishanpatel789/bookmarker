import logging
from pathlib import Path
from typing import Final

from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv(Path.home() / ".bookmarker" / "config.env"))

TIMEOUT_MULTITHREADING: Final[int] = config("TIMEOUT_MULTITHREADING", 15, cast=int)


def set_up_logging():
    DEBUG = config("DEBUG", cast=bool, default=False)
    log_level = logging.DEBUG if DEBUG else logging.CRITICAL
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
