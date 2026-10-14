# Previsão do IPCA

Previsão da inflação mensal (IPCA) a partir de séries do Banco Central (SGS).

## Etapas

1. **Coleta** (`src/coleta.py`) — IPCA, Selic e câmbio mensais do SGS, desde 2003. ✅
2. **Análise exploratória** (`notebooks/01_eda.ipynb`)
3. **Modelos clássicos de referência** (`notebooks/02_baselines_classicos.ipynb`)
4. **Modelos de ML com backtest** (`notebooks/03_modelos_ml_backtest.ipynb`, `src/features.py`, `src/modelos.py`, `src/avaliacao.py`)
5. **App** (`app.py`)

## Séries usadas

| Coluna | Série SGS | Descrição |
|---|---|---|
| `ipca` | 433 | IPCA — variação mensal (%) |
| `selic` | 4390 | Selic acumulada no mês (%) |
| `cambio` | 3698 | Dólar (venda), média mensal (R$/US$) |

Período: desde jan/2003, com o regime de metas de inflação já consolidado.

## Dados

- **Baixar e usar são etapas separadas.** `src/coleta.py` baixa do SGS uma vez e grava a cópia bruta em
  `data/raw/series_bcb.csv`. Os notebooks e o resto de `src/` só leem essa cópia (`carregar_series()`), sem chamar a API,
  então quem clonar o repositório trabalha com exatamente os mesmos números.
- **Corte no último mês completo das três séries**, descoberto pelo código: a Selic e o câmbio saem no início do mês
  seguinte, mas o IPCA só é divulgado pelo IBGE entre os dias 8 e 11. O mês corrente nunca entra (a Selic dele ainda
  está acumulada só até a data do download).
- **Metadados** em `data/raw/metadados.json`: data do download, período, códigos das séries e versão do `python-bcb`.
- **Formato largo** (uma coluna por série, uma linha por mês): as três séries têm a mesma frequência e o mesmo índice
  mensal, e os modelos usam cada variável como uma coluna (com suas defasagens), então o formato largo já é o que a
  modelagem consome.

## Como rodar

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.coleta   # baixa do SGS e regrava data/raw/ (CSV + metadados)
```
