# Previsão do IPCA

Previsão da inflação mensal (IPCA) a partir de séries do Banco Central (SGS).

## Etapas

1. **Coleta** (`src/coleta.py`) — IPCA, Selic e câmbio mensais do SGS, desde 2003. ✅
2. **Análise exploratória** (`notebooks/01_eda.ipynb`) ✅ — figuras em `reports/figures/`
3. **Modelos clássicos de referência** (`notebooks/02_baselines_classicos.ipynb`)
4. **Modelos de ML com backtest** (`notebooks/03_modelos_ml_backtest.ipynb`, `src/features.py`, `src/modelos.py`, `src/avaliacao.py`)
5. **App** (`app.py`)

## Principais achados da análise exploratória

- O IPCA mensal é **estacionário** e tem **memória curta** (autocorrelação de 0,54 em 1 mês, 0,14 em 3), com
  sazonalidade moderada: mais alto de dezembro a março, mais baixo de junho a agosto.
- Selic e câmbio em nível não são estacionários; entram nos modelos como diferença mensal e variação % mensal.
- O câmbio tem correlação com o IPCA de 4 e 7 meses depois (repasse cambial); a Selic, nenhuma relevante. Sinais
  fracos — quem decide se ajudam é a ablação com backtest.
- A volatilidade do IPCA dobrou em 2020–23 em relação a 2009–14: os erros serão reportados também por período.
- Baseline a bater: o ingênuo (repetir o último valor) erra em média 0,24 p.p. em 1 mês e 0,37 p.p. em 6; o
  ingênuo sazonal (mesmo mês do ano anterior), 0,31 p.p.

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

# executa um notebook e grava as saídas e as figuras
cd notebooks && ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb
```
