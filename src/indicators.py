import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators for a clean OHLC dataframe.
    """
    df = df.copy()
    
    close = df['close']
    high = df['high']
    low = df['low']
    open_p = df['open']

    # --- Exponential Moving Averages (EMA) ---
    df['ema_20'] = close.ewm(span=20, adjust=False).mean()
    df['ema_50'] = close.ewm(span=50, adjust=False).mean()
    df['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # EMA Trend Alignment
    df['ema_50_above_200'] = (df['ema_50'] > df['ema_200']).astype(int)
    df['price_above_ema200'] = (close > df['ema_200']).astype(int)
    df['ema_slope_20'] = df['ema_20'].diff(3)

    # --- Relative Strength Index (RSI 14) ---
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, 1e-9))
    df['rsi_14'] = 100 - (100 / (1 + rs))

    # --- MACD (12, 26, 9) ---
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # --- Average True Range (ATR 14) ---
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = tr.rolling(window=14).mean()

    # --- Bollinger Bands (20, 2) ---
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    df['bollinger_upper'] = sma_20 + (std_20 * 2)
    df['bollinger_lower'] = sma_20 - (std_20 * 2)
    df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / sma_20

    # --- Candlestick Features ---
    df['candle_body'] = (close - open_p).abs()
    df['candle_range'] = high - low
    df['upper_wick'] = high - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - low
    df['is_bullish'] = (close >= open_p).astype(int)

    # --- Support & Resistance (Swing High/Low rolling 20) ---
    df['support_20'] = low.rolling(window=20).min()
    df['resistance_20'] = high.rolling(window=20).max()
    df['dist_to_support'] = close - df['support_20']
    df['dist_to_resistance'] = df['resistance_20'] - close

    # --- Returns ---
    df['return_1'] = close.pct_change(1)
    df['return_3'] = close.pct_change(3)
    df['return_5'] = close.pct_change(5)

    # Fill initial NaN values from rolling calculations
    df = df.bfill().ffill()
    return df
