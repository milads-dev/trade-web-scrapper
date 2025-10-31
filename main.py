from pathlib import Path
from api import fetch_all_trades
from transform import transform_trades
from config import update_env_var
from process import process_trades, extract_trade_setups
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


"""Extract trade setups from cleaned daily trades CSV."""


def trade_setup():
    latest = sorted(Path("daily_trades_cleaned").glob("*.csv"))[-1]
    extract_trade_setups(latest)


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
