import pandas as pd
from datetime import datetime, timedelta

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False

class MetaTrader5Bridge:
    def __init__(self):
        self.connected = False
        self.active_accounts = {}  # {account_id: {broker, balance, equity, last_ping}}
        if HAS_MT5:
            self.connected = mt5.initialize()

    def register_account_ping(self, account_id: str, broker: str = "Unknown Broker", balance: float = 1000.0, equity: float = 1000.0, leverage: int = 100):
        self.active_accounts[str(account_id)] = {
            "account_id": str(account_id),
            "broker": broker,
            "balance": balance,
            "equity": equity,
            "leverage": leverage,
            "last_ping": datetime.now()
        }

    def get_connected_accounts(self):
        now = datetime.now()
        active = []
        for acc_id, data in self.active_accounts.items():
            is_online = (now - data["last_ping"]) < timedelta(seconds=60)
            active.append({
                "account_id": data["account_id"],
                "broker": data["broker"],
                "balance": data["balance"],
                "equity": data["equity"],
                "leverage": data["leverage"],
                "status": "ONLINE" if is_online else "OFFLINE",
                "last_seen": data["last_ping"].strftime("%H:%M:%S")
            })
        return active

    def get_account_info(self):
        accounts = self.get_connected_accounts()
        if self.connected and HAS_MT5:
            info = mt5.account_info()
            if info:
                return {
                    "balance": info.balance,
                    "equity": info.equity,
                    "margin": info.margin,
                    "free_margin": info.margin_free,
                    "leverage": info.leverage,
                    "broker": info.company,
                    "mode": "LIVE_MT5",
                    "connected_accounts": accounts,
                    "connected_count": len([a for a in accounts if a["status"] == "ONLINE"])
                }
        return {
            "balance": 1000.0,
            "equity": 1000.0,
            "margin": 0.0,
            "free_margin": 1000.0,
            "leverage": 100,
            "broker": "Simulated Demo Broker",
            "mode": "SIMULATION",
            "connected_accounts": accounts,
            "connected_count": len([a for a in accounts if a["status"] == "ONLINE"])
        }

    def fetch_live_candles(self, symbol: str = "EURUSD", timeframe: str = "M15", num_bars: int = 500):
        if self.connected and HAS_MT5:
            tf_map = {
                "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15,
                "H1": mt5.TIMEFRAME_H1,
                "H4": mt5.TIMEFRAME_H4
            }
            mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_M15)
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, num_bars)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
        return None

    def execute_order(self, symbol: str, signal_type: str, lot: float, sl: float, tp: float):
        if self.connected and HAS_MT5:
            order_type = mt5.ORDER_TYPE_BUY if signal_type == "BUY" else mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).ask if signal_type == "BUY" else mt5.symbol_info_tick(symbol).bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(lot),
                "type": order_type,
                "price": price,
                "sl": float(sl),
                "tp": float(tp),
                "deviation": 20,
                "magic": 424242,
                "comment": "ForexMind AI Automated Trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return {"status": "SUCCESS", "ticket": result.order, "price": result.price}
            else:
                return {"status": "FAILED", "error": result.comment}

        return {
            "status": "SIMULATED_SUCCESS",
            "ticket": int(datetime.now().timestamp()),
            "price": 0.0,
            "message": "Order executed in simulation mode."
        }

mt5_bridge = MetaTrader5Bridge()
