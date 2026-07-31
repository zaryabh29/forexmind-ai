import os
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def check_news_blackout(current_time, symbol: str = "EURUSD", buffer_minutes: int = 30):
    """
    Checks if there is a high-impact economic news event within buffer_minutes of current_time.
    """
    calendar_path = os.path.join(DATA_DIR, "economic_calendar.csv")
    if not os.path.exists(calendar_path):
        return False, None

    df_news = pd.read_csv(calendar_path)
    if df_news.empty or 'time' not in df_news.columns:
        return False, None

    df_news['time'] = pd.to_datetime(df_news['time'])
    
    # Filter for high impact
    df_high = df_news[df_news['impact'] == 'High']

    # Extract base currency or quote currency from symbol
    curr1 = symbol[:3]
    curr2 = symbol[3:] if len(symbol) >= 6 else ""
    
    df_symbol_news = df_high[df_high['currency'].isin([curr1, curr2])]

    if isinstance(current_time, str):
        current_time = pd.to_datetime(current_time)

    start_window = current_time - timedelta(minutes=buffer_minutes)
    end_window = current_time + timedelta(minutes=buffer_minutes)

    upcoming = df_symbol_news[
        (df_symbol_news['time'] >= start_window) & 
        (df_symbol_news['time'] <= end_window)
    ]

    if not upcoming.empty:
        event_info = upcoming.iloc[0].to_dict()
        event_info['time'] = event_info['time'].strftime("%Y-%m-%d %H:%M:%S")
        return True, event_info

    return False, None
