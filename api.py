from utils import create_session
from config import BASE_URL
from typing import List, Tuple
import logging


def fetch_trades_page(session, account_id: str, page: int, limit: int = 25) -> Tuple[List[dict], dict]:
    url = f"{BASE_URL}/{account_id}?page={page}&limit={limit}&sort=-timeStamp"
    response = session.get(url)
    response.raise_for_status()

    data = response.json()
    return data.get("account", {}).get("trades", []), data.get("account", {}).get("tradesPagination", {})


def fetch_all_trades(account_id: str, limit: int = 25) -> List[dict]:
    session = create_session()
    all_trades = []
    page = 1

    while True:
        trades, pagination = fetch_trades_page(
            session, account_id, page, limit)
        if not trades:
            break

        all_trades.extend(trades)
        logging.info(
            f"📄 Page {page} fetched — total trades: {len(all_trades)}")

        if page >= pagination.get("totalPages", page):
            break
        page += 1

    return all_trades
