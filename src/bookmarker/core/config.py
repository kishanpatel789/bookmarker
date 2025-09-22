import logging

from decouple import config

DATABASE_URL = config("DATABASE_URL")
DEBUG = config("DEBUG", cast=bool, default=False)

log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
