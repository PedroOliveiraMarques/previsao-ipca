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

O mês corrente é descartado na coleta: a Selic dele ainda está incompleta.

## Como rodar

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.coleta              # baixa (ou lê do cache) e salva em data/raw/
.venv/bin/python -m src.coleta --atualizar  # força baixar tudo de novo
```
