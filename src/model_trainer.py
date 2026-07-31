import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

FEATURE_COLS = [
    'rsi_14', 'atr_14', 'ema_50_above_200', 'price_above_ema200', 'ema_slope_20',
    'macd', 'macd_hist', 'bollinger_width', 'candle_body', 'candle_range',
    'upper_wick', 'lower_wick', 'dist_to_support', 'dist_to_resistance',
    'return_1', 'return_3', 'return_5', 'hour', 'day_of_week',
    'is_asian', 'is_london', 'is_ny', 'is_overlap',
    'h1_trend_bullish', 'h1_ema_50_above_200', 'h1_rsi', 'h1_atr',
    'h4_trend_bullish', 'h4_ema_50_above_200', 'h4_rsi', 'h4_atr',
    'mtf_bias'
]

def prepare_feature_matrix(df: pd.DataFrame):
    """
    Extracts features matrix X and labels y.
    """
    existing_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[existing_cols].copy().fillna(0)
    y = df['target_label'].copy().fillna(0).astype(int) if 'target_label' in df.columns else None
    return X, y, existing_cols

def train_model(df_features: pd.DataFrame, model_type: str = "random_forest", symbol: str = "EURUSD"):
    """
    Trains High-Precision ML Classifier with class weight balancing.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    X, y, feature_names = prepare_feature_matrix(df_features)

    # Time-series chronological train/test split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    label_map = {-1: 0, 0: 1, 1: 2}
    inv_map = {0: -1, 1: 0, 2: 1}
    y_train_mapped = y_train.map(label_map)

    if model_type == "xgboost" and HAS_XGBOOST:
        model = XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.03,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train, y_train_mapped)
        y_pred_mapped = model.predict(X_test)
        y_pred = [inv_map[p] for p in y_pred_mapped]
    else:
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=4,
            class_weight='balanced_subsample',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    # Calculate Evaluation Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_test, y_pred).tolist()

    importances = model.feature_importances_
    feat_imp = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]

    model_filename = os.path.join(MODELS_DIR, f"{symbol}_model.joblib")
    joblib.dump({
        'model': model,
        'feature_names': feature_names,
        'model_type': model_type,
        'label_map': label_map if model_type == "xgboost" else None
    }, model_filename)

    metrics = {
        'symbol': symbol,
        'model_type': model_type,
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'confusion_matrix': cm,
        'feature_importances': feat_imp
    }
    return metrics, model

def predict_signal(model_dict: dict, df_features_last: pd.DataFrame):
    """
    Predicts signal probabilities for a single candle or dataframe.
    """
    model = model_dict['model']
    feature_names = model_dict['feature_names']
    
    X = df_features_last[feature_names].copy().fillna(0)
    probs = model.predict_proba(X)
    
    classes = model.classes_
    last_probs = probs[-1]
    
    prob_dict = {}
    for cls, prob in zip(classes, last_probs):
        orig_label = cls
        if model_dict.get('label_map') is not None:
            inv_map = {0: -1, 1: 0, 2: 1}
            orig_label = inv_map.get(cls, cls)
        prob_dict[orig_label] = float(prob)
        
    p_buy = prob_dict.get(1, 0.0)
    p_sell = prob_dict.get(-1, 0.0)
    p_notrade = prob_dict.get(0, 0.0)
    
    return p_buy, p_sell, p_notrade
