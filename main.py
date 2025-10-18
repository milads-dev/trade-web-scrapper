import requests
import pandas as pd
import os
from dotenv import set_key, load_dotenv
from pathlib import Path
import argparse


ENV_PATH = Path(".env")
load_dotenv(ENV_PATH)

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

BASE_URL = "https://trm-api.topstep.com/me/accounts"

def fetch_trades_page(account_id: str, page: int, limit: int = 25):
    url = f"{BASE_URL}/{account_id}?page={page}&limit={limit}&sort=-timeStamp"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None

    data = response.json()
    trades = data.get("account", {}).get("trades", [])
    pagination = data.get("account", {}).get("tradesPagination", {})
    return trades, pagination

def fetch_all_trades(account_id: str, limit: int = 25):
    all_trades = []
    page = 1

    while True:
        result = fetch_trades_page(account_id, page, limit)
        if not result:
            break

        trades, pagination = result

        if not trades:
            break

        all_trades.extend(trades)
        print(f"📄 Page {page} fetched, total trades: {len(all_trades)}")

        if page >= pagination.get("totalPages", page):
            break
        page += 1

    return all_trades

def transform_trades(trades):
    df = pd.DataFrame(trades)

    if df.empty:
        print("⚠️ No trades found.")
        return df

    # Convert timestamp from CT → EST → remove timezone
    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
    df['timeStamp'] = df['timeStamp'].dt.tz_localize('America/Chicago').dt.tz_convert('America/New_York')
    df['timeStamp'] = df['timeStamp'].dt.tz_localize(None)

    df = df.sort_values('timeStamp', ascending=False)

    df = df[["timeStamp", "contractName", "action", "lots", "price", "pl", "fees"]].rename(columns={
        "timeStamp": "Timestamp",
        "contractName": "Contract",
        "action": "Side",
        "lots": "Volume",
        "price": "Price",
        "pl": "PnL",
        "fees": "Fees"
    })

    return df

def save_trades_to_csv(df, filename="trades.csv"):
    output_path = Path(filename)
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} trades → {output_path.resolve()}")

# "Fetch trades from API and save to CSV."
def fetch_trades():
    account_id = input("🏦 Enter your account number: ").strip()

    if not account_id.isdigit():
        print("❌ Invalid account number — must be numeric.")
        return

    print(f"🔍 Fetching trades for account {account_id}...")
    trades = fetch_all_trades(account_id)

    df = transform_trades(trades)
    if not df.empty:
        save_trades_to_csv(df)
    else:
        print("⚠️ No trades to save.")

# "Process and clean trades, then save daily CSVs."
def process_trades(input_file: str = "trades.csv", output_dir: str = "daily_trades_cleaned"):
    df = pd.read_csv(input_file)
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    df['date'] = df['Timestamp'].dt.date

    grouped = (
        df.groupby(['Timestamp', 'Contract', 'Side', 'Price'], as_index=False)
          .agg({
              'Volume': 'sum',
              'PnL': 'sum',
              'Fees': 'sum',
              'date': 'first'  # keep one date
          })
    )
    
    grouped = grouped.sort_values('Timestamp', ascending=False)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

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
                "EntryPrice": entry_price.round(2),
                "ExitPrice": exit_price.round(2),
                "PnL": net_pnl.round(2),
            })
            current_trades = []

    setups_df = pd.DataFrame(setups)
    setups_df.to_csv("trade_setups.csv", index=False)

    print(f"✅ Extracted {len(setups_df)} trade setups → trade_setups.csv")

def main_menu():
    menu_options = {
        "1": ("Fetch Trades", fetch_trades),
        "2": ("Transform Trades", process_trades),
        "3": ("Generate Summary", trade_setup),
        "4": ("Exit", None)
    }

    while True:
        print("\n=== TRADE AUTOMATION MENU ===")
        for key, (desc, _) in menu_options.items():
            print(f"{key}. {desc}")

        choice = input("\nEnter your choice: ").strip()

        if choice == "4":
            print("👋 Exiting program.")
            break
        elif choice in menu_options:
            _, action = menu_options[choice]
            action()  # run the selected function
        else:
            print("❌ Invalid option, try again.")

def update_env_var(key, value):
    if not ENV_PATH.exists():
        print("⚠️ No .env file found — creating a new one.")
        ENV_PATH.touch()

    set_key(ENV_PATH, key, value)
    os.environ[key] = value
    print(f"✅ Updated {key} in .env")

def main():
    parser = argparse.ArgumentParser(description="Trade Automation Tool CLI")
    parser.add_argument("--update-token", help="Update token in .env")
    parser.add_argument("--update-cookie", help="Update Cookie in .env")

    args = parser.parse_args()

    if args.update_token:
        update_env_var("BEARER_TOKEN", args.update_token)
    if args.update_cookie:
        update_env_var("COOKIE", args.update_cookie)
    if not any(vars(args).values()):
        main_menu()



if __name__ == "__main__":
    main()