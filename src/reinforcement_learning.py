import numpy as np
import pandas as pd

class RLTrailingStopAgent:
    """
    Reinforcement Learning Dynamic Trailing Stop Agent.
    Protects trade capital while allowing price room to breathe and reach Take Profit.
    """
    def __init__(self, risk_reward_base: float = 2.0):
        self.rr_base = risk_reward_base

    def evaluate_trailing_stop(self, entry_price: float, current_price: float, signal_type: str, atr: float, open_pips: float):
        """
        Determines whether to adjust trailing stop loss based on trade progress.
        """
        if atr <= 0 or entry_price <= 0:
            return {"action": "HOLD", "new_stop_loss": None, "reason": "Insufficient data"}

        # Calculate unrealized profit in ATR multiples
        if signal_type == "BUY":
            profit_dist = current_price - entry_price
        else:
            profit_dist = entry_price - current_price

        atr_profit_multiple = profit_dist / atr

        action = "HOLD"
        new_sl = None
        reason = "Trade within normal volatility bounds."

        # Rule 1: Move Stop Loss to Break-Even + 0.2x ATR locking after 1.4x ATR profit
        if atr_profit_multiple >= 1.4 and atr_profit_multiple < 1.8:
            action = "MOVE_TO_BREAKEVEN"
            if signal_type == "BUY":
                new_sl = entry_price + (0.2 * atr)
            else:
                new_sl = entry_price - (0.2 * atr)
            reason = "RL Agent: Moved Stop Loss to Break-Even + Lock-in after 1.4x ATR profit."

        # Rule 2: Active Trailing Stop Loss at 1.8x ATR profit
        elif atr_profit_multiple >= 1.8:
            action = "TRAIL_STOP"
            if signal_type == "BUY":
                new_sl = current_price - (0.6 * atr)
            else:
                new_sl = current_price + (0.6 * atr)
            reason = f"RL Agent: Trailing Stop Loss activated at {atr_profit_multiple:.1f}x ATR profit."

        return {
            "action": action,
            "new_stop_loss": round(new_sl, 5) if new_sl else None,
            "atr_profit_multiple": round(atr_profit_multiple, 2),
            "reason": reason
        }

rl_agent = RLTrailingStopAgent()
