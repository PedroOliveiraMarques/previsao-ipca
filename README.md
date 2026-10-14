# Previsão do IPCA

Previsão da inflação mensal (IPCA) a partir de séries do Banco Central (SGS).

## Etapas

1. **Coleta** (`src/coleta.py`) — IPCA, Selic e câmbio mensais do SGS, desde 2003. ✅
2. **Análise exploratória** (`notebooks/01_eda.ipynb`) ✅ — figuras em `reports/figures/`
3. **Backtest, baselines e modelos clássicos** (`notebooks/02_baselines_classicos.ipynb`, `src/avaliacao.py`, `src/modelos.py`) ✅
4. **Modelos de ML e ablação** (`notebooks/03_modelos_ml_backtest.ipynb`)
5. **App** (`app.py`)

## Resultados até agora (backtest jan/2015 a set/2026)

Janela expansiva com 141 origens; em cada uma o modelo treina com todo o passado e prevê 1 a 6 meses à frente.
MAE em pontos percentuais:

| Modelo | 1 mês | 3 meses | 6 meses |
|---|---|---|---|
| Ingênuo (repete o último valor) | 0,293 | 0,389 | 0,411 |
| Ingênuo sazonal | 0,382 | 0,379 | 0,382 |
| Média histórica | 0,315 | 0,310 | 0,308 |
| ETS(A,N,A) | 0,263 | 0,314 | 0,321 |
| **SARIMA(1,0,0)(1,0,0)₁₂** | **0,257** | **0,285** | **0,300** |
| SARIMAX (+ Selic e câmbio) | 0,257 | 0,290 | 0,304 |

- O SARIMA bate o ingênuo em todos os horizontes (−12% em 1 mês, −27% em 3 e 6; Diebold-Mariano p < 0,01).
- Em 3 e 6 meses, o baseline mais difícil é a média histórica: o SARIMA a bate em 3 meses (−8%, p = 0,02), mas
  não em 6 (−2%, p = 0,40).
- Selic e câmbio, defasados em 6 meses para não haver vazamento, não melhoraram o SARIMA.

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

# testes (inclui o de vazamento: nenhum modelo pode usar dados posteriores à origem)
.venv/bin/python -m pytest -q tests
```
