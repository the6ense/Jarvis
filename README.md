# 🤖 JARVIS — AI Crypto Portfolio Analyst

A smart, personal crypto portfolio manager that fetches live prices, calculates real-time P&L, tracks profit targets & stop losses, and delivers AI-powered analysis using GPT.

Built for serious crypto investors who want data-driven insights, not just numbers.

---
## ✨ Features
- **Live Price Tracking** — Real-time prices + 24h change from CoinGecko API
- **Advanced P&L Calculator** — Per asset and total portfolio (in $ and %)
- **Smart Alerts** — Profit target and Stop Loss notifications
- **AI Analyst (Jarvis)** — Professional-grade analysis and trade recommendations using GPT
- **Professional Reports** — Timestamped .txt reports with full AI analysis included
- **User-Friendly** — Simple step-by-step input flow
- **Portfolio Persistence** — Auto-saves holdings to `portfolio.json` so you don’t re-enter data each run
- **Historical CSV Tracking** — Automatically appends daily snapshots to `portfolio_history.csv`
- **Skip-AI Mode** — Run a quick price and P&L dashboard without waiting for OpenAI
- **Add/Remove Coin Menu** — Edit an existing saved portfolio directly from the menu
- **Input Validation** — Prevents bad entries like zero quantity, negative investment, or invalid numbers
- **Better API Error Handling** — Retries CoinGecko on transient failures / rate limits and handles OpenAI errors gracefully

---

## 🪙 Supported Coins

BTC, ETH, SOL, BNB, XRP, ADA, DOGE, DOT, MATIC, LINK

> Easy to extend by updating the `SYMBOL_TO_ID` dictionary in the code.

---

## ⚙️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/the6ense/jarvis.git
cd jarvis
```

**2. Install dependencies**
```bash
pip install requests openai
```

**3. Set up your OpenAI API Key**
```bash
export OPENAI_API_KEY="your-api-key-here"
```
> Add this to your `~/.bashrc` to make it permanent.

**4. Run Jarvis**
```bash
python3 jarvis_v1.py
```

---

## 🚀 How to Use
1. Set your OpenAI API key (see Installation)
2. Run the script
3. JARVIS will check for `portfolio.json` and load your saved holdings
4. Review loaded coins on the Portfolio Management menu:
   - A — Add coin
   - R — Remove coin
   - D — Done editing
5. Wait for live prices to load
6. Review your portfolio dashboard with real-time P&L and alerts
7. Choose whether to run AI analysis
8. Optionally save a full professional report to file

## 📁 Project Structure
jarvis_v1.py                              # Main file
portfolio.json                            # Saved portfolio data
portfolio_history.csv                     # Daily price / P&L history
jarvis_report_YYYY-MM-DD_HH-MM-SS.txt    # Generated reports (gitignored)

---

## 🛠 Built With

- **Python 3** 
- **CoinGecko API** — Free live cryptocurrency data
- **OpenAI GPT** — Intelligent portfolio analysis
- **requests** — HTTP library

---

## ⚠️ Disclaimer

This tool is for informational purposes only. Nothing here constitutes financial advice. Always do your own research before making any investment decisions.

---

## 👤 Author

StefCo — [the6ense](https://github.com/the6ense)