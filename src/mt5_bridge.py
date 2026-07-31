import pandas as pd
from datetime import datetime

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False

class MetaTrader5Bridge:
    def __init__(self):
        self.connected = False
        if HAS_MT5:
            self.connected = mt5.initialize()

    def get_account_info(self):
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
                    "mode": "LIVE_MT5"
                }
        return {
            "balance": 1000.0,
            "equity": 1000.0,
            "margin": 0.0,
            "free_margin": 1000.0,
            "leverage": 100,
            "broker": "Simulated Demo Broker",
            "mode": "SIMULATION"
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

        # Simulated fallback execution
        return {
            "status": "SIMULATED_SUCCESS",
            "ticket": int(datetime.now().timestamp()),
            "price": 0.0,
            "message": "Order executed in simulation mode."
        }

mt5_bridge = MetaTrader5Bridge()
