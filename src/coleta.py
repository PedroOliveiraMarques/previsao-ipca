"""Coleta das séries mensais do Banco Central (SGS) usadas na previsão do IPCA.

Uso:
    python -m src.coleta              # usa o cache em data/raw, se existir
    python -m src.coleta --atualizar  # baixa tudo de novo do SGS
"""
import argparse
from pathlib import Path

import pandas as pd
from bcb import sgs

# Código das séries no SGS (https://www3.bcb.gov.br/sgspub).
SERIES = {
    "ipca": 433,     # IPCA — variação mensal (%)
    "selic": 4390,   # Selic acumulada no mês (%)
    "cambio": 3698,  # Dólar (venda), média mensal (R$/US$)
}
INICIO = "2003-01-01"

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO = RAIZ / "data" / "raw" / "series_bcb.parquet"


def baixar_series(inicio: str = INICIO) -> pd.DataFrame:
    """Baixa as séries do SGS, alinhadas por mês (índice = 1º dia do mês).

    O mês corrente é descartado: a Selic acumulada dele ainda está pela
    metade (ex.: em 14/10 o SGS já devolve outubro só com os dias corridos),
    e um mês incompleto entraria no modelo como se fosse um valor real.
    """
    df = sgs.get(SERIES, start=inicio)
    df.index = pd.DatetimeIndex(df.index, name="data", freq="MS")
    mes_corrente = pd.Timestamp.today().to_period("M").to_timestamp()
    return df[df.index < mes_corrente]


def carregar_series(atualizar: bool = False) -> pd.DataFrame:
    """Séries do cache em data/raw; baixa do SGS se não houver cache ou se
    ``atualizar`` for True."""
    if ARQUIVO.exists() and not atualizar:
        return pd.read_parquet(ARQUIVO).asfreq("MS")
    df = baixar_series()
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ARQUIVO)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--atualizar", action="store_true", help="baixa tudo de novo do SGS")
    args = parser.parse_args()

    df = carregar_series(atualizar=args.atualizar)
    print(f"{len(df)} meses, de {df.index.min():%m/%Y} a {df.index.max():%m/%Y} -> {ARQUIVO}")
    faltando = df.isna().sum()
    if faltando.any():
        print("Valores faltando por série:", faltando[faltando > 0].to_dict())
    print(df.tail())
