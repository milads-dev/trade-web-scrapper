import pandas as pd
from pathlib import Path
from api import fetch_all_trades
from transform import transform_trades
from config import update_env_var
import argparse


def save_trades_to_csv(df, filename="trades.csv"):
    output_path = Path(filename)
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} trades → {output_path.resolve()}")


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
    df = pd.read_csv("./daily_trades_cleaned/trades_merged_2025-10-30.csv")
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

        if abs(position) == 0:  # back to zero
            setup_df = pd.DataFrame(current_trades)
            total_volume = setup_df["Volume"].sum()
            entry_price = setup_df[setup_df["Side"] == "Sell"]["Price"].mean()
            exit_price = setup_df[setup_df["Side"] == "Buy"]["Price"].mean()

            gross_pnl = setup_df["PnL"].sum()
            total_fees = setup_df["Fees"].sum()
            net_pnl = gross_pnl - total_fees   # ✅ PnL adjusted for fees

            entry_time = pd.to_datetime(
                setup_df.iloc[0]["Timestamp"]).strftime("%m/%d/%Y %H:%M:%S")
            exit_time = pd.to_datetime(
                setup_df.iloc[-1]["Timestamp"]).strftime("%m/%d/%Y %H:%M:%S")

            setups.append({
                "ContractName": row["Contract"],
                "Type": "Short" if setup_df.iloc[0]["Side"] == "Sell" else "Long",
                "EnteredAt": entry_time,
                "ExitedAt": exit_time,
                "Size": total_volume / 2,
                "EntryPrice": entry_price.round(2),
                "ExitPrice": exit_price.round(2),
                "PnL": net_pnl.round(2),
            })
            current_trades = []

    setups_df = pd.DataFrame(setups)
    setups_df.to_csv("trade_positions.csv", index=False)

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

        if choice == "5":

            df = pd.read_csv("trade_positions.csv", parse_dates=[
                             "EnteredAt", "ExitedAt"])

            # df = pd.read_csv("./daily_trades_cleaned/trades_merged_2025-10-21.csv", parse_dates=[
            #     "EnteredAt", "ExitedAt"])

            df = df.sort_values("EnteredAt")

            # Compare ExitedAt of current row to EnteredAt of *next* row
            mask = df["EnteredAt"] == df["ExitedAt"].shift(1)

            matches = df[mask]
            print(matches[['EnteredAt', 'ExitedAt',
                           'EntryPrice', 'ExitPrice', 'PnL', 'Size', 'Type']])

        if choice == "4":
            print("👋 Exiting program.")
            break
        elif choice in menu_options:
            _, action = menu_options[choice]
            action()  # run the selected function
        else:
            print("❌ Invalid option, try again.")


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
