import numpy as np
import pandas as pd
from tensorflow import keras


class LSTMModel:
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.model = None
        self.scaler = None

    def build_model(self):
        # TODO: 2 capas LSTM (64 y 32 unidades) + dropout 20% + capa densa de salida
        pass

    def fit(self, series: pd.Series, epochs: int = 50):
        # TODO: normalizar con MinMaxScaler, crear ventanas deslizantes, entrenar
        pass

    def predict(self, horizon: int) -> pd.Series:
        # TODO: predicción con ventana deslizante para los próximos `horizon` días
        pass
