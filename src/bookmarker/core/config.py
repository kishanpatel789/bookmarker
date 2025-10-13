import logging
import os
from pathlib import Path

from decouple import Config, RepositoryEnv


def load_config() -> Config:
    env = os.getenv("BOOKMARKER_ENV", "prod")

    if env == "dev":
        config_path = Path(".env")
    else:
        config_path = Path.home() / ".bookmarker" / "config.env"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Run `bookmarker init` or set BOOKMARKER_ENV=dev."
        )

    return Config(RepositoryEnv(config_path))


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_up_logging():
    config = get_config()
    DEBUG = config("DEBUG", cast=bool, default=False)
    log_level = logging.DEBUG if DEBUG else logging.CRITICAL
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_timeout_multithreading() -> int:
    config = get_config()
    return config("TIMEOUT_MULTITHREADING", 15, cast=int)
