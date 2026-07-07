"""
train_lstm.py — LSTM training loop with walk-forward cross-validation.
Saves checkpoints to /checkpoints/lstm_v{timestamp}.pt
"""
import os
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
import logging
from .lstm import PriceLSTM, create_sequences, normalize_features, get_model, DEVICE

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "../../checkpoints")
SEQ_LEN = 30
EPOCHS = 30
BATCH_SIZE = 32
LR = 1e-3


def train_lstm(features_array: np.ndarray, ticker: str = "multi",
                epochs: int = EPOCHS, seq_len: int = SEQ_LEN):
    """
    Walk-forward training: train on 70% window, validate on next 30%.
    Returns (trained_model, val_loss).
    """
    X, y = create_sequences(features_array, seq_len)
    if len(X) < 100:
        logger.warning(f"Insufficient sequences for {ticker}: {len(X)}")
        n_features = features_array.shape[1] - 1
        return get_model(n_features), 0.0

    X_norm, feat_mean, feat_std = normalize_features(X)
    n_features = X_norm.shape[2]

    split = int(len(X_norm) * 0.7)
    X_train, X_val = X_norm[:split], X_norm[split:]
    y_train, y_val = y[:split], y[split:]

    model = get_model(n_features)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.HuberLoss()

    X_train_t = torch.tensor(X_train).to(DEVICE)
    y_train_t = torch.tensor(y_train).unsqueeze(-1).to(DEVICE)
    X_val_t = torch.tensor(X_val).to(DEVICE)
    y_val_t = torch.tensor(y_val).unsqueeze(-1).to(DEVICE)

    best_val = float("inf")
    best_state = None

    for epoch in range(epochs):
        model.train()
        idxs = np.random.permutation(len(X_train_t))
        total_loss = 0.0
        for i in range(0, len(idxs), BATCH_SIZE):
            batch_idx = idxs[i:i + BATCH_SIZE]
            batch_X = X_train_t[batch_idx]
            batch_y = y_train_t[batch_idx]
            optimizer.zero_grad()
            pred = model(batch_X)
            loss = criterion(pred, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
        scheduler.step()

        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                val_pred = model(X_val_t)
                val_loss = criterion(val_pred, y_val_t).item()
            if val_loss < best_val:
                best_val = val_loss
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            logger.info(f"Epoch {epoch+1}/{epochs} | Train: {total_loss:.4f} | Val: {val_loss:.4f}")

    if best_state:
        model.load_state_dict(best_state)

    return model, best_val


def save_lstm(model: PriceLSTM, ticker: str = "multi", meta: dict = None) -> str:
    """Save LSTM checkpoint with metadata."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CHECKPOINT_DIR, f"lstm_{ticker}_{ts}.pt")
    torch.save({
        "state_dict": model.state_dict(),
        "input_size": model.input_size,
        "hidden_size": model.hidden_size,
        "num_layers": model.num_layers,
        "meta": meta or {},
        "timestamp": ts,
    }, path)
    logger.info(f"LSTM saved: {path}")
    return path


def load_lstm(ticker: str = "multi"):
    """Load the most recent LSTM checkpoint for a ticker."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    candidates = [
        f for f in os.listdir(CHECKPOINT_DIR)
        if f.startswith(f"lstm_{ticker}") and f.endswith(".pt")
    ]
    if not candidates:
        logger.warning(f"No LSTM checkpoint found for {ticker}")
        return None
    candidates.sort()
    path = os.path.join(CHECKPOINT_DIR, candidates[-1])
    ckpt = torch.load(path, map_location=DEVICE)
    model = PriceLSTM(
        input_size=ckpt["input_size"],
        hidden_size=ckpt["hidden_size"],
        num_layers=ckpt["num_layers"],
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(DEVICE)
    model.eval()
    logger.info(f"LSTM loaded: {path}")
    return model


def lstm_predict(model: PriceLSTM, sequence: np.ndarray, current_price: float) -> dict:
    """
    Run LSTM inference on a feature sequence.
    sequence: (seq_len, n_features) numpy array
    Returns predicted close and pct change.
    """
    if model is None:
        return {"predicted_close": current_price, "predicted_pct": 0.0, "direction": "HOLD"}

    model.eval()
    seq_norm = (sequence - sequence.mean(axis=0)) / (sequence.std(axis=0) + 1e-8)
    x_tensor = torch.tensor(seq_norm[np.newaxis], dtype=torch.float32).to(DEVICE)

    with torch.no_grad():
        raw_pred = model(x_tensor).item()

    predicted_pct = float(np.clip(raw_pred * 0.02, -0.05, 0.05))
    predicted_close = round(current_price * (1 + predicted_pct), 2)
    direction = "UP" if predicted_pct > 0 else "DOWN"

    return {
        "predicted_close": predicted_close,
        "predicted_pct": round(predicted_pct * 100, 3),
        "direction": direction,
    }
