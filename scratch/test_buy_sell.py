import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.generator import generate_all_datasets
from src.preprocessing import clean_data
from src.indicators import calculate_indicators
from src.multi_timeframe import align_multi_timeframe
from src.decision_engine import evaluate_signal

generate_all_datasets()

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

for sym in ["EURUSD", "GBPUSD", "XAUUSD"]:
    df_m15 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_M15.csv"))))
    df_h1 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_H1.csv"))))
    df_h4 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_H4.csv"))))

    df_merged = align_multi_timeframe(df_m15, df_h1, df_h4)

    buy_res = evaluate_signal(df_merged, p_buy=0.75, p_sell=0.10, p_notrade=0.15, symbol=sym, signal_direction="BUY")
    sell_res = evaluate_signal(df_merged, p_buy=0.10, p_sell=0.75, p_notrade=0.15, symbol=sym, signal_direction="SELL")

    print(f"=== {sym} SIGNAL VERIFICATION ===")
    print(f"BUY Setup  -> Signal: {buy_res['final_signal']}, Entry: {buy_res['entry_price']}, SL: {buy_res['stop_loss']}, TP: {buy_res['take_profit']}, Lot: {buy_res['suggested_lot']}")
    print(f"SELL Setup -> Signal: {sell_res['final_signal']}, Entry: {sell_res['entry_price']}, SL: {sell_res['stop_loss']}, TP: {sell_res['take_profit']}, Lot: {sell_res['suggested_lot']}\n")
