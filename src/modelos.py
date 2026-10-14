"""Modelos de previsão do IPCA mensal.

Todos seguem a mesma assinatura, usada pelo backtest (src/avaliacao.py):

    modelo(y, h, X=None, X_futuro=None) -> np.ndarray com h previsões

``y`` é o IPCA até a origem (inclusive); ``X``/``X_futuro`` são as variáveis
exógenas no mesmo período de ``y`` e nos h meses seguintes (já defasadas, ver
src/features.py — não há valor futuro desconhecido nelas).
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX


# ── Baselines ────────────────────────────────────────────────────────────────
def ingenuo(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """Repete o último valor observado."""
    return np.repeat(y.iloc[-1], h)


def ingenuo_sazonal(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """Repete o valor do mesmo mês do ano anterior (vale para h <= 12)."""
    return y.iloc[-12:].to_numpy()[:h]


def media_historica(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """Média de todo o histórico de treino."""
    return np.repeat(y.mean(), h)


# ── Modelos clássicos ────────────────────────────────────────────────────────
def ets(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """ETS(A,N,A): erro e sazonalidade aditivos, sem tendência — a EDA mostrou
    um IPCA estacionário com sazonalidade de 12 meses. Aditivo porque o IPCA
    tem valores negativos (deflação)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        ajuste = ExponentialSmoothing(
            y, trend=None, seasonal="add", seasonal_periods=12, initialization_method="estimated"
        ).fit()
    return ajuste.forecast(h).to_numpy()


def _sarimax(y, h, X=None, X_futuro=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)  # avisos de chute inicial dos parâmetros
        ajuste = SARIMAX(
            y, exog=X, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12), trend="c"
        ).fit(disp=False)
    return ajuste.forecast(h, exog=X_futuro).to_numpy()


def sarima(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """SARIMA(1,0,0)(1,0,0)12 com constante: AR(1) + AR sazonal, como
    sugerem a ACF/PACF da EDA. Sem variáveis exógenas."""
    return _sarimax(y, h)


def sarimax(y: pd.Series, h: int, X=None, X_futuro=None) -> np.ndarray:
    """Mesmo SARIMA com Selic e câmbio (defasados) como regressores."""
    return _sarimax(y, h, X, X_futuro)


BASELINES = {"Ingênuo": ingenuo, "Ingênuo sazonal": ingenuo_sazonal, "Média histórica": media_historica}
CLASSICOS = {"ETS(A,N,A)": ets, "SARIMA": sarima, "SARIMAX (Selic + câmbio)": sarimax}
