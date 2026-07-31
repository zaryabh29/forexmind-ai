import os
import pandas as pd
import numpy as np
import joblib
from src.risk_management import calculate_trade_levels, calculate_lot_size, PIP_VALUES
from src.reinforcement_learning import rl_agent

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

def run_backtest(
    df_merged: pd.DataFrame,
    initial_balance: float = 1000.0,
    risk_percent: float = 1.0,
    symbol: str = "EURUSD",
    min_confidence: float = 0.55,
    max_holding_bars: int = 36
):
    """
    High-Performance Institutional Quantitative Backtester.
    Calculates accurate Win/Loss ratios, Profit Factor, Net Returns, and Drawdown.
    """
    df = df_merged.copy().reset_index(drop=True)
    balance = initial_balance
    equity_curve = [initial_balance]
    drawdown_curve = [0.0]
    peak_balance = initial_balance

    trades = []
    in_position = False
    current_trade = None

    pip_info = PIP_VALUES.get(symbol, PIP_VALUES["EURUSD"])
    pip_size = pip_info["pip_size"]
    pip_val_per_lot = pip_info["pip_value_per_lot"]

    model_file = os.path.join(MODELS_DIR, f"{symbol}_model.joblib")
    model_dict = None
    if os.path.exists(model_file):
        try:
            model_dict = joblib.load(model_file)
        except Exception:
            model_dict = None

    for i in range(50, len(df)):
        row = df.iloc[i]
        curr_time = str(row['time'])
        curr_close = float(row['close'])
        curr_high = float(row['high'])
        curr_low = float(row['low'])
        atr = float(row.get('atr_14', 0.0010))
        spread = float(row.get('spread', 0.00015))
        mtf_bias = int(row.get('mtf_bias', 0))
        rsi = float(row.get('rsi_14', 50.0))
        ema_20 = float(row.get('ema_20', curr_close))
        ema_50 = float(row.get('ema_50', curr_close))
        ema_200 = float(row.get('ema_200', curr_close))
        macd_hist = float(row.get('macd_hist', 0.0))

        # 1. Manage Open Position Exits & Trailing Stops
        if in_position and current_trade:
            sig = current_trade['signal']
            sl = current_trade['stop_loss']
            tp = current_trade['take_profit']
            lot = current_trade['lot_size']
            entry = current_trade['entry_price']
            holding_bars = i - current_trade['entry_bar']

            # Evaluate RL Trailing Stop adjustment
            open_pips = (curr_close - entry) / pip_size if sig == "BUY" else (entry - curr_close) / pip_size
            rl_res = rl_agent.evaluate_trailing_stop(entry, curr_close, sig, atr, open_pips)
            if rl_res['action'] in ["MOVE_TO_BREAKEVEN", "TRAIL_STOP"] and rl_res['new_stop_loss']:
                if sig == "BUY" and rl_res['new_stop_loss'] > sl:
                    sl = rl_res['new_stop_loss']
                    current_trade['stop_loss'] = sl
                elif sig == "SELL" and rl_res['new_stop_loss'] < sl:
                    sl = rl_res['new_stop_loss']
                    current_trade['stop_loss'] = sl

            exit_price = None
            result = None

            if sig == "BUY":
                if curr_low <= sl:
                    exit_price = sl
                    pnl_pips = (exit_price - entry) / pip_size
                    result = "WIN" if pnl_pips > 5 else ("BREAKEVEN" if abs(pnl_pips) <= 5 else "LOSS")
                elif curr_high >= tp:
                    exit_price = tp
                    result = "WIN"
                elif holding_bars >= max_holding_bars:
                    exit_price = curr_close
                    pnl_pips = (exit_price - entry) / pip_size
                    result = "WIN" if pnl_pips > 5 else ("BREAKEVEN" if abs(pnl_pips) <= 5 else "LOSS")
            elif sig == "SELL":
                if curr_high >= sl:
                    exit_price = sl
                    pnl_pips = (entry - exit_price) / pip_size
                    result = "WIN" if pnl_pips > 5 else ("BREAKEVEN" if abs(pnl_pips) <= 5 else "LOSS")
                elif curr_low <= tp:
                    exit_price = tp
                    result = "WIN"
                elif holding_bars >= max_holding_bars:
                    exit_price = curr_close
                    pnl_pips = (entry - exit_price) / pip_size
                    result = "WIN" if pnl_pips > 5 else ("BREAKEVEN" if abs(pnl_pips) <= 5 else "LOSS")

            if result:
                pips = (exit_price - entry) / pip_size if sig == "BUY" else (entry - exit_price) / pip_size
                pnl = (pips * pip_val_per_lot * lot) - (spread / pip_size * pip_val_per_lot * lot)
                balance += pnl

                current_trade['exit_time'] = curr_time
                current_trade['exit_price'] = round(exit_price, 5 if pip_size < 0.01 else 2)
                current_trade['pnl'] = round(pnl, 2)
                current_trade['result'] = "WIN" if pnl > 0.50 else ("LOSS" if pnl < -0.50 else "BREAKEVEN")
                trades.append(current_trade)

                in_position = False
                current_trade = None

        # 2. Check High-Confluence Entry Conditions
        if not in_position:
            p_buy, p_sell, p_notrade = 0.3, 0.3, 0.4
            if model_dict:
                try:
                    feature_names = model_dict['feature_names']
                    feat_vector = df.iloc[[i]][feature_names].fillna(0)
                    probs = model_dict['model'].predict_proba(feat_vector)[0]
                    classes = list(model_dict['model'].classes_)
                    p_buy = probs[classes.index(1)] if 1 in classes else 0.0
                    p_sell = probs[classes.index(-1)] if -1 in classes else 0.0
                    p_notrade = probs[classes.index(0)] if 0 in classes else 0.0
                except Exception:
                    pass

            signal_candidate = "NO TRADE"

            # Strict High-Probability Entry Filters
            if (p_buy >= min_confidence or (ema_20 > ema_50 > ema_200 and 48 <= rsi <= 68 and macd_hist > 0)) and mtf_bias >= 0:
                signal_candidate = "BUY"
            elif (p_sell >= min_confidence or (ema_20 < ema_50 < ema_200 and 32 <= rsi <= 52 and macd_hist < 0)) and mtf_bias <= 0:
                signal_candidate = "SELL"

            if signal_candidate != "NO TRADE":
                levels = calculate_trade_levels(curr_close, signal_candidate, atr, symbol=symbol, rr_target=2.0)
                lot, _ = calculate_lot_size(balance, risk_percent, levels['sl_pips'], symbol=symbol)

                current_trade = {
                    "trade_id": len(trades) + 1,
                    "entry_time": curr_time,
                    "entry_bar": i,
                    "signal": signal_candidate,
                    "entry_price": round(curr_close, 5 if pip_size < 0.01 else 2),
                    "stop_loss": levels['stop_loss'],
                    "take_profit": levels['take_profit'],
                    "lot_size": lot
                }
                in_position = True

        equity_curve.append(round(balance, 2))
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance * 100.0 if peak_balance > 0 else 0.0
        drawdown_curve.append(round(dd, 2))

    # Calculate Statistics
    total_trades = len(trades)
    wins = [t for t in trades if t['pnl'] > 0.50]
    losses = [t for t in trades if t['pnl'] < -0.50]
    breakevens = [t for t in trades if abs(t['pnl']) <= 0.50]

    decisive_trades = len(wins) + len(losses)
    win_rate = (len(wins) / decisive_trades * 100.0) if decisive_trades > 0 else 0.0
    
    total_profit = sum(t['pnl'] for t in wins)
    total_loss = abs(sum(t['pnl'] for t in losses))
    net_profit = round(balance - initial_balance, 2)
    profit_factor = round(total_profit / total_loss, 2) if total_loss > 0 else (99.0 if total_profit > 0 else 0.0)
    max_drawdown = round(max(drawdown_curve) if drawdown_curve else 0.0, 2)

    return {
        "summary": {
            "symbol": symbol,
            "initial_balance": initial_balance,
            "final_balance": round(balance, 2),
            "net_profit": net_profit,
            "net_return_pct": round((net_profit / initial_balance) * 100.0, 2),
            "total_trades": total_trades,
            "win_count": len(wins),
            "loss_count": len(losses),
            "breakeven_count": len(breakevens),
            "win_rate_pct": round(win_rate, 1),
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown
        },
        "equity_curve": equity_curve[::max(1, len(equity_curve)//100)],
        "trades": trades
    }
