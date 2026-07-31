import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, log_signal, get_recent_signals, get_db_stats
from src.sentiment_analyzer import analyze_market_news
from src.deep_learning import train_ensemble_model
from src.mt5_bridge import mt5_bridge
from src.telegram_bot import format_telegram_message
from src.preprocessing import clean_data
from src.indicators import calculate_indicators
from src.multi_timeframe import align_multi_timeframe
from src.labeling import create_target_labels
from src.decision_engine import evaluate_signal
from src.model_trainer import predict_signal
import pandas as pd

print("--- TESTING MARKET-READY MODULES ---")

print("\n1. Testing Database Initialization & Logging...")
init_db()
mock_sig = {
    "symbol": "EURUSD",
    "timeframe": "M15",
    "final_signal": "BUY",
    "confidence_pct": 74.5,
    "entry_price": 1.0850,
    "stop_loss": 1.0825,
    "take_profit": 1.0900,
    "risk_reward": "1:2.0",
    "suggested_lot": 0.04,
    "market_condition": "Bullish Confluence",
    "reasons": ["Price above EMA 200", "H1 Bullish"],
    "warnings": []
}
log_signal(mock_sig)
stats = get_db_stats()
print(f"Database Stats: Total Signals={stats['total_signals']}")

print("\n2. Testing Financial NLP Sentiment Analysis...")
sentiment = analyze_market_news("EURUSD")
print(f"EURUSD Sentiment: {sentiment['sentiment_label']} (Score: {sentiment['sentiment_score']})")

print("\n3. Testing MetaTrader 5 Bridge Status...")
mt5_info = mt5_bridge.get_account_info()
print(f"MT5 Account Info: Broker={mt5_info['broker']}, Mode={mt5_info['mode']}")

print("\n4. Testing Telegram Signal Message Formatting...")
tg_text = format_telegram_message(mock_sig)
print("Telegram Message Preview Formatted Successfully!")

print("\n5. Testing Deep Learning Ensemble Training & Signal Engine Integration...")
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
df_m15 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, "EURUSD_M15.csv"))))
df_h1 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, "EURUSD_H1.csv"))))
df_h4 = calculate_indicators(clean_data(pd.read_csv(os.path.join(data_dir, "EURUSD_H4.csv"))))

df_merged = align_multi_timeframe(df_m15, df_h1, df_h4)
df_labeled = create_target_labels(df_merged)

ensemble_metrics, ensemble_model = train_ensemble_model(df_labeled, symbol="EURUSD")
print(f"Deep Ensemble Metrics: Accuracy={ensemble_metrics['accuracy']}, Precision={ensemble_metrics['precision']}")

feature_names = list(ensemble_model.rf.feature_names_in_)
model_dict = {'model': ensemble_model, 'feature_names': feature_names}
p_buy, p_sell, p_notrade = predict_signal(model_dict, df_merged)

final_res = evaluate_signal(df_merged, p_buy, p_sell, p_notrade, symbol="EURUSD")
print(f"\nFinal Engine Output: Signal={final_res['final_signal']} ({final_res['confidence_pct']}%)")
print(f"Sentiment Impact: {final_res['sentiment_label']} ({final_res['sentiment_score']})")

print("\n--- ALL MARKET-READY TESTS PASSED SUCCESSFULLY! ---")
