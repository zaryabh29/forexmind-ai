import math

PIP_VALUES = {
    "EURUSD": {"pip_size": 0.0001, "pip_value_per_lot": 10.0},
    "GBPUSD": {"pip_size": 0.0001, "pip_value_per_lot": 10.0},
    "USDJPY": {"pip_size": 0.01,   "pip_value_per_lot": 6.45},
    "XAUUSD": {"pip_size": 0.1,    "pip_value_per_lot": 10.0},
    "AUDUSD": {"pip_size": 0.0001, "pip_value_per_lot": 10.0},
}

def calculate_trade_levels(entry_price: float, signal_type: str, atr: float, symbol: str = "EURUSD", rr_target: float = 2.0):
    """
    Calculates Stop Loss and Take Profit levels using ATR.
    """
    pip_info = PIP_VALUES.get(symbol, PIP_VALUES["EURUSD"])
    pip_size = pip_info["pip_size"]
    
    # ATR multiplier: Gold requires wider SL (1.5x ATR), Forex (1.0x ATR)
    atr_mult = 1.5 if symbol == "XAUUSD" else 1.0
    sl_dist = max(atr * atr_mult, pip_size * 10)
    tp_dist = sl_dist * rr_target

    if signal_type == "BUY":
        stop_loss = entry_price - sl_dist
        take_profit = entry_price + tp_dist
    elif signal_type == "SELL":
        stop_loss = entry_price + sl_dist
        take_profit = entry_price - tp_dist
    else:
        stop_loss = entry_price
        take_profit = entry_price

    sl_pips = round(sl_dist / pip_size, 1)
    tp_pips = round(tp_dist / pip_size, 1)
    actual_rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0.0

    return {
        "entry_price": round(entry_price, 5 if pip_size < 0.01 else 2),
        "stop_loss": round(stop_loss, 5 if pip_size < 0.01 else 2),
        "take_profit": round(take_profit, 5 if pip_size < 0.01 else 2),
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "risk_reward": f"1:{actual_rr}",
        "rr_ratio": actual_rr
    }

def calculate_lot_size(account_balance: float, risk_percent: float, sl_pips: float, symbol: str = "EURUSD"):
    """
    Calculates suggested lot size based on account risk and SL distance.
    Formula: Lot Size = Risk Amount / (SL Pips * Pip Value per Lot)
    """
    if account_balance <= 0 or risk_percent <= 0 or sl_pips <= 0:
        return 0.01, 0.0

    risk_amount = account_balance * (risk_percent / 100.0)
    pip_info = PIP_VALUES.get(symbol, PIP_VALUES["EURUSD"])
    pip_val_per_lot = pip_info["pip_value_per_lot"]

    raw_lot = risk_amount / (sl_pips * pip_val_per_lot)
    lot_size = max(0.01, round(raw_lot, 2))
    
    return lot_size, round(risk_amount, 2)
