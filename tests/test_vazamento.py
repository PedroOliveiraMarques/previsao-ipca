"""Nenhum modelo pode usar dados posteriores à origem da previsão.

Troca todos os dados depois de uma origem por ruído e confere que as
previsões feitas naquela origem não mudam.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.avaliacao import backtest
from src.coleta import carregar_series
from src.features import macro_defasadas
from src.modelos import BASELINES, CLASSICOS

ORIGEM = pd.Timestamp("2020-06-01")


@pytest.mark.parametrize("nome", list({**BASELINES, **CLASSICOS}))
def test_previsao_nao_depende_do_futuro(nome):
    modelo = {**BASELINES, **CLASSICOS}[nome]
    df = carregar_series()
    alterado = df.copy()
    depois = alterado.index > ORIGEM
    alterado.loc[depois] = np.random.default_rng(0).normal(5, 3, size=(depois.sum(), df.shape[1]))

    def previsoes(dados):
        p = backtest(dados["ipca"], modelo, X=macro_defasadas(dados), primeira_origem=ORIGEM, ultima_origem=ORIGEM)
        return p.loc[p["origem"] == ORIGEM, "previsto"].to_numpy()

    np.testing.assert_allclose(previsoes(df), previsoes(alterado))
