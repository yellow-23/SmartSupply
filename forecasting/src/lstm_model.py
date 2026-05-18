import logging
import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Suprimir mensajes de TensorFlow antes de que se importe
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("absl").setLevel(logging.ERROR)


class LSTMModel:
    """
    Red LSTM con dos capas (64 → 32 unidades), Dropout 20% y capa densa
    de salida. Predicción iterativa multi-paso con ventana deslizante.
    """

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self._last_window: np.ndarray | None = None
        self._last_date: pd.Timestamp | None = None

    def build_model(self):
        from tensorflow import keras  # diferido: no falla si TF no está instalado
        model = keras.Sequential([
            keras.layers.Input(shape=(self.window_size, 1)),
            keras.layers.LSTM(64, return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(1),
        ])
        model.compile(optimizer="adam", loss="mse")
        return model

    def fit(self, series: pd.Series, epochs: int = 50):
        values = series.values.astype(float).reshape(-1, 1)
        scaled = self.scaler.fit_transform(values)
        X, y = [], []
        for i in range(self.window_size, len(scaled)):
            X.append(scaled[i - self.window_size:i, 0])
            y.append(scaled[i, 0])
        X_arr = np.array(X).reshape(-1, self.window_size, 1)
        y_arr = np.array(y)
        self.model = self.build_model()
        self.model.fit(X_arr, y_arr, epochs=epochs, batch_size=32, verbose=0)
        self._last_window = scaled[-self.window_size:].flatten()
        self._last_date = pd.to_datetime(series.index[-1])

    def predict(self, horizon: int) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Llama a fit() antes de predict()")
        window = list(self._last_window)
        preds_scaled: list[float] = []
        for _ in range(horizon):
            x = np.array(window[-self.window_size:]).reshape(1, self.window_size, 1)
            val = float(self.model.predict(x, verbose=0)[0, 0])
            preds_scaled.append(val)
            window.append(val)
        preds = self.scaler.inverse_transform(
            np.array(preds_scaled).reshape(-1, 1)
        ).flatten()
        idx = pd.date_range(
            start=self._last_date + pd.Timedelta(days=1), periods=horizon
        )
        return pd.Series(np.maximum(preds, 0), index=idx)
