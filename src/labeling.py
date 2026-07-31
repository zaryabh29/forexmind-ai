import pandas as pd
import numpy as np

def create_target_labels(df: pd.DataFrame, sl_atr_mult: float = 1.0, tp_atr_mult: float = 2.0, forward_candles: int = 12) -> pd.DataFrame:
    """
    Creates realistic target labels based on triple-barrier outcome:
    1  = Buy (TP hit before SL)
    -1 = Sell (TP hit before SL for Sell)
    0  = No Trade (Neither or SL hit first)
    """
    df = df.copy()
    n = len(df)
    labels = np.zeros(n, dtype=int)

    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    atrs = df['atr_14'].values

    for i in range(n - forward_candles):
        entry = closes[i]
        atr = atrs[i]
        
        if atr <= 0 or np.isnan(atr):
            continue

        sl_dist = sl_atr_mult * atr
        tp_dist = tp_atr_mult * atr

        # Buy setup check
        buy_sl = entry - sl_dist
        buy_tp = entry + tp_dist

        # Sell setup check
        sell_sl = entry + sl_dist
        sell_tp = entry - tp_dist

        buy_result = 0  # 1 for TP hit, -1 for SL hit
        sell_result = 0

        # Check future forward candles
        for j in range(i + 1, i + 1 + forward_candles):
            curr_high = highs[j]
            curr_low = lows[j]

            # Check Buy outcome
            if buy_result == 0:
                if curr_high >= buy_tp:
                    buy_result = 1
                elif curr_low <= buy_sl:
                    buy_result = -1

            # Check Sell outcome
            if sell_result == 0:
                if curr_low <= sell_tp:
                    sell_result = 1
                elif curr_high >= sell_sl:
                    sell_result = -1

            if buy_result != 0 and sell_result != 0:
                break

        if buy_result == 1 and sell_result != 1:
            labels[i] = 1
        elif sell_result == 1 and buy_result != 1:
            labels[i] = -1
        else:
            labels[i] = 0

    df['target_label'] = labels
    return df
