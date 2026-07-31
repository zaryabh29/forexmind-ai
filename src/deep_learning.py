import os
import joblib
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

class EnsembleStackingModel:
    """
    Ensemble Meta-Learner combining Random Forest, XGBoost, and Deep Neural Network (MLP).
    """
    def __init__(self, n_estimators: int = 100):
        self.rf = RandomForestClassifier(n_estimators=n_estimators, max_depth=8, random_state=42)
        self.mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42)
        self.xgb = XGBClassifier(n_estimators=n_estimators, max_depth=5, learning_rate=0.05, random_state=42) if HAS_XGBOOST else None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series):
        # Fit Random Forest
        self.rf.fit(X_train, y_train)
        # Fit Deep Neural Network (MLP)
        self.mlp.fit(X_train, y_train)
        # Fit XGBoost if available
        if self.xgb:
            label_map = {-1: 0, 0: 1, 1: 2}
            y_mapped = y_train.map(label_map)
            self.xgb.fit(X_train, y_mapped)

    def predict_proba(self, X: pd.DataFrame):
        p_rf = self.rf.predict_proba(X)
        p_mlp = self.mlp.predict_proba(X)

        if self.xgb:
            p_xgb = self.xgb.predict_proba(X)
            # Average probabilities across 3 models
            p_ensemble = (p_rf * 0.4) + (p_mlp * 0.3) + (p_xgb * 0.3)
        else:
            p_ensemble = (p_rf * 0.6) + (p_mlp * 0.4)

        return p_ensemble

    @property
    def classes_(self):
        return self.rf.classes_

def train_ensemble_model(df_features: pd.DataFrame, symbol: str = "EURUSD"):
    from src.model_trainer import prepare_feature_matrix
    X, y, feature_names = prepare_feature_matrix(df_features)

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = EnsembleStackingModel()
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)
    y_pred = model.rf.classes_[np.argmax(probs, axis=1)]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    model_filename = os.path.join(MODELS_DIR, f"{symbol}_ensemble_model.joblib")
    joblib.dump({
        'model': model,
        'feature_names': feature_names,
        'model_type': 'ensemble_stacking'
    }, model_filename)

    return {
        'symbol': symbol,
        'model_type': 'Ensemble Deep Learning + RF + XGBoost',
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4)
    }, model
