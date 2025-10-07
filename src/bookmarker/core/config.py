import logging

from decouple import config

TIMEOUT_MULTITHREADING = config("TIMEOUT_MULTITHREADING", 10, cast=int)


def set_up_logging():
    DEBUG = config("DEBUG", cast=bool, default=False)
    log_level = logging.DEBUG if DEBUG else logging.CRITICAL
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
