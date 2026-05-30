import requests
import os
import json
import csv
import time
from openai import OpenAI
from datetime import datetime

SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink",
}

PORTFOLIO_FILE = "portfolio.json"
HISTORY_FILE = "portfolio_history.csv"

ANALYST_SYSTEM_MESSAGE = """
You are a professional crypto analyst with a strong track record of positive 
expected value trades. You prioritise data over news, understanding that 
'sell the news, buy the fear' often applies to short term price action.

Your analysis framework:
- Technical data always comes first
- News is secondary — relevant for short term only
- Risk/reward ratio must always justify the trade
- Long term positive EV is the goal, not individual wins
- A losing trade on a good setup is acceptable
- A winning trade on a bad setup is not repeatable

When analysing a portfolio you will:
1. Assess current P&L and market position for each asset
2. Identify whether current prices represent opportunity or risk
3. Give a clear recommendation: Add / Hold / Take Profit / Cut Loss
4. Always state the risk level: Low / Medium / High
5. Give reasoning based on data, not emotion

Respond in a clear structured format:
For each coin:
- Symbol: TICKER
- Recommendation: [Add / Hold / Take Profit / Cut Loss]
- Risk: [Low / Medium / High]
- Reason: <brief reasoning>

Then provide:
- Portfolio Health: [Healthy / Needs Attention / Critical]
- Urgent Actions: <list any urgent actions or "None">
- Market Observations: <brief notes based on 24h changes and current signals>
"""


def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return None
    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)
    print(f"\n💾 Portfolio saved to {PORTFOLIO_FILE}")


def prompt_float(message, allow_zero=False):
    while True:
        value = input(message)
        try:
            value = float(value)
            if not allow_zero and value <= 0:
                print("Please enter a positive number.")
                continue
            if allow_zero and value < 0:
                print("Please enter zero or a positive number.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")


def prompt_yn(message):
    while True:
        choice = input(message).strip().upper()
        if choice in ("Y", "N"):
            return choice
        print("Please enter Y or N.")


def get_portfolio():
    portfolio = load_portfolio()
    if portfolio:
        print(f"\n📂 Loaded saved portfolio ({len(portfolio)} coin(s)).")
        print("Current coins:")
        for coin in portfolio:
            print(f"  {coin['symbol']} - {coin['name']}")
        edit = prompt_yn("Edit this portfolio? (Y/N): ")
        if edit == "Y":
            portfolio = manage_portfolio(portfolio)

    if not portfolio:
        portfolio = []
        while True:
            print("\n--- Add a coin to your portfolio ---")
            name = input("Token name (e.g. Bitcoin): ").strip().title()
            symbol = input("Token symbol (e.g. BTC): ").strip().upper()
            if symbol not in SYMBOL_TO_ID:
                print(f"Sorry, {symbol} is not supported. Supported coins: {', '.join(SYMBOL_TO_ID.keys())}")
                continue

            quantity = prompt_float(f"How many {symbol} do you own? ")
            total_invested = prompt_float(f"How much did you invest in {symbol} total? $")
            profit_target = prompt_float(f"Profit target for {symbol}? (e.g. 25 for 25%): ", allow_zero=True)
            stop_loss = prompt_float(f"Stop loss for {symbol}? (e.g. 15 for 15%): ", allow_zero=True)

            buy_price_per_coin = total_invested / quantity if quantity else 0

            coin = {
                "name": name,
                "symbol": symbol,
                "quantity": quantity,
                "total_invested": total_invested,
                "buy_price_per_coin": buy_price_per_coin,
                "profit_target": profit_target,
                "stop_loss": stop_loss,
            }
            portfolio.append(coin)

            if prompt_yn("\nAdd another coin? (Y/N): ") == "N":
                break
    return portfolio


def manage_portfolio(portfolio):
    while True:
        print("\nPortfolio menu:")
        print("  A - Add coin")
        print("  R - Remove coin")
        print("  D - Done editing")
        choice = input("Choose: ").strip().upper()
        if choice == "D":
            break
        elif choice == "A":
            portfolio = add_coin_to_portfolio(portfolio)
        elif choice == "R":
            portfolio = remove_coin_from_portfolio(portfolio)
        else:
            print("Please enter A, R, or D.")
    return portfolio


def add_coin_to_portfolio(portfolio):
    print("\n--- Add a coin to your portfolio ---")
    name = input("Token name (e.g. Bitcoin): ").strip().title()
    symbol = input("Token symbol (e.g. BTC): ").strip().upper()
    if symbol not in SYMBOL_TO_ID:
        print(f"Sorry, {symbol} is not supported. Supported coins: {', '.join(SYMBOL_TO_ID.keys())}")
        return portfolio

    quantity = prompt_float(f"How many {symbol} do you own? ")
    total_invested = prompt_float(f"How much did you invest in {symbol} total? $")
    profit_target = prompt_float(f"Profit target for {symbol}? (e.g. 25 for 25%): ", allow_zero=True)
    stop_loss = prompt_float(f"Stop loss for {symbol}? (e.g. 15 for 15%): ", allow_zero=True)

    buy_price_per_coin = total_invested / quantity if quantity else 0

    coin = {
        "name": name,
        "symbol": symbol,
        "quantity": quantity,
        "total_invested": total_invested,
        "buy_price_per_coin": buy_price_per_coin,
        "profit_target": profit_target,
        "stop_loss": stop_loss,
    }

    portfolio = [c for c in portfolio if c["symbol"] != symbol]
    portfolio.append(coin)
    print(f"✅ {symbol} added/updated in portfolio.")
    return portfolio


def remove_coin_from_portfolio(portfolio):
    if not portfolio:
        print("Portfolio is empty.")
        return portfolio
    symbol = input("\nEnter symbol to remove (e.g. BTC): ").strip().upper()
    portfolio = [c for c in portfolio if c["symbol"] != symbol]
    print(f"🗑 Removed {symbol} (if present).")
    return portfolio


def fetch_live_prices(portfolio, retries=3, delay=5):
    """Fetch live USD prices for portfolio coins from CoinGecko API"""
    ids = ",".join([SYMBOL_TO_ID[coin["symbol"]] for coin in portfolio if coin["symbol"] in SYMBOL_TO_ID])
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limited by CoinGecko. Retrying in {delay} seconds...")
            else:
                print(f"API Error: {response.status_code}")
                return None
        except requests.RequestException as exc:
            print(f"Network error: {exc}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
            else:
                return None
        time.sleep(delay)
    return None


def calculate_pnl(portfolio, live_prices):
    """Calculate P&L, current value and check targets for each coin."""
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for coin in portfolio:
        symbol = coin["symbol"]
        coin_id = SYMBOL_TO_ID[symbol].lower()

        if coin_id not in live_prices:
            print(f"Could not find live price for {symbol}")
            continue

        live_price = live_prices[coin_id]["usd"]
        change_24h = live_prices[coin_id].get("usd_24h_change", 0)
        current_value = coin["quantity"] * live_price
        pnl_dollars = current_value - coin["total_invested"]
        pnl_percent = (pnl_dollars / coin["total_invested"]) * 100 if coin["total_invested"] else 0
        profit_hit = pnl_percent >= coin["profit_target"]
        stoploss_hit = pnl_percent <= -coin["stop_loss"]

        results.append({
            **coin,
            "timestamp": timestamp,
            "live_price": live_price,
            "change_24h": change_24h,
            "current_value": current_value,
            "pnl_dollars": pnl_dollars,
            "pnl_percent": pnl_percent,
            "profit_hit": profit_hit,
            "stoploss_hit": stoploss_hit,
        })
    return results


def display_dashboard(results):
    """Display formatted portfolio dashboard with alerts."""
    print("\n" + "=" * 60)
    print("         🚀 CRYPTO PORTFOLIO TRACKER 🚀")
    print("="*60)

    total_invested = 0
    total_value = 0

    for coin in results:
        pnl_arrow = "🟢" if coin["pnl_percent"] >= 0 else "🔴"

        print(f"""
{pnl_arrow} {coin['name'].title()} ({coin['symbol']})
    Quantity:           {coin['quantity']} coins
    Bought at:          ${coin['buy_price_per_coin']:,.2f} per coin
    Live Price:         ${coin['live_price']:,.2f}
    24h change:         {coin['change_24h']:+.2f}%
    Invested:           ${coin['total_invested']:,.2f}
    Current value:      ${coin['current_value']:,.2f}
    P&L:                ${coin['pnl_dollars']:+,.2f} ({coin['pnl_percent']:+.2f}%)
        """)

        if coin["profit_hit"]:
            print(f"    🎯 PROFIT TARGET HIT! {coin['symbol']} is up {coin['pnl_percent']:.2f}% - consider taking profits!")
        if coin["stoploss_hit"]:
            print(f"    ⚠ STOP LOSS HIT! {coin['symbol']} is down {abs(coin['pnl_percent']):.2f}% - consider cutting losses!")

        total_invested += coin["total_invested"]
        total_value += coin["current_value"]

    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested) * 100 if total_invested else 0
    total_arrow = "🟢" if total_pnl >= 0 else "🔴"

    print("="*60)
    print("PORTFOLIO SUMMARY")
    print(f"Total Invested:     ${total_invested:,.2f}")
    print(f"Total Value:        ${total_value:,.2f}")
    print(f"{total_arrow} Total P&L:        ${total_pnl:+,.2f} ({total_pnl_percent:+.2f}%)")
    print("="*60)


def append_history(results):
    """Append current portfolio snapshot to historical CSV."""
    file_exists = os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0
    fieldnames = ["timestamp", "date", "symbol", "name", "quantity", "buy_price_per_coin",
                  "live_price", "change_24h", "total_invested", "current_value",
                  "pnl_dollars", "pnl_percent", "profit_hit", "stoploss_hit"]

    with open(HISTORY_FILE, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for coin in results:
            row = {k: coin.get(k, "") for k in fieldnames}
            row["date"] = coin["timestamp"].split(" ")[0]
            writer.writerow(row)

    print(f"\n📈 History updated in {HISTORY_FILE}")


def format_portfolio_for_ai(results):
    """Format portfolio data into clear text for AI analysis."""
    summary = "PORTFOLIO SUMMARY FOR ANALYSIS:\n\n"

    for coin in results:
        summary += f"{coin['name']} ({coin['symbol']})\n"
        summary += f"  Quantity: {coin['quantity']} coins\n"
        summary += f"  Buy price: ${coin['buy_price_per_coin']:,.2f}\n"
        summary += f"  Current price: ${coin['live_price']:,.2f}\n"
        summary += f"  24h change: {coin['change_24h']:+.2f}%\n"
        summary += f"  P&L: ${coin['pnl_dollars']:+,.2f} ({coin['pnl_percent']:+.2f}%)\n"
        summary += f"  Profit target: {coin['profit_target']}% "
        summary += f"({'HIT' if coin['profit_hit'] else 'not hit'})\n"
        summary += f"  Stop loss: {coin['stop_loss']}% "
        summary += f"({'HIT' if coin['stoploss_hit'] else 'not hit'})\n\n"

    total_invested = sum(c['total_invested'] for c in results)
    total_value = sum(c['current_value'] for c in results)
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

    summary += f"PORTFOLIO TOTALS:\n"
    summary += f"  Total invested: ${total_invested:,.2f}\n"
    summary += f"  Current value: ${total_value:,.2f}\n"
    summary += f"  Total P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)\n"

    return summary


def get_ai_analysis(portfolio_summary):
    """Send portfolio data to OpenAI and get back structured analysis."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key not found. Skipping AI analysis."

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ANALYST_SYSTEM_MESSAGE},
                {"role": "user", "content": f"""
Please analyse this crypto portfolio using the required structured format:
1. Per-coin section with Recommendation, Risk, and Reason
2. Portfolio Health
3. Urgent Actions
4. Market Observations

Portfolio data:
{portfolio_summary}
                """}
            ],
            max_tokens=1200,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"AI analysis failed: {exc}"


def save_report(results, analysis):
    """Save portfolio report and AI analysis to a timestamped .txt file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"jarvis_report_{timestamp}.txt"

    with open(filename, "w") as f:
        f.write("JARVIS PORTFOLIO REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")

        for coin in results:
            f.write(f"{coin['name']} ({coin['symbol']})\n")
            f.write(f"  Quantity:      {coin['quantity']} coins\n")
            f.write(f"  Bought at:     ${coin['buy_price_per_coin']:,.2f}\n")
            f.write(f"  Live price:    ${coin['live_price']:,.2f}\n")
            f.write(f"  Invested:      ${coin['total_invested']:,.2f}\n")
            f.write(f"  Current value: ${coin['current_value']:,.2f}\n")
            f.write(f"  P&L:           ${coin['pnl_dollars']:+,.2f} ({coin['pnl_percent']:+.2f}%)\n")

            if coin["profit_hit"]:
                f.write("  >>> PROFIT TARGET HIT!\n")
            if coin["stoploss_hit"]:
                f.write("  >>> STOP LOSS HIT!\n")

            f.write("\n")

        f.write("="*60 + "\n")
        f.write("JARVIS AI ANALYSIS\n")
        f.write("="*60 + "\n\n")
        f.write(analysis)
        f.write("\n")

    print(f"\n📄 Report saved as: {filename}")
    return filename


def main():
    print("="*60)
    print("   🤖 JARVIS — Crypto Portfolio Analyst")
    print("="*60)

    portfolio = get_portfolio()
    if not portfolio:
        print("No portfolio entered. Exiting.")
        return

    save_portfolio(portfolio)

    print("\n⏳ Fetching live prices...")
    live_prices = fetch_live_prices(portfolio)
    if not live_prices:
        print("Failed to fetch prices. Check your connection.")
        return

    results = calculate_pnl(portfolio, live_prices)
    display_dashboard(results)
    append_history(results)

    run_ai = prompt_yn("\nRun AI analysis? (Y/N): ")
    if run_ai == "Y":
        print("\n🤖 Jarvis is analysing your portfolio...")
        portfolio_summary = format_portfolio_for_ai(results)
        analysis = get_ai_analysis(portfolio_summary)

        print("\n" + "="*60)
        print("   📊 JARVIS ANALYSIS")
        print("="*60)
        print(analysis)
    else:
        print("\nSkipping AI analysis.")
        analysis = ""

    save = prompt_yn("\nSave full report? (Y/N): ")
    if save == "Y" and analysis:
        save_report(results, analysis)

    print("\n✅ Jarvis signing off.")


if __name__ == "__main__":
    main()
