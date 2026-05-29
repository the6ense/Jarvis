import requests
import os
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
"""

def get_portfolio():
    """Collect user's crypto holdings and targets."""
    portfolio = []

    while True:
        print("\n--- Add a coin to your portfolio ---")
        name = input("Token name (e.g. Bitcoin): ").strip().title()
        symbol = input("Token symbol (e.g. BTC): ").strip().upper()
        if symbol not in SYMBOL_TO_ID:
            print(f"Sorry, {symbol} is not supported. Supported coins: {', '.join(SYMBOL_TO_ID.keys())}")
            continue

        quantity = float(input(f"How many {symbol} do you own? "))
        total_invested = float(input(f"How much did you invest in {symbol} total? $"))
        profit_target = float(input(f"Profit target for {symbol}? (e.g. 25 for 25%): "))
        stop_loss = float(input(f"Stop loss for {symbol}? (e.g. 15 for 15%): "))

        buy_price_per_coin = total_invested / quantity

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

        another = input("\nAdd another coin? (Y/N): ").strip().upper()
        if another != "Y":
            break
    return portfolio

def fetch_live_prices(portfolio):
    """Fetch live USD prices for portfolio coins from CoinGecko API"""
    # Convert symbols to CoinGecko IDs
    ids = ",".join([SYMBOL_TO_ID[coin["symbol"]] for coin in portfolio if coin["symbol"] in SYMBOL_TO_ID])
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API Error: {response.status_code}")
        return None
    
def calculate_pnl(portfolio, live_prices):
    """Caluclate P&L, current value and check targets for each coin."""
    results = []
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
        pnl_percent = (pnl_dollars / coin["total_invested"]) * 100
        profit_hit = pnl_percent >= coin["profit_target"]
        stoploss_hit = pnl_percent <= -coin["stop_loss"]
        
        results.append({
            **coin,
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
{pnl_arrow} {coin['name']} ({coin['symbol']})
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
    total_pnl_percent = (total_pnl / total_invested) * 100
    total_arrow = "🟢" if total_pnl >= 0 else "🔴"

    print("="*60)
    print("PORTFOLIO SUMMARY")
    print(f"Total Invested:     ${total_invested:,.2f}")
    print(f"Total Value:        ${total_value:,.2f}")
    print(f"{total_arrow} Total P&L:        ${total_pnl:+,.2f} ({total_pnl_percent:+.2f}%)")
    print("="*60)


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
    total_pnl_pct = (total_pnl / total_invested) * 100
    
    summary += f"PORTFOLIO TOTALS:\n"
    summary += f"  Total invested: ${total_invested:,.2f}\n"
    summary += f"  Current value: ${total_value:,.2f}\n"
    summary += f"  Total P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)\n"
    
    return summary

def get_ai_analysis(portfolio_summary):
    """Send portfolio data to OpenAI and get back analysis."""
    import os
    from openai import OpenAI
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": ANALYST_SYSTEM_MESSAGE},
            {"role": "user", "content": f"""
Please analyse this crypto portfolio and provide:
1. Assessment for each coin (Add / Hold / Take Profit / Cut Loss)
2. Risk level for each (Low / Medium / High)
3. Overall portfolio health
4. Any urgent actions needed
5. Brief market observations based on 24h changes

{portfolio_summary}
            """}
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def save_report(results, analysis):
    """Save portfolio report and AI analysis to a timestamped .txt file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"jarvis_report_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write("JARVIS PORTFOLIO REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        total_invested = 0
        total_value = 0
        
        for coin in results:
            f.write(f"{coin['name']} ({coin['symbol']})\n")
            f.write(f"  Quantity:      {coin['quantity']} coins\n")
            f.write(f"  Bought at:     ${coin['buy_price_per_coin']:,.2f}\n")
            f.write(f"  Live price:    ${coin['live_price']:,.2f}\n")
            f.write(f"  Invested:      ${coin['total_invested']:,.2f}\n")
            f.write(f"  Current value: ${coin['current_value']:,.2f}\n")
            f.write(f"  P&L:           ${coin['pnl_dollars']:+,.2f} ({coin['pnl_percent']:+.2f}%)\n")
            
            if coin["profit_hit"]:
                f.write(f"  >>> PROFIT TARGET HIT!\n")
            if coin["stoploss_hit"]:
                f.write(f"  >>> STOP LOSS HIT!\n")
            
            f.write("\n")
            total_invested += coin["total_invested"]
            total_value += coin["current_value"]
        
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested) * 100
        
        f.write("="*60 + "\n")
        f.write(f"Total Invested:  ${total_invested:,.2f}\n")
        f.write(f"Total Value:     ${total_value:,.2f}\n")
        f.write(f"Total P&L:       ${total_pnl:+,.2f} ({total_pnl_percent:+.2f}%)\n")
        
        # AI Analysis section
        f.write("\n" + "="*60 + "\n")
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
    
    # Step 1: Get portfolio
    portfolio = get_portfolio()
    
    # Step 2: Fetch live prices
    print("\n⏳ Fetching live prices...")
    live_prices = fetch_live_prices(portfolio)
    
    if not live_prices:
        print("Failed to fetch prices. Check your connection.")
        return
    
    # Step 3: Calculate P&L
    results = calculate_pnl(portfolio, live_prices)
    
    # Step 4: Display dashboard
    display_dashboard(results)
    
    # Step 5: Format for AI
    print("\n🤖 Jarvis is analysing your portfolio...")
    portfolio_summary = format_portfolio_for_ai(results)
    
    # Step 6: Get AI analysis
    analysis = get_ai_analysis(portfolio_summary)
    
    # Step 7: Display analysis
    print("\n" + "="*60)
    print("   📊 JARVIS ANALYSIS")
    print("="*60)
    print(analysis)
    
    # Step 8: Save full report
    save = input("\nSave full report? (Y/N): ").strip().upper()
    if save == "Y":
        save_report(results, analysis)
    
    print("\n✅ Jarvis signing off.")

if __name__ == "__main__":
    main()