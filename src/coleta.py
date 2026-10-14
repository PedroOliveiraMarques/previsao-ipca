"""Coleta das séries mensais do Banco Central (SGS) usadas na previsão do IPCA.

Baixar e usar os dados são etapas separadas: este script baixa do SGS e grava
a cópia bruta em data/raw/ (CSV + metadados); os notebooks e o resto de src/
só leem essa cópia com ``carregar_series()``, sem nunca chamar a API. Assim
quem clonar o repositório trabalha exatamente com os mesmos números.

Uso:
    python -m src.coleta    # baixa do SGS e regrava data/raw/
"""
import json
import time
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from bcb import sgs
from bcb.exceptions import SGSError

# Código das séries no SGS (https://www3.bcb.gov.br/sgspub).
SERIES = {
    "ipca": 433,     # IPCA — variação mensal (%)
    "selic": 4390,   # Selic acumulada no mês (%)
    "cambio": 3698,  # Dólar (venda), média mensal (R$/US$)
}
# Início do período: regime de metas de inflação já consolidado.
INICIO = "2003-01-01"
# O SGS às vezes responde 502/503 de forma passageira.
TENTATIVAS = 3
ESPERA_S = 10

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_DADOS = RAIZ / "data" / "raw" / "series_bcb.csv"
ARQUIVO_METADADOS = RAIZ / "data" / "raw" / "metadados.json"


def ultimo_mes_completo(df: pd.DataFrame, hoje: pd.Timestamp | None = None) -> pd.Timestamp:
    """Último mês com valor publicado nas TRÊS séries ao mesmo tempo.

    Cada série tem seu calendário: a Selic e o câmbio de um mês saem logo no
    início do mês seguinte, mas o IBGE só divulga o IPCA entre os dias 8 e 11.
    O corte é o menor entre os últimos meses com valor de cada série. O mês
    corrente nunca entra: o SGS já devolve a Selic dele acumulada só até hoje.
    """
    hoje = hoje or pd.Timestamp.today()
    mes_corrente = hoje.to_period("M").to_timestamp()
    ultimos = df[df.index < mes_corrente].apply(pd.Series.last_valid_index)
    return ultimos.min()


def coleta_series(inicio: str = INICIO) -> pd.DataFrame:
    """Baixa as séries do SGS e devolve o DataFrame (formato largo: uma
    coluna por série, índice = 1º dia do mês) cortado no último mês completo
    das três séries."""
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            df = sgs.get(SERIES, start=inicio)
            break
        except SGSError as erro:
            if tentativa == TENTATIVAS:
                raise
            print(f"SGS falhou ({erro}); nova tentativa em {ESPERA_S} s...")
            time.sleep(ESPERA_S)
    df.index = pd.DatetimeIndex(df.index, name="data")
    df = df.loc[: ultimo_mes_completo(df)].asfreq("MS")
    faltando = df.isna().sum()
    if faltando.any():
        raise ValueError(f"Meses sem valor dentro do período: {faltando[faltando > 0].to_dict()}")
    return df


def salvar(df: pd.DataFrame) -> None:
    """Grava o CSV bruto e os metadados da coleta em data/raw/."""
    ARQUIVO_DADOS.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQUIVO_DADOS, date_format="%Y-%m-%d")
    metadados = {
        "fonte": "Banco Central do Brasil — SGS",
        "series": SERIES,
        "data_download": datetime.now().astimezone().isoformat(timespec="seconds"),
        "periodo_inicio": f"{df.index.min():%Y-%m}",
        "periodo_fim": f"{df.index.max():%Y-%m}",
        "meses": len(df),
        "python_bcb": version("python-bcb"),
    }
    ARQUIVO_METADADOS.write_text(json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def carregar_series() -> pd.DataFrame:
    """Lê a cópia bruta de data/raw/ (não chama a API)."""
    if not ARQUIVO_DADOS.exists():
        raise FileNotFoundError(f"{ARQUIVO_DADOS} não existe — rode `python -m src.coleta` primeiro.")
    df = pd.read_csv(ARQUIVO_DADOS, index_col="data", parse_dates=["data"])
    return df.asfreq("MS")


if __name__ == "__main__":
    df = coleta_series()
    salvar(df)
    print(f"{len(df)} meses, de {df.index.min():%m/%Y} a {df.index.max():%m/%Y}")
    print(f"-> {ARQUIVO_DADOS.relative_to(RAIZ)} e {ARQUIVO_METADADOS.relative_to(RAIZ)}")
    print(df.tail())
