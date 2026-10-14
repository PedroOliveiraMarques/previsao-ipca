"""Transformações das séries para a modelagem.

A EDA (notebook 01) mostrou que o IPCA mensal é estacionário, mas a Selic e o
câmbio em nível não são: eles entram nos modelos como diferença mensal e
variação percentual mensal.
"""
import pandas as pd

# Defasagem mínima das variáveis macro: para prever t+h a partir da origem t,
# só podem entrar valores até t. Com h até 6, a defasagem precisa ser >= 6.
DEFASAGEM_MACRO = 6


def macro_estacionarias(df: pd.DataFrame) -> pd.DataFrame:
    """Selic em diferença mensal (p.p.) e câmbio em variação % mensal."""
    return pd.DataFrame({
        "selic_dif": df["selic"].diff(),
        "cambio_var": df["cambio"].pct_change() * 100,
    })


def macro_defasadas(df: pd.DataFrame, defasagem: int = DEFASAGEM_MACRO) -> pd.DataFrame:
    """Variáveis macro estacionárias defasadas: a linha do mês m traz os
    valores de m - ``defasagem``. Assim, prever qualquer mês até
    ``defasagem`` meses à frente usa só dados já publicados na origem. O
    índice vai ``defasagem`` meses além do fim dos dados: esses meses futuros
    já têm valor conhecido (vêm do passado)."""
    macro = macro_estacionarias(df)
    indice = pd.date_range(macro.index[0], periods=len(macro) + defasagem, freq="MS", name=macro.index.name)
    return macro.reindex(indice).shift(defasagem).add_suffix(f"_l{defasagem}")
