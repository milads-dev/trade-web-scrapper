import logging
import requests
from requests.adapters import HTTPAdapter, Retry
from config import get_env_var


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def create_session() -> requests.Session:
    session = requests.Session()

    token = get_env_var("BEARER_TOKEN")
    cookie = get_env_var("COOKIE")

    session.headers.update({
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://dashboard.topstep.com",
        "Referer": "https://dashboard.topstep.com/",
        "Cookie": cookie,
    })

    retries = Retry(total=3, backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session
