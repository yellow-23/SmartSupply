import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.utils.data as data_utils


# Feriados fijos chilenos como conjunto MM-DD (igual que xgboost_model)
_CHILE_HOLIDAYS_MD: set[str] = {
    "01-01", "05-01", "05-21", "07-16", "08-15",
    "09-18", "09-19", "10-12", "11-01", "12-08", "12-25",
}


class _LSTMNet(nn.Module):
    """
    Arquitectura seq-to-vec:  LSTM(num_layers) → Linear(output_size).
    Entrada:  (batch, seq_len, n_features)
    Salida:   (batch, output_size)  — predicción directa de output_size pasos.
    """

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        num_layers: int,
        output_size: int,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            n_features,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.head = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)          # (B, seq_len, hidden)
        return self.head(out[:, -1, :])  # (B, output_size)


class LSTMModel:
    """
    Red LSTM con estrategia DIRMO (Direct Multi-Step Output) usando PyTorch.

    Predice los próximos ``effective_horizon`` pasos en una sola pasada,
    sin usar predicciones propias como entradas (sin error acumulado).

    Arquitectura: 2 capas LSTM (64 unidades) + Dropout(0.2) + Dense(max_k).

    Features por timestep (6 columnas):
      [ventas_norm, dow_sin, dow_cos, month_sin, month_cos, is_holiday]

    Hiperparámetros:
      hidden=64, layers=2, lr=5e-3, weight_decay=1e-4, HuberLoss, grad_clip=1
    """

    MAX_HORIZON = 90
    HIDDEN_SIZE = 64
    NUM_LAYERS  = 2
    LR          = 5e-3
    WEIGHT_DECAY = 1e-4
    BATCH_SIZE  = 32
    N_FEATURES  = 6   # [sales, dow_sin, dow_cos, month_sin, month_cos, is_holiday]
    MIN_SERIES_LEN = 91

    def __init__(self):
        self._net: _LSTMNet | None = None
        self._last_date: pd.Timestamp | None = None
        self._seq_len: int = 30
        self._effective_horizon: int = 30
        self._scaler_mean: float = 0.0
        self._scaler_std: float = 1.0
        self._tail_features: np.ndarray | None = None  # (seq_len, N_FEATURES)
        self._dow_mean: dict[int, float] = {}  # media historica por dia de semana

    def _build_features(self, series: pd.Series) -> np.ndarray:
        """
        Devuelve array (n, 6): ventas + features cíclicas de calendario.
        La columna 0 (ventas) está en escala original; normalizar en fit().
        """
        idx = pd.to_datetime(series.index)
        sales = series.values.astype(np.float32)

        dow   = idx.dayofweek.values
        month = idx.month.values
        is_hol = np.array(
            [1.0 if d.strftime("%m-%d") in _CHILE_HOLIDAYS_MD else 0.0 for d in idx],
            dtype=np.float32,
        )
        dow_sin   = np.sin(2 * np.pi * dow / 7).astype(np.float32)
        dow_cos   = np.cos(2 * np.pi * dow / 7).astype(np.float32)
        month_sin = np.sin(2 * np.pi * (month - 1) / 12).astype(np.float32)
        month_cos = np.cos(2 * np.pi * (month - 1) / 12).astype(np.float32)

        return np.column_stack([sales, dow_sin, dow_cos, month_sin, month_cos, is_hol])

    def fit(self, series: pd.Series, epochs: int = 50):
        series = series.astype(float)
        n = len(series)

        if n < self.MIN_SERIES_LEN:
            raise ValueError(f"Serie muy corta para LSTM: {n} < {self.MIN_SERIES_LEN}")

        self._last_date = pd.to_datetime(series.index[-1])
        self._seq_len   = min(30, max(7, n // 4))
        self._effective_horizon = min(
            self.MAX_HORIZON, max(7, n - self._seq_len - 20)
        )

        # Construir features y normalizar ventas (col 0) por media/std
        feats = self._build_features(series)
        self._scaler_mean = float(feats[:, 0].mean())
        self._scaler_std  = max(float(feats[:, 0].std()), 1.0)
        feats[:, 0] = (feats[:, 0] - self._scaler_mean) / self._scaler_std

        # Guardar últimas seq_len filas para inferencia
        self._tail_features = feats[-self._seq_len:].copy()

        # Media histórica por día de semana: usada en predict() para cerrar días apagados
        raw_vals = series.values.astype(float)
        raw_idx  = pd.to_datetime(series.index)
        series_mean = raw_vals.mean()
        for dow in range(7):
            self._dow_mean[dow] = float(raw_vals[raw_idx.dayofweek == dow].mean())

        # Dataset DIRMO: X[i]=feats[i:i+seq_len], y[i]=ventas_norm[i+seq_len:i+seq_len+eff_h]
        X_list, y_list = [], []
        for i in range(n - self._seq_len - self._effective_horizon + 1):
            X_list.append(feats[i : i + self._seq_len])
            y_list.append(
                feats[i + self._seq_len : i + self._seq_len + self._effective_horizon, 0]
            )

        if not X_list:
            raise ValueError(f"Sin ventanas de entrenamiento: n={n}")

        X_t = torch.tensor(np.array(X_list))                        # (N, seq, 6)
        y_t = torch.tensor(np.array(y_list, dtype=np.float32))      # (N, eff_h)

        self._net = _LSTMNet(
            n_features   = self.N_FEATURES,
            hidden_size  = self.HIDDEN_SIZE,
            num_layers   = self.NUM_LAYERS,
            output_size  = self._effective_horizon,
        )

        optimizer = torch.optim.Adam(
            self._net.parameters(), lr=self.LR, weight_decay=self.WEIGHT_DECAY
        )
        loss_fn = nn.HuberLoss()
        loader  = data_utils.DataLoader(
            data_utils.TensorDataset(X_t, y_t),
            batch_size=self.BATCH_SIZE,
            shuffle=True,
        )

        self._net.train()
        for _ in range(epochs):
            for xb, yb in loader:
                pred = self._net(xb)
                loss = loss_fn(pred, yb)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self._net.parameters(), 1.0)
                optimizer.step()
        self._net.eval()

    def predict(self, horizon: int) -> pd.Series:
        if self._net is None:
            raise RuntimeError("Llama a fit() antes de predict()")

        tail = torch.tensor(self._tail_features[np.newaxis])  # (1, seq_len, 6)
        with torch.no_grad():
            raw = self._net(tail)[0].numpy()  # (effective_horizon,)

        # Denormalizar y recortar a [horizon] pasos
        n_use = min(horizon, self._effective_horizon)
        preds = raw[:n_use] * self._scaler_std + self._scaler_mean
        preds = np.maximum(0.0, preds).astype(float)

        # Corregir días de cierre: si la media histórica del DOW es <1 % de la media
        # general, la predicción se escala al valor histórico (evita ~40k en domingos cerrados)
        series_mean = float(self._scaler_mean) if self._scaler_mean > 0 else 1.0
        pred_dates = pd.date_range(
            start=self._last_date + pd.Timedelta(days=1), periods=len(preds)
        )
        for i, d in enumerate(pred_dates):
            dm = self._dow_mean.get(d.dayofweek, series_mean)
            if dm < 0.01 * series_mean:   # día esencialmente cerrado
                preds[i] = dm             # ancla al promedio histórico (~0)

        # Rellenar si horizon > effective_horizon (repite último valor)
        if horizon > n_use:
            preds = np.concatenate([preds, np.full(horizon - n_use, preds[-1])])

        idx = pd.date_range(
            start=self._last_date + pd.Timedelta(days=1), periods=horizon
        )
        return pd.Series(preds, index=idx)
