import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import generate_all_datasets
from src.preprocessing import clean_data
from src.indicators import calculate_indicators
from src.multi_timeframe import align_multi_timeframe
from src.labeling import create_target_labels
from src.model_trainer import train_model, predict_signal, FEATURE_COLS
from src.decision_engine import evaluate_signal
from src.backtester import run_backtest
import pandas as pd

print("1. Generating synthetic market data...")
generate_all_datasets()

print("2. Testing data pipeline for EURUSD...")
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
df_m15 = pd.read_csv(os.path.join(data_dir, "EURUSD_M15.csv"))
df_h1 = pd.read_csv(os.path.join(data_dir, "EURUSD_H1.csv"))
df_h4 = pd.read_csv(os.path.join(data_dir, "EURUSD_H4.csv"))

df_m15 = calculate_indicators(clean_data(df_m15))
df_h1 = calculate_indicators(clean_data(df_h1))
df_h4 = calculate_indicators(clean_data(df_h4))

print("3. Aligning Multi-Timeframe Data...")
df_merged = align_multi_timeframe(df_m15, df_h1, df_h4)
df_labeled = create_target_labels(df_merged)

print("4. Training Random Forest Model...")
metrics, model = train_model(df_labeled, model_type="random_forest", symbol="EURUSD")
print(f"Model Metrics: Accuracy={metrics['accuracy']}, Precision={metrics['precision']}, F1={metrics['f1_score']}")

print("5. Evaluating Signal Engine...")
feature_names = [c for c in FEATURE_COLS if c in df_labeled.columns]
model_dict = {'model': model, 'feature_names': feature_names}
p_buy, p_sell, p_notrade = predict_signal(model_dict, df_labeled)

signal_res = evaluate_signal(df_merged, p_buy, p_sell, p_notrade, symbol="EURUSD")
print(f"Signal Result: {signal_res['final_signal']} ({signal_res['confidence_pct']}%)")
print(f"Entry={signal_res['entry_price']}, SL={signal_res['stop_loss']}, TP={signal_res['take_profit']}, Lot={signal_res['suggested_lot']}")

print("6. Running Backtest...")
bt_res = run_backtest(df_merged, symbol="EURUSD")
print(f"Backtest Summary: Total Trades={bt_res['summary']['total_trades']}, Win Rate={bt_res['summary']['win_rate_pct']}%, Net Return={bt_res['summary']['net_return_pct']}%")
print("ALL TESTS PASSED SUCCESSFULLY!")
