"""Backtest com janela expansiva e métricas de erro por horizonte.

Em cada origem t (último mês conhecido), o modelo é treinado com todo o
histórico até t e prevê t+1, ..., t+H. Nada é embaralhado: o teste sempre
vem depois do treino, como numa previsão real.
"""
from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats

HORIZONTE_MAX = 6
HORIZONTES = (1, 3, 6)  # os que o projeto reporta
INICIO_TREINO = "2004-01-01"  # jan–mar/2003 ainda carregam o choque de 2002
PRIMEIRA_ORIGEM = "2014-12-01"  # teste a partir de jan/2015: anos calmos e a alta de 2020–23


def backtest(
    y: pd.Series,
    modelo: Callable,
    X: pd.DataFrame | None = None,
    inicio_treino: str = INICIO_TREINO,
    primeira_origem: str = PRIMEIRA_ORIGEM,
    horizonte: int = HORIZONTE_MAX,
    ultima_origem: str | None = None,
) -> pd.DataFrame:
    """Previsões de ``modelo`` em todas as origens, uma linha por (origem, h).

    Colunas: origem, alvo (mês previsto), h, previsto, real. As origens vão de
    ``primeira_origem`` até o penúltimo mês da série (ou ``ultima_origem``); no
    fim da amostra, os horizontes cujo alvo ainda não aconteceu ficam de fora.
    """
    y = y.loc[inicio_treino:]
    if X is not None:
        X = X.loc[inicio_treino:]
        if X.loc[y.index].isna().any().any():
            raise ValueError("X tem valores faltando no período de treino — ajuste inicio_treino.")
    origens = y.loc[primeira_origem:ultima_origem].index
    origens = origens[origens < y.index[-1]]
    linhas = []
    for origem in origens:
        y_treino = y.loc[:origem]
        futuro = pd.date_range(origem, periods=horizonte + 1, freq="MS")[1:]
        if X is None:
            previsto = modelo(y_treino, horizonte)
        else:
            previsto = modelo(y_treino, horizonte, X.loc[:origem], X.loc[futuro])
        for h, (alvo, valor) in enumerate(zip(futuro, previsto), start=1):
            if alvo in y.index:
                linhas.append((origem, alvo, h, float(valor), float(y.loc[alvo])))
    return pd.DataFrame(linhas, columns=["origem", "alvo", "h", "previsto", "real"])


def rodar_modelos(y, modelos: dict, X=None, **kwargs) -> pd.DataFrame:
    """Backtest de vários modelos; acrescenta as colunas ``modelo`` e ``erro``."""
    partes = []
    for nome, modelo in modelos.items():
        prev = backtest(y, modelo, X=X, **kwargs)
        partes.append(prev.assign(modelo=nome))
    previsoes = pd.concat(partes, ignore_index=True)
    previsoes["erro"] = previsoes["previsto"] - previsoes["real"]
    return previsoes


def metricas(previsoes: pd.DataFrame, por=("modelo", "h")) -> pd.DataFrame:
    """MAE e RMSE (em p.p.) e número de previsões, agrupados por ``por``."""
    return previsoes.groupby(list(por))["erro"].agg(
        MAE=lambda e: e.abs().mean(),
        RMSE=lambda e: np.sqrt((e ** 2).mean()),
        n="size",
    )


def diebold_mariano(erro_a: pd.Series, erro_b: pd.Series, h: int) -> tuple[float, float]:
    """Teste de Diebold-Mariano (com a correção de Harvey, Leybourne e Newbold)
    para perda absoluta. H0: os dois modelos têm o mesmo erro esperado.
    Estatística negativa = A erra menos que B. Devolve (estatística, p-valor
    bicaudal)."""
    d = (erro_a.abs() - erro_b.abs()).to_numpy()
    n = len(d)
    d_media = d.mean()
    # variância de longo prazo com autocovariâncias até h-1 (previsões h passos à frente se sobrepõem)
    gamma = [np.mean((d[k:] - d_media) * (d[: n - k] - d_media)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    if var <= 0:
        return float("nan"), float("nan")
    dm = d_media / np.sqrt(var)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)  # correção HLN para amostras pequenas
    p = 2 * stats.t.sf(abs(dm), df=n - 1)
    return float(dm), float(p)


def comparar_com(previsoes: pd.DataFrame, referencia: str, horizontes=HORIZONTES) -> pd.DataFrame:
    """Para cada modelo e horizonte: MAE relativo à ``referencia`` (< 1 = erra
    menos) e p-valor do Diebold-Mariano contra ela, nos mesmos alvos."""
    largo = previsoes.pivot_table(index=["h", "alvo"], columns="modelo", values="erro")
    linhas = []
    for h in horizontes:
        bloco = largo.loc[h].dropna()
        mae_ref = bloco[referencia].abs().mean()
        for modelo in bloco.columns:
            if modelo == referencia:
                continue
            _, p = diebold_mariano(bloco[modelo], bloco[referencia], h)
            linhas.append({
                "modelo": modelo, "h": h,
                "MAE relativo": bloco[modelo].abs().mean() / mae_ref,
                "p-valor DM": p,
            })
    return pd.DataFrame(linhas).set_index(["modelo", "h"])
