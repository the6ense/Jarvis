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
3. Add your coins one by one (name, symbol, quantity, total invested, profit target %, stop loss %)
4. Wait for live prices to load
5. Review your portfolio dashboard with real-time P&L and alerts
6. Read Jarvis AI Analysis — clear recommendations (Add / Hold / Take Profit / Cut Loss)
7. Optionally save a full professional report to file

---

## 📁 Project Structure
jarvis_v1.py                              # Main file
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