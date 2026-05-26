import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import torch
import torch.nn as nn


class _LSTMNet(nn.Module):
    def __init__(self, window_size: int):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size=1, hidden_size=64, batch_first=True)
        self.drop1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(input_size=64, hidden_size=32, batch_first=True)
        self.drop2 = nn.Dropout(0.2)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.drop1(out)
        out, _ = self.lstm2(out)
        out = self.drop2(out)
        return self.fc(out[:, -1, :])


class LSTMModel:
    """
    Red LSTM con dos capas (64 → 32 unidades), Dropout 20% y capa densa
    de salida. Predicción iterativa multi-paso con ventana deslizante.
    Implementada en PyTorch.
    """

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.net: _LSTMNet | None = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self._last_window: np.ndarray | None = None
        self._last_date: pd.Timestamp | None = None
        self._device = torch.device("cpu")

    def fit(self, series: pd.Series, epochs: int = 50):
        values = series.values.astype(float).reshape(-1, 1)
        scaled = self.scaler.fit_transform(values).flatten()

        X, y = [], []
        for i in range(self.window_size, len(scaled)):
            X.append(scaled[i - self.window_size:i])
            y.append(scaled[i])

        X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1).to(self._device)
        y_t = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1).to(self._device)

        self.net = _LSTMNet(self.window_size).to(self._device)
        optimizer = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        loss_fn = nn.MSELoss()

        self.net.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            pred = self.net(X_t)
            loss = loss_fn(pred, y_t)
            loss.backward()
            optimizer.step()

        self._last_window = scaled[-self.window_size:]
        self._last_date = pd.to_datetime(series.index[-1])

    def predict(self, horizon: int) -> pd.Series:
        if self.net is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        self.net.eval()
        window = list(self._last_window)
        preds_scaled: list[float] = []
        with torch.no_grad():
            for _ in range(horizon):
                x = torch.tensor(window[-self.window_size:], dtype=torch.float32)
                x = x.unsqueeze(0).unsqueeze(-1).to(self._device)
                val = float(self.net(x).item())
                preds_scaled.append(val)
                window.append(val)

        preds = self.scaler.inverse_transform(
            np.array(preds_scaled).reshape(-1, 1)
        ).flatten()
        idx = pd.date_range(
            start=self._last_date + pd.Timedelta(days=1), periods=horizon
        )
        return pd.Series(np.maximum(preds, 0), index=idx)
