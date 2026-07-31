import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def post_json(path, data):
    url = BASE_URL + path
    data_bytes = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_json(path):
    url = BASE_URL + path
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())

def get_text(path):
    url = BASE_URL + path
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode('utf-8')

print("==========================================================")
print("   FOREXMIND AI PRO - FULL LIVE SYSTEM DIAGNOSTIC")
print("==========================================================")

# 1. System Config & Status
symbols_data = get_json("/api/symbols")
print("\n[1] SYMBOLS & SYSTEM STATUS:")
print(f"    Available Pairs: {symbols_data['symbols']}")
print(f"    Directions     : {symbols_data['directions']}")
print(f"    Database Stats : {symbols_data['db_stats']}")
print(f"    MT5 Execution  : {symbols_data['mt5_status']['broker']} (Mode: {symbols_data['mt5_status']['mode']})")

# 2. Testing Signals for All Pairs & Directions
print("\n[2] LIVE SIGNAL EVALUATION ACROSS ASSETS:")
for sym in ["EURUSD", "GBPUSD", "XAUUSD"]:
    for mode in ["AUTO", "BUY", "SELL"]:
        sig = post_json("/api/signal", {
            "symbol": sym,
            "main_timeframe": "M15",
            "account_balance": 1000,
            "risk_percent": 1.0,
            "min_confidence": 0.55,
            "use_ensemble": False,
            "signal_direction": mode
        })
        print(f"    - {sym} ({mode} Mode): Signal={sig['final_signal']} ({sig['confidence_pct']}%), Entry={sig['entry_price']}, SL={sig['stop_loss']}, TP={sig['take_profit']}, Lot={sig['suggested_lot']}")

# 3. Multi-Timeframe Confluence Matrix
print("\n[3] MULTI-TIMEFRAME CONFLUENCE MATRIX (EURUSD):")
mtf = get_json("/api/mtf-matrix?symbol=EURUSD")
for row in mtf['matrix']:
    print(f"    - {row['timeframe']}: Close={row['close']}, Trend={row['trend']}, RSI={row['rsi']}, State={row['state']}")

# 4. Strategy Backtest Metrics
print("\n[4] STRATEGY BACKTEST RESULTS (EURUSD, GBPUSD, XAUUSD):")
for sym in ["EURUSD", "GBPUSD", "XAUUSD"]:
    bt = post_json("/api/backtest", {
        "symbol": sym,
        "main_timeframe": "M15",
        "initial_balance": 1000,
        "risk_percent": 1.0,
        "min_confidence": 0.55
    })
    s = bt['summary']
    print(f"    - {sym}: Profit=${s['net_profit']} ({s['net_return_pct']}%), Win Rate={s['win_rate_pct']}% ({s['win_count']}W/{s['loss_count']}L), Profit Factor={s['profit_factor']}, Max DD={s['max_drawdown_pct']}%")

# 5. Financial NLP News Sentiment Radar
print("\n[5] FINANCIAL NLP NEWS RADAR:")
sent = get_json("/api/sentiment?symbol=EURUSD")
print(f"    Sentiment: {sent['sentiment_label']} (Score: {sent['sentiment_score']})")
headlines = sent.get('items') or (sent['news_feed']['headlines'] if 'news_feed' in sent else [])
for h in headlines[:3]:
    t = h.get('headline') or h.get('title')
    print(f"    * {t}")

# 6. Risk Calculator
print("\n[6] POSITION RISK CALCULATOR:")
risk = post_json("/api/calculate-risk", {"account_balance": 1000, "risk_percent": 1.0, "sl_pips": 25, "symbol": "EURUSD"})
print(f"    Suggested Lot Size for 25 Pips Risk: {risk['suggested_lot_size']} Lot (${risk['risk_amount_usd']})")

# 7. MetaTrader 5 EA Script
ea_code = get_text("/api/mql5/download")
print(f"\n[7] METATRADER 5 EA SCRIPT:")
print(f"    EA Code Downloaded Successfully ({len(ea_code)} bytes)")

print("\n==========================================================")
print("   ALL OPTIONS AND OUTPUTS TESTED & OPERATIONAL LIVE!")
print("==========================================================")
