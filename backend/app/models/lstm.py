"""
lstm.py — PyTorch LSTM for price sequence prediction.
Input: sequence of OHLCV + technical features.
Output: predicted next close price (or normalized return).
"""
import torch
import torch.nn as nn
import numpy as np
import logging

logger = logging.getLogger(__name__)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class PriceLSTM(nn.Module):
    """
    Stacked LSTM for time-series price prediction.
    Predicts next-period close (normalized).
    """

    def __init__(self, input_size: int = 15, hidden_size: int = 128,
                 num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.norm = nn.LayerNorm(hidden_size)
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, seq_len, input_size) → (batch, 1)"""
        lstm_out, _ = self.lstm(x)
        last = lstm_out[:, -1, :]
        last = self.norm(last)
        return self.head(last)


def create_sequences(data: np.ndarray, seq_len: int = 30):
    """
    Create sliding window sequences for LSTM training.
    data: (T, n_features) where last column is the target (close or return)
    Returns X: (N, seq_len, n_features-1), y: (N,)
    """
    X, y = [], []
    features = data[:, :-1]
    targets = data[:, -1]
    for i in range(len(data) - seq_len):
        X.append(features[i:i + seq_len])
        y.append(targets[i + seq_len])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def normalize_features(X: np.ndarray):
    """Z-score normalize. Returns (X_norm, mean, std)."""
    mean = X.mean(axis=(0, 1), keepdims=True)
    std = X.std(axis=(0, 1), keepdims=True) + 1e-8
    return (X - mean) / std, mean.squeeze(), std.squeeze()


def get_model(input_size: int = 15) -> PriceLSTM:
    """Instantiate and return model on the right device."""
    model = PriceLSTM(input_size=input_size)
    model.to(DEVICE)
    return model
