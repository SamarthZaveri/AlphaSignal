"""
random_forest.py — sklearn RandomForestClassifier.
Train on historical features, save/load checkpoints, run inference.
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import logging

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "../../checkpoints")


def train_rf(X: np.ndarray, y: np.ndarray, ticker: str = "multi"):
    """
    Train a Random Forest on features X with direction labels y.
    Uses time-series cross-validation to get honest accuracy estimate.
    Returns (model, cv_accuracy).
    """
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=10,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    for train_idx, val_idx in tscv.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        model.fit(X_tr, y_tr)
        preds = model.predict(X_val)
        cv_scores.append(accuracy_score(y_val, preds))

    cv_acc = float(np.mean(cv_scores))
    logger.info(f"RF CV accuracy for {ticker}: {cv_acc:.4f}")

    model.fit(X, y)
    return model, cv_acc


def save_rf(model: RandomForestClassifier, ticker: str = "multi") -> str:
    """Save RF model to checkpoints dir. Returns filepath."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CHECKPOINT_DIR, f"rf_{ticker}_{ts}.pkl")
    joblib.dump(model, path)
    logger.info(f"RF model saved: {path}")
    return path


def load_rf(ticker: str = "multi"):
    """Load the most recent RF checkpoint for a ticker."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    candidates = [
        f for f in os.listdir(CHECKPOINT_DIR)
        if f.startswith(f"rf_{ticker}") and f.endswith(".pkl")
    ]
    if not candidates:
        logger.warning(f"No RF checkpoint found for {ticker}")
        return None
    candidates.sort()
    path = os.path.join(CHECKPOINT_DIR, candidates[-1])
    model = joblib.load(path)
    logger.info(f"RF loaded: {path}")
    return model


def rf_predict(model, features: np.ndarray) -> dict:
    """
    Run inference. Returns direction ('UP'/'DOWN') and probability.
    features: shape (1, n_features)
    """
    if model is None:
        return {"direction": "HOLD", "prob_up": 0.5, "confidence": "LOW"}
    prob = model.predict_proba(features)[0]
    prob_up = float(prob[1]) if len(prob) > 1 else 0.5
    direction = "UP" if prob_up >= 0.5 else "DOWN"
    confidence = "HIGH" if abs(prob_up - 0.5) > 0.15 else "LOW"
    return {
        "direction": direction,
        "prob_up": round(prob_up, 4),
        "confidence": confidence,
    }


def get_feature_importances(model, feature_names: list) -> dict:
    """Return feature importances sorted descending."""
    if model is None or not hasattr(model, "feature_importances_"):
        return {}
    imps = model.feature_importances_
    return dict(sorted(zip(feature_names, imps.tolist()), key=lambda x: -x[1]))
