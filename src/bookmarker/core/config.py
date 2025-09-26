import logging

from decouple import config

DATABASE_URL = config("DATABASE_URL")
DEBUG = config("DEBUG", cast=bool, default=False)
OPENAI_API_KEY = config("OPENAI_API_KEY")
OPENAI_MODEL_NAME = config("OPENAI_MODEL_NAME")

log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
