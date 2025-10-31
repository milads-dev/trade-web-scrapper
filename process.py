from pathlib import Path
import pandas as pd
import logging
from .config import DATE_FORMAT


def save_to_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    logging.info(f"✅ Saved {len(df)} records → {path.resolve()}")


def process_trades(input_file="trades.csv", output_dir="daily_trades_cleaned"):
    df = pd.read_csv(input_file, parse_dates=["Timestamp"])
    df["date"] = df["Timestamp"].dt.date

    grouped = (
        df.groupby(["Timestamp", "Contract", "Side", "Price"], as_index=False)
          .agg({"Volume": "sum", "PnL": "sum", "Fees": "sum", "date": "first"})
          .sort_values("Timestamp", ascending=False)
    )

    output_dir = Path(output_dir)
    for date, group in grouped.groupby("date"):
        save_to_csv(group, output_dir / f"trades_merged_{date}.csv")


def extract_trade_setups(input_file: Path):
    df = pd.read_csv(input_file, parse_dates=[
                     "Timestamp"]).sort_values("Timestamp")
    setups, position, current = [], 0, []

    for _, row in df.iterrows():
        position += row["Volume"] if row["Side"] == "Buy" else -row["Volume"]
        current.append(row)

        if abs(position) == 0:
            setup_df = pd.DataFrame(current)
            type_ = "Short" if setup_df.iloc[0]["Side"] == "Sell" else "Long"
            pnl = setup_df["PnL"].sum() - setup_df["Fees"].sum()

            setups.append({
                "Contract": row["Contract"],
                "Type": type_,
                "EnteredAt": setup_df.iloc[0]["Timestamp"].strftime(DATE_FORMAT),
                "ExitedAt": setup_df.iloc[-1]["Timestamp"].strftime(DATE_FORMAT),
                "Size": setup_df["Volume"].sum(),
                "EntryPrice": round(setup_df[setup_df["Side"] == "Sell"]["Price"].mean(), 2),
                "ExitPrice": round(setup_df[setup_df["Side"] == "Buy"]["Price"].mean(), 2),
                "PnL": round(pnl, 2),
            })
            current = []

    setups_df = pd.DataFrame(setups)
    save_to_csv(setups_df, Path("trade_setups.csv"))
