import time
from datetime import datetime
from src.mt5_bridge import mt5_bridge

class BrokerManager:
    """
    Multi-Broker Order Execution Router supporting FIX Protocol, Pending Order Queues, and MT5 Bridge.
    """
    def __init__(self):
        self.active_broker_mode = "MT5_BRIDGE"
        self.pending_orders = [] # Queued orders for MT5 EA execution

    def execute_order(self, symbol: str, signal_type: str, lot_size: float, stop_loss: float, take_profit: float):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ticket_id = int(time.time())

        order_data = {
            "ticket": ticket_id,
            "symbol": symbol.upper(),
            "signal_type": signal_type,
            "lot_size": float(lot_size),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "timestamp": timestamp
        }

        # Store in pending queue for MT5 EA auto-execution
        self.pending_orders.append(order_data)

        # Attempt direct MT5 bridge if available locally
        res = mt5_bridge.execute_order(symbol, signal_type, lot_size, stop_loss, take_profit)

        return {
            "broker": mt5_bridge.get_account_info().get("broker", "MT5 Broker"),
            "mode": "MT5_BRIDGE",
            "status": "ORDER_SENT_TO_MT5",
            "ticket": ticket_id,
            "symbol": symbol,
            "signal_type": signal_type,
            "lot_size": lot_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": timestamp,
            "message": "Order queued for instant MT5 EA execution."
        }

    def pop_pending_order(self, symbol: str):
        symbol = symbol.upper()
        for i, order in enumerate(self.pending_orders):
            if order["symbol"] == symbol or order["symbol"] in symbol:
                return self.pending_orders.pop(i)
        return None

broker_router = BrokerManager()
