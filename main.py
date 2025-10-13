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

# account_id = 3741740
# account_id = 3837297

def fetch_trades():
    account_id = 3672903
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
    df.to_csv("trades3.csv", index=False)
    print(f"Exported {len(df)} trades to trades.csv")

def convert_and_export_daily_trades():
    # 1. Read the CSV file

    df = pd.read_csv("trades3.csv",)

    print(df.head())

    # 2. Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # 3. Extract just the date part
    df['date'] = df['Timestamp'].dt.date

    # 4. Create an output directory
    output_dir = Path("daily_trades_raw")
    output_dir.mkdir(exist_ok=True)
# 
    # 5. Group by date and export each group
    for date, group in df.groupby('date'):
        # Sort newest to oldest before saving (optional)
        group = group.sort_values('Timestamp', ascending=False)
        
        # Define output filename
        output_file = output_dir / f"trades_{date}.csv"
        
        # Save to CSV without the extra index column
        group.to_csv(output_file, index=False)
        
        print(f"✅ Saved {output_file}")

def merge_duplicate_trades():
    output_dir = Path("daily_trades")
    output_file = output_dir / "trades_2025-10-08.csv"
    

    df = pd.read_csv(output_file)
    print(df.head())
 

    # Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        # Group by the identifying fields
    grouped = (
        df.groupby(['Timestamp', 'Contract', 'Side', 'Price'], as_index=False)
        .agg({
            'Volume': 'sum',
            'PnL': 'sum',
            'Fees': 'sum',
            'date': 'first'  # keep one date value (they should all be the same)
        })
    )

        # Save the merged data
    grouped = grouped.sort_values('Timestamp', ascending=False)
    df['date'] = df['Timestamp'].dt.date

    grouped.to_csv(f"trades_merged_{df['date']}.csv", index=False)

    print("✅ Merged duplicate trades and saved to trades_merged.csv")

def process_trades(input_file: str, output_dir: str = "daily_trades_cleaned_new"):
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

def main():
    print("This script fetches trades from Topstep and saves them into daily CSV files.")
    fetch_trades()
    # convert_and_export_daily_trades()
    # merge_duplicate_trades()
    # process_trades("trades3.csv")


if __name__ == "__main__":
    main()