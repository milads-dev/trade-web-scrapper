import pandas as pd
import logging


def transform_trades(trades):
    if not trades:
        logging.warning("⚠️ No trades to transform.")
        return pd.DataFrame()

    df = pd.DataFrame(trades)

    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
    df['timeStamp'] = df['timeStamp'].dt.tz_localize(
        'America/Chicago').dt.tz_convert('America/New_York')
    df['timeStamp'] = df['timeStamp'].dt.tz_localize(None)

    df = df.rename(columns={
        "timeStamp": "Timestamp",
        "contractName": "Contract",
        "action": "Side",
        "lots": "Volume",
        "price": "Price",
        "pl": "PnL",
        "fees": "Fees",
    })[["Timestamp", "Contract", "Side", "Volume", "Price", "PnL", "Fees"]]

    df = df.sort_values("Timestamp", ascending=False)
    return df
