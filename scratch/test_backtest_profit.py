import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.generator import generate_all_datasets
from src.preprocessing import clean_data
from src.indicators import calculate_indicators
from src.multi_timeframe import align_multi_timeframe
from src.labeling import create_target_labels
from src.model_trainer import train_model
from src.backtester import run_backtest

generate_all_datasets()

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

for sym in ["EURUSD", "GBPUSD", "XAUUSD"]:
    df_m15 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_M15.csv"))))
    df_h1 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_H1.csv"))))
    df_h4 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, f"{sym}_H4.csv"))))

    df_merged = align_multi_timeframe(df_m15, df_h1, df_h4)
    df_labeled = create_target_labels(df_merged)

    # Train model first for accurate predictive signals
    train_model(df_labeled, model_type="random_forest", symbol=sym)

    # Run upgraded backtest with RL Trailing Stops
    bt_res = run_backtest(df_merged, initial_balance=1000.0, risk_percent=1.0, symbol=sym, min_confidence=0.55)
    s = bt_res['summary']

    print(f"=== {sym} HIGH-PERFORMANCE BACKTEST RESULTS ===")
    print(f"Initial Balance : ${s['initial_balance']}")
    print(f"Final Balance   : ${s['final_balance']}")
    print(f"Net Profit      : ${s['net_profit']} ({s['net_return_pct']}%)")
    print(f"Win Rate        : {s['win_rate_pct']}% ({s['win_count']} Wins / {s['loss_count']} Losses / {s['breakeven_count']} Break-Even)")
    print(f"Profit Factor   : {s['profit_factor']}")
    print(f"Max Drawdown    : {s['max_drawdown_pct']}%\n")
