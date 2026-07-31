import urllib.request
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:8000"

endpoints_to_test = [
    ("/", "GET", None),
    ("/static/css/style.css", "GET", None),
    ("/static/js/api.js", "GET", None),
    ("/static/js/charts.js", "GET", None),
    ("/static/js/websocket.js", "GET", None),
    ("/static/js/app.js", "GET", None),
    ("/api/symbols", "GET", None),
    ("/api/mtf-matrix?symbol=EURUSD", "GET", None),
    ("/api/sentiment?symbol=EURUSD", "GET", None),
    ("/api/database/signals", "GET", None),
    ("/api/mql5/download", "GET", None),
    ("/api/signal", "POST", {"symbol": "EURUSD", "main_timeframe": "M15", "account_balance": 1000, "risk_percent": 1, "min_confidence": 0.55, "use_ensemble": False, "signal_direction": "AUTO"}),
    ("/api/signal", "POST", {"symbol": "GBPUSD", "main_timeframe": "M15", "account_balance": 1000, "risk_percent": 1, "min_confidence": 0.55, "use_ensemble": False, "signal_direction": "SELL"}),
    ("/api/backtest", "POST", {"symbol": "EURUSD", "main_timeframe": "M15", "initial_balance": 1000, "risk_percent": 1, "min_confidence": 0.55}),
    ("/api/calculate-risk", "POST", {"account_balance": 1000, "risk_percent": 1, "sl_pips": 25, "symbol": "EURUSD"}),
]

print("--- STARTING SYSTEM ENDPOINT & FRONTEND ASSET VALIDATION ---")

passed = 0
failed = 0

for path, method, payload in endpoints_to_test:
    url = BASE_URL + path
    try:
        if method == "GET":
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        else:
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})

        with urllib.request.urlopen(req) as resp:
            code = resp.status
            content = resp.read()
            if code == 200:
                print(f"[OK 200] {method} {path} ({len(content)} bytes)")
                passed += 1
            else:
                print(f"[FAIL {code}] {method} {path}")
                failed += 1
    except Exception as e:
        print(f"[ERROR] {method} {path} -> {e}")
        failed += 1

print(f"\n--- VALIDATION SUMMARY: {passed} PASSED, {failed} FAILED ---")
