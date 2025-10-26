import os
from pathlib import Path
from dotenv import load_dotenv, set_key
import logging

ENV_PATH = Path(".env")
load_dotenv(ENV_PATH)

BASE_URL = "https://trm-api.topstep.com/me/accounts"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S"


def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Missing environment variable: {key}")
    return value


def update_env_var(key: str, value: str) -> None:

    if not ENV_PATH.exists():

        logging.warning("⚠️ No .env file found — creating new one.")

        ENV_PATH.touch()

    set_key(ENV_PATH, key, value)

    os.environ[key] = value

    logging.info(f"✅ Updated {key} in .env")
