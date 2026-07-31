import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SYMBOLS_CONFIG = {
    "EURUSD": {"start_price": 1.0850, "pip_value": 0.0001, "spread_pips": 1.2, "volatility": 0.0008, "default_regime": 1},
    "GBPUSD": {"start_price": 1.2700, "pip_value": 0.0001, "spread_pips": 1.5, "volatility": 0.0012, "default_regime": -1}, # Bearish trend
    "USDJPY": {"start_price": 155.20, "pip_value": 0.01,   "spread_pips": 1.4, "volatility": 0.12,   "default_regime": 1},
    "XAUUSD": {"start_price": 2340.50, "pip_value": 0.1,   "spread_pips": 2.5, "volatility": 3.20,   "default_regime": -1}, # Bearish trend for gold
    "AUDUSD": {"start_price": 0.6650, "pip_value": 0.0001, "spread_pips": 1.3, "volatility": 0.0009, "default_regime": 1},
}

TIMEFRAME_MINUTES = {
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440
}

def generate_symbol_timeframe_data(symbol: str, timeframe: str, num_bars: int = 1500) -> pd.DataFrame:
    """
    Generates realistic synthetic OHLC data with both Bullish and Bearish market regimes.
    """
    config = SYMBOLS_CONFIG.get(symbol, SYMBOLS_CONFIG["EURUSD"])
    start_price = config["start_price"]
    pip_val = config["pip_value"]
    base_spread = config["spread_pips"] * pip_val
    base_vol = config["volatility"] * np.sqrt(TIMEFRAME_MINUTES.get(timeframe, 15) / 15.0)

    np.random.seed(hash(f"{symbol}_{timeframe}") % (2**32 - 1))
    
    end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    minutes_step = TIMEFRAME_MINUTES.get(timeframe, 15)
    timestamps = [end_time - timedelta(minutes=minutes_step * i) for i in range(num_bars)][::-1]

    prices = [start_price]
    regime = config.get("default_regime", 0)  # -1: Bearish, 0: Ranging, 1: Bullish
    
    for i in range(1, num_bars):
        # Switch regime periodically to create dynamic trends
        if i % 150 == 0:
            regime = np.random.choice([-1, 0, 1], p=[0.45, 0.1, 0.45])
        
        drift = regime * (base_vol * 0.35)
        shock = np.random.normal(0, base_vol)
        price_change = drift + shock
        new_price = max(pip_val * 10, prices[-1] + price_change)
        prices.append(new_price)

    data = []
    for i in range(num_bars):
        close_p = prices[i]
        open_p = prices[i-1] if i > 0 else close_p
        
        high_extra = abs(np.random.normal(base_vol * 0.5, base_vol * 0.3))
        low_extra = abs(np.random.normal(base_vol * 0.5, base_vol * 0.3))
        
        high_p = max(open_p, close_p) + high_extra
        low_p = min(open_p, close_p) - low_extra
        
        volume = int(np.random.normal(1200, 300))
        spread = round(base_spread + np.random.uniform(0, base_spread * 0.3), 6)

        data.append({
            "time": timestamps[i].strftime("%Y-%m-%d %H:%M:%S"),
            "open": round(open_p, 5 if pip_val < 0.01 else 2),
            "high": round(high_p, 5 if pip_val < 0.01 else 2),
            "low": round(low_p, 5 if pip_val < 0.01 else 2),
            "close": round(close_p, 5 if pip_val < 0.01 else 2),
            "tick_volume": max(100, volume),
            "spread": spread
        })

    df = pd.DataFrame(data)
    return df

def generate_all_datasets():
    """Generates and saves datasets for all symbol and timeframe combinations."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for symbol in SYMBOLS_CONFIG.keys():
        for tf in ["M5", "M15", "H1", "H4"]:
            filepath = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
            df = generate_symbol_timeframe_data(symbol, tf, num_bars=1200)
            df.to_csv(filepath, index=False)

    generate_economic_calendar()

def generate_economic_calendar():
    """Generates economic events dataset with high impact news."""
    now = datetime.now()
    events = []
    news_titles = [
        ("NFP - Non-Farm Payrolls", "USD", "High"),
        ("CPI Inflation Rate MoM", "USD", "High"),
        ("FOMC Interest Rate Decision", "USD", "High"),
        ("ECB Press Conference", "EUR", "High"),
        ("BOE Interest Rate Decision", "GBP", "High"),
        ("GDP Growth Rate QoQ", "USD", "High"),
        ("Retail Sales MoM", "USD", "Medium"),
        ("Unemployment Rate", "AUD", "High"),
        ("BOJ Monetary Policy Statement", "JPY", "High"),
    ]

    for i in range(-10, 10):
        event_date = now + timedelta(days=i)
        for title, curr, impact in news_titles[:3]:
            event_time = event_date.replace(hour=13, minute=30, second=0)
            events.append({
                "time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "currency": curr,
                "event": title,
                "impact": impact
            })
            
    df_news = pd.DataFrame(events)
    df_news.to_csv(os.path.join(DATA_DIR, "economic_calendar.csv"), index=False)

if __name__ == "__main__":
    generate_all_datasets()
