import pandas as pd
import numpy as np

def align_multi_timeframe(df_lower: pd.DataFrame, df_h1: pd.DataFrame, df_h4: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns higher timeframe (H1, H4) indicators onto lower timeframe (M15/M5) candles
    strictly without lookahead bias.
    """
    df_lower = df_lower.copy().sort_values('time').reset_index(drop=True)
    df_h1 = df_h1.copy().sort_values('time').reset_index(drop=True)
    df_h4 = df_h4.copy().sort_values('time').reset_index(drop=True)

    # Compute H1 Trend Features
    df_h1_feat = pd.DataFrame({
        'time': df_h1['time'],
        'h1_trend_bullish': (df_h1['close'] > df_h1['ema_200']).astype(int),
        'h1_ema_50_above_200': (df_h1['ema_50'] > df_h1['ema_200']).astype(int),
        'h1_rsi': df_h1['rsi_14'],
        'h1_atr': df_h1['atr_14']
    })

    # Compute H4 Trend Features
    df_h4_feat = pd.DataFrame({
        'time': df_h4['time'],
        'h4_trend_bullish': (df_h4['close'] > df_h4['ema_200']).astype(int),
        'h4_ema_50_above_200': (df_h4['ema_50'] > df_h4['ema_200']).astype(int),
        'h4_rsi': df_h4['rsi_14'],
        'h4_atr': df_h4['atr_14']
    })

    # As-of merge to prevent lookahead data leakage
    # backward direction matches lower timeframe time T with highest H1 time <= T
    df_merged = pd.merge_asof(
        df_lower,
        df_h1_feat,
        on='time',
        direction='backward'
    )

    df_merged = pd.merge_asof(
        df_merged,
        df_h4_feat,
        on='time',
        direction='backward'
    )

    # Overall Multi-Timeframe Bias Calculation
    # 1: Strong Bullish, -1: Strong Bearish, 0: Mixed/Ranging
    h1_bull = df_merged['h1_trend_bullish']
    h4_bull = df_merged['h4_trend_bullish']
    
    bias = np.where((h1_bull == 1) & (h4_bull == 1), 1,
           np.where((h1_bull == 0) & (h4_bull == 0), -1, 0))
    
    df_merged['mtf_bias'] = bias
    df_merged = df_merged.bfill().ffill()
    return df_merged
