import requests
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv() 

TOKEN = os.getenv("BEARER_TOKEN")
COOKIE = os.getenv("COOKIE")


headers = {
    "Authorization": f"Bearer {TOKEN}",   
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "origin": "https://dashboard.topstep.com",
    "referer": "https://dashboard.topstep.com/",
    "cookie": COOKIE
}

def fetch_trades():
    account_id = 3978190
    # account_id = 3978190
    # account_id =4020848
    limit = 25   
    all_trades = []
    page = 1

    while True:
        url = f"https://trm-api.topstep.com/me/accounts/{account_id}?page={page}&limit={limit}sort=-timeStamp"
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print(f"Error {r.status_code}: {r.text}")
            break

        data = r.json()
        trades = data.get("account", {}).get("trades", [])

        if not trades: 
            break

        all_trades.extend(trades)
        print(f"Fetched page {page}, total trades so far: {len(all_trades)}")


        # Pagination info
        pagination = data.get("account", {}).get("tradesPagination", {})
        if page >= pagination.get("totalPages", page):
            break

        page += 1


    # Save to CSV
    df = pd.DataFrame(all_trades)
    # --- Convert timestamp from CT to EST ---
    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
    df['timeStamp'] = df['timeStamp'].dt.tz_localize('America/Chicago').dt.tz_convert('America/New_York')
    df['timeStamp'] = df['timeStamp'].dt.tz_localize(None)
    df = df.sort_values('timeStamp', ascending=False)
    df = df[["timeStamp", "contractName", "action", "lots", "price", "pl", "fees"]]

    df = df.rename(columns={
        "timeStamp": "Timestamp",
        "contractName": "Contract",
        "action": "Side",
        "lots": "Volume",
        "price": "Price",
        "pl": "PnL",
        "fees": "Fees"
    })
    df.to_csv("trades.csv", index=False)
    print(f"Exported {len(df)} trades to trades.csv")

def process_trades(input_file: str, output_dir: str = "daily_trades_cleaned"):
    """
    Load trades CSV, merge duplicates, sort by timestamp descending,
    and save one CSV per day.
    """
    # --- Load CSV ---
    df = pd.read_csv(input_file)
    
    # --- Convert Timestamp column to datetime ---
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # --- Extract date for grouping ---
    df['date'] = df['Timestamp'].dt.date

    # --- Merge duplicates ---
    grouped = (
        df.groupby(['Timestamp', 'Contract', 'Side', 'Price'], as_index=False)
          .agg({
              'Volume': 'sum',
              'PnL': 'sum',
              'Fees': 'sum',
              'date': 'first'  # keep one date
          })
    )
    
    # --- Sort descending by Timestamp ---
    grouped = grouped.sort_values('Timestamp', ascending=False)

    # --- Create output directory ---
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # --- Split by date and save ---
    for date, group in grouped.groupby('date'):
        file_name = output_path / f"trades_merged_{date}.csv"
        group.to_csv(file_name, index=False)
        print(f"✅ Saved {file_name}")

"""Extract trade setups from cleaned daily trades CSV."""
def trade_setup():
    df = pd.read_csv("./daily_trades_cleaned/trades_merged_2025-10-13.csv")
    df = df.sort_values("Timestamp")

    setups = []
    position = 0
    current_trades = []

    for _, row in df.iterrows():
        lots = row["Volume"]
        if row["Side"] == "Buy":
            position += lots
        else:  
            position -= lots
        current_trades.append(row)

        if abs(position) < 1e-6:  # back to zero
            setup_df = pd.DataFrame(current_trades)
            total_volume = setup_df["Volume"].sum()
            entry_price = setup_df[setup_df["Side"] == "Sell"]["Price"].mean()
            exit_price = setup_df[setup_df["Side"] == "Buy"]["Price"].mean()

            gross_pnl = setup_df["PnL"].sum()
            total_fees = setup_df["Fees"].sum()
            net_pnl = gross_pnl - total_fees   # ✅ PnL adjusted for fees

            entry_time = pd.to_datetime(setup_df.iloc[0]["Timestamp"]).strftime("%m/%d/%Y %H:%M:%S")
            exit_time  = pd.to_datetime(setup_df.iloc[-1]["Timestamp"]).strftime("%m/%d/%Y %H:%M:%S")


            setups.append({
                "ContractName": row["Contract"],
                "Type": "Short" if setup_df.iloc[0]["Side"] == "Sell" else "Long",
                "EnteredAt": entry_time,
                "ExitedAt": exit_time,
                "Size": total_volume,
                "EntryPrice": entry_price,
                "ExitPrice": exit_price,
                "PnL": net_pnl.round(2),
            })
            current_trades = []

    setups_df = pd.DataFrame(setups)
    setups_df.to_csv("trade_setups.csv", index=False)

def main():
    print("This script fetches trades from Topstep and saves them into daily CSV files.")
    fetch_trades()
    process_trades("trades.csv","daily_trades_cleaned")
    trade_setup()


if __name__ == "__main__":
    main()